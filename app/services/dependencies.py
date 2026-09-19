from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.database import SessionLocal


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def require_admin(request: Request):
    admin_id = request.session.get("admin_id")

    if not admin_id:
        raise HTTPException(
            status_code=401,
            detail="Admin login required"
        )

    return admin_id