import os
import sys
from pathlib import Path
from src import config as c
from src.etl import readPdf as pdf, loadDB as db, csvHandler as csv

TEST = False

path_to_pdf_folder = c.TEST_INPUT_PDF_DIR if TEST else c.INPUT_PDF_DIR

list_of_pdf = [str(Path(path_to_pdf_folder) / f).replace("\\", "/") 
               for f in os.listdir(path_to_pdf_folder) if f.endswith(".pdf")]

if TEST:
    pdf.test_transfer_to_csv(list_of_pdf, c.OUTPUT_CSV_DIR)
    # db.load_to_db(c.OUTPUT_CSV_DIR)
else:
    df, success_processed_pdf = pdf.read_pdf(list_of_pdf)
    if df.empty:
        print("No data to write; exiting.")
        sys.exit(0)
    
    csv_filepath, csv_filename = csv.save_to_csv(df, c.OUTPUT_CSV_DIR)
    if csv_filepath is None:
        print("Failed to save CSV.")
        sys.exit(1)

    load_db = db.load_to_db(csv_filepath)
    if not load_db:
        print("Failed to load to DB.")
        sys.exit(1)

    csv.move_to_processed_csv_dir(csv_filepath)
    pdf.move_to_processed_pdf_dir(success_processed_pdf, csv_filename)


    
