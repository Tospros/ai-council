from fastapi import FastAPI
from db.session import Base, engine
from api.v1.router import router as api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI AI COUNCIL")

app.include_router(api_router, prefix="/api/v1")