import random

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes.constants import (
    MAX_AVAILABLE_VALUE, MAX_INGREDIENT_NAME_LENGTH,
    MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH, MAX_RECIPE_NAME_LENGTH,
    MAX_RECIPE_SHORT_URL_LENGTH, MAX_TAG_NAME_LENGTH, MAX_TAG_SLUG_LENGTH,
    MIN_INGREDIENT_AMOUNT, MIN_RECIPE_COOKING_TIME, SHORT_URL_LENGTH,
    SHORT_URL_SYMBOLS
)

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""
    name = models.CharField(
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True,
        help_text=f'Максимальное кол-во символов: {MAX_TAG_NAME_LENGTH}.',
        verbose_name='Название'
    )
    slug = models.SlugField(
        max_length=MAX_TAG_SLUG_LENGTH,
        unique=True,
        verbose_name='Идентификатор',
        help_text='Символы латиницы, цифры, дефис, подчёркивание.',
    )

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента."""
    name = models.CharField(
        max_length=MAX_INGREDIENT_NAME_LENGTH,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_name_measure'
            )
        ]

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):
    def favorite_and_shopping_cart_annotate(self, user):
        """
        Метод, позволяющий добавить к объекту аннотированные поля
        с помощью подзапросов.
        """
        return self.annotate(
            is_favorited=models.Exists(
                Favorite.objects.filter(
                    recipe=models.OuterRef('pk'),
                    user=user
                )
            ),
            is_in_shopping_cart=models.Exists(
                ShoppingCart.objects.filter(
                    recipe=models.OuterRef('pk'),
                    user=user
                )
            ),
        )


class Recipe(models.Model):
    """Модель рецепта."""
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        help_text=f'Максимальное кол-во символов: {MAX_RECIPE_NAME_LENGTH}.',
        verbose_name='Название'
    )
    text = models.TextField('Описание')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        help_text='Укажите время в минутах.',
        validators=[MinValueValidator(MIN_RECIPE_COOKING_TIME),
                    MaxValueValidator(MAX_AVAILABLE_VALUE)]
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        verbose_name='Изображение'
    )
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    short_url = models.SlugField(
        max_length=MAX_RECIPE_SHORT_URL_LENGTH,
        verbose_name='Короткая ссылка',
        unique=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    objects = RecipeQuerySet.as_manager()

    @staticmethod
    def generate_short_url():
        while True:
            url = str.join('', random.choices(SHORT_URL_SYMBOLS,
                                              k=SHORT_URL_LENGTH))
            if not Recipe.objects.filter(short_url=url).exists():
                return url

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.short_url:
            self.short_url = self.generate_short_url()

        return super().save(force_insert, force_update, using, update_fields)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at', 'name')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    """Промежуточная модель связи ингредиентов и рецепта."""
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Кол-во',
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT),
                    MaxValueValidator(MAX_AVAILABLE_VALUE)]
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.ingredient.name


class FavoriteAndShoppingCartModel(models.Model):
    """Абстрактная модель для избранного и списка покупок."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        ordering = ('user', 'recipe')
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_%(class)s'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(FavoriteAndShoppingCartModel):
    """Модель добавления рецепта пользователем в избранное."""
    class Meta(FavoriteAndShoppingCartModel.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'


class ShoppingCart(FavoriteAndShoppingCartModel):
    """Модель добавления рецепта пользователем в список покупок."""
    class Meta(FavoriteAndShoppingCartModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Список покупок'
        default_related_name = 'shopping_cart'
