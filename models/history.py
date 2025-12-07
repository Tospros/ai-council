from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from db.session import Base


llm_group = Table(
    "llm_group",
    Base.metadata,
    Column(
        "history_id",
        Integer,
        ForeignKey("history.id", ondelete="CASCADE"),
        primary_key=True),
    Column(
        "llm_id",
        Integer,
        ForeignKey("llms.id", ondelete="CASCADE"),
        primary_key=True),
)


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String, nullable=False)
    response = Column(String, nullable=True)

    llms = relationship("Llm", secondary=llm_group, back_populates="history_list")