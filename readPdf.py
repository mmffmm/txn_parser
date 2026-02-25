import pdfplumber
import pandas as pd
import re

def transfer_to_table(path_to_pdf):
    all_data = []
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
                    if not row or len(row) < 2:
                        continue
                    # first: day number (1-2 digits), second: optional leading '/' then MM/YY
                    if is_valid_transfer_date_row(row):
                        print("The row:  ", row)

                        # Fix overflow: a digit leaked into index 8 instead of staying with the amount at index 9
                        normalize_transfer_value_column_overflow(row)

                        # Fix short row: pad with '' before the 3rd last place so amount lands at index 9
                        normalize_transfer_row_padding(row)

                        print("Fixed row:", row)
                        all_data.append(row)

    if all_data:
        transfer_to_csv(all_data)
        print("CSV saved successfully!")
    else:
        print("No tables found.")

def is_valid_transfer_date_row(row):
    if len(row) < 2:
        return False

    first = row[0].strip() if row[0] else ''
    second = row[1].strip() if row[1] else ''

    return (
        re.match(r'^\d{1,2}$', first) and
        re.match(r'^/?\d{2}/\d{2}$', second)
    )

def normalize_transfer_value_column_overflow(row):
    if len(row) >= 4 and row[-4]:
        row[-3] = row[-4] + row[-3]
        row[-4] = ''

def normalize_transfer_row_padding(row):
    if len(row) < 12:
        missing = 12 - len(row)
        for _ in range(missing):
            row.insert(len(row) - 3, '')

def transfer_to_csv(all_data):
    targetPath = "target_CSV/transfer_log.csv"
    df = pd.DataFrame(all_data)
    df.to_csv(targetPath, index=False, encoding='utf-8')



    
