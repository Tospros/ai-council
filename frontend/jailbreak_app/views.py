"""
Views for LLM Jailbreak Testing application.
"""
import asyncio
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

import sys
from pathlib import Path

# Add project root to path
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from database import SessionLocal, JailbreakSession, JailbreakAttempt, ModelStats
from backend.services import get_jailbreak_service


def get_db():
    """Get database session."""
    return SessionLocal()


class IndexView(View):
    """Main page view."""

    def get(self, request):
        """Render the main page."""
        db = get_db()
        try:
            sessions = db.query(JailbreakSession).order_by(
                JailbreakSession.created_at.desc()
            ).limit(10).all()

            stats = db.query(ModelStats).all()

            return render(request, 'index.html', {
                'sessions': sessions,
                'stats': stats
            })
        finally:
            db.close()


class SubmitPromptView(View):
    """Handle prompt submission."""

    def post(self, request):
        """Submit a new jailbreak test."""
        prompt = request.POST.get('prompt', '').strip()

        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)

        db = get_db()
        try:
            service = get_jailbreak_service(db)

            # Run the async jailbreak test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                session = loop.run_until_complete(
                    service.run_jailbreak_test(prompt)
                )
            finally:
                loop.close()

            return redirect('session_detail', session_id=session.id)
        finally:
            db.close()


class SessionDetailView(View):
    """View details of a jailbreak session."""

    def get(self, request, session_id):
        """Render session details."""
        db = get_db()
        try:
            session = db.query(JailbreakSession).filter(
                JailbreakSession.id == session_id
            ).first()

            if not session:
                return render(request, '404.html', status=404)

            attempts = db.query(JailbreakAttempt).filter(
                JailbreakAttempt.session_id == session_id
            ).all()

            return render(request, 'session_detail.html', {
                'session': session,
                'attempts': attempts
            })
        finally:
            db.close()


class RateAttemptView(View):
    """Handle rating submissions."""

    def post(self, request, attempt_id):
        """Rate a jailbreak attempt."""
        try:
            data = json.loads(request.body)
            rating = float(data.get('rating', 0))
            comment = data.get('comment', '')

            if not 1 <= rating <= 5:
                return JsonResponse(
                    {'error': 'Rating must be between 1 and 5'},
                    status=400
                )

            db = get_db()
            try:
                service = get_jailbreak_service(db)
                attempt = service.rate_attempt(attempt_id, rating, comment)

                if not attempt:
                    return JsonResponse(
                        {'error': 'Attempt not found'},
                        status=404
                    )

                return JsonResponse({
                    'success': True,
                    'rating': attempt.user_rating,
                    'comment': attempt.rating_comment
                })
            finally:
                db.close()

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except ValueError:
            return JsonResponse({'error': 'Invalid rating value'}, status=400)


class StatsView(View):
    """View model statistics."""

    def get(self, request):
        """Render statistics page."""
        db = get_db()
        try:
            stats = db.query(ModelStats).order_by(
                ModelStats.average_rating.desc()
            ).all()

            return render(request, 'stats.html', {'stats': stats})
        finally:
            db.close()


class ApiSessionsView(View):
    """API endpoint for sessions."""

    def get(self, request):
        """Get all sessions as JSON."""
        db = get_db()
        try:
            sessions = db.query(JailbreakSession).order_by(
                JailbreakSession.created_at.desc()
            ).limit(50).all()

            return JsonResponse({
                'sessions': [
                    {
                        'id': s.id,
                        'original_prompt': s.original_prompt,
                        'created_at': s.created_at.isoformat()
                    }
                    for s in sessions
                ]
            })
        finally:
            db.close()
