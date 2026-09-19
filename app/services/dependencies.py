from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.models import User


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Login required",
        )

    user = (
        db.query(User)
        .filter(User.id == user_id, User.is_active == True)
        .first()
    )

    if not user:
        request.session.clear()
        raise HTTPException(
            status_code=401,
            detail="User account not found",
        )

    return user


def require_admin(
    user: User = Depends(get_current_user),
):
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return user.id


def require_member(
    user: User = Depends(get_current_user),
):
    if user.role != "member":
        raise HTTPException(
            status_code=403,
            detail="Member access required",
        )

    return user.id
