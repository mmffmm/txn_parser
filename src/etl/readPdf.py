import pdfplumber
import pandas as pd
import re

COLUMN_SEPARATOR = '|'
ROW_SEPARATOR = ';'

# Main Function

def transfer_to_csv(path_to_pdf, target_csv_path):
    all_data = []
    current_record = None
    with pdfplumber.open(path_to_pdf) as pdf:
        for page in pdf.pages:
            print("Page Number: ", page.page_number)

            tables = page.extract_tables({
                "vertical_strategy": "text",
                "horizontal_strategy": "text"
            })
            for table in tables:
                if not table:
                    continue
                # iterate rows skipping header row (assume first row is header)
                for row in table[1:]:
                    if not row:
                        continue

                    col_b = row[1].strip() if len(row) > 1 and row[1] else ''

                    if not col_b:
                        # Column B is empty: continuation row, merge description into current record
                        if current_record is not None:
                            merge_description_value_in_diff_rows(current_record, row)

                    elif is_valid_transfer_date_row(row):
                        # Column B is a date: flush previous record and start a new one
                        if current_record is not None:
                            print("Fixed row:", current_record)
                            all_data.append(current_record)

                        print("The row:  ", row)
                        normalize_date_column_overflow(row)
                        normalize_transfer_value_column_overflow(row)
                        normalize_transfer_row_padding(row)
                        merge_description_value_in_diff_columns(row)
                        current_record = row

                    else:
                        # Column B has a value but is NOT a date: flush and stop — not a transaction row
                        if current_record is not None:
                            print("Fixed row:", current_record)
                            all_data.append(current_record)
                            current_record = None

    # Flush the last accumulated record
    if current_record is not None:
        print("Fixed row:", current_record)
        all_data.append(current_record)

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(target_csv_path, index=False, encoding='utf-8')
        print("CSV saved successfully!")
    else:
        print("No tables found.")

# Util Functions

def merge_description_value_in_diff_rows(current_record, row):
    """Merge continuation row: join cols before amount cols, then '|', then join amount cols."""
    # check the columns value first

    merge_description_value_in_diff_columns(row)
    continuation_desc = row[2]
    if continuation_desc:
        if current_record[2]:
            current_record[2] = (
                current_record[2] + ROW_SEPARATOR + continuation_desc
            ).strip()
        else:
            current_record[2] = continuation_desc

def merge_description_value_in_diff_columns(row):
    desc_part = row[2:-3]

    merged_desc = COLUMN_SEPARATOR.join(
        v.strip() for v in desc_part if v and v.strip()
    )

    # clear description columns
    for i in range(2, len(row) - 3):
        row[i] = ''

    # put merged value into first description column
    if len(row) > 5:   # make sure structure valid
        row[2] = merged_desc

def is_valid_transfer_date_row(row):
    if len(row) < 2:
        return False

    first = row[0].strip() if row[0] else ''
    second = row[1].strip() if row[1] else ''

    return (
        re.match(r'^\d{1,2}$', first) and
        re.match(r'^/?\d{2}/\d{2}$', second)
    )

def normalize_date_column_overflow(row):
    if row[0]:
        row[1] = row[0] + row[1]
        row[0] = ''

def normalize_transfer_value_column_overflow(row):
    if len(row) >= 4 and row[-4]:
        row[-3] = row[-4] + row[-3]
        row[-4] = ''

def normalize_transfer_row_padding(row):
    if len(row) < 12:
        missing = 12 - len(row)
        for _ in range(missing):
            row.insert(len(row) - 3, '')
