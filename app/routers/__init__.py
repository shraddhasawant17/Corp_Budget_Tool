# app/routers/__init__.py
# ═══════════════════════════════════════════════════════════
# Yeh file routers package ko Python package banati hai
# Matlab "from app.routers import auth_router" kaam karega
# Bina is file ke Python "app/routers" ko package nahi manega
# ═══════════════════════════════════════════════════════════

from app.routers import auth_router, budget_router, approval_router, dashboard_router, dummy_router
