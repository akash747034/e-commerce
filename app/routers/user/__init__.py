from fastapi import APIRouter
from .profile import router as profile_router
from .address import router as address_router
from .notification import router as notification_router

router = APIRouter()
router.include_router(profile_router)
router.include_router(address_router)
router.include_router(notification_router)
