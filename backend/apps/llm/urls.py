"""
URL configuration for LLM app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LLMConfigViewSet, LLMAnalysisResultViewSet, LLMUsageLogViewSet

app_name = 'llm'

router = DefaultRouter()
router.register(r'llm-configs', LLMConfigViewSet, basename='llm-config')
router.register(r'analysis-results', LLMAnalysisResultViewSet, basename='llm-analysis-result')
router.register(r'usage', LLMUsageLogViewSet, basename='llm-usage')

urlpatterns = [
    path('', include(router.urls)),
]
