# ═══════════════════════════════════════════════════════════
# main.py — FastAPI Application ka Entry Point
# ═══════════════════════════════════════════════════════════
#
# Yeh file kya karti hai:
#   1. FastAPI app instance banati hai
#   2. Database tables create karti hai (pehli baar run hone par)
#   3. Static files serve karti hai (CSS, JS, images)
#   4. Jinja2 templates setup karti hai
#   5. Saare routers register karti hai
#   6. Root redirect set karti hai
#
# Entry point matlab: jab "uvicorn main:app" chalate ho
#   - main = yeh file (main.py)
#   - app = is file mein banaya gaya FastAPI instance
#   Uvicorn "app" object ko dhundta hai aur server start karta hai
# ═══════════════════════════════════════════════════════════

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import uvicorn

# Database imports
from app.database import engine, Base
from app import models  # noqa — models import karna zaroori hai taaki Base.metadata mein register ho

# Router imports — har feature ka apna router hai
from app.routers import (
    auth_router,
    budget_router,
    approval_router,
    dashboard_router,
    dummy_router,      # Dummy1 + Dummy2 ke liye
)

# ── DATABASE TABLES CREATE KARO ───────────────────────────
# Yeh line pehli baar run hone par saari tables create karegi
# models.py mein jo bhi Base inherit kiya hai woh sab tables ban jayenge
# Agar tables pehle se hain to kuch nahi hoga — safe to run multiple times
# Production mein Alembic use karte hain migrations ke liye (future topic)
Base.metadata.create_all(bind=engine)

# ── FASTAPI APP INSTANCE ──────────────────────────────────
app = FastAPI(
    title="RBL Bank IT Budget Portal",
    description="Internal IT Budget Planning & Approval System for RBL Bank",
    version="1.0.0-prototype",
    # docs_url = Swagger UI automatically milti hai — /docs pe ja ke APIs test kar sakte ho
    # Yeh development ke liye bohot useful hai — Postman ki zarurat nahi
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── STATIC FILES ──────────────────────────────────────────
# Static files = CSS, JavaScript, images — jo change nahi hote
# StaticFiles = FastAPI ki built-in class jo files directly serve karti hai
# directory="app/static" = yahan se files serve hongi
# name="static" = templates mein {{ url_for('static', path='css/style.css') }} se access karenge
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── JINJA2 TEMPLATES ──────────────────────────────────────
# Jinja2 = Python ka templating engine
# Matlab HTML files mein Python variables use kar sakte ho
# Example in HTML: <h1>Welcome {{ user.full_name }}</h1>
# FastAPI yeh variable inject karega — dynamic HTML banta hai
templates = Jinja2Templates(directory="app/templates")

# ── ROUTERS REGISTER KARO ────────────────────────────────
# Router = ek group of related endpoints
# include_router = main app mein add karo
# prefix = har route ke aage yeh laga do
# tags = Swagger docs mein grouping ke liye

app.include_router(
    auth_router.router,
    prefix="/auth",
    tags=["Authentication"]
    # Routes: /auth/login, /auth/logout, /auth/register
)

app.include_router(
    dashboard_router.router,
    prefix="/dashboard",
    tags=["Dashboard"]
    # Routes: /dashboard/, /dashboard/kpi
)

app.include_router(
    budget_router.router,
    prefix="/budget",
    tags=["Budget Lines"]
    # Routes: /budget/, /budget/new, /budget/{id}, /budget/{id}/submit
)

app.include_router(
    approval_router.router,
    prefix="/approval",
    tags=["Approvals"]
    # Routes: /approval/, /approval/{id}/approve, /approval/{id}/reject
)

app.include_router(
    dummy_router.router,
    prefix="/dummy",
    tags=["Future Features"]
    # Routes: /dummy/dummy1, /dummy/dummy2
)

# ── ROOT REDIRECT ─────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    # Koi / pe aaye to login page pe bhejo
    return RedirectResponse(url="/auth/login")

# ── HEALTH CHECK ──────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    """
    Server chal raha hai ya nahi check karne ke liye
    Production mein monitoring tools yeh endpoint ping karte rehte hain
    Agar 200 response aaye = server theek hai
    """
    return {
        "status": "healthy",
        "app": "RBL Bank IT Budget Portal",
        "version": "1.0.0-prototype",
        "database": "SQLite — connected"
    }

# ── RUN SERVER ────────────────────────────────────────────
# Yeh block sirf tab chalega jab directly "python main.py" karo
# "uvicorn main:app" se chalate ho to yeh block nahi chalega — that's fine
# reload=True = code save karte hi server automatically restart hoga — development ke liye useful
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",   # 0.0.0.0 = sabhi network interfaces — localhost + local network
        port=8000,
        reload=True        # Auto-reload on code changes
    )
