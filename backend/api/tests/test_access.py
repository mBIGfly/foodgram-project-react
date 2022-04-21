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
    user_follower: User
    tag: Tag
    ingredient: Ingredient
    recipe: Recipe
    recipe_follower: Recipe

    recipe_to_delete: Recipe

    user_client: APIClient
    anon_client: APIClient

    missing_id = 10000

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_follower = get_object_or_404(User, pk=3)
        cls.tag = Tag.objects.all().first()
        cls.ingredient = Ingredient.objects.all().first()
        cls.recipe = Recipe.objects.all().first()
        cls.recipe_follower = get_object_or_404(
            Recipe, author=cls.user_follower)
        cls.recipe_to_delete = Recipe.objects.all().last()
        cls.user = cls.recipe.author

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

    def __launch_tests(self, endpoints_dict, apiclient):
        for http_data, endpoints in endpoints_dict.items():
            http_status, method = http_data

            for endpoint in endpoints:
                with self.subTest(method=method, endpoint=endpoint):
                    response = getattr(apiclient, method)(endpoint)
                    self.assertEqual(response.status_code, http_status)

    def test_anon_endpoint_access(self):
        """Неавторизованные пользователи. Доступ к ресурсам API."""

        endpoints_dict = {
            (status.HTTP_200_OK, 'get'): (
                reverse('api:customuser-list'),
                reverse('api:tags-list'),
                reverse('api:tags-detail', args=(self.tag.pk,)),
                reverse('api:recipes-list'),
                reverse('api:recipes-detail', args=(self.recipe.pk,)),
                reverse('api:ingredients-list'),
                reverse('api:ingredients-detail', args=(self.ingredient.pk,)),
            ),
            (status.HTTP_401_UNAUTHORIZED, 'get'): (
                reverse('api:customuser-detail', args=(self.user.pk,)),
                reverse('api:customuser-me'),
                reverse('api:download_shopping_cart'),
                reverse('api:subscriptions'),
                reverse('api:customuser-detail', args=(self.missing_id,)),
            ),
            (status.HTTP_400_BAD_REQUEST, 'post'): (
                reverse('api:customuser-list'),
                reverse('api:login'),
            ),
            (status.HTTP_401_UNAUTHORIZED, 'post'): (
                reverse('api:customuser-set-password'),
                reverse('api:logout'),
                reverse('api:recipes-list'),
                reverse('api:shopping_cart', args=(self.recipe.pk,)),
                reverse('api:favorites', args=(self.recipe.pk,)),
                reverse('api:subscribe', args=(self.user_follower.pk,)),
            ),
            (status.HTTP_401_UNAUTHORIZED, 'patch'): (
                reverse('api:recipes-detail', args=(self.recipe.pk,)),
            ),
            (status.HTTP_401_UNAUTHORIZED, 'delete'): (
                reverse('api:recipes-detail', args=(self.recipe.pk,)),
                reverse('api:shopping_cart', args=(self.recipe.pk,)),
                reverse('api:favorites', args=(self.recipe.pk,)),
                reverse('api:subscribe', args=(self.user_follower.pk,)),
            ),
            (status.HTTP_404_NOT_FOUND, 'get'): (
                reverse('api:recipes-detail', args=(self.missing_id,)),
                reverse('api:tags-detail', args=(self.missing_id,)),
                reverse('api:ingredients-detail', args=(self.missing_id,)),
            ),
        }

        self.__launch_tests(endpoints_dict, self.anon_client)

    def test_user_endpoint_access(self):
        """Авторизованные пользователи. Доступ к ресурсам API."""

        endpoints_dict = {
            (status.HTTP_200_OK, 'get'): (
                reverse('api:customuser-list'),
                reverse('api:customuser-detail', args=(self.user.pk,)),
                reverse('api:customuser-me'),
                reverse('api:tags-list'),
                reverse('api:tags-detail', args=(self.tag.pk,)),
                reverse('api:recipes-list'),
                reverse('api:recipes-detail', args=(self.recipe.pk,)),
                reverse('api:subscriptions'),
                reverse('api:ingredients-list'),
                reverse('api:ingredients-detail', args=(self.ingredient.pk,)),
            ),
            (status.HTTP_400_BAD_REQUEST, 'post'): (
                reverse('api:customuser-set-password'),
                reverse('api:recipes-list'),
            ),
            (status.HTTP_204_NO_CONTENT, 'get'): (
                reverse('api:download_shopping_cart'),
            ),
            (status.HTTP_201_CREATED, 'post'): (
                reverse('api:favorites', args=(self.recipe.pk,)),
                reverse('api:subscribe', args=(self.user_follower.pk,)),
                reverse('api:shopping_cart', args=(self.recipe.pk,)),
            ),
            (status.HTTP_400_BAD_REQUEST, 'patch'): (
                reverse(
                    'api:recipes-detail', args=(self.recipe.pk,)),
            ),
            (status.HTTP_403_FORBIDDEN, 'patch'): (
                reverse('api:recipes-detail', args=(self.recipe_follower.pk,)),
            ),
            (status.HTTP_404_NOT_FOUND, 'patch'): (
                reverse('api:recipes-detail', args=(self.missing_id,)),
            ),
            (status.HTTP_403_FORBIDDEN, 'delete'): (
                reverse('api:recipes-detail', args=(self.recipe_follower.pk,)),
            ),
            (status.HTTP_204_NO_CONTENT, 'delete'): (
                reverse(
                    'api:recipes-detail', args=(self.recipe_to_delete.pk,)),
                reverse('api:shopping_cart', args=(self.recipe.pk,)),
                reverse('api:favorites', args=(self.recipe.pk,)),
                reverse('api:subscribe', args=(self.user_follower.pk,)),
            ),
            (status.HTTP_404_NOT_FOUND, 'delete'): (
                reverse('api:recipes-detail', args=(self.missing_id,)),
                reverse('api:shopping_cart', args=(self.missing_id,)),
                reverse('api:favorites', args=(self.missing_id,)),
                reverse('api:subscribe', args=(self.missing_id,)),
            ),
            (status.HTTP_403_FORBIDDEN, 'post'): (
                reverse('api:login'),
                reverse('api:customuser-list'),
            ),
            (status.HTTP_204_NO_CONTENT, 'post'): (
                reverse('api:logout'),
            ),
            (status.HTTP_404_NOT_FOUND, 'get'): (
                reverse('api:recipes-detail', args=(self.missing_id,)),
                reverse('api:customuser-detail', args=(self.missing_id,)),
                reverse('api:recipes-detail', args=(self.missing_id,)),
                reverse('api:tags-detail', args=(self.missing_id,)),
                reverse('api:ingredients-detail', args=(self.missing_id,)),
            ),
            (status.HTTP_404_NOT_FOUND, 'post'): (
                reverse('api:shopping_cart', args=(self.missing_id,)),
                reverse('api:favorites', args=(self.missing_id,)),
                reverse('api:subscribe', args=(self.missing_id,)),
            ),
        }

        self.__launch_tests(endpoints_dict, self.user_client)
