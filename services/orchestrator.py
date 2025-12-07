from typing import List
from services.llm_service import LlmService
from services.history_service import HistoryService
from schemas.history import HistoryCreate
from sqlalchemy.orm import Session

class OrchestratorService:
    def __init__(self, llm_service: LlmService, history_service: HistoryService):
        self.llm_service = llm_service
        self.history_service = history_service

    def run_prompt(self, db: Session, prompt: str, llm_ids: List[int], final_llm_id: int):
        llms = [llm for llm in self.llm_service.list_llms() if llm.id in llm_ids]

        responses = []
        for llm in llms:
            response = f"Response from {llm.name} for prompt '{prompt}'"
            responses.append({"llm": llm, "response": response})

        best = max(responses, key=lambda r: len(r["response"]))

        final_llm = next((llm for llm in self.llm_service.list_llms() if llm.id == final_llm_id), None)
        final_response = f"Final LLM ({final_llm.name}) response to '{best['response']}'"

        history_create = HistoryCreate(
            prompt=prompt,
            response=final_response,
            llm_ids=[llm.id for llm in llms]
        )
        history_obj = self.history_service.create_history(history_create)

        return {
            "responses": responses,
            "best_response": best,
            "final_response": final_response,
            "history_id": history_obj.id
        }