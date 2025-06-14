from fastapi import FastAPI
from app.api.v1.routers import api_router
from app.db.base import SessionLocal
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(api_router, prefix="/api/v1")

# @app.get("/")
# def read_root():
#     return 'api works'