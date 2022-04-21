from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import include, path
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from recipes.models import Ingredient, IngredientRecipeRelation, Recipe, Tag

User = get_user_model()


class APITests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api/', include('api.urls')),
    ]
    fixtures = ('users.json', 'recipes.json',)

    user: User
    ingredient: Ingredient

    user_client: APIClient
    anon_client: APIClient

    keys_get_list: list
    keys_get_detail: list

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_object_or_404(User, pk=2)
        cls.ingredient = Ingredient.objects.all().first()

        cls.keys_get_list = sorted(['id', 'name', 'measurement_unit'])
        cls.keys_get_detail = cls.keys_get_list

    @classmethod
    def tearDownClass(cls):
        IngredientRecipeRelation.objects.all().delete()
        Tag.objects.all().delete()
        Ingredient.objects.all().delete()
        Recipe.objects.all().delete()
        User.objects.all().delete()

    def setUp(self):
        self.anon_client = APIClient()

        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

    def __ingredient_list(self, apiclient):
        endpoint = reverse('api:ingredients-list')

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(list(response.data[0].keys())), self.keys_get_list)
        self.assertEqual(response.data[0]['id'], self.ingredient.pk)
        self.assertEqual(response.data[0]['name'], self.ingredient.name)
        self.assertEqual(len(response.data), Ingredient.objects.all().count())

        last_ingredient = Ingredient.objects.all().last()
        endpoint = reverse('api:ingredients-list') + '?name={}'.format(
            last_ingredient.name)

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(list(response.data[0].keys())), self.keys_get_list)
        self.assertEqual(response.data[0]['id'], last_ingredient.pk)
        self.assertEqual(response.data[0]['name'], last_ingredient.name)
        self.assertEqual(
            len(response.data),
            Ingredient.objects.filter(name=last_ingredient.name).count())

        missing_ingredient = 'neverfindit'
        endpoint = reverse('api:ingredients-list') + '?name={}'.format(
            missing_ingredient)

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data),
            Ingredient.objects.filter(name=missing_ingredient).count())

    def __ingredient_detail(self, apiclient):
        endpoint = reverse(
            'api:ingredients-detail', args=(self.ingredient.pk,))

        response = apiclient.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(list(response.data.keys())), self.keys_get_detail)
        self.assertEqual(response.data['id'], self.ingredient.pk)
        self.assertEqual(response.data['name'], self.ingredient.name)

    def test_anon_ingredient_list(self):
        """Неавторизованные пользователи. Список ингредиентов.
        Список ингредиентов с возможностью поиска по имени."""

        self.__ingredient_list(self.anon_client)

    def test_anon_ingredient_detail(self):
        """Неавторизованные пользователи. Получение ингредиента.
        Уникальный идентификатор этого ингредиента."""

        self.__ingredient_detail(self.anon_client)

    def test_user_ingredient_list(self):
        """Авторизованные пользователи. Список ингредиентов.
        Список ингредиентов с возможностью поиска по имени."""

        self.__ingredient_list(self.user_client)

    def test_user_ingredient_detail(self):
        """Авторизованные пользователи. Получение ингредиента.
        Уникальный идентификатор этого ингредиента."""

        self.__ingredient_detail(self.user_client)
