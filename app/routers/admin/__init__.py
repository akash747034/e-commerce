from fastapi import APIRouter
from .user import router as user_router

router = APIRouter(prefix="/admin")
router.include_router(user_router)
