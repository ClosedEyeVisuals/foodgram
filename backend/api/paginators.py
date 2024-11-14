from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    """
    Класс, позволяющий использовать кастомное название параметра запроса
    при пагинации списка объектов.
    """
    page_size = settings.PAGE_SIZE
    page_size_query_param = settings.PAGE_SIZE_QUERY_PARAM
