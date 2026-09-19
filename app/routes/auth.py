from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.models import Admin
from app.services.auth import verify_password

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/admin/login")
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    admin = (
        db.query(Admin)
        .filter(Admin.username == username)
        .first()
    )

    if not admin or not verify_password(password, admin.password_hash):
        return {"error": "Invalid username or password"}

    request.session["admin_id"] = admin.id

    return {"message": "Login successful"}