from repositories.llm_repo import LlmRepository
from schemas.llm import LlmCreate

class LlmService:
    def __init__(self, repo: LlmRepository):
        self.repo = repo

    def create_llm(self, obj: LlmCreate):
        return self.repo.create(obj)

    def list_llms(self):
        return self.repo.list_all()
