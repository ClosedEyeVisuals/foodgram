from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import LimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarChangeSerializer, FavoriteWriteSerializer, FollowWriteSerializer,
    IngredientSerializer, RecipeReadSerializer, RecipeWriteSerializer,
    ShoppingCartWriteSerializer, SubscriptionSerializer, TagSerializer
)
from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow

User = get_user_model()


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для чтения списка/объекта тега."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для чтения списка/объекта ингредиента."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(DjoserUserViewSet):
    """
    Вьюсет для выполнения операций чтения/создания/изменения/удаления
    объектов пользователя и подписки на других пользователей.
    """
    queryset = User.objects.all()
    pagination_class = LimitPagination
    lookup_field = 'pk'

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(['put', 'delete'], detail=False,
            url_path='me/avatar', permission_classes=(IsAuthenticated,))
    def avatar(self, request):
        user = self.request.user
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarChangeSerializer(
            user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk):
        if request.method == 'POST':
            data = {"user": request.user.id, "following": pk}
            serializer = FollowWriteSerializer(
                data=data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        count, _ = Follow.objects.filter(
            user=self.request.user,
            following=self.get_object()
        ).delete()
        if not count:
            return Response({"error": "Вы не подписаны на этого пользователя"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        subs = User.objects.annotate(
            recipes_count=Count('recipes')
        ).filter(
            followers__user=self.request.user
        )
        page = self.paginate_queryset(subs)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """
    Вьюсет для выполнения операций чтения/создания/изменения/удаления
    объектов рецепта и добавление их в избранное или список покупок.
    """
    pagination_class = LimitPagination
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly]
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        return Recipe.objects.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    recipe=OuterRef('pk'),
                    user=self.request.user.is_authenticated
                    and self.request.user
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    recipe=OuterRef('pk'),
                    user=self.request.user.is_authenticated
                    and self.request.user
                )
            ),
        )

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'partial_update':
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @staticmethod
    def create_recipe_subscription(request, pk, serializer_class):
        data = {"user": request.user.id, "recipe": pk}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_recipe_subscription(self, model):
        count, _ = model.objects.filter(
            user=self.request.user,
            recipe=self.get_object()
        ).delete()
        if not count:
            return Response({"error": "Данный рецепт уже удалён."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.create_recipe_subscription(
                request,
                pk,
                FavoriteWriteSerializer
            )
        return self.delete_recipe_subscription(Favorite)

    @action(['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.create_recipe_subscription(
                request,
                pk,
                ShoppingCartWriteSerializer
            )
        return self.delete_recipe_subscription(ShoppingCart)

    def create_shopping_list(self, product_list):
        user = self.request.user
        product_dict = {}
        for product in product_list:
            name = product[0]
            if name not in product_dict:
                product_dict[name] = {
                    'Единица измерения': product[1],
                    'Кол-во': product[2]
                }
            else:
                product_dict[name]['Кол-во'] += product[2]
        shopping_list = ''
        for name, value in product_dict.items():
            shopping_list += (
                f"{name}: {value['Кол-во']} {value['Единица измерения']}.\n"
            )
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            f'attachment; filename="{user.username}`s_shopping_list.txt"'
        )
        return response

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        product_list = Recipe.objects.filter(
            shopping_cart__user=self.request.user
        ).values_list(
            'recipe_ingredients__ingredient__name',
            'recipe_ingredients__ingredient__measurement_unit',
            'recipe_ingredients__amount'
        )
        if not product_list:
            return Response({"message": "Список покупок пуст."},
                            status=status.HTTP_200_OK)
        return self.create_shopping_list(product_list)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk):
        short_url = self.get_object().short_url
        return Response(
            {"short-link": request.build_absolute_uri(f'/s/{short_url}')})
