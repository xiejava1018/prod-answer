from .base import *

DEBUG = True

# Add django-debug-toolbar
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Allow unauthenticated API access in development
REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = [
    'rest_framework.permissions.AllowAny',
]

# Display emails in console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# More verbose logging
LOGGING['root']['level'] = 'DEBUG'
