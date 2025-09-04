from rest_framework.pagination import PageNumberPagination
from shared.utils import standard_response


class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'  # Allow clients to set page size
    max_page_size = 50

    def get_paginated_response(self, data):
        """
        Override the default paginated response to include pagination details in the standard format.
        """
        return standard_response(
            success=True,
            message="Data fetched successfully.",
            data={
                "items": data,  # Paginated items
                "pagination": {
                    "count": self.page.paginator.count,
                    "current_page": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                }
            },
            errors=None,
            status_code=200  # HTTP 200 OK
        )
