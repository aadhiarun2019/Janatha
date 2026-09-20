from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.models.models import Book, Rental, User
from app.services.dependencies import get_current_user, get_db, require_admin


router = APIRouter()


class RentalCreate(BaseModel):
    book_id: int
    user_id: int
    due_date: datetime

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v):
        if v <= datetime.utcnow():
            raise ValueError("Due date must be in the future")
        return v


class UserResponse(BaseModel):
    id: int
    full_name: str
    username: str
    email: str


@router.get("/api/member/rentals")
def get_member_rentals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all rentals for the logged-in member"""
    if current_user.role != "member":
        raise HTTPException(
            status_code=403,
            detail="Member access required",
        )

    rentals = (
        db.query(Rental)
        .filter(Rental.user_id == current_user.id)
        .order_by(Rental.borrowed_date.desc())
        .all()
    )

    result = []
    for rental in rentals:
        book = db.query(Book).filter(Book.id == rental.book_id).first()
        result.append(
            {
                "id": rental.id,
                "book_id": rental.book_id,
                "book_title_en": book.title_en if book else None,
                "book_title_ml": book.title_ml if book else None,
                "book_author": book.author if book else None,
                "book_image_url": book.image_url if book else None,
                "borrowed_date": rental.borrowed_date.isoformat(),
                "due_date": rental.due_date.isoformat(),
                "returned_date": (
                    rental.returned_date.isoformat()
                    if rental.returned_date
                    else None
                ),
                "status": rental.status,
            }
        )

    return result


@router.get("/api/admin/rentals")
def get_all_rentals(
    status: str | None = None,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin),
):
    """Get all rentals with optional status filter"""
    query = db.query(Rental)

    if status:
        query = query.filter(Rental.status == status)

    rentals = query.order_by(Rental.borrowed_date.desc()).all()

    result = []
    for rental in rentals:
        book = db.query(Book).filter(Book.id == rental.book_id).first()
        user = db.query(User).filter(User.id == rental.user_id).first()

        result.append(
            {
                "id": rental.id,
                "book_id": rental.book_id,
                "book_title_en": book.title_en if book else None,
                "book_title_ml": book.title_ml if book else None,
                "book_author": book.author if book else None,
                "book_image_url": book.image_url if book else None,
                "user_id": rental.user_id,
                "user_name": user.full_name if user else None,
                "user_username": user.username if user else None,
                "borrowed_date": rental.borrowed_date.isoformat(),
                "due_date": rental.due_date.isoformat(),
                "returned_date": (
                    rental.returned_date.isoformat()
                    if rental.returned_date
                    else None
                ),
                "status": rental.status,
            }
        )

    return result


@router.post("/api/admin/rentals")
def create_rental(
    rental_data: RentalCreate,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin),
):
    """Issue a book to a member"""
    # Validate book exists
    book = (
        db.query(Book)
        .filter(Book.id == rental_data.book_id)
        .with_for_update()
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=404,
            detail="Book not found",
        )

    # Validate book is available
    if not book.is_available:
        raise HTTPException(
            status_code=400,
            detail="Book is not available for rental",
        )

    # Check for existing active rental of this book
    existing_active = (
        db.query(Rental)
        .filter(
            Rental.book_id == rental_data.book_id,
            Rental.status == "active",
        )
        .first()
    )

    if existing_active:
        raise HTTPException(
            status_code=400,
            detail="Book already has an active rental",
        )

    # Validate user exists
    user = db.query(User).filter(User.id == rental_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Validate user is an active member
    if user.role != "member":
        raise HTTPException(
            status_code=400,
            detail="Can only issue books to members",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="User account is not active",
        )

    # Create rental and mark book as unavailable in single transaction
    rental = Rental(
        book_id=rental_data.book_id,
        user_id=rental_data.user_id,
        due_date=rental_data.due_date,
        status="active",
    )

    book.is_available = False

    db.add(rental)
    db.commit()
    db.refresh(rental)

    return {
        "message": "Book issued successfully",
        "rental_id": rental.id,
        "book_id": rental.book_id,
        "user_id": rental.user_id,
        "due_date": rental.due_date.isoformat(),
        "status": rental.status,
    }


@router.put("/api/admin/rentals/{rental_id}/return")
def return_rental(
    rental_id: int,
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin),
):
    """Mark a rental as returned"""
    rental = (
        db.query(Rental)
        .filter(Rental.id == rental_id)
        .with_for_update()
        .first()
    )

    if not rental:
        raise HTTPException(
            status_code=404,
            detail="Rental not found",
        )

    if rental.status != "active":
        raise HTTPException(
            status_code=400,
            detail="Rental is not active",
        )

    # Get the book
    book = (
        db.query(Book)
        .filter(Book.id == rental.book_id)
        .with_for_update()
        .first()
    )
    if not book:
        raise HTTPException(
            status_code=404,
            detail="Associated book not found",
        )

    # Update rental and mark book as available in single transaction
    rental.status = "returned"
    rental.returned_date = datetime.utcnow()
    book.is_available = True

    db.commit()
    db.refresh(rental)

    return {
        "message": "Book returned successfully",
        "rental_id": rental.id,
        "returned_date": rental.returned_date.isoformat(),
        "status": rental.status,
    }


@router.get("/api/admin/users")
def get_members(
    db: Session = Depends(get_db),
    admin_id: int = Depends(require_admin),
):
    """Get all members (for issuing books)"""
    members = (
        db.query(User)
        .filter(User.role == "member", User.is_active == True)
        .order_by(User.full_name)
        .all()
    )

    return [
        {
            "id": member.id,
            "full_name": member.full_name,
            "username": member.username,
            "email": member.email,
        }
        for member in members
    ]
