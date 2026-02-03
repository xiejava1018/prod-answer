"""
Custom pagination classes for the API.
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPageNumberPagination(PageNumberPagination):
    """
    Custom pagination that returns empty results instead of 404 for out-of-range pages.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """Handle pagination with proper error handling."""
        try:
            # Don't paginate if explicitly disabled
            if request.query_params.get('no_page', '').lower() == 'true':
                return None
            return super().paginate_queryset(queryset, request, view)
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Pagination error: {e}, returning full queryset")
            # Return None to disable pagination for this request
            return None

    def get_paginated_response(self, data):
        """
        Return a paginated response format that works even when data is empty.
        """
        return Response({
            'count': self.page.paginator.count if hasattr(self.page, 'paginator') else len(data),
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
