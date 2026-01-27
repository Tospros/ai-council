"""
Backend services for jailbreak testing.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from database import (
    JailbreakSession,
    JailbreakAttempt,
    ModelStats,
    SessionLocal
)
from agents import get_orchestrator, JailbreakResult


class JailbreakService:
    """Service for managing jailbreak sessions and attempts."""

    def __init__(self, db: Session):
        self.db = db

    async def run_jailbreak_test(self, original_prompt: str) -> JailbreakSession:
        """Run a full jailbreak test and save results to database."""
        # Create session
        session = JailbreakSession(original_prompt=original_prompt)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Run orchestrator
        orchestrator = get_orchestrator()
        results = await orchestrator.run(original_prompt)

        # Save attempts
        for result in results:
            attempt = JailbreakAttempt(
                session_id=session.id,
                attacker_model=result.attacker_model,
                attacker_prompt=result.jailbreak_prompt,
                target_model="gemma3:1b",
                target_response=result.target_response
            )
            self.db.add(attempt)

            # Update model stats
            self._update_model_stats(result.attacker_model)

        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session(self, session_id: int) -> Optional[JailbreakSession]:
        """Get a jailbreak session by ID."""
        return self.db.query(JailbreakSession).filter(
            JailbreakSession.id == session_id
        ).first()

    def get_all_sessions(self, limit: int = 50) -> List[JailbreakSession]:
        """Get all jailbreak sessions."""
        return self.db.query(JailbreakSession).order_by(
            JailbreakSession.created_at.desc()
        ).limit(limit).all()

    def get_attempt(self, attempt_id: int) -> Optional[JailbreakAttempt]:
        """Get a jailbreak attempt by ID."""
        return self.db.query(JailbreakAttempt).filter(
            JailbreakAttempt.id == attempt_id
        ).first()

    def rate_attempt(
        self,
        attempt_id: int,
        rating: float,
        comment: Optional[str] = None
    ) -> Optional[JailbreakAttempt]:
        """Rate a jailbreak attempt."""
        attempt = self.get_attempt(attempt_id)
        if not attempt:
            return None

        attempt.user_rating = rating
        attempt.rating_comment = comment
        attempt.rated_at = datetime.utcnow()

        # Update model stats with new rating
        self._update_model_stats_with_rating(attempt.attacker_model, rating)

        self.db.commit()
        self.db.refresh(attempt)

        return attempt

    def get_model_stats(self) -> List[ModelStats]:
        """Get statistics for all models."""
        return self.db.query(ModelStats).all()

    def _update_model_stats(self, model_name: str) -> None:
        """Update model stats after an attempt."""
        stats = self.db.query(ModelStats).filter(
            ModelStats.model_name == model_name
        ).first()

        if not stats:
            stats = ModelStats(
                model_name=model_name,
                total_attempts=0,
                total_ratings=0,
                average_rating=0.0
            )
            self.db.add(stats)

        stats.total_attempts += 1
        stats.updated_at = datetime.utcnow()

    def _update_model_stats_with_rating(
        self,
        model_name: str,
        new_rating: float
    ) -> None:
        """Update model stats with a new rating."""
        stats = self.db.query(ModelStats).filter(
            ModelStats.model_name == model_name
        ).first()

        if stats:
            # Recalculate average
            total = stats.average_rating * stats.total_ratings + new_rating
            stats.total_ratings += 1
            stats.average_rating = total / stats.total_ratings
            stats.updated_at = datetime.utcnow()


def get_jailbreak_service(db: Session) -> JailbreakService:
    """Factory function for JailbreakService."""
    return JailbreakService(db)
