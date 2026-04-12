from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app import models
from app.auth import generate_budget_key

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def get_user_from_cookie(request: Request, db: Session):
    from app.auth import decode_token
    from jose import JWTError
    token = request.cookies.get("rbl_token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        return db.query(models.User).filter(models.User.email == email).first()
    except JWTError:
        return None

@router.get("/", response_class=HTMLResponse)
async def budget_list_page(request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    if user.role == models.UserRole.IT_HEAD:
        lines = db.query(models.BudgetLine).filter(
            models.BudgetLine.submitted_by == user.id
        ).order_by(models.BudgetLine.created_at.desc()).all()
    else:
        lines = db.query(models.BudgetLine).order_by(models.BudgetLine.created_at.desc()).all()
    counts = {
        "draft"    : sum(1 for l in lines if l.status == models.BudgetStatus.DRAFT),
        "submitted": sum(1 for l in lines if l.status == models.BudgetStatus.SUBMITTED),
        "approved" : sum(1 for l in lines if l.status == models.BudgetStatus.FINAL_APPROVED),
    }
    return templates.TemplateResponse("budget/list.html", {
        "request": request,
        "user": user, "lines": lines, "counts": counts, "active_page": "budget"
    })

@router.get("/new", response_class=HTMLResponse)
async def new_budget_form(request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    if user.role != models.UserRole.IT_HEAD:
        return RedirectResponse(url="/dashboard/")
    next_key = generate_budget_key(db)
    return templates.TemplateResponse("budget/form.html", {
        "request": request,
        "user": user, "next_key": next_key, "entry": None,
        "error": None, "active_page": "new_entry"
    })

@router.post("/new")
async def create_budget_entry(
    request: Request, db: Session = Depends(get_db),
    old_new              : str   = Form(...),
    budget_key_previous  : Optional[str]   = Form(None),
    business_name        : str   = Form(...),
    expense_sub_type     : str   = Form(...),
    description          : str   = Form(...),
    expense_description  : Optional[str]   = Form(None),
    application_platform : Optional[str]   = Form(None),
    vendor_name          : Optional[str]   = Form(None),
    resource_count       : Optional[int]   = Form(None),
    budget_amt_current_fy: float = Form(...),
    projected_consumption: float = Form(...),
    budget_amt_next_fy   : float = Form(...),
    detailed_reasoning   : Optional[str]   = Form(None),
    action               : str   = Form("draft"),
):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")

    diff_a_b = budget_amt_current_fy - projected_consumption
    diff_c_b = budget_amt_next_fy - projected_consumption
    diff_c_a = budget_amt_next_fy - budget_amt_current_fy
    initial_status = models.BudgetStatus.SUBMITTED if action == "submit" else models.BudgetStatus.DRAFT
    new_key = generate_budget_key(db)

    entry = models.BudgetLine(
        budget_key_current   = new_key,
        budget_key_previous  = budget_key_previous if old_new == "old" else None,
        old_new              = models.OldNew(old_new),
        business_name        = business_name,
        cost_code            = user.cost_code or "N/A",
        submitted_by         = user.id,
        expense_sub_type     = models.ExpenseSubType(expense_sub_type),
        description          = description,
        expense_description  = expense_description,
        application_platform = application_platform,
        vendor_name          = vendor_name,
        resource_count       = resource_count,
        budget_amt_current_fy= budget_amt_current_fy,
        projected_consumption= projected_consumption,
        budget_amt_next_fy   = budget_amt_next_fy,
        diff_a_minus_b       = diff_a_b,
        diff_c_minus_b       = diff_c_b,
        diff_c_minus_a       = diff_c_a,
        detailed_reasoning   = detailed_reasoning,
        status               = initial_status,
    )
    db.add(entry)
    db.commit()
    return RedirectResponse(url="/budget/", status_code=302)

@router.post("/{entry_id}/submit")
async def submit_for_approval(entry_id: int, request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    entry = db.query(models.BudgetLine).filter(
        models.BudgetLine.id == entry_id,
        models.BudgetLine.submitted_by == user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    if entry.status != models.BudgetStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT entries can be submitted")
    entry.status = models.BudgetStatus.SUBMITTED
    db.commit()
    return RedirectResponse(url="/budget/", status_code=302)

@router.post("/{entry_id}/delete")
async def delete_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")
    entry = db.query(models.BudgetLine).filter(
        models.BudgetLine.id == entry_id,
        models.BudgetLine.submitted_by == user.id
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    if entry.status != models.BudgetStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT entries can be deleted")
    db.delete(entry)
    db.commit()
    return RedirectResponse(url="/budget/", status_code=302)

@router.get("/api/list")
async def budget_list_json(request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    query = db.query(models.BudgetLine)
    if user.role == models.UserRole.IT_HEAD:
        query = query.filter(models.BudgetLine.submitted_by == user.id)
    lines = query.order_by(models.BudgetLine.created_at.desc()).all()
    return JSONResponse([{
        "id"               : l.id,
        "budget_key"       : l.budget_key_current,
        "business_name"    : l.business_name,
        "description"      : l.description,
        "expense_sub_type" : l.expense_sub_type.value,
        "application"      : l.application_platform,
        "budget_current_fy": l.budget_amt_current_fy,
        "projected"        : l.projected_consumption,
        "budget_next_fy"   : l.budget_amt_next_fy,
        "diff_a_b"         : l.diff_a_minus_b,
        "status"           : l.status.value,
    } for l in lines])