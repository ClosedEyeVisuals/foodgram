from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.fields import Base64ImageField
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения списка/объекта пользователя."""
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return bool(
            request
            and request.user.is_authenticated
            and Follow.objects.filter(user=request.user,
                                      following=obj).exists()
        )


class AvatarChangeSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения аватара у объекта пользователя."""
    avatar = Base64ImageField(label='Изображение', required=True)

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения списка/объекта тега."""
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения списка/объекта ингредиента."""
    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для объектов ингредиента у объекта рецепта."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(),
                                            source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/изменения объекта рецепта."""
    ingredients = RecipeIngredientSerializer(many=True, label='Ингредиенты')
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True, label='Теги',)
    image = Base64ImageField(label='Изображение')

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )

    def validate(self, data):
        for value in ['ingredients', 'tags']:
            if value not in data:
                raise serializers.ValidationError(f'Добавьте {value}!')
        for field in data:
            if not data[field]:
                raise serializers.ValidationError(f'Поле {field} - пустое!')
        return data

    def validate_ingredients(self, value):
        ingredients_list = [elem['ingredient']['id'] for elem in value]
        if len(value) > len(set(ingredients_list)):
            raise serializers.ValidationError('Ингредиенты повторяются!')
        return value

    def validate_tags(self, value):
        if len(value) > len(set(value)):
            raise serializers.ValidationError('Теги повторяются!')
        return value

    @staticmethod
    def create_ingredients(recipe, ingredients):
        ingredient_list = [
            RecipeIngredient(
                ingredient=ingredient['ingredient']['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredient_list)

    @atomic()
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(
            **validated_data,
            author=self.context['request'].user,
        )
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    @atomic()
    def update(self, instance, validated_data):
        instance.ingredients.clear()
        self.create_ingredients(
            recipe=instance,
            ingredients=validated_data.pop('ingredients'),
        )
        instance.tags.clear()
        instance.tags.set(validated_data.pop('tags'))
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения списка/объекта рецепта."""
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients',
                                             many=True)
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        read_only_fields = fields


class RecipeMiniReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения объекта рецепта в с неполными данными."""
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = fields


class FavoriteAndShoppingCartSerializer(serializers.ModelSerializer):
    """
    Базовый класс для наследования сериализаторами избранного и списка покупок.
    """
    class Meta:
        fields = (
            'user',
            'recipe'
        )

    def to_representation(self, instance):
        return RecipeMiniReadSerializer(instance.recipe,
                                        context=self.context).data


class FavoriteWriteSerializer(FavoriteAndShoppingCartSerializer):
    """
    Сериализатор для добавления объекта рецепта в избранное пользователя.
    """
    class Meta(FavoriteAndShoppingCartSerializer.Meta):
        model = Favorite
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже есть в избранном!'
            )
        ]


class ShoppingCartWriteSerializer(FavoriteAndShoppingCartSerializer):
    """
    Сериализатор для добавления объекта рецепта в список покупок пользователя.
    """
    class Meta(FavoriteAndShoppingCartSerializer.Meta):
        model = ShoppingCart
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Этот рецепт уже есть в списке покупок!'
            )
        ]


class FollowWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления объекта пользователя в подписки."""
    class Meta:
        model = Follow
        fields = (
            'user',
            'following'
        )
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Вы уже подписаны на этого пользователя!'
            )
        ]

    def validate(self, data):
        if data['user'] == data['following']:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя!')
        return data

    def to_representation(self, instance):
        return SubscriptionSerializer(instance.following,
                                      context=self.context).data


class SubscriptionSerializer(UserSerializer):
    """
    Сериализатор для чтения объекта пользователя с объектами рецептов внутри.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar'
        )
        read_only_fields = fields

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        limit = self.context['request'].GET.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeMiniReadSerializer(
            recipes,
            many=True,
            context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
