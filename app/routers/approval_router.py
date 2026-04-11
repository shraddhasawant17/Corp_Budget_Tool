from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import models

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def get_user_from_cookie(request: Request, db: Session):
    from app.auth import decode_token
    from jose import JWTError
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        return db.query(models.User).filter(models.User.email == email).first()
    except JWTError:
        return None

@router.get("/", response_class=HTMLResponse)
async def approval_page(request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    if user.role == models.UserRole.ADMIN:
        pending = db.query(models.BudgetLine).filter(
            models.BudgetLine.status == models.BudgetStatus.SUBMITTED
        ).order_by(models.BudgetLine.created_at.desc()).all()
    elif user.role == models.UserRole.SUPER_ADMIN:
        pending = db.query(models.BudgetLine).filter(
            models.BudgetLine.status == models.BudgetStatus.ADMIN_APPROVED
        ).order_by(models.BudgetLine.created_at.desc()).all()
    else:
        pending = db.query(models.BudgetLine).filter(
            models.BudgetLine.submitted_by == user.id
        ).order_by(models.BudgetLine.created_at.desc()).all()
    return templates.TemplateResponse(request, "approval/index.html", {
        "user": user, "pending": pending, "active_page": "approval"
    })

@router.post("/{entry_id}/approve")
async def approve_entry(
    entry_id: int, request: Request,
    db: Session = Depends(get_db),
    comment: Optional[str] = Form(None)
):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    entry = db.query(models.BudgetLine).filter(models.BudgetLine.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role == models.UserRole.ADMIN:
        if entry.status != models.BudgetStatus.SUBMITTED:
            raise HTTPException(status_code=400, detail="Entry not in SUBMITTED state")
        entry.status = models.BudgetStatus.ADMIN_APPROVED
    elif user.role == models.UserRole.SUPER_ADMIN:
        if entry.status != models.BudgetStatus.ADMIN_APPROVED:
            raise HTTPException(status_code=400, detail="Entry not in ADMIN_APPROVED state")
        entry.status = models.BudgetStatus.FINAL_APPROVED
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.add(models.Approval(
        budget_line_id=entry_id, action_by=user.id,
        action=models.ApprovalAction.APPROVED, comment=comment
    ))
    db.commit()
    return RedirectResponse(url="/approval/", status_code=302)

@router.post("/{entry_id}/reject")
async def reject_entry(
    entry_id: int, request: Request,
    db: Session = Depends(get_db),
    comment: str = Form(...)
):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    entry = db.query(models.BudgetLine).filter(models.BudgetLine.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role == models.UserRole.ADMIN:
        entry.status = models.BudgetStatus.REJECTED_BY_ADMIN
    elif user.role == models.UserRole.SUPER_ADMIN:
        entry.status = models.BudgetStatus.REJECTED_BY_CEO
    else:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.add(models.Approval(
        budget_line_id=entry_id, action_by=user.id,
        action=models.ApprovalAction.REJECTED, comment=comment
    ))
    db.commit()
    return RedirectResponse(url="/approval/", status_code=302)