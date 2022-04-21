from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models, transaction
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.urls import include, path
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from recipes.models import (Favorite, Ingredient, IngredientRecipeRelation,
                            Recipe, ShoppingCart, Subscription, Tag)

User = get_user_model()


class APITests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api/', include('api.urls')),
    ]
    fixtures = ('users.json', 'recipes.json',)

    user: User
    user_follower: User
    tag: Tag
    ingredient: Ingredient
    recipe: Recipe

    recipe_count: int

    user_client: APIClient
    user_follower_client: APIClient
    anon_client: APIClient

    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    )
    small_gif_name = 'small.gif'

    keys_get_list_detail: list
    keys_get_list_detail_author: list
    keys_get_list_detail_tags: list
    keys_get_list_detail_ingredients: list
    keys_post_list_detail: list
    keys_post_list_detail_author: list
    keys_post_list_detail_tags: list
    keys_post_list_detail_ingredients: list

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.tag = Tag.objects.all().first()
        cls.ingredient = Ingredient.objects.all().first()
        cls.recipe = Recipe.objects.all().first()
        cls.recipe_count = Recipe.objects.all().count()
        cls.user = cls.recipe.author
        cls.user_follower = get_object_or_404(User, pk=3)

        for model in [Favorite, ShoppingCart]:
            model.objects.create(user=cls.user_follower, recipe=cls.recipe)

        cls.keys_get_list_detail = sorted(
            ['id', 'tags', 'author', 'ingredients', 'is_favorited',
             'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'])
        cls.keys_get_list_detail_author = sorted(
            ['email', 'username', 'id', 'first_name', 'last_name',
             'is_subscribed'])
        cls.keys_get_list_detail_tags = sorted(['id', 'name', 'color', 'slug'])
        cls.keys_get_list_detail_ingredients = sorted(
            ['id', 'name', 'amount', 'measurement_unit'])
        cls.keys_post_list_detail = cls.keys_get_list_detail
        cls.keys_post_list_detail_author = cls.keys_get_list_detail_author
        cls.keys_post_list_detail_tags = cls.keys_get_list_detail_tags
        cls.keys_post_list_detail_ingredients = (
            cls.keys_get_list_detail_ingredients)

    @classmethod
    def tearDownClass(cls):
        IngredientRecipeRelation.objects.all().delete()
        Tag.objects.all().delete()
        Ingredient.objects.all().delete()
        Recipe.objects.all().delete()
        User.objects.all().delete()
        Favorite.objects.all().delete()
        Subscription.objects.all().delete()
        ShoppingCart.objects.all().delete()

    def setUp(self):
        self.anon_client = APIClient()

        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

        self.user_follower_client = APIClient()
        self.user_follower_client.force_authenticate(user=self.user_follower)

    def __recipe_list(self, apiclient):
        """Список рецептов.
        Страница доступна всем пользователям. Доступна фильтрация по
        избранному, автору, списку покупок и тегам."""

        # Запрос без параметров
        endpoint = reverse('api:recipes-list')

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data['results'][0].keys()),
            self.keys_get_list_detail)
        self.assertEqual(
            sorted(response.data['results'][0]['ingredients'][0].keys()),
            self.keys_get_list_detail_ingredients)
        self.assertEqual(
            sorted(response.data['results'][0]['author'].keys()),
            self.keys_get_list_detail_author)
        self.assertEqual(
            sorted(response.data['results'][0]['tags'][0].keys()),
            self.keys_get_list_detail_tags)
        self.assertEqual(response.data['count'], self.recipe_count)
        self.assertEqual(response.data['results'][0]['name'], self.recipe.name)
        self.assertIsNone(response.data['next'])

        # Пагинатор
        endpoint = reverse('api:recipes-list') + '?limit=1'

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], self.recipe_count)
        self.assertEqual(response.data['results'][0]['name'], self.recipe.name)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        self.assertEqual(len(response.data['results']), 1)

        endpoint = reverse('api:recipes-list') + '?limit=1&page=2'

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], self.recipe_count)
        self.assertNotEqual(
            response.data['results'][0]['name'], self.recipe.name)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])
        self.assertEqual(len(response.data['results']), 1)

        # Фильтрация по автору
        endpoint = reverse('api:recipes-list') + '?author={}'.format(
            self.user.pk)
        author_recipes = self.user.recipes.all()
        author_recipe_count = author_recipes.count()

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], author_recipe_count)
        self.assertEqual(
            response.data['results'][0]['name'], author_recipes[0].name)

        # Фильтрация по тегам
        endpoint = reverse('api:recipes-list') + '?tags={}'.format(
            self.tag.slug)
        tag1_recipe_count = self.tag.recipes.all().count()

        query = models.Q(tags__pk=1) | models.Q(tags__pk=2)
        tag1_2_recipe_count = Recipe.objects.filter(query).distinct().count()

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], tag1_recipe_count)

        endpoint = reverse('api:recipes-list') + '?tags={}&tags={}'.format(
            self.tag.slug, get_object_or_404(Tag, pk=2).slug)

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], tag1_2_recipe_count)

    def __recipe_detail(self, apiclient):
        """Получение рецепта."""
        endpoint = reverse('api:recipes-detail', args=(self.recipe.pk,))

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data.keys()), self.keys_get_list_detail)
        self.assertEqual(
            sorted(response.data['ingredients'][0].keys()),
            self.keys_get_list_detail_ingredients)
        self.assertEqual(
            sorted(response.data['author'].keys()),
            self.keys_get_list_detail_author)
        self.assertEqual(
            sorted(response.data['tags'][0].keys()),
            self.keys_get_list_detail_tags)
        self.assertEqual(response.data['id'], self.recipe.pk)

    def test_anon_recipe_list(self):
        """Неавторизованные пользователи. Список рецептов.
        Страница доступна всем пользователям. Доступна фильтрация по
        избранному, автору, списку покупок и тегам."""

        self.__recipe_list(self.anon_client)

        # Фильтрация по избранному
        endpoint = reverse('api:recipes-list') + '?is_favorited=1'

        response = self.anon_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Фильтрация по списку покупок
        endpoint = reverse('api:recipes-list') + '?is_in_shopping_cart=1'

        response = self.anon_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_anon_recipe_detail(self):
        """Неавторизованные пользователи. Получение рецепта."""

        self.__recipe_detail(self.anon_client)

    def test_user_recipe_list(self):
        """Авторизованные пользователи. Список рецептов.
        Страница доступна всем пользователям. Доступна фильтрация по
        избранному, автору, списку покупок и тегам."""

        self.__recipe_list(self.user_client)

        # Фильтрация по избранному
        endpoint = reverse('api:recipes-list') + '?is_favorited=1'

        response = self.user_follower_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.recipe.pk)

        # Фильтрация по списку покупок
        endpoint = reverse('api:recipes-list') + '?is_in_shopping_cart=1'

        response = self.user_follower_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.recipe.pk)

    def test_user_recipe_detail(self):
        """Авторизованные пользователи. Получение рецепта."""

        self.__recipe_detail(self.user_client)

    def test_user_recipe_create(self):
        """Авторизованные пользователи. Создание рецепта."""

        endpoint = reverse('api:recipes-list')
        recipe_data = {
            'ingredients': [{'id': self.ingredient.pk, 'amount': 100}],
            'tags': [self.tag.pk],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAg'
                     'MAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAA'
                     'AOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg'
                     '==',
            'name': 'string',
            'text': 'string',
            'cooking_time': 1
        }

        recipe_data_with_missing_ingredient = recipe_data.copy()
        recipe_data_with_missing_ingredient['ingredients'] = [{
            'id': 10000, 'amount': 135}]
        recipe_data_with_missing_tags = recipe_data.copy()
        recipe_data_with_missing_tags['tags'] = [10000]

        response = self.user_client.post(
            endpoint, data=recipe_data_with_missing_tags, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.user_client.post(
            endpoint, data=recipe_data_with_missing_ingredient, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.user_client.post(
            endpoint, data=recipe_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            sorted(response.data.keys()), self.keys_post_list_detail)
        self.assertEqual(
            sorted(response.data['ingredients'][0].keys()),
            self.keys_post_list_detail_ingredients)
        self.assertEqual(
            sorted(response.data['author'].keys()),
            self.keys_post_list_detail_author)
        self.assertEqual(
            sorted(response.data['tags'][0].keys()),
            self.keys_post_list_detail_tags)
        self.assertEqual(response.data['name'], recipe_data['name'])

        recipe_count = Recipe.objects.count()
        self.assertEqual(self.recipe_count + 1, recipe_count)

    @transaction.atomic
    def __create_recipe(self):
        uploaded = SimpleUploadedFile(
            name=self.small_gif_name, content=self.small_gif,
            content_type='image/gif')

        new_recipe = Recipe.objects.create(
            cooking_time=100, author=self.user, name='recipe name',
            text='recipe instructions', image=uploaded)
        new_recipe.tags.set([self.tag])
        IngredientRecipeRelation.objects.create(
            recipe=new_recipe, ingredient=self.ingredient, amount=1001).save()

        new_recipe.save()

        return new_recipe

    def test_user_recipe_update(self):
        """Авторизованные пользователи. Обновление рецепта."""

        new_recipe = self.__create_recipe()
        endpoint = reverse('api:recipes-detail', args=(new_recipe.pk,))
        updated_recipe_name = 'updated_recipe_name'
        update_data = model_to_dict(
            new_recipe, fields=('text', 'cooking_time'))
        update_data.update({
            'ingredients': [{'id': self.ingredient.pk, 'amount': 100}],
            'tags': [self.tag.pk],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAg'
                     'MAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAA'
                     'AOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg'
                     '==',
            'name': updated_recipe_name
        })

        recipe_count = Recipe.objects.all().count()
        response = self.user_client.patch(
            endpoint, data=update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data.keys()), self.keys_post_list_detail)
        self.assertEqual(
            sorted(response.data['ingredients'][0].keys()),
            self.keys_post_list_detail_ingredients)
        self.assertEqual(
            sorted(response.data['author'].keys()),
            self.keys_post_list_detail_author)
        self.assertEqual(
            sorted(response.data['tags'][0].keys()),
            self.keys_post_list_detail_tags)
        self.assertEqual(Recipe.objects.all().count(), recipe_count)
        self.assertEqual(response.data['name'], updated_recipe_name)

        new_recipe.delete()

    def test_user_notmine_recipe_update(self):
        """Авторизованные пользователи.
        Обновление рецепта другого пользователя."""

        new_recipe = self.__create_recipe()
        endpoint = reverse('api:recipes-detail', args=(new_recipe.pk,))

        update_data = model_to_dict(
            new_recipe, fields=('text', 'name', 'cooking_time'))

        update_data.update({
            'ingredients': [{'id': self.ingredient.pk, 'amount': 100}],
            'tags': [self.tag.pk],
            'image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAg'
                     'MAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAA'
                     'AOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg'
                     '==',
        })

        recipe_count = Recipe.objects.all().count()
        response = self.user_follower_client.patch(
            endpoint, data=update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Recipe.objects.all().count(), recipe_count)

        new_recipe.delete()

    def test_user_recipe_delete(self):
        """Авторизованные пользователи. Удаление рецепта."""

        new_recipe = self.__create_recipe()
        endpoint = reverse('api:recipes-detail', args=(new_recipe.pk,))

        recipe_count = Recipe.objects.all().count()
        response = self.user_client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recipe.objects.all().count() + 1, recipe_count)

    def test_user_notmine_recipe_delete(self):
        """Авторизованные пользователи.
        Удаление рецепта другого пользователя."""

        new_recipe = self.__create_recipe()
        endpoint = reverse('api:recipes-detail', args=(new_recipe.pk,))

        recipe_count = Recipe.objects.all().count()
        response = self.user_follower_client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Recipe.objects.all().count(), recipe_count)
