from fastapi import APIRouter
from .endpoints import history, llm

router = APIRouter()
router.include_router(history.router)
router.include_router(llm.router)