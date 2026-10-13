from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers.address import router as address_router
from app.routers.auth import router as auth_router
from app.routers.brand import router as brand_router
from app.routers.cart import router as cart_router
from app.routers.category import router as category_router
from app.routers.notification import router as notification_router
from app.routers.order import router as order_router
from app.routers.product import router as product_router
from app.routers.review import router as review_router
from app.routers.user import router as user_router
from app.routers.wishlist import router as wishlist_router
from app.schemas.response import ApiResponse

app = FastAPI(title=settings.app_name)

# Centralized error handlers
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth
app.include_router(auth_router)
# User & profile
app.include_router(user_router)
app.include_router(address_router)

# Catalogue
app.include_router(category_router)
app.include_router(brand_router)
app.include_router(product_router)

# Shopping
app.include_router(cart_router)
app.include_router(order_router)

# Engagement
app.include_router(review_router)
app.include_router(wishlist_router)
app.include_router(notification_router)


@app.get("/health", response_model=ApiResponse[dict])
def health():
    return ApiResponse(message="API is healthy", data={"status": "ok"})
