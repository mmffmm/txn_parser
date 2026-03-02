import os
import re
import pandas as pd
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DEBIT = 'Debit'
CREDIT = 'Credit'

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


def parse_description(row):
    """Join cols 2-8 into a single description string."""
    parts = [str(row[str(i)]).strip() for i in range(2, 9) if str(row[str(i)]).strip()]
    return ' '.join(parts)


def load_to_db(csv_path):
    df = pd.read_csv(csv_path, header=0, dtype=str).fillna('')

    records = []
    for _, row in df.iterrows():
        transaction_date = parse_date(row['1'])
        description = parse_description(row)
        amount, transaction_type = parse_amount(row['9'])
        balance = parse_balance(row['11'])
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
    finally:
        conn.close()
