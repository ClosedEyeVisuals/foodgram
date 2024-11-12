from rest_framework.pagination import PageNumberPagination

from recipes.constants import PAGE_SIZE, PAGE_SIZE_QUERY_PARAM


class LimitPagination(PageNumberPagination):
    """
    Класс, позволяющий использовать кастомное название параметра запроса
    при пагинации списка объектов.
    """
    page_size = PAGE_SIZE
    page_size_query_param = PAGE_SIZE_QUERY_PARAM
