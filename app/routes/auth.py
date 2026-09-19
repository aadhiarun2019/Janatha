from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.models.models import User
from app.services.auth import hash_password, verify_password
from app.services.dependencies import get_db

router = APIRouter()


def clean(value: str | None) -> str:
    return (value or "").strip()


@router.post("/admin/login")
def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = clean(username)

    user = (
        db.query(User)
        .filter(User.username == username, User.role == "admin")
        .first()
    )

    if not user or not user.is_active or not verify_password(
        password, user.password_hash
    ):
        return {"error": "Invalid admin username or password"}

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["role"] = "admin"

    return {"message": "Admin login successful", "role": "admin"}


@router.post("/api/member/register")
def member_register(
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(""),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
):
    full_name = clean(full_name)
    email = clean(email).lower()
    phone = clean(phone)
    username = clean(username).lower()

    if not full_name or not email or not username:
        return {"error": "Name, email and username are required"}

    if len(password) < 8:
        return {"error": "Password must be at least 8 characters"}

    if password != confirm_password:
        return {"error": "Passwords do not match"}

    if "@" not in email:
        return {"error": "Please enter a valid email address"}

    existing_email = (
        db.query(User).filter(User.email == email).first()
    )
    if existing_email:
        return {"error": "Email is already registered"}

    existing_username = (
        db.query(User).filter(User.username == username).first()
    )
    if existing_username:
        return {"error": "Username is already taken"}

    user = User(
        full_name=full_name,
        email=email,
        phone=phone or None,
        username=username,
        password_hash=hash_password(password),
        role="member",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "Registration successful. You can now log in.",
        "role": "member",
    }


@router.post("/api/member/login")
def member_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = clean(username).lower()

    user = (
        db.query(User)
        .filter(
            User.username == username,
            User.role == "member",
        )
        .first()
    )

    if not user or not user.is_active or not verify_password(
        password, user.password_hash
    ):
        return {"error": "Invalid member username or password"}

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["role"] = "member"

    return {
        "message": "Member login successful",
        "role": "member",
    }


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


@router.get("/api/auth/me")
def current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")

    if not user_id:
        return {"authenticated": False}

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        request.session.clear()
        return {"authenticated": False}

    return {
        "authenticated": True,
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "username": user.username,
        "role": user.role,
    }


@router.get("/member")
def member_page(request: Request):
    if request.session.get("role") != "member":
        return RedirectResponse("/")

    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="templates")

    return templates.TemplateResponse(
        request=request,
        name="member.html",
    )
