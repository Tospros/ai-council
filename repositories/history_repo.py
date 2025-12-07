from sqlalchemy.orm import Session
from models.history import History
from models.llm import Llm
from schemas.history import HistoryCreate

class HistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, obj: HistoryCreate):
        history = History(prompt=obj.prompt, response=obj.response)
        if obj.llm_ids:
            llms = self.db.query(Llm).filter(Llm.id.in_(obj.llm_ids)).all()
            history.llms.extend(llms)
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        return history

    def list_all(self):
        return self.db.query(History).all()