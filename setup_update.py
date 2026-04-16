"""
RBL Budget Portal — Auto Setup Script
Run this from inside rbl-budget-portal folder:
    python setup_update.py
"""

import os

BASE = os.path.dirname(os.path.abspath(__file__))


def write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"✓ {path}")


print("Creating/updating all files...")


# ── DUMMY ROUTER ───────────────────────────────────────
write(
    "app/routers/dummy_router.py",
    """
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def dummy_home():
    return {"message": "Dummy route working"}
""",
)


# ── INIT FILES ─────────────────────────────────────────
write(
    "app/__init__.py",
    """
# Makes app a package
""",
)

write(
    "app/routers/__init__.py",
    """
from app.routers import (
    auth_router,
    budget_router,
    approval_router,
    dashboard_router,
    dummy_router,
    import_router,
)
""",
)


# ── MAIN.PY ────────────────────────────────────────────
write(
    "main.py",
    """
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import uvicorn

from app.database import engine, Base
from app import models  # noqa

from app.routers import (
    auth_router,
    budget_router,
    approval_router,
    dashboard_router,
    dummy_router,
    import_router,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RBL Bank IT Budget Portal",
    version="1.0.0",
    docs_url="/docs"
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router.router,      prefix="/auth",      tags=["Auth"])
app.include_router(dashboard_router.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(budget_router.router,    prefix="/budget",    tags=["Budget"])
app.include_router(approval_router.router,  prefix="/approval",  tags=["Approvals"])
app.include_router(import_router.router,    prefix="/import",    tags=["Import"])
app.include_router(dummy_router.router,     prefix="/dummy",     tags=["Future"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/auth/login")


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
""",
)


# ── REQUIRED FOLDERS ───────────────────────────────────
os.makedirs(os.path.join(BASE, "uploads"), exist_ok=True)
os.makedirs(os.path.join(BASE, "app/static/images"), exist_ok=True)
os.makedirs(os.path.join(BASE, "app/templates/import_export"), exist_ok=True)


print("\nAll fixes applied successfully!")

print(
    """
Next steps:

1. Delete old DB:
   del rbl_budget.db

2. Install dependencies:
   pip install -r requirements.txt

3. Seed data:
   python seed.py

4. Run server:
   uvicorn main:app --reload
"""
)