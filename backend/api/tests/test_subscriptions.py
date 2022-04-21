from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import include, path
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

from recipes.models import (Ingredient, IngredientRecipeRelation, Recipe,
                            Subscription, Tag)

User = get_user_model()


class APITests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api/', include('api.urls')),
    ]
    fixtures = ('users.json', 'recipes.json',)

    user: User
    user_follower: User
    recipe: Recipe

    user_follower_client: APIClient
    anon_client: APIClient

    keys_get_list: list
    keys_get_list_recipes: list
    keys_post_detail: list
    keys_post_detail_recipes: list

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_object_or_404(User, pk=2)
        cls.user_follower = get_object_or_404(User, pk=3)

        cls.keys_get_list = sorted(
            ['email', 'id', 'username', 'first_name', 'last_name',
             'is_subscribed', 'recipes', 'recipes_count'])
        cls.keys_post_detail = cls.keys_get_list
        cls.keys_get_list_recipes = sorted(
            ['id', 'name', 'image', 'cooking_time'])
        cls.keys_post_detail_recipes = cls.keys_get_list_recipes

    @classmethod
    def tearDownClass(cls):
        IngredientRecipeRelation.objects.all().delete()
        Tag.objects.all().delete()
        Ingredient.objects.all().delete()
        Recipe.objects.all().delete()
        User.objects.all().delete()

    def setUp(self):
        self.anon_client = APIClient()

        self.user_follower_client = APIClient()
        self.user_follower_client.force_authenticate(user=self.user_follower)

    def tearDown(self):
        Subscription.objects.all().delete()

    def test_user_subscriptions_list(self):
        """Авторизованные пользователи. Мои подписки.
        Возвращает пользователей, на которых подписан текущий пользователь. В
        выдачу добавляются рецепты."""

        endpoint = reverse('api:subscriptions')
        subscription_count_0 = Subscription.objects.all().count()

        response = self.user_follower_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], subscription_count_0)

        Subscription.objects.create(user=self.user_follower, author=self.user)

        response = self.user_follower_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data['results'][0].keys()), self.keys_get_list)
        self.assertEqual(
            sorted(response.data['results'][0]['recipes'][0].keys()),
            self.keys_get_list_recipes)
        self.assertEqual(response.data['count'], subscription_count_0 + 1)

    def test_user_subscriptions_add_item(self):
        """Авторизованные пользователи. Подписаться на пользователя."""

        endpoint = reverse('api:subscribe', args=(self.user.pk,))
        subscription_count_0 = Subscription.objects.all().count()

        response = self.user_follower_client.post(endpoint)
        subscription_count_1 = Subscription.objects.all().count()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(sorted(response.data.keys()), self.keys_get_list)
        self.assertEqual(
            sorted(response.data['recipes'][0].keys()),
            self.keys_get_list_recipes)
        self.assertEqual(subscription_count_1, subscription_count_0 + 1)

        response = self.user_follower_client.post(endpoint)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Subscription.objects.all().count(), subscription_count_1)

    def test_user_subscriptions_delete_item(self):
        """Авторизованные пользователи. Отписаться от пользователя.
        Доступно только авторизованным пользователям."""

        endpoint = reverse('api:subscribe', args=(self.user.pk,))
        Subscription.objects.create(user=self.user_follower, author=self.user)
        subscription_count_0 = Subscription.objects.all().count()

        response = self.user_follower_client.delete(endpoint)
        subscription_count_1 = Subscription.objects.all().count()
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(subscription_count_1 + 1, subscription_count_0)

        response = self.user_follower_client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            Subscription.objects.all().count(), subscription_count_1)
