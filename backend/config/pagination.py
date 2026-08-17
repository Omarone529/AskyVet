from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """
    Project-wide pagination.

    Clients can shrink or grow a page with ?page_size=, up to a ceiling that
    stops a single request from pulling an entire table.
    """

    page_size_query_param = "page_size"
    max_page_size = 100
