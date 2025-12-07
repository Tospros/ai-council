from pydantic import BaseModel
from typing import List, Optional

class HistoryBase(BaseModel):
    prompt: str
    response: Optional[str]


class HistoryCreate(HistoryBase):
    llm_ids: List[int] = []


class HistoryRead(HistoryBase):
    id: int
    llms: List[str] = []

    class Config:
        orm_mode = True