from repositories.history_repo import HistoryRepository
from schemas.history import HistoryCreate

class HistoryService:
    def __init__(self, repo: HistoryRepository):
        self.repo = repo

    def create_history(self, obj: HistoryCreate):
        return self.repo.create(obj)

    def list_history(self):
        return self.repo.list_all()