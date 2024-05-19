from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, get_list_or_404

from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework.validators import UniqueTogetherValidator
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField, PrimaryKeyRelatedField
from rest_framework.exceptions import ValidationError

from api.validators import validate_ingredients
from recipes.models import (
    Ingredients, Tag, Recipes, Favorite,
    ShoppingList, RecipesIngridientsRelation,
    RecipesTagRelation,
)
from users.models import User, Follows


class CreateUserSerializer(UserCreateSerializer):
    """
    Сериализатор регистрации пользователя.
    """

    password = serializers.CharField(
        style={
            'input_type': 'password'
        },
        write_only=True,
    )

    class Meta(UserCreateSerializer.Meta):
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')


class CurrentUserSerializer(UserSerializer):
    """
    Сериализатор модели пользователя.
    """

    is_subscribed = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Follows.objects.filter(
                user=request.user, author=obj).exists()
        return False


class IngridientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели ингридиентов.
    """

    class Meta:
        model = Ingredients
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели тегов.
    """

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngridientsSerializer(serializers.ModelSerializer):
    """
    Сериализатор вывода ингридиентов в рецепте.
    """

    name = serializers.ReadOnlyField(source='ingredients.name')
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all()
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = RecipesIngridientsRelation
        fields = ('id', 'name', 'amount', 'measurement_unit')


class CreateIngridientInRecipeSerializer(serializers.Serializer):
    """
    Сериализатор добавления ингридиентов в рецепт.
    """
    id = serializers.IntegerField()
    amount = serializers.IntegerField(write_only=True)


class GetRecipeSerializer(serializers.ModelSerializer):
    """
    Сриализатор модели рецепта:
    Получение и просмотр рецепта.
    """

    tags = TagSerializer(many=True)
    author = CurrentUserSerializer(read_only=True)
    ingredients = SerializerMethodField(

    )
    is_favorited = SerializerMethodField(

    )
    is_in_shopping_cart = SerializerMethodField(

    )
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipes
        fields = [
            'tags',
            'author',
            'name',
            'image',
            'text',
            'id',
            'ingredients',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart'
        ]
        read_only_fields = [
            'tags', 'author', 'name', 'image', 'text', 'id', 'ingredients', 'cooking_time'
        ]

    def get_ingredients(self, obj):
        return RecipeIngridientsSerializer(
            obj.recipeingredients.all(), many=True
        ).data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is request.user.is_anonymous:
            return False
        data = Favorite.objects.filter(
            recipe=obj, user=request.user
        ).exists()
        return data

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is request.user.is_anonymous:
            return False
        data = ShoppingList.objects.filter(
            user=request.user, recipe=obj
        ).exists()
        return data


class CreateUpdateRecipeSerializer(serializers.ModelSerializer):
    """
    Сериализатор модели Recipe:
    создание и изменение рецепта.
    """
    author = CurrentUserSerializer(read_only=True)
    ingredients = CreateIngridientInRecipeSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField(use_url=True)

    class Meta:
        model = Recipes
        fields = ('id', 'author', 'tags', 'name', 'image', 'text',
                  'ingredients', 'cooking_time')

    @staticmethod
    def __add_ingredients__(recipe, ingredients):
        RecipesIngridientsRelation.objects.bulk_create([
            RecipesIngridientsRelation(
                recipe=recipe,
                ingredients=get_object_or_404(
                    Ingredients,
                    pk=ingr.get('id')),
                amount=ingr.get('amount')
            ) for ingr in ingredients
        ])

    def validate_ingredients(self, attrs):
        ingredients = self.initial_data.get('ingredients')
        list = []
        if not ingredients:
            raise ValidationError(
                'Количество ингридиентов не может быть меньше 0'
            )
        if len(set(list)) != len(list):
            raise ValidationError(
                'Ингридиенты не должны повторяться.'
            )
        return attrs

    def create(self, validated_data):
        author = self.context.get('request').user
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        recipe = Recipes.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.__add_ingredients__(recipe, ingredients)
        recipe.tags.set(tags)
        return recipe

    def update(self, recipe, validated_data):
        ingredients = self.initial_data.pop('ingredients')
        recipe.recipeingredients.all().delete()
        self.__add_ingredients__(recipe, ingredients)
        tags = self.initial_data.pop('tags')
        recipe.tags.set(tags)
        return super().update(recipe, validated_data)

    def to_representation(self, instance):
        serializer = GetRecipeSerializer(instance, context=self.context)
        return serializer.data


class FavoritesSerializer(serializers.ModelSerializer):
    """
    Сериализатор отображения избранного.
    """

    class Meta:
        model = Favorite
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeListSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class ShoppingListSerialSerializer(serializers.ModelSerializer):
    """
    Сериализатор списка покупок.
    """

    class Meta:
        model = ShoppingList
        fields = '__all__'

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeListSerializer(
            instance.recipe,
            context={'request': request}
        ).data


class FollowsSerializer(serializers.ModelSerializer):
    """
    Сериализатор подписок.
    """

    class Meta:
        model = Follows
        fields = '__all__'

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and not request.user.is_anonymous:
            return Follows.objects.filter(
                user=request.user, author=obj).exists()
        return False

    def to_representation(self, instance):
        request = self.context.get('request')
        return GetFollowsSerializer(
            instance.author, context={'request': request}
        ).data


class GetFollowsSerializer(serializers.ModelSerializer):
    """
    Сериализатор получения/отображения подписок.
    """
    id = serializers.IntegerField(source='author.id')
    email = serializers.EmailField(source='author.email')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        ]

    def get_is_subscribed(self, obj):
        return Follows.objects.filter(user=obj.user,
                                      author=obj.author).exists()

    def get_recipes(self, obj):
        recipes = get_list_or_404(Recipes, author=obj.author)
        serializer = RecipeListSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(author=obj.author).count()


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для предоставления информации о рецептах."""

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')
