import random

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from api.fields import Base64ImageField
from recipes.constants import (MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH,
                               SHORT_URL_LENGTH, SHORT_URL_SYMBOLS)
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow

User = get_user_model()


class UserSignupReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения объектов пользователя при регистрации."""
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name'
        )


class UserSignupWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания объектов пользователя при регистрации."""
    password = serializers.CharField(min_length=MIN_PASSWORD_LENGTH)

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def to_representation(self, instance):
        return UserSignupReadSerializer(instance).data


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
            'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context['request']
        return (
            request.user.is_authenticated and
            Follow.objects.filter(user=request.user,
                                  following=obj).exists()
        )


class AvatarChangeSerializer(serializers.Serializer):
    """Сериализатор для изменения аватара у объекта пользователя."""
    avatar = Base64ImageField(label='Изображение', required=True)

    def set_avatar(self, instance, validated_data):
        instance.avatar = validated_data['avatar']
        instance.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля у объекта пользователя."""
    new_password = serializers.CharField(max_length=MAX_PASSWORD_LENGTH,
                                         min_length=MIN_PASSWORD_LENGTH,
                                         label='Новый пароль')
    current_password = serializers.CharField(max_length=MAX_PASSWORD_LENGTH,
                                             label='Текущий пароль')

    def validate(self, data):
        if data['current_password'] == data['new_password']:
            raise serializers.ValidationError(
                'Новый пароль не должен совпадать с текущим!')
        return data

    def validate_current_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Неправильный текущий пароль!')
        return value

    def change_password(self, instance, validated_data):
        instance.set_password(validated_data['new_password'])
        instance.save()
        return instance


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


class IngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания объекта ингредиента при создании рецета."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'amount'
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/изменения объекта рецепта."""
    ingredients = IngredientWriteSerializer(many=True, label='Ингредиенты')
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
        ingredients_list = [elem['id'] for elem in value]
        if len(value) > len(set(ingredients_list)):
            raise serializers.ValidationError('Ингредиенты повторяются!')
        return value

    def validate_tags(self, value):
        if len(value) > len(set(value)):
            raise serializers.ValidationError('Теги повторяются!')
        return value

    def create_ingredients(self, recipe, ingredients):
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount']
            )

    def create_tags(self, recipe, tags):
        for tag in tags:
            Recipe.tags.through.objects.create(recipe=recipe, tag=tag)

    def generate_short_url(self):
        return str.join('', random.choices(SHORT_URL_SYMBOLS,
                                           k=SHORT_URL_LENGTH))

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe(
            name=validated_data['name'],
            text=validated_data['text'],
            image=validated_data['image'],
            cooking_time=validated_data['cooking_time'],
            author=validated_data['author'],
            short_url=self.generate_short_url()
        )
        recipe.save()
        self.create_ingredients(recipe, ingredients)
        self.create_tags(recipe, tags)
        return recipe

    def update(self, instance, validated_data):
        instance.ingredients.clear()
        self.create_ingredients(
            recipe=instance,
            ingredients=validated_data.get('ingredients'),
        )
        instance.tags.clear()
        self.create_tags(
            recipe=instance,
            tags=validated_data.get('tags')
        )
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения объектов ингредиента у объекта рецепта."""
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения списка/объекта рецепта."""
    tags = TagSerializer(many=True)
    author = UserSerializer()
    ingredients = RecipeIngredientSerializer(source='recipe_ingredients',
                                             many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

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

    def get_is_favorited(self, obj):
        request = self.context['request']
        return (
                request.user.is_authenticated and
                Favorite.objects.filter(user=request.user,
                                        recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        request = self.context['request']
        return (
                request.user.is_authenticated and
                ShoppingCart.objects.filter(user=request.user,
                                            recipe=obj).exists()
        )


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

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        limit = self.context['request'].GET.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeMiniReadSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()
