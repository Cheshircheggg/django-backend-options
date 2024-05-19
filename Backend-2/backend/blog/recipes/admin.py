from django.contrib import admin

from .models import (
    Recipes, Ingredients, Tag, Favorite, ShoppingList, RecipesIngridientsRelation
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipesIngridientsRelation


@admin.register(Recipes)
class RecipesOnAdminPanel(admin.ModelAdmin):
    """
    Отображение модели Recipes в админ-зоне.
    """

    list_display = ('pk', 'name', 'author', 'favorites_amount')
    search_fields = ('name', 'author')
    list_filter = ('name', 'author', 'tags')
    inlines = [
        RecipeIngredientInline,
    ]

    @admin.display(description='В избранном')
    def favorites_amount(self, obj):
        return obj.favorites.count()


@admin.register(Ingredients)
class IngridientsOnAdminPanel(admin.ModelAdmin):
    """
    Отображение модели Ingridients в админ-зоне.
    """
    list_display = ('pk', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Tag)
class TagOnAdminPanel(admin.ModelAdmin):
    """
    Отображение модели Tag в админ-зоне.
    """

    list_display = ('pk', 'name', 'color', 'slug')
    search_fields = ('name', 'color', 'slug')
    list_filter = ('name', 'color', 'slug')


@admin.register(Favorite)
class FavoritesOnAdminPanel(admin.ModelAdmin):
    """
    Отображение модели Favorites в админ-зоне.
    """

    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')


@admin.register(ShoppingList)
class ShoppingListOnAdminPanel(admin.ModelAdmin):
    """
    Отображение модели ShoppingList в админ-зоне.
    """

    list_display = ('pk', 'user', 'recipe')
    search_fields = ('user', 'recipe')