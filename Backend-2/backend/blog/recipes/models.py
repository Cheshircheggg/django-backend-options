from django.db import models
from django.db.models import PositiveIntegerField, UniqueConstraint
from django.core.validators import MinValueValidator

from colorfield.fields import ColorField

from users.models import User

FIRST_LETTERS = 15


class Ingredients(models.Model):
    """
    Модель ингридиентов в рецепте.
    """

    name = models.CharField(
        'Название ингридиента',
        max_length=200,
        null=False,
        blank=False,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=50,
    )
    amount = models.CharField(
        'Количество',
        max_length=50,
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='ingridient_unique_relations'
            )
        ]

    def __str__(self):
        return self.name[:FIRST_LETTERS]


class Tag(models.Model):
    """
    Модель тега в рецепте.
    """

    name = models.CharField(
        'Название тега',
        max_length=200,
        unique=True,
    )
    color = ColorField(
        'Цвет',
        default='#FF0000',
        format='hex',
    )
    slug = models.SlugField(
        'Ссылка',
        max_length=200,
        unique=True,

    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:FIRST_LETTERS]


class Recipes(models.Model):
    """
    Модель рецепта.
    """

    name = models.CharField(
        'Название рецепта',
        max_length=200,
        null=False,
        blank=False,
    )
    text = models.TextField(
        'Описание рецепта',
        help_text='Опишите рецепт',
    )
    pud_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True,
    )
    image = models.ImageField(
        'Фото рецепта',
        upload_to='media/',
        null=True,
        blank=True,
    )
    author = models.ForeignKey(
        User,
        null=True,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
    )
    # ingredients = models.ManyToManyField(
    #     Ingredients,
    #     through='RecipesIngridientsRelation',
    #     verbose_name='Рецепты',
    # )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэги',
        # through='RecipesTagRelation',
        # null=True,
        related_name='recipes',
    )
    cooking_time = PositiveIntegerField(
        'Время приготовления',
        default=1,
        validators=[
            MinValueValidator(
                limit_value=1,
                message='Время приготовления должно быть не меньше 1 мин'
            )
        ]
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipesIngridientsRelation(models.Model):
    """
    рецепты в ингридиенте.
    """

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipeingredients'
    )
    ingredients = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        verbose_name='Ингридинеты',
        related_name='recipeingredients'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(
                1, 'Количество ингредиентов не может быть меньше 1!'
            ),
        ],
        default=1,
        verbose_name='Количество',
        help_text='Количество',
    )

    class Meta:
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredients'],
                name='recipe_ingridients_unique_relations'
            )
        ]


class RecipesTagRelation(models.Model):
    """
    Модель отношения рецепта к тегам.
    """

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_name',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        verbose_name='Тег',
    )

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'tag'],
                name='recipe_tag_unique_relations'
            )
        ]


class Favorite(models.Model):
    """
    Модель избранныйх рецептов.
    """

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'user'],
                name='favorite_unique_relations'
            )
        ]

    def __str__(self):
        return f'Избранные рецепты {self.user}: {self.recipe.name}'


class ShoppingList(models.Model):
    """
    Модель списка покупок.
    """

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='ShoppingCart',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ShoppingCart',
        verbose_name='Пользователь',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'user'],
                name='shoppingcart_unique_relations'
            )
        ]

    def __str__(self):
        return f'{self.recipe} у {self.user}'
