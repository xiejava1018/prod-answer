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
        try:
            return super().paginate_queryset(queryset, request, view)
        except Exception:
            # If page is out of range, return empty list
            return list()

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
