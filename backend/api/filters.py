from django_filters.rest_framework import (
    BooleanFilter, CharFilter, FilterSet, ModelMultipleChoiceFilter,
    NumberFilter
)

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """Класс, реализующий фильтрацию при получении объектов рецепта."""
    author = NumberFilter(field_name='author__id', label='id автора')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        label='Теги',
    )
    is_favorited = BooleanFilter(method='filter_is_favorited',
                                 label='Избранные')
    is_in_shopping_cart = BooleanFilter(method='filter_is_in_shopping_cart',
                                        label='В списке покупок')

    def filter_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart'
        )
