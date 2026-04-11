from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
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
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/auth/login")

    base_query = db.query(models.BudgetLine)
    if user.role == models.UserRole.IT_HEAD:
        base_query = base_query.filter(models.BudgetLine.submitted_by == user.id)

    all_lines = base_query.all()

    total_budget = sum(l.budget_amt_current_fy for l in all_lines)
    total_opex   = sum(l.budget_amt_current_fy for l in all_lines if l.expense_sub_type == models.ExpenseSubType.OPEX)
    total_capex  = sum(l.budget_amt_current_fy for l in all_lines if l.expense_sub_type == models.ExpenseSubType.CAPEX)
    budget_keys  = len(set(l.budget_key_current for l in all_lines))
    it_heads     = len(set(l.submitted_by for l in all_lines))

    it_head_data = {}
    for line in all_lines:
        u = db.query(models.User).filter(models.User.id == line.submitted_by).first()
        name = u.full_name if u else "Unknown"
        if name not in it_head_data:
            it_head_data[name] = {"budget": 0, "projected": 0}
        it_head_data[name]["budget"]    += line.budget_amt_current_fy
        it_head_data[name]["projected"] += line.projected_consumption

    kpi = {
        "total_budget": total_budget,
        "total_opex"  : total_opex,
        "total_capex" : total_capex,
        "budget_keys" : budget_keys,
        "it_heads"    : it_heads,
    }

    return templates.TemplateResponse(request, "dashboard/index.html", {
        "user"        : user,
        "kpi"         : kpi,
        "it_head_data": it_head_data,
        "recent_lines": all_lines[:5],
        "active_page" : "dashboard",
    })

@router.get("/kpi")
async def dashboard_kpi_json(request: Request, db: Session = Depends(get_db)):
    user = await get_user_from_cookie(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    lines = db.query(models.BudgetLine).all()
    it_head_data = {}
    for line in lines:
        u = db.query(models.User).filter(models.User.id == line.submitted_by).first()
        name = u.full_name if u else "Unknown"
        if name not in it_head_data:
            it_head_data[name] = {"budget": 0, "projected": 0}
        it_head_data[name]["budget"]    += line.budget_amt_current_fy
        it_head_data[name]["projected"] += line.projected_consumption
    return JSONResponse({
        "labels"   : list(it_head_data.keys()),
        "budget"   : [v["budget"]    for v in it_head_data.values()],
        "projected": [v["projected"] for v in it_head_data.values()],
        "opex"     : sum(l.budget_amt_current_fy for l in lines if l.expense_sub_type == models.ExpenseSubType.OPEX),
        "capex"    : sum(l.budget_amt_current_fy for l in lines if l.expense_sub_type == models.ExpenseSubType.CAPEX),
    })