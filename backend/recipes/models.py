from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from sorl.thumbnail import ImageField

from core.images import upload_to

User = get_user_model()


class BaseModel(models.Model):
    created = models.DateTimeField(
        verbose_name='Дата создания', auto_now_add=True)

    class Meta:
        abstract = True


class Tag(models.Model):
    name = models.CharField(
        'Имя тега', max_length=150, unique=True,)
    color = models.CharField(
        'Цвет', help_text=(
            'Введите код цвета в шестнадцетиричном формате (#ABCDEF)'),
        max_length=7, validators=(
            RegexValidator(
                regex='^#[a-fA-F0-9]{6}$', code='wrong_hex_code',
                message='Неправильный формат цвета'),))
    slug = models.SlugField(
        'Slug', help_text='Введите slug тега', unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'теги'
        ordering = ('id',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингридиента', max_length=200)
    measurement_unit = models.CharField(
        'Единица измерения', max_length=32)

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'ингридиенты'
        ordering = ('id',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'), name='Unique ingredient')
        ]

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(BaseModel):
    """Модель рецептов."""
    author = models.ForeignKey(
        User, verbose_name='Автор рецепта', on_delete=models.CASCADE,
        related_name='recipes', )
    image = ImageField(
        'Картинка', upload_to=upload_to, blank=False)
    name = models.CharField(
        'Название рецепта', max_length=200)
    text = models.TextField(
        'Описание рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления', validators=(MinValueValidator(1),))
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes')
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name='Ингридиенты', related_name='recipes',
        through='IngredientRecipeRelation')

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'рецепты'
        ordering = ('-created',)

    def __str__(self):
        return self.name


class TagInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
    )


class IngredientRecipeRelation(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        'Количество', validators=(MinValueValidator(1),))

    class Meta:
        verbose_name = 'Ингредиенты для рецепта'
        verbose_name_plural = 'Ингредиенты для рецепта'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='Unique ingredient for recipe')
        ]

    def __str__(self):
        return '{} ({})'.format(self.ingredient.name, self.recipe.name)


class Subscription(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions',
        verbose_name='Пользователь')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscripters',
        verbose_name='Автор')

    class Meta:
        ordering = ('id',)
        verbose_name = 'подписка'
        verbose_name_plural = 'подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'user'), name='Unique subscription')
        ]

    def __str__(self):
        return '\'{} {}\' подписан на \'{} {}\''.format(
            self.user.first_name, self.user.last_name, self.author.first_name,
            self.author.last_name
        )


class ShoppingCart(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='shopping_cart',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='shopping_cart',
        verbose_name='Рецепт')

    class Meta:
        ordering = ('id',)
        verbose_name = 'список покупок'
        verbose_name_plural = 'список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'), name='Unique cart')
        ]

    def __str__(self):
        return 'Рецепт \'{}\' в списке покупок \'{} {}\''.format(
            self.recipe.name, self.user.first_name, self.user.last_name
        )


class Favorite(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='favorites',
        verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт',
        related_name='favorites')

    class Meta:
        ordering = ('id',)
        verbose_name = 'избранное'
        verbose_name_plural = 'избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'user'), name='Unique favorite')
        ]

    def __str__(self):
        return 'Рецепт \'{}\' в избранном \'{} {}\''.format(
            self.recipe.name, self.user.first_name, self.user.last_name
        )
