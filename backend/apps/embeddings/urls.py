"""
URL configuration for embeddings app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EmbeddingConfigViewSet, EmbeddingServiceViewSet

app_name = 'embeddings'

router = DefaultRouter()
router.register(r'configs', EmbeddingConfigViewSet, basename='embedding-config')
router.register(r'service', EmbeddingServiceViewSet, basename='embedding-service')

urlpatterns = [
    path('', include(router.urls)),
]
