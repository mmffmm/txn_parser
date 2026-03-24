import re
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_FILES, UPLOAD_DIR
from app.models import StatementUpload, Transaction, User
from src.etl.loadDB import parse_amount, parse_balance, parse_date, parse_description
from src.etl.readPdf import read_pdf


def ensure_storage_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(filename: str) -> str:
    cleaned_name = re.sub(r"[^A-Za-z0-9._-]+", "_", filename).strip("._")
    return cleaned_name or f"statement_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"


def _serialize_decimal(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _serialize_transaction(transaction: Transaction) -> dict:
    return {
        "id": transaction.id,
        "upload_id": transaction.upload_id,
        "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
        "description": transaction.description,
        "amount": _serialize_decimal(transaction.amount),
        "transaction_type": transaction.transaction_type,
        "balance": _serialize_decimal(transaction.balance),
    }


def _serialize_upload(upload: StatementUpload) -> dict:
    return {
        "id": upload.id,
        "original_filename": upload.original_filename,
        "status": upload.status,
        "transaction_count": upload.transaction_count,
        "created_at": upload.created_at.isoformat(),
    }


def _dataframe_to_transactions(dataframe) -> list[dict]:
    transactions: list[dict] = []
    if dataframe.empty:
        return transactions

    for _, row in dataframe.iterrows():
        raw_date = row.get(0, "")
        raw_description = row.get(1, "")
        raw_amount = row.get(2, "")
        raw_balance = row.get(3, "")

        amount, transaction_type = parse_amount(raw_amount)
        transactions.append(
            {
                "transaction_date": parse_date(raw_date),
                "description": parse_description(raw_description),
                "amount": amount,
                "transaction_type": transaction_type,
                "balance": parse_balance(raw_balance),
            }
        )

    return transactions


def _validate_uploads(files: list[UploadFile]) -> None:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload at least one PDF file.")
    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You can upload up to {MAX_UPLOAD_FILES} files at once.",
        )

    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type for '{upload.filename}'. Only PDF files are allowed.",
            )


def process_uploaded_files(db: Session, user: User, files: list[UploadFile]) -> list[dict]:
    _validate_uploads(files)
    processed_results: list[dict] = []

    for uploaded_file in files:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        safe_filename = _safe_filename(uploaded_file.filename or "statement.pdf")
        user_directory = UPLOAD_DIR / f"user_{user.id}"
        user_directory.mkdir(parents=True, exist_ok=True)
        destination = user_directory / f"{timestamp}_{safe_filename}"

        with destination.open("wb") as file_handle:
            shutil.copyfileobj(uploaded_file.file, file_handle)

        upload_record = StatementUpload(
            user_id=user.id,
            original_filename=uploaded_file.filename or safe_filename,
            stored_filename=destination.name,
            stored_path=str(destination),
            status="processing",
            transaction_count=0,
        )
        db.add(upload_record)
        db.commit()
        db.refresh(upload_record)

        try:
            dataframe, _ = read_pdf([str(destination)])
            normalized_transactions = _dataframe_to_transactions(dataframe)

            for transaction in normalized_transactions:
                db.add(
                    Transaction(
                        user_id=user.id,
                        upload_id=upload_record.id,
                        transaction_date=transaction["transaction_date"],
                        description=transaction["description"],
                        amount=transaction["amount"],
                        transaction_type=transaction["transaction_type"],
                        balance=transaction["balance"],
                    )
                )

            upload_record.status = "processed" if normalized_transactions else "empty"
            upload_record.transaction_count = len(normalized_transactions)
            db.add(upload_record)
            db.commit()
            processed_results.append(
                {
                    **_serialize_upload(upload_record),
                    "message": f"Imported {len(normalized_transactions)} transactions.",
                }
            )
        except Exception as exc:
            db.rollback()
            upload_record = db.get(StatementUpload, upload_record.id)
            if upload_record is not None:
                upload_record.status = "failed"
                db.add(upload_record)
                db.commit()

            processed_results.append(
                {
                    "id": upload_record.id if upload_record is not None else None,
                    "original_filename": uploaded_file.filename,
                    "status": "failed",
                    "transaction_count": 0,
                    "created_at": datetime.utcnow().isoformat(),
                    "message": str(exc),
                }
            )

    return processed_results


def get_dashboard_data(db: Session, user_id: int) -> dict:
    debit_case = case((Transaction.transaction_type == "DEBIT", Transaction.amount), else_=0)
    credit_case = case((Transaction.transaction_type == "CREDIT", Transaction.amount), else_=0)

    transaction_count = db.execute(
        select(func.count(Transaction.id)).where(Transaction.user_id == user_id)
    ).scalar_one()
    upload_count = db.execute(
        select(func.count(StatementUpload.id)).where(StatementUpload.user_id == user_id)
    ).scalar_one()
    total_debits = db.execute(
        select(func.coalesce(func.sum(debit_case), 0)).where(Transaction.user_id == user_id)
    ).scalar_one()
    total_credits = db.execute(
        select(func.coalesce(func.sum(credit_case), 0)).where(Transaction.user_id == user_id)
    ).scalar_one()
    latest_balance = db.execute(
        select(Transaction.balance)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.transaction_date), desc(Transaction.id))
        .limit(1)
    ).scalar_one_or_none()

    return {
        "transaction_count": int(transaction_count or 0),
        "upload_count": int(upload_count or 0),
        "total_debits": _serialize_decimal(total_debits),
        "total_credits": _serialize_decimal(total_credits),
        "net_cashflow": _serialize_decimal((total_credits or 0) - (total_debits or 0)),
        "latest_balance": _serialize_decimal(latest_balance),
    }


def get_recent_transactions(db: Session, user_id: int, limit: int = 100) -> list[dict]:
    transactions = db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.transaction_date), desc(Transaction.id))
        .limit(limit)
    ).scalars().all()
    return [_serialize_transaction(transaction) for transaction in transactions]


def get_recent_uploads(db: Session, user_id: int, limit: int = 10) -> list[dict]:
    uploads = db.execute(
        select(StatementUpload)
        .where(StatementUpload.user_id == user_id)
        .order_by(desc(StatementUpload.created_at))
        .limit(limit)
    ).scalars().all()
    return [_serialize_upload(upload) for upload in uploads]
