from pydantic import BaseModel
from typing import List, Optional

class LlmBase(BaseModel):
    name: str


class LlmCreate(LlmBase):
    pass


class LlmRead(LlmBase):
    id: int
    history: Optional[List[str]] = []

    class Config:
        orm_mode = True