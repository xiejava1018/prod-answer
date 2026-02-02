# Portal App Configuration

from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portal'
    verbose_name = '产品门户'

    def ready(self):
        # Import signal handlers when the app is ready
        from . import signals
        
        # Register portal models with admin
        from django.contrib import admin
        from . import models
        
        # Auto-register portal models
        portal_models = [
            models.Solution,
            models.Resource,
            models.PortalViewLog,
        ]
        
        for model in portal_models:
            if not admin.site.is_registered(model):
                admin.site.register(model)