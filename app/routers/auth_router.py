from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app import models, schemas
from app.auth import (
    verify_password, hash_password,
    create_rbl_token,
    require_admin, rbl_token_EXPIRE_MINUTES
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

MAX_BCRYPT_LENGTH = 72  # bcrypt only supports passwords up to 72 bytes


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get("rbl_token")
    if token:
        return RedirectResponse(url="/dashboard/", status_code=302)
    return templates.TemplateResponse(
        "auth/login.html", {"request": request, "error": None}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if password is too long
    if len(password.encode("utf-8")) > MAX_BCRYPT_LENGTH:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": f"Password too long (max {MAX_BCRYPT_LENGTH} bytes)."},
            status_code=400
        )

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid email or password. Please try again."},
            status_code=400
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Account deactivated. Contact IT Admin."},
            status_code=403
        )

    rbl_token = create_rbl_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "user_id": user.id,
            "full_name": user.full_name
        },
        expires_delta=timedelta(minutes=rbl_token_EXPIRE_MINUTES)
    )

    redirect = RedirectResponse(url="/dashboard/", status_code=302)
    redirect.set_cookie(
        key="rbl_token",
        value=rbl_token,
        httponly=True,
        samesite="lax",
        max_age=rbl_token_EXPIRE_MINUTES * 60
    )
    return redirect


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("rbl_token")
    return response


@router.post("/register", response_model=schemas.UserResponse)
async def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    # Check password length
    if len(user_data.password.encode("utf-8")) > MAX_BCRYPT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Password too long (max {MAX_BCRYPT_LENGTH} bytes)."
        )

    existing = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    new_user = models.User(
        full_name=user_data.full_name,
        email=user_data.email,
        password=hash_password(user_data.password),
        role=user_data.role,
        department=user_data.department,
        spoc_email=user_data.spoc_email,
        cost_code=user_data.cost_code,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user