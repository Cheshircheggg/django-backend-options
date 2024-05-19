from django_filters import (
    FilterSet, CharFilter, ModelMultipleChoiceFilter,
    BooleanFilter, ModelChoiceFilter
)
from recipes.models import Recipes, Ingredients, Tag


class IngridientsFilter(FilterSet):
    name = CharFilter(
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredients
        fields = [
            'name'
        ]


class RecipeFilter(FilterSet):
    author = CharFilter(
        field_name='author__id',
        lookup_expr='icontains'
    )
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    is_favorite = BooleanFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = BooleanFilter(
        method='get_is_in_shopping_cart',
    )

    class Meta:
        model = Recipes
        fields = [
            'tags',
            'author',
            'is_favorite',
            'is_in_shopping_cart',
        ]

    def get_is_favorited(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(favorite__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if self.request.user.is_authenticated and value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset
