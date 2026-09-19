from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.models import Notice
from app.services.dependencies import get_db, require_admin


router = APIRouter()


# =========================
# REQUEST SCHEMA
# =========================

class NoticeCreate(BaseModel):
    title_en: str
    title_ml: str


# =========================
# PUBLIC ROUTES
# =========================

@router.get("/api/notices")
def get_notices(
    db: Session = Depends(get_db)
):
    return (
        db.query(Notice)
        .filter(Notice.is_active == True)
        .order_by(Notice.created_at.desc())
        .all()
    )


# =========================
# ADMIN ROUTES
# =========================

@router.post("/api/admin/notices")
def create_notice(
    notice_data: NoticeCreate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):
    notice = Notice(
        title_en=notice_data.title_en,
        title_ml=notice_data.title_ml
    )

    db.add(notice)
    db.commit()
    db.refresh(notice)

    return notice


@router.delete("/api/admin/notices/{notice_id}")
def delete_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):
    notice = (
        db.query(Notice)
        .filter(Notice.id == notice_id)
        .first()
    )

    if not notice:
        raise HTTPException(
            status_code=404,
            detail="Notice not found"
        )

    db.delete(notice)
    db.commit()

    return {
        "message": "Notice deleted"
    }