# ═══════════════════════════════════════════════════════════
# routers/dummy_router.py — Future Features Placeholder
# ═══════════════════════════════════════════════════════════
#
# Yeh router Dummy1 aur Dummy2 tables ke liye hai
# Abhi basic CRUD hai — future mein implement karenge:
#   Dummy1 → Budget Templates / Notifications
#   Dummy2 → Audit Logs / System Events
# ═══════════════════════════════════════════════════════════

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import models

router = APIRouter()

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

# ── DUMMY1 ROUTES ──────────────────────────────────────────

@router.get("/dummy1")
async def dummy1_list(request: Request, db: Session = Depends(get_db)):
    """Future: Budget Templates list"""
    user = await get_user_from_cookie(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    items = db.query(models.Dummy1).filter(models.Dummy1.is_active == True).all()
    return JSONResponse([{
        "id"         : i.id,
        "title"      : i.title,
        "description": i.description,
        "created_at" : str(i.created_at),
    } for i in items])

@router.post("/dummy1")
async def dummy1_create(
    request: Request,
    db: Session = Depends(get_db),
    title      : Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    meta_json  : Optional[str] = Form(None),
):
    """Future: Create Budget Template"""
    user = await get_user_from_cookie(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    item = models.Dummy1(
        title       = title,
        description = description,
        ref_user_id = user.id,
        meta_json   = meta_json,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return JSONResponse({"message": "Dummy1 created", "id": item.id})

@router.delete("/dummy1/{item_id}")
async def dummy1_delete(item_id: int, request: Request, db: Session = Depends(get_db)):
    """Future: Delete Template"""
    user = await get_user_from_cookie(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    item = db.query(models.Dummy1).filter(models.Dummy1.id == item_id).first()
    if item:
        item.is_active = False  # Soft delete — actually delete nahi karte
        db.commit()
    return JSONResponse({"message": "Deleted"})

# ── DUMMY2 ROUTES ──────────────────────────────────────────

@router.get("/dummy2")
async def dummy2_list(request: Request, db: Session = Depends(get_db)):
    """Future: Audit Logs / System Events"""
    user = await get_user_from_cookie(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    # Sirf Admin/CEO dekh sakta hai
    if user.role == models.UserRole.IT_HEAD:
        return JSONResponse({"error": "Access denied"}, status_code=403)
    items = db.query(models.Dummy2).order_by(models.Dummy2.created_at.desc()).limit(100).all()
    return JSONResponse([{
        "id"          : i.id,
        "event_type"  : i.event_type,
        "event_data"  : i.event_data,
        "triggered_by": i.triggered_by,
        "created_at"  : str(i.created_at),
    } for i in items])

@router.post("/dummy2/log")
async def dummy2_log_event(
    request: Request,
    db: Session = Depends(get_db),
    event_type: Optional[str] = Form(None),
    event_data: Optional[str] = Form(None),
):
    """Future: Log system event"""
    user = await get_user_from_cookie(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    log = models.Dummy2(
        event_type   = event_type,
        event_data   = event_data,
        triggered_by = user.id,
    )
    db.add(log)
    db.commit()
    return JSONResponse({"message": "Event logged", "id": log.id})
