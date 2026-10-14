from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.customer import router as customer_router
from app.routers.seller import router as seller_router
from app.routers.user import router as user_router
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

# Domain-Driven Modular Routers
app.include_router(auth_router)       # /auth (login, register, refresh)
app.include_router(user_router)       # /users/me, /notifications (shared account & alerts)
app.include_router(catalog_router)    # /products, /categories, /brands (browsing & management)
app.include_router(customer_router)   # /cart, /orders, /reviews, /wishlist (shopper checkout)
app.include_router(seller_router)     # /seller/dashboard/stats, /seller/orders (seller portal)
app.include_router(admin_router)      # /admin/* (platform governance)


@app.get("/health", response_model=ApiResponse[dict])
def health():
    return ApiResponse(message="API is healthy", data={"status": "ok"})
