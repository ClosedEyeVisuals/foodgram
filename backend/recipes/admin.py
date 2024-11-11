from django.contrib import admin

from .models import Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag


class RecipeIngredientInLine(admin.TabularInline):
    model = RecipeIngredient
    extra = 0


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'cooking_time',
        'author',
        'in_favorites_count'
    )
    search_fields = (
        'author__username',
        'name',
    )
    list_filter = ('tags',)
    filter_horizontal = ('tags',)
    inlines = (RecipeIngredientInLine,)
    empty_value_display = 'Не задано'

    @admin.decorators.display(description='В избранном')
    def in_favorites_count(self, recipe):
        return recipe.favorites.count()


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'slug'
    )


class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = (
        'name',
    )


admin.site.register(Favorite)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(ShoppingCart)

