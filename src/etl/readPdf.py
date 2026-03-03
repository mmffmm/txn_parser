import pdfplumber
import pandas as pd
import re

COLUMN_SEPARATOR = '|'
ROW_SEPARATOR = ';'

# Main Function

    # DATE COLUMN consists of column 1 and 2, will be combined into column 2
    # DESCRIPTION COLUMN consists of column 3 onwards and rows below, will be combined into column 3
    # TOTAL BALANCE AND TRANSACTION COLUMNS is on the last 3 columns
    # TOTAL NUMBER OF COLUMNS in csv should be set to 12 only

    # Merging Description Column MUST RUN AFTER normalizing transaction date, because transaction got overflow

def transfer_to_csv(list_of_pdf, target_csv_path):

    all_data = []

    for pdf_file in list_of_pdf:
        
        current_record = None

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # print("Page Number: ", page.page_number)

                table_settings = {
                    "vertical_strategy": "explicit",
                    "horizontal_strategy": "text",
                    "explicit_vertical_lines": [43.4, 50.578, 74.958, 95.168, 214.42, 235.0, 325.28, 365.66, 371.12, 422.87, 445.65, 485.65]
                }   
                tables = page.extract_tables(table_settings)

                for table in tables:
                    if not table:
                        continue

                    # iterate rows skipping header row (assume first row is header)
                    for row in table[1:]:
                        if not row:
                            continue

                        col_b = row[1].strip() if len(row) > 1 and row[1] else ''
                        if not col_b:
                            if current_record is not None:
                                merge_description_value_in_diff_rows(current_record, row)
                        
                        elif is_valid_transfer_date_row(row):    
                            # flush previous record and start a new one
                            if current_record is not None:
                                all_data.append(current_record)

                            normalize_date_column_overflow(row)
                            normalize_transfer_value_column_overflow(row)
                            merge_description_value_in_diff_columns(row)

                            normalize_total_columns(row)

                            current_record = row

                        else:
                            # flush and stop — not a transaction row
                            if current_record is not None:
                                all_data.append(current_record)
                                current_record = None

        # Flush the last accumulated record
        if current_record is not None:
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

def normalize_total_columns(row):
    if len(row) < 12:
        missing = 12 - len(row)
        for _ in range(missing):
            row.insert(len(row) - 3, '')
    elif len(row) >12:
        extra = len(row) - 12
        for _ in range(extra):
            row.pop(3)


# Test functions
 
def test_transfer_to_csv(list_of_pdf, target_csv_path):

    all_data = []

    for pdf_file in list_of_pdf:
        
        current_record = None

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                # print("Page Number: ", page.page_number)
                table_settings = {
                    "vertical_strategy": "explicit",
                    "horizontal_strategy": "text",
                    # "explicit_vertical_lines": [43.4, 214.42, 235.0, 325.28, 371.12, 422.87, 445.65],
                    "explicit_vertical_lines": [43.4, 50.578, 74.958, 95.168, 214.42, 235.0, 325.28, 365.66, 371.12, 422.87, 445.65, 485.65]
                }   

                tables = page.extract_tables(table_settings)

                for table in tables:
                    if not table:
                        continue

                    # iterate rows skipping header row (assume first row is header)
                    for row in table[1:]:
                        if not row:
                            continue

                        all_data.append(row)
                        continue

                        col_b = row[1].strip() if len(row) > 1 and row[1] else ''
                        if not col_b:
                            if current_record is not None:
                                merge_description_value_in_diff_rows(current_record, row)
                        
                        elif is_valid_transfer_date_row(row):    
                            # flush previous record and start a new one
                            if current_record is not None:
                                all_data.append(current_record)

                            normalize_date_column_overflow(row)
                            normalize_transfer_value_column_overflow(row)
                            merge_description_value_in_diff_columns(row)

                            normalize_total_columns(row)

                            current_record = row

                        else:
                            # flush and stop — not a transaction row
                            if current_record is not None:
                                all_data.append(current_record)
                                current_record = None

        # Flush the last accumulated record
        if current_record is not None:
            all_data.append(current_record)

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv(target_csv_path, index=False, encoding='utf-8')
        print("CSV saved successfully!")
    else:
        print("No tables found.")
