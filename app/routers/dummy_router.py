from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def dummy_home():
    return {"message": "Dummy route working"}
