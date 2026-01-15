"""
URL configuration for requirements app.
"""
from django.urls import path
from .views import RequirementUploadViewSet

app_name = 'requirements'

# ViewSet actions - use as_view to map HTTP methods to ViewSet actions
upload_view = RequirementUploadViewSet.as_view({
    'post': 'upload'
})

parse_text_view = RequirementUploadViewSet.as_view({
    'post': 'parse_text'
})

supported_formats_view = RequirementUploadViewSet.as_view({
    'get': 'supported_formats'
})

urlpatterns = [
    # Upload endpoints - 使用 file-uploads 前缀避免与 matching app 的 requirements 路由冲突
    path('file-uploads/upload/', upload_view, name='requirement-upload'),
    path('file-uploads/parse_text/', parse_text_view, name='requirement-parse-text'),
    path('file-uploads/supported_formats/', supported_formats_view, name='requirement-supported-formats'),
]
