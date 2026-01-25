"""
URL configuration for prod_answer project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.products.urls')),
    path('api/v1/', include('apps.embeddings.urls')),
    path('api/v1/', include('apps.matching.urls')),
    path('api/v1/', include('apps.requirements.urls')),
    path('api/v1/', include('apps.reports.urls')),
]

# Add debug toolbar URLs if installed
if 'debug_toolbar' in settings.INSTALLED_APPS:
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
