from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from db.session import get_db
from services.llm_service import LlmService
from services.history_service import HistoryService
from services.orchestrator import OrchestratorService

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

def get_orchestrator(db: Session = Depends(get_db)):
    llm_service = LlmService(repo=None)
    history_service = HistoryService(repo=None)
    orchestrator = OrchestratorService(llm_service, history_service)
    return orchestrator

@router.post("/")
def run_orchestrator(prompt: str, llm_ids: List[int], final_llm_id: int,
                     orchestrator: OrchestratorService = Depends(get_orchestrator),
                     db: Session = Depends(get_db)):
    return orchestrator.run_prompt(db, prompt, llm_ids, final_llm_id)