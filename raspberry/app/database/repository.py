from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List

from app.database.models import PromptHistory


class PromptHistoryRepository:
    """Repository for PromptHistory database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(
        self,
        id: str,
        prompt: str,
        rating: int,
        llm_name: str,
        response: Optional[str] = None
    ) -> PromptHistory:
        """Create a new prompt history record."""
        record = PromptHistory(
            id=id,
            prompt=prompt,
            rating=rating,
            llm_name=llm_name,
            response=response
        )
        self.session.add(record)
        await self.session.flush()
        await self.session.refresh(record)
        return record
    
    async def get_by_id(self, id: str) -> Optional[PromptHistory]:
        """Get a prompt history record by ID."""
        result = await self.session.execute(
            select(PromptHistory).where(PromptHistory.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[PromptHistory]:
        """Get all prompt history records with pagination."""
        result = await self.session.execute(
            select(PromptHistory)
            .order_by(PromptHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_llm_name(self, llm_name: str, limit: int = 100) -> List[PromptHistory]:
        """Get prompt history records by LLM name."""
        result = await self.session.execute(
            select(PromptHistory)
            .where(PromptHistory.llm_name == llm_name)
            .order_by(PromptHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_rating(self, id: str, rating: int) -> Optional[PromptHistory]:
        """Update the rating for a prompt history record."""
        record = await self.get_by_id(id)
        if record:
            record.rating = rating
            await self.session.flush()
            await self.session.refresh(record)
        return record
    
    async def delete(self, id: str) -> bool:
        """Delete a prompt history record."""
        record = await self.get_by_id(id)
        if record:
            await self.session.delete(record)
            await self.session.flush()
            return True
        return False
    
    async def bulk_create(self, records: List[dict]) -> List[PromptHistory]:
        """Bulk create prompt history records."""
        created = []
        for record_data in records:
            record = PromptHistory(**record_data)
            self.session.add(record)
            created.append(record)
        await self.session.flush()
        for record in created:
            await self.session.refresh(record)
        return created
