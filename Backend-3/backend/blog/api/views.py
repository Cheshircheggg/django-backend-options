from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, mixins, viewsets

from api.filters import IngredientFilter, RecipeFilter
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipesWriteSerializer,
    TagSerialiser,
    UserCreateSerializer,
    UserGetSerializer,
    SetPasswordSerializer,
    UserSubscribeRepresentSerializer,
    ShoppingCartSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    ShoppingCart,
    Tag,
    RecipeIngredient,
)
from api.permissions import IsAdminAuthorOrReadOnly
from api.utils import create_model_instance, delete_model_instance
from users.models import Subscription, User
from api.services import convert_to_file
from api.pagination import PageLimitPagination


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение информации теги"""

    queryset = Tag.objects.all()
    serializer_class = TagSerialiser
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Получение информации ингридиенты."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipesViewSet(viewsets.ModelViewSet):
    """Использование рецепто. Создание/удадение/изменение"""

    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = RecipeFilter
    filterset_fields = ('tags',)
    permission_classes = (IsAdminAuthorOrReadOnly,)
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.action == 'favorite' or self.action == 'shopping_cart':
            return FavoriteSerializer
        return RecipesWriteSerializer

    def get_queryset(self):
        queryset = Recipe.objects.all()
        author = self.request.user
        if self.request.GET.get('is_favorited'):
            favorite_recipes_ids = Favorite.objects.filter(
                user=author).values('recipe_id')

            return queryset.filter(pk__in=favorite_recipes_ids)

        if self.request.GET.get('is_in_shopping_cart'):
            cart_recipes_ids = ShoppingCart.objects.filter(
                user=author).values('recipe_id')
            return queryset.filter(pk__in=cart_recipes_ids)
        return queryset

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def favorite(self, request, pk):
        """
        Работа с избранными рецептами.
        Удаление/добавление в избранное.
        """
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            return create_model_instance(request, recipe, FavoriteSerializer)

        error_message = 'У вас нет этого рецепта в избранном'
        return delete_model_instance(
            request.user,
            Favorite,
            recipe,
            error_message
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated, ]
    )
    def shopping_cart(self, request, pk):
        """
        Работа со списком покупок.
        Удаление/добавление в список покупок.
        """
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            return create_model_instance(
                request,
                recipe,
                ShoppingCartSerializer
            )

        error_message = 'У вас нет этого рецепта в списке покупок'
        return delete_model_instance(
            request.user,
            ShoppingCart,
            recipe,
            error_message
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated, ]
    )
    def download_shopping_cart(self, request):
        """Выгрузка списка покупок"""
        cart_ingredients = (
            RecipeIngredient.objects.filter(
                recipe__shopping_cart__user=request.user
            )
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
            )
            .annotate(ingredient_total_amount=Sum('amount'))
        )
        return convert_to_file(cart_ingredients)


class UserSubscriptionsViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Получение списка всех подписок."""

    pagination_class = PageLimitPagination
    serializer_class = UserSubscribeRepresentSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserGetSerializer
        return UserCreateSerializer

    @action(
        detail=False, methods=['get'], pagination_class=None,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = UserGetSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Пароль успешно изменен!'},
            status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=PageLimitPagination)
    def subscriptions(self, request):
        user = request.user
        favorites = user.follower.all()
        paginated_queryset = self.paginate_queryset(favorites)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True, methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            Subscription.objects.create(user=user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
