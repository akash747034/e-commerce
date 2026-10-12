from app.core.database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter,Depends, status
from app.schemas.user import UserCreate,UserResponse,LoginResponse,LoginPayload
import app.services.user as user_service
from app.models.user import User
from app.services.user import get_current_user


router=APIRouter(prefix="/users",tags=["Users"])

@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register(payload:UserCreate,db:Session=Depends(get_db)):
    return user_service.register(payload,db)

@router.post("/login",response_model=LoginResponse)
def login(payload:LoginPayload,db:Session=Depends(get_db)):
    return user_service.login(payload,db)

@router.get("/me",response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


