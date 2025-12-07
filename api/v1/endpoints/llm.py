from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from schemas.llm import LlmCreate, LlmRead
from repositories.llm_repo import LlmRepository
from services.llm_service import LlmService

router = APIRouter(prefix="/llms", tags=["llms"])


def get_llm_service(db: Session = Depends(get_db)):
    repo = LlmRepository(db)
    service = LlmService(repo)
    return service


@router.post("/", response_model=LlmRead)
def create_llm(llm: LlmCreate, service: LlmService = Depends(get_llm_service)):
    return service.create_llm(llm)


@router.get("/", response_model=list[LlmRead])
def list_llms(service: LlmService = Depends(get_llm_service)):
    return service.list_llms()