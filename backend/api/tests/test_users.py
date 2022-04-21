from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.urls import include, path
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient, APITestCase, URLPatternsTestCase

User = get_user_model()


class APITests(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        path('api/', include('api.urls')),
    ]
    fixtures = ('users.json',)

    user: User
    user_follower: User

    user_email = 'test_user@resource.ru'
    user_password = 'DGCtnLWZ8NHcv42'

    user_count: int

    first_user_username = 'admin'

    user_client: APIClient
    anon_client: APIClient

    keys_get_list: list
    keys_get_detail: list
    keys_get_me: list
    keys_post_list: list
    keys_post_login: list

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_object_or_404(User, pk=2)
        cls.user_follower = get_object_or_404(User, pk=3)

        cls.user_count = User.objects.all().count()

        cls.keys_get_list = sorted(
            ['email', 'id', 'username', 'first_name', 'last_name',
             'is_subscribed'])
        cls.keys_get_detail = sorted(
            ['email', 'id', 'username', 'first_name', 'last_name',
             'is_subscribed'])
        cls.keys_get_me = sorted(
            ['email', 'id', 'username', 'first_name', 'last_name',
             'is_subscribed'])
        cls.keys_post_list = sorted(
            ['email', 'id', 'username', 'first_name', 'last_name'])
        cls.keys_post_login = ['auth_token']

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def setUp(self):
        self.anon_client = APIClient()

        self.user_client = APIClient()
        self.user_client.force_authenticate(user=self.user)

    def test_anon_user_list(self):
        """Неавторизованные пользователи. Список пользователей."""

        endpoint = reverse('api:customuser-list')

        response = self.anon_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data['results'][0].keys()), self.keys_get_list)
        self.assertEqual(
            response.data['results'][0]['username'], self.first_user_username)
        self.assertEqual(response.data['count'], self.user_count)

    def test_anon_create_account(self):
        """Неавторизованные пользователи. Создать аккаунт."""

        endpoint = reverse('api:customuser-list')
        new_user_data = {
            'email': 'newuser@example.ru',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'Secret45^password'
        }
        user_count_0 = User.objects.all().count()

        # Email уникален
        wrong_user_data = new_user_data.copy()
        wrong_user_data['email'] = self.user.email

        response = self.anon_client.post(endpoint, data=wrong_user_data)
        self.assertIn('email', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.all().count(), user_count_0)

        # Username уникален
        wrong_user_data = new_user_data.copy()
        wrong_user_data['username'] = self.user.username

        response = self.anon_client.post(endpoint, data=wrong_user_data)
        self.assertIn('username', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.all().count(), user_count_0)

        # Все поля необходимы
        response = self.anon_client.post(endpoint)
        for key in new_user_data.keys():
            self.assertIn(key, response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.all().count(), user_count_0)

        # Создание пользователя
        response = self.anon_client.post(endpoint, data=new_user_data)
        new_user_username = get_object_or_404(
            User, username=new_user_data.get('username'),
            email=new_user_data.get('email')).username
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            sorted(response.data.keys()), self.keys_post_list)
        self.assertEqual(User.objects.all().count(), user_count_0 + 1)
        self.assertEqual(new_user_username, new_user_data['username'])

        get_object_or_404(
            User, username=new_user_data.get('username'),
            email=new_user_data.get('email')).delete()

    def test_anon_login(self):
        """Неавторизованные пользователи. Входить в систему под своим логином и
        паролем.
        Используется для авторизации по емейлу и паролю, чтобы далее
        использовать токен при запросах."""

        endpoint = reverse('api:login')
        auth_data = {'email': self.user_email, 'password': self.user_password}

        response = self.anon_client.post(endpoint, data=auth_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data.keys()), self.keys_post_login)

    def test_anon_user_profile(self):
        """Неавторизованные пользователи. Профиль пользователя."""

        endpoint = reverse(
            'api:customuser-detail', args=(self.user.pk,))

        response = self.anon_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_logout(self):
        """Авторизованные пользователи. Выходить из системы (разлогиниваться).
        Удаляет токен текущего пользователя."""

        endpoint = reverse('api:logout')

        response = self.user_client.post(endpoint)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_user_change_password(self):
        """Авторизованные пользователи. Менять свой пароль.
        Изменение пароля текущего пользователя."""

        endpoint = reverse('api:customuser-set-password')
        newpassword = 'password$5r'
        password_data = {
            'new_password': newpassword,
            'current_password': self.user_password
        }
        revert_password_data = {
            'new_password': self.user_password,
            'current_password': newpassword,
        }

        password1 = self.user.password

        response = self.user_client.post(endpoint, password_data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        password2 = self.user.password
        self.assertNotEqual(password1, password2)

        response = self.user_client.post(endpoint, revert_password_data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotEqual(self.user.password, password2)

    def test_user_user_list(self):
        """Авторизованные пользователи. Список пользователей."""

        endpoint = reverse('api:customuser-list')

        response = self.user_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data['results'][0].keys()), self.keys_get_list)
        self.assertEqual(
            response.data['results'][0]['username'], self.first_user_username)
        self.assertEqual(response.data['count'], self.user_count)

    def test_user_user_profile(self):
        """Авторизованные пользователи. Профиль пользователя."""

        endpoint = reverse(
            'api:customuser-detail', args=(self.user.pk,))

        response = self.user_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data.keys()), self.keys_get_detail)
        self.assertEqual(
            response.data['username'], self.user.username)

    def test_user_user_me(self):
        """Авторизованные пользователи. Текущий пользователь."""

        endpoint = reverse('api:customuser-me')

        response = self.user_client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            sorted(response.data.keys()), self.keys_get_me)
        self.assertEqual(
            response.data['username'], self.user.username)
