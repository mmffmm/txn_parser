from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import select

from app.auth import (
    clear_session,
    clear_session_cookie,
    create_session,
    get_current_user,
    hash_password,
    set_session_cookie,
    verify_password,
)
from app.config import APP_NAME, SESSION_COOKIE_NAME, STATIC_DIR, TEMPLATES_DIR
from app.database import SessionLocal, init_db
from app.models import User
from app.services import ensure_storage_dirs, get_dashboard_data, get_recent_transactions, get_recent_uploads, process_uploaded_files


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_storage_dirs()
    init_db()
    yield


app = FastAPI(title=APP_NAME, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class Credentials(BaseModel):
    email: str
    password: str


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _validate_credentials(credentials: Credentials) -> tuple[str, str]:
    email = _normalize_email(credentials.email)
    password = credentials.password
    if not email or "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enter a valid email address.")
    if not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required.")
    return email, password


def _auth_payload(user: User) -> dict:
    return {"user": {"id": user.id, "email": user.email}}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "app_name": APP_NAME})


@app.post("/api/auth/register")
async def register(credentials: Credentials):
    email, password = _validate_credentials(credentials)
    database = SessionLocal()
    try:
        existing_user = database.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing_user is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered.")

        user = User(email=email, password_hash=hash_password(password))
        database.add(user)
        database.commit()
        database.refresh(user)

        token = create_session(database, user)
        response = JSONResponse(_auth_payload(user), status_code=status.HTTP_201_CREATED)
        set_session_cookie(response, token)
        return response
    finally:
        database.close()


@app.post("/api/auth/login")
async def login(credentials: Credentials):
    email, password = _validate_credentials(credentials)
    database = SessionLocal()
    try:
        user = database.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

        token = create_session(database, user)
        response = JSONResponse(_auth_payload(user))
        set_session_cookie(response, token)
        return response
    finally:
        database.close()


@app.post("/api/auth/logout")
async def logout(request: Request):
    database = SessionLocal()
    try:
        clear_session(database, request.cookies.get(SESSION_COOKIE_NAME))
        response = JSONResponse({"ok": True})
        clear_session_cookie(response)
        return response
    finally:
        database.close()


@app.get("/api/auth/me")
async def me(request: Request):
    database = SessionLocal()
    try:
        user = get_current_user(request, database)
        return _auth_payload(user)
    finally:
        database.close()


@app.get("/api/dashboard")
async def dashboard(request: Request):
    database = SessionLocal()
    try:
        user = get_current_user(request, database)
        return {
            "summary": get_dashboard_data(database, user.id),
            "uploads": get_recent_uploads(database, user.id),
            "transactions": get_recent_transactions(database, user.id),
        }
    finally:
        database.close()


@app.get("/api/transactions")
async def transactions(request: Request, limit: int = 200):
    database = SessionLocal()
    try:
        user = get_current_user(request, database)
        capped_limit = min(max(limit, 1), 500)
        return {"transactions": get_recent_transactions(database, user.id, limit=capped_limit)}
    finally:
        database.close()


@app.post("/api/uploads")
async def upload_statements(request: Request, files: list[UploadFile] = File(...)):
    database = SessionLocal()
    try:
        user = get_current_user(request, database)
        results = process_uploaded_files(database, user, files)
        return {
            "results": results,
            "summary": get_dashboard_data(database, user.id),
            "uploads": get_recent_uploads(database, user.id),
            "transactions": get_recent_transactions(database, user.id),
        }
    finally:
        database.close()
