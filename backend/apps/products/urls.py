"""
URL configuration for products app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, FeatureViewSet

app_name = 'products'

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'features', FeatureViewSet, basename='feature')

urlpatterns = [
    path('', include(router.urls)),
]
