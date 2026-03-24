import argparse
import os
import sys
from pathlib import Path

import uvicorn

from app.config import HOST, PORT
from src import config as c
from src.etl import csvHandler as csv
from src.etl import loadDB as db
from src.etl import readPdf as pdf


def run_legacy_etl(test_mode: bool = False) -> int:
    path_to_pdf_folder = c.TEST_INPUT_PDF_DIR if test_mode else c.INPUT_PDF_DIR
    list_of_pdf = [
        str(Path(path_to_pdf_folder) / filename).replace("\\", "/")
        for filename in os.listdir(path_to_pdf_folder)
        if filename.endswith(".pdf")
    ]

    if test_mode:
        pdf.test_transfer_to_csv(list_of_pdf, c.OUTPUT_CSV_DIR)
        return 0

    dataframe, success_processed_pdf = pdf.read_pdf(list_of_pdf)
    if dataframe.empty:
        print("No data to write; exiting.")
        return 0

    csv_filepath, csv_filename = csv.save_to_csv(dataframe, c.OUTPUT_CSV_DIR)
    if csv_filepath is None:
        print("Failed to save CSV.")
        return 1

    load_db = db.load_to_db(csv_filepath)
    if not load_db:
        print("Failed to load to DB.")
        return 1

    csv.move_to_processed_csv_dir(csv_filepath)
    pdf.move_to_processed_pdf_dir(success_processed_pdf, csv_filename)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Bank statement parser")
    parser.add_argument("--mode", choices=["web", "etl"], default="web")
    parser.add_argument("--test", action="store_true", help="Run the legacy ETL test mode.")
    parser.add_argument("--reload", action="store_true", help="Enable auto reload for the web server.")
    args = parser.parse_args()

    if args.mode == "etl":
        return run_legacy_etl(test_mode=args.test)

    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=args.reload)
    return 0


if __name__ == "__main__":
    sys.exit(main())


    
