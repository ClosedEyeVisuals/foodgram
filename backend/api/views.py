from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (CreateModelMixin, ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (GenericViewSet, ModelViewSet,
                                     ReadOnlyModelViewSet)

from api.filters import IngredientFilter, RecipeFilter
from api.paginators import LimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarChangeSerializer, FavoriteWriteSerializer, FollowWriteSerializer,
    IngredientSerializer, PasswordChangeSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, ShoppingCartWriteSerializer, SubscriptionSerializer,
    TagSerializer, UserSerializer, UserSignupWriteSerializer
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


class UserViewSet(CreateModelMixin, ListModelMixin,
                  RetrieveModelMixin, GenericViewSet):
    """
    Вьюсет для выполнения операций чтения/создания/изменения/удаления
    объектов пользователя и подписки на других пользователей.
    """
    queryset = User.objects.all()
    pagination_class = LimitPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserSignupWriteSerializer
        elif self.action == 'set_password':
            return PasswordChangeSerializer
        elif self.action == 'avatar':
            return AvatarChangeSerializer
        elif self.action == 'subscribe':
            return FollowWriteSerializer
        elif self.action == 'subscriptions':
            return SubscriptionSerializer
        return UserSerializer

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data)

    @action(['put', 'delete'], detail=False,
            url_path='me/avatar', permission_classes=(IsAuthenticated,))
    def avatar(self, request):
        user = self.request.user
        if request.method == 'DELETE':
            user.avatar = None
            user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.set_avatar(instance=user,
                              validated_data=serializer.validated_data)
        return Response(
            {"avatar": f"{request.build_absolute_uri(user.avatar.url)}"},
            status=status.HTTP_200_OK
        )

    @action(['post'], detail=False, permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.change_password(instance=self.request.user,
                                   validated_data=serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk):
        if request.method == 'POST':
            data = {"user": request.user.id, "following": pk}
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        obj = Follow.objects.filter(user=self.request.user,
                                    following=self.get_object())
        if not obj.exists():
            return Response({"error": "Вы не подписаны на этого пользователя"},
                            status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        subs = User.objects.filter(followers__user=self.request.user)
        page = self.paginate_queryset(subs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    """
    Вьюсет для выполнения операций чтения/создания/изменения/удаления
    объектов рецепта и добавление их в избранное или список покупок.
    """
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    permission_classes = (IsAuthorOrReadOnly,)
    http_method_names = ('get', 'post', 'patch', 'delete')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action == 'create':
            return (IsAuthenticated(),)
        return super().get_permissions()

    def get_serializer_class(self):
        if (
                self.action == 'create' or
                self.action == 'partial_update'
        ):
            return RecipeWriteSerializer
        elif self.action == 'favorite':
            return FavoriteWriteSerializer
        elif self.action == 'shopping_cart':
            return ShoppingCartWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def manage_recipe_subscription(self, request, pk, model):
        if request.method == 'POST':
            data = {"user": request.user.id, "recipe": pk}
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        obj = model.objects.filter(user=self.request.user,
                                   recipe=self.get_object())
        if not obj.exists():
            return Response({"error": "Данный рецепт уже удалён."},
                            status=status.HTTP_400_BAD_REQUEST)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def create_shopping_list(self):
        user = self.request.user
        product_list = Recipe.objects.filter(
            shopping_cart__user=user
        ).values_list(
            'recipe_ingredients__ingredient__name',
            'recipe_ingredients__ingredient__measurement_unit',
            'recipe_ingredients__amount'
        )

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

    @action(['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return self.manage_recipe_subscription(request, pk, Favorite)

    @action(['post', 'delete'], detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.manage_recipe_subscription(request, pk, ShoppingCart)

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk):
        short_url = self.get_object().short_url
        return Response(
            {"short-link": request.build_absolute_uri(f'/s/{short_url}')})

    @action(detail=False, permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        return self.create_shopping_list()
