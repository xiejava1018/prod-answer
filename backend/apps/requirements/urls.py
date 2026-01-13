"""
URL configuration for requirements app.
"""
from django.urls import path
from .views import RequirementUploadViewSet

app_name = 'requirements'

urlpatterns = [
    # Upload endpoints (these are custom actions, not standard CRUD)
    path('requirements/upload/', RequirementUploadViewSet.as_view({'post': 'create'}), name='requirement-upload'),
    path('requirements/parse_text/', RequirementUploadViewSet.as_view({'post': 'parse_text'}), name='requirement-parse-text'),
    path('requirements/supported_formats/', RequirementUploadViewSet.as_view({'get': 'supported_formats'}), name='requirement-supported-formats'),
]
