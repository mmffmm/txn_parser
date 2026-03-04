import pdfplumber
import pandas as pd
import re
import shutil
import os

# Separator config
COLUMN_SEPARATOR = '|'
ROW_SEPARATOR = ';'

# Configuration constants
PROCESSED_PDF_DIR = 'transaction_PDF/processed_PDF'

DEFAULT_ENCODING = 'utf-8'
EXPECTED_COLUMN_COUNT = 4
MAX_DESCRIPTION_ROWS = 4

DATE_COLUMN_INDEX = 0
DESCRIPTION_COLUMN_INDEX = 1
AMOUNT_COLUMN_INDEX = 2
BALANCE_COLUMN_INDEX = 3

# PDF table extraction settings
TABLE_EXTRACTION_SETTINGS = {
    "vertical_strategy": "explicit",
    "horizontal_strategy": "explicit",
    "explicit_horizontal_lines": [
        217.05, 221.65, 229.65, 233.65, 241.65,
        245.65, 253.65, 257.65, 265.65, 269.65, 277.65, 281.65, 289.65, 293.65, 301.65,
        305.65, 313.65, 317.65, 325.65, 329.65, 337.65, 341.65, 349.65, 353.65, 361.65,
        365.65, 373.65, 377.65, 385.65, 389.65, 397.65, 401.65, 409.65, 413.65, 421.65,
        425.65, 433.65, 437.65, 445.65, 449.65, 457.65, 461.65, 469.65, 473.65, 481.65,
        485.65, 493.65, 497.65, 505.65, 509.65, 517.65, 521.65, 529.65, 533.65, 541.65,
        545.65, 553.65, 557.65, 565.65, 569.65, 577.65, 581.65, 589.65, 593.65, 601.65,
        605.65, 613.65, 617.65, 625.65, 629.65, 637.65, 641.65, 649.65, 653.65, 661.65,
        665.65, 673.65, 677.65, 685.65, 689.65, 697.65, 701.65, 723.26
    ],
    "explicit_vertical_lines": [40, 80, 310, 400, 500],
}

# MAIN FUNCTIONS

def read_pdf(list_of_pdf):
    all_data = []
    success_processed_pdf = []

    for pdf_file in list_of_pdf:
        current_record = None

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables(TABLE_EXTRACTION_SETTINGS)
                for table in tables:
                    if not table:
                        continue
                    for row in table:
                        if not row:
                            continue
                        col_b = row[DATE_COLUMN_INDEX].strip() if len(row) > 1 and row[DATE_COLUMN_INDEX] else ''
                        if not col_b:
                            if current_record is not None:
                                _merge_description_value_in_diff_rows(current_record, row)
                        
                        elif _is_valid_transfer_date_row(row):    
                            # flush previous record and start a new one
                            if current_record is not None:
                                all_data.append(current_record)
                            current_record = row

                        else:
                            # flush and stop — not a transaction row
                            if current_record is not None:
                                all_data.append(current_record)
                                current_record = None

        # Flush the last accumulated record
        if current_record is not None:
            all_data.append(current_record)
        
        # If success
        success_processed_pdf.append(pdf_file)

    df = pd.DataFrame(all_data)
    if not df.empty:
        return df, success_processed_pdf
    else:
        print("No data found.")
        return df, success_processed_pdf

# UTIL FUNCTIONS

def _is_valid_transfer_date_row(row):
    date = row[DATE_COLUMN_INDEX].strip() if row[DATE_COLUMN_INDEX] else ''
    return re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', date)

def _merge_description_value_in_diff_rows(current_record, row):
    continuation_desc = row[DESCRIPTION_COLUMN_INDEX]
    if continuation_desc:
        if current_record[DESCRIPTION_COLUMN_INDEX]:
            existing_separators = current_record[DESCRIPTION_COLUMN_INDEX].count(ROW_SEPARATOR)
            if existing_separators < MAX_DESCRIPTION_ROWS - 1:
                current_record[DESCRIPTION_COLUMN_INDEX] = (
                    current_record[DESCRIPTION_COLUMN_INDEX] + ROW_SEPARATOR + continuation_desc
                ).strip()
        else:
            current_record[DESCRIPTION_COLUMN_INDEX] = continuation_desc

def move_to_processed_pdf_dir(list_of_pdf, csv_filename):

    folder_name = os.path.splitext(csv_filename)[0]
    target_dir = os.path.join(PROCESSED_PDF_DIR, folder_name)
    os.makedirs(target_dir, exist_ok=True)

    moved_files = []

    for pdf in list_of_pdf:
        try:
            shutil.move(pdf, target_dir)
            moved_files.append(pdf)
            print(f"Moved: {pdf}")
        except FileNotFoundError:
            print(f"Error: File not found — {pdf}")
        except Exception as e:
            print(f"Error moving '{pdf}': {e}")
    
    return moved_files

# TEST FUNCTIONS
 
def test_transfer_to_csv(list_of_pdf, target_csv_path):
    all_data = []

    for pdf_file in list_of_pdf:
        current_record = None

        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables(TABLE_EXTRACTION_SETTINGS)
                for table in tables:
                    if not table:
                        continue
                    for row in table:
                        if not row:
                            continue
                        col_b = row[DATE_COLUMN_INDEX].strip() if len(row) > 1 and row[DATE_COLUMN_INDEX] else ''
                        if not col_b:
                            if current_record is not None:
                                _merge_description_value_in_diff_rows(current_record, row)
                        
                        elif _is_valid_transfer_date_row(row):    
                            # flush previous record and start a new one
                            if current_record is not None:
                                all_data.append(current_record)
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
        df.to_csv(target_csv_path, index=False, encoding=DEFAULT_ENCODING)
        print("CSV saved successfully!")
    else:
        print("No tables found.")