from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import include, path
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from recipes.models import (Ingredient, IngredientRecipeRelation, Recipe,
                            ShoppingCart, Tag)

User = get_user_model()


class APITests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api/', include('api.urls')),
    ]
    fixtures = ('users.json', 'recipes.json',)

    user: User
    user_follower: User
    recipe: Recipe

    user_client: APIClient
    anon_client: APIClient

    keys_post_detail: list

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_follower = get_object_or_404(User, pk=3)
        cls.recipe = Recipe.objects.all().first()
        cls.user = cls.recipe.author

        cls.keys_post_detail = sorted(
            ['id', 'name', 'image', 'cooking_time'])

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

    def tearDown(self):
        ShoppingCart.objects.all().delete()

    def test_user_download_shopping_cart(self):
        """Авторизованные пользователи. Скачать список покупок.
        Скачать файл со списком покупок. Это может быть TXT/PDF/CSV. Важно,
        чтобы контент файла удовлетворял требованиям задания."""

        endpoint = reverse('api:download_shopping_cart')
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)

        response = self.user_client.get(endpoint)
        headers = response._headers
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('content-length', headers)
        self.assertIn('content-disposition', headers)
        self.assertIn('content-type', headers)
        self.assertEqual(len(headers['content-length']), 2)
        self.assertEqual(len(headers['content-disposition']), 2)
        self.assertEqual(len(headers['content-type']), 2)
        self.assertGreater(int(headers['content-length'][1]), 0)
        self.assertEqual(
            headers['content-disposition'][1],
            'attachment; filename="shoppingcart.pdf"')
        self.assertEqual(headers['content-type'][1], 'application/pdf')

    def test_user_shopping_cart_add_item(self):
        """Авторизованные пользователи. Добавить рецепт в список покупок."""

        endpoint = reverse('api:shopping_cart', args=(self.recipe.pk,))
        recipes_in_cart_count_0 = ShoppingCart.objects.all().count()

        response = self.user_client.post(endpoint)
        recipes_in_cart_count_1 = ShoppingCart.objects.all().count()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sorted(response.data.keys()), self.keys_post_detail)
        self.assertEqual(recipes_in_cart_count_1, recipes_in_cart_count_0 + 1)
        self.assertEqual(self.user.shopping_cart.get().recipe, self.recipe)

        response = self.user_client.post(endpoint)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            ShoppingCart.objects.all().count(), recipes_in_cart_count_1)

    def test_user_shopping_cart_delete_item(self):
        """Авторизованные пользователи. Удалить рецепт из списка покупок."""

        endpoint = reverse('api:shopping_cart', args=(self.recipe.pk,))
        ShoppingCart.objects.create(user=self.user, recipe=self.recipe)
        recipes_in_cart_count_0 = ShoppingCart.objects.all().count()
        self.assertEqual(recipes_in_cart_count_0, 1)

        response = self.user_client.delete(endpoint)
        recipes_in_cart_count_1 = ShoppingCart.objects.all().count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(recipes_in_cart_count_1, recipes_in_cart_count_0 - 1)

        response = self.user_client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            ShoppingCart.objects.all().count(), recipes_in_cart_count_1)
