from sqlalchemy.orm import Session
from models.llm import Llm
from schemas.llm import LlmCreate

class LlmRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, obj: LlmCreate):
        llm = Llm(name=obj.name)
        self.db.add(llm)
        self.db.commit()
        self.db.refresh(llm)
        return llm

    def list_all(self):
        return self.db.query(Llm).all()