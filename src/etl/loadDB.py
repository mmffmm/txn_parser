import os
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from .readPdf import DATE_COLUMN_INDEX, DESCRIPTION_COLUMN_INDEX, AMOUNT_COLUMN_INDEX, BALANCE_COLUMN_INDEX

DEBIT = 'Debit'
CREDIT = 'Credit'

# convert to strings if df.columns are strings
DATE_COLUMN_INDEX_STR = str(DATE_COLUMN_INDEX)
DESCRIPTION_COLUMN_INDEX_STR = str(DESCRIPTION_COLUMN_INDEX)
AMOUNT_COLUMN_INDEX_STR = str(AMOUNT_COLUMN_INDEX)
BALANCE_COLUMN_INDEX_STR = str(BALANCE_COLUMN_INDEX)

load_dotenv()

def parse_amount(raw: str):
    """Return (amount: float, transaction_type: str) from strings like '36.55-' or '40.00+'."""
    if not raw:
        return None, None
    raw = raw.strip().replace(',', '')
    if raw.endswith('-'):
        return float(raw[:-1]), DEBIT
    elif raw.endswith('+'):
        return float(raw[:-1]), CREDIT
    # fallback: treat bare number as credit
    try:
        return float(raw), CREDIT
    except ValueError:
        return None, None


def parse_balance(raw: str):
    """Return balance as float from strings like '13,228.17'."""
    if not raw:
        return None
    try:
        return float(raw.strip().replace(',', ''))
    except ValueError:
        return None


def parse_date(date_col: str):
    """Parse full date string from column 1, e.g. '02/01/26'."""
    try:
        return datetime.strptime(date_col.strip(), '%d/%m/%y').date()
    except (ValueError, AttributeError):
        return None


def parse_description(value):
    """Return the description string from the passed value."""
    return str(value).strip() if value else ''


def load_to_db(csv_path):
    df = pd.read_csv(csv_path, header=0, dtype=str).fillna('')

    records = []
    for _, row in df.iterrows():
        transaction_date = parse_date(row[DATE_COLUMN_INDEX_STR])
        description = parse_description(row[DESCRIPTION_COLUMN_INDEX_STR])
        amount, transaction_type = parse_amount(row[AMOUNT_COLUMN_INDEX_STR])
        balance = parse_balance(row[BALANCE_COLUMN_INDEX_STR])
        records.append((transaction_date, description, amount, transaction_type, balance))

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )

    try:
        with conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO transactions
                        (transaction_date, description, amount, transaction_type, balance)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    records,
                )
        print(f"Loaded {len(records)} rows into 'transactions' table.")
        return True
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        return False
    except psycopg2.IntegrityError as e:
        print(f"Data integrity error (duplicate or constraint violation): {e}")
        return False
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error while loading to DB: {e}")
        return False
    finally:
        conn.close()
