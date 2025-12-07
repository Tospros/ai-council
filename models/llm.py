from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.session import Base


class Llm(Base):
    __tablename__ = "llms"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    history_list = relationship("History", secondary="llm_group", back_populates="llms")