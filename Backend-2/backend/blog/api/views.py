from http import HTTPStatus

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from djoser.views import UserViewSet

from rest_framework import status, viewsets, mixins
from rest_framework.filters import SearchFilter
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (
    AllowAny, IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination


from recipes.models import (
    Ingredients, Tag, Recipes, Favorite, ShoppingList,
    RecipesIngridientsRelation
)
from users.models import User, Follows
from .filter import IngridientsFilter, RecipeFilter
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    IngridientsSerializer, TagSerializer,RecipeListSerializer,
    GetRecipeSerializer, CreateUpdateRecipeSerializer,
    FavoritesSerializer, ShoppingListSerialSerializer,
    FollowsSerializer, GetFollowsSerializer, CreateUserSerializer, CurrentUserSerializer
)


class BaseUserViewset(
        mixins.ListModelMixin,
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        viewsets.GenericViewSet,
    ):
    """Получение списка всех подписок."""

    pagination_class = LimitOffsetPagination
    serializer_class = GetFollowsSerializer
    permission_classes = (AllowAny,)
    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return CurrentUserSerializer
        return CreateUserSerializer

    @action(
        detail=False, methods=['get'], pagination_class=None,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,),
        pagination_class=LimitOffsetPagination)
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
            Follows.objects.create(user=user, author=author)
            serializer = self.get_serializer(author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Follows.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewset(viewsets.ReadOnlyModelViewSet):
    """
        Вьха тегов
        """

    queryset = Tag.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = TagSerializer
    pagination_class = None


class IngridientViewset(viewsets.ReadOnlyModelViewSet):
    """
        вьюха ингридиентов
        """

    queryset = Ingredients.objects.all()
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    serializer_class = IngridientsSerializer
    filter_backend = (DjangoFilterBackend,)
    filterset_class = IngridientsFilter
    pagination_class = None


class RecipeViewset(viewsets.ModelViewSet):
    """
        вьюха рецептов.
        """

    queryset = Recipes.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = CreateUpdateRecipeSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    filterset_fields = ('tags',)

    def get_recipe_class_selection(self):
        if self.action in ('list', 'retrieve'):
            return GetRecipeSerializer
        return CreateUpdateRecipeSerializer

    def get_queryset(self):
        queryset = Recipes.objects.all()
        author = self.request.user
        if self.request.GET.get('is_favorited'):
            favorite_recipes_ids = Favorite.objects.filter(
                user=author).values('recipe_id')

            return queryset.filter(pk__in=favorite_recipes_ids)

        if self.request.GET.get('is_in_shopping_cart'):
            cart_recipes_ids = ShoppingList.objects.filter(
                user=author).values('recipe_id')
            return queryset.filter(pk__in=cart_recipes_ids)
        return queryset

    @action(detail=True, methods=['post', 'delete'],
            pagination_class=None,
            permission_classes=[IsAuthenticated, ])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == 'POST':
            serializer = FavoritesSerializer(
                data={'user': request.user.id, 'recipe': recipe.id, },
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if not Favorite.objects.filter(
                user=request.user, recipe=recipe).exists():
                Favorite.objects.create(
                    user=request.user, recipe=recipe)
                return Response(
                    'Рецепт уже добавлен в избранном',
                    status=status.HTTP_204_NO_CONTENT)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(
                Favorite, user=request.user,
                recipe=recipe).delete()
            return Response(
                'Рецепт удален из избранного',
                status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'],
            pagination_class=None,
            permission_classes=[IsAuthenticated, ])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        if request.method == 'POST':
            serializer = ShoppingListSerialSerializer(
                data={'user': request.user.id, 'recipe': recipe.id, },
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if not ShoppingList.objects.filter(
                    user=request.user, recipe=recipe).exists():
                ShoppingList.objects.create(
                    user=request.user, recipe=recipe)
                return Response(
                    'Рецепт уже добавлен в избранном',
                    status=status.HTTP_204_NO_CONTENT)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(
                ShoppingList, user=request.user,
                recipe=recipe).delete()
            return Response(
                'Рецепт удален из спика покупок',
                status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = self.request.user
        queryset_shopping_cart = ShoppingList.objects.filter(
            user=user
        ).select_related(
            'recipe'
        ).values_list(
            'recipe__recipeingredients__ingredients__name',
            'recipe__recipeingredients__ingredients__measurement_unit'
        ).annotate(
            amount=Sum('recipe__recipeingredients__amount')
        )

        shopping_cart_list = f'Список покупок пользователя {user.username}:\n'
        for ingredient in queryset_shopping_cart:
            shopping_cart_list += (
                f'{ingredient[0]}: {ingredient[2]} {ingredient[1]}\n'
            )

        response = HttpResponse(
            shopping_cart_list, content_type='text.txt; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename=shopping_cart_list.txt'
        )
        return response
