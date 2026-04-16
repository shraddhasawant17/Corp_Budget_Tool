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
