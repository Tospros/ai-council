from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.history import HistoryCreate, HistoryRead
from repositories.history_repo import HistoryRepository
from services.history_service import HistoryService

router = APIRouter(prefix="/history", tags=["history"])

def get_history_service(db: Session = Depends(get_db)):
    repo = HistoryRepository(db)
    service = HistoryService(repo)
    return service

@router.post("/", response_model=HistoryRead)
def create_history(history: HistoryCreate, service: HistoryService = Depends(get_history_service)):
    return service.create_history(history)

@router.get("/", response_model=list[HistoryRead])
def list_history(service: HistoryService = Depends(get_history_service)):
    return service.list_history()