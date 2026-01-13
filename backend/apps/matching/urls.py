"""
URL configuration for matching app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import MatchingViewSet, RequirementViewSet

app_name = 'matching'

router = DefaultRouter()
router.register(r'matching', MatchingViewSet, basename='matching')
router.register(r'requirements', RequirementViewSet, basename='requirement')

urlpatterns = [
    path('', include(router.urls)),
]
