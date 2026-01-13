"""
URL configuration for reports app.
"""
from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

app_name = 'reports'

urlpatterns = [
    # Report endpoints will be added here
]

# Placeholder view
@api_view(['GET'])
def report_list(request):
    return Response({
        'message': 'Report functionality coming soon'
    })
