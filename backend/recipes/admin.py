from django.contrib import admin
from django.db.models import Count

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'cooking_time',
        'author',
        'in_favorites_count'
    )
    search_fields = (
        'author__username',
        'name'
    )
    list_filter = ('tags',)
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInLine,)
    empty_value_display = 'Не задано'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(in_favorites_count=Count('favorites'))
        return queryset

    @admin.decorators.display(description='В избранном')
    def in_favorites_count(self, obj):
        return obj.in_favorites_count


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )
    search_fields = (
        'name',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = (
        'name',
    )


@admin.register(Favorite, ShoppingCart)
class FavoriteAndShoppingCartAdmin(admin.ModelAdmin):
    search_fields = (
        'user__username',
        'recipe__name'
    )
