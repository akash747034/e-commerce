from fastapi import FastAPI
from app.core.database import engine, Base
from app.models.user import User
from app.models.category import Category
from app.models.subcategory import SubCategory
from app.models.products import Product

from app.routers.user import router as user_router

app=FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(user_router)

@app.get('/')
def home():
    return {
        "message":"welcome"
    }
