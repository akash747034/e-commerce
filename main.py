from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.routers.auth import router as auth_router
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
app.include_router(auth_router)


@app.get("/health", response_model=ApiResponse[dict])
def health():
    return ApiResponse(message="API is healthy", data={"status": "ok"})
