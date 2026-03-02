import os
from dotenv import load_dotenv
from src.etl.readPdf import transfer_to_csv
from src.etl.loadDB import load_to_db

load_dotenv()
path_to_pdf = os.getenv("TRANSACTION_PDF_PATH") # PDF name might have personal infos
path_to_csv = "target_CSV/transfer_log.csv"

if not os.path.isfile(path_to_pdf):
    raise SystemExit(f"PDF not found: {path_to_pdf}")

transfer_to_csv(path_to_pdf, path_to_csv)
load_to_db(path_to_csv)