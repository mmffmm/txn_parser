import os
from dotenv import load_dotenv
from readPdf import transfer_to_table

load_dotenv()
path_to_pdf = os.getenv("TRANSACTION_PDF_PATH") # PDF name might have personal infos
if not os.path.isfile(path_to_pdf):
    raise SystemExit(f"PDF not found: {path_to_pdf}")

transfer_to_table(path_to_pdf)