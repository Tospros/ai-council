"""
URL patterns for jailbreak_app.
"""
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    # Main pages
    path('', views.IndexView.as_view(), name='index'),
    path('submit/', views.SubmitPromptView.as_view(), name='submit_prompt'),
    path('session/<int:session_id>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('stats/', views.StatsView.as_view(), name='stats'),

    # Rating endpoint
    path('rate/<int:attempt_id>/', csrf_exempt(views.RateAttemptView.as_view()), name='rate_attempt'),

    # API endpoints
    path('api/sessions/', views.ApiSessionsView.as_view(), name='api_sessions'),
]
