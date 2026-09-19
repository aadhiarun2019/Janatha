from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, model_validator

from app.models.models import (
    Notice,
    Book,
    BuildingUpdate,
    SiteSetting
)
from app.services.dependencies import get_db, require_admin


router = APIRouter()


# =========================================================
# VALIDATION HELPER
# =========================================================

def validate_languages(value_en, value_ml, item_name):
    """
    At least one language must be provided.
    English only, Malayalam only, or both are allowed.
    """

    en = value_en.strip() if value_en else ""
    ml = value_ml.strip() if value_ml else ""

    if not en and not ml:
        raise ValueError(
            f"{item_name}: English or Malayalam content is required."
        )

    return value_en, value_ml


# =========================================================
# SCHEMAS
# =========================================================

class NoticeCreate(BaseModel):

    title_en: str | None = None
    title_ml: str | None = None

    @model_validator(mode="after")
    def validate_notice(self):

        validate_languages(
            self.title_en,
            self.title_ml,
            "Notice"
        )

        return self


class BookCreate(BaseModel):

    title_en: str | None = None
    title_ml: str | None = None
    author: str | None = None

    description_en: str | None = None
    description_ml: str | None = None

    image_url: str | None = None
    is_available: bool = True

    @model_validator(mode="after")
    def validate_book(self):

        validate_languages(
            self.title_en,
            self.title_ml,
            "Book title"
        )

        return self


class BuildingUpdateCreate(BaseModel):

    title_en: str | None = None
    title_ml: str | None = None

    description_en: str | None = None
    description_ml: str | None = None

    image_url: str | None = None

    @model_validator(mode="after")
    def validate_building_update(self):

        validate_languages(
            self.title_en,
            self.title_ml,
            "Building update title"
        )

        return self


class SiteSettingCreate(BaseModel):

    key: str
    value_en: str | None = None
    value_ml: str | None = None

    @model_validator(mode="after")
    def validate_setting(self):

        validate_languages(
            self.value_en,
            self.value_ml,
            "Site setting"
        )

        return self


# =========================================================
# NOTICES
# =========================================================

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

    return {"message": "Notice deleted"}


# =========================================================
# BOOKS
# =========================================================

@router.get("/api/books")
def get_books(
    db: Session = Depends(get_db)
):

    return (
        db.query(Book)
        .order_by(Book.id.desc())
        .all()
    )


@router.post("/api/admin/books")
def create_book(
    book_data: BookCreate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):

    book = Book(
        title_en=book_data.title_en,
        title_ml=book_data.title_ml,
        author=book_data.author,
        description_en=book_data.description_en,
        description_ml=book_data.description_ml,
        image_url=book_data.image_url,
        is_available=book_data.is_available
    )

    db.add(book)
    db.commit()
    db.refresh(book)

    return book


@router.delete("/api/admin/books/{book_id}")
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):

    book = (
        db.query(Book)
        .filter(Book.id == book_id)
        .first()
    )

    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    db.delete(book)
    db.commit()

    return {"message": "Book deleted"}


# =========================================================
# BUILDING UPDATES
# =========================================================

@router.get("/api/building-updates")
def get_building_updates(
    db: Session = Depends(get_db)
):

    return (
        db.query(BuildingUpdate)
        .order_by(BuildingUpdate.created_at.desc())
        .all()
    )


@router.post("/api/admin/building-updates")
def create_building_update(
    update_data: BuildingUpdateCreate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):

    update = BuildingUpdate(
        title_en=update_data.title_en,
        title_ml=update_data.title_ml,
        description_en=update_data.description_en,
        description_ml=update_data.description_ml,
        image_url=update_data.image_url
    )

    db.add(update)
    db.commit()
    db.refresh(update)

    return update


@router.delete("/api/admin/building-updates/{update_id}")
def delete_building_update(
    update_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):

    update = (
        db.query(BuildingUpdate)
        .filter(BuildingUpdate.id == update_id)
        .first()
    )

    if not update:
        raise HTTPException(
            status_code=404,
            detail="Building update not found"
        )

    db.delete(update)
    db.commit()

    return {"message": "Building update deleted"}


# =========================================================
# SITE SETTINGS
# =========================================================

@router.get("/api/settings")
def get_settings(
    db: Session = Depends(get_db)
):

    return (
        db.query(SiteSetting)
        .order_by(SiteSetting.key)
        .all()
    )


@router.post("/api/admin/settings")
def create_setting(
    setting_data: SiteSettingCreate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):

    existing = (
        db.query(SiteSetting)
        .filter(
            SiteSetting.key == setting_data.key
        )
        .first()
    )

    if existing:

        existing.value_en = setting_data.value_en
        existing.value_ml = setting_data.value_ml

        db.commit()
        db.refresh(existing)

        return existing

    setting = SiteSetting(
        key=setting_data.key,
        value_en=setting_data.value_en,
        value_ml=setting_data.value_ml
    )

    db.add(setting)
    db.commit()
    db.refresh(setting)

    return setting


@router.delete("/api/admin/settings/{setting_id}")
def delete_setting(
    setting_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin)
):

    setting = (
        db.query(SiteSetting)
        .filter(SiteSetting.id == setting_id)
        .first()
    )

    if not setting:
        raise HTTPException(
            status_code=404,
            detail="Setting not found"
        )

    db.delete(setting)
    db.commit()

    return {"message": "Setting deleted"}