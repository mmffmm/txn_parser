import shutil
import os
from datetime import datetime

PROCESSED_CSV_DIR = 'transaction_CSV/processed_CSV'
DEFAULT_ENCODING = 'utf-8'
FILENAME_PREFIX = 'transaction_log'

def save_to_csv(df, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    try:
        filename = _generate_csv_filename(FILENAME_PREFIX)
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, index=False, encoding=DEFAULT_ENCODING)
        return filepath, filename
    except Exception as e:
        print (f"Fail to save csv.")
        return None, None

def _generate_csv_filename(prefix):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{timestamp}.csv"

def move_to_processed_csv_dir(csv_filepath):
    os.makedirs(PROCESSED_CSV_DIR, exist_ok=True)
    try:
        shutil.move(csv_filepath, PROCESSED_CSV_DIR)
        print(f"Moved: {csv_filepath}")
    except FileNotFoundError:
        print(f"Error: File not found - {csv_filepath}")
    except Exception as e:
        print(f"Error moving '{csv_filepath}': {e}")
