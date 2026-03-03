import os
from pathlib import Path
from src.etl.readPdf import transfer_to_csv, test_transfer_to_csv
from src.etl.loadDB import load_to_db

TEST = False

path_to_csv = "target_CSV/transfer_log.csv"
path_to_pdf_folder = "test/transpdf_test" if TEST else "transaction_PDF"
list_of_pdf = [str(Path(path_to_pdf_folder) / f).replace("\\", "/") 
               for f in os.listdir(path_to_pdf_folder) if f.endswith(".pdf")]

if TEST:
    test_transfer_to_csv(list_of_pdf, path_to_csv)
    load_to_db(path_to_csv)
else:
    transfer_to_csv(list_of_pdf, path_to_csv)
    load_to_db(path_to_csv)
