from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from users.models import Follow

User = get_user_model()


class UserViewSetTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1', password='password')
        self.user2 = User.objects.create(username='user2', password='password')
        self.user3 = User.objects.create(username='user3', password='password')

        self.authenticated_client = APIClient()
        token = Token.objects.create(user=self.user1)
        self.authenticated_client.credentials(
            HTTP_AUTHORIZATION=f'Token {token.key}')
        self.unauthenticated_client = APIClient()

    def test_list_users(self):
        url = reverse('users-list')
        response = self.unauthenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['username'], 'user1')
        self.assertEqual(response.data['results'][1]['username'], 'user2')
        self.assertEqual(response.data['results'][2]['username'], 'user3')

    def test_create_user(self):
        url = reverse('users-list')
        data = {
            'username': 'new_user',
            'password': 'ReallySuperSecret123'
        }
        response = self.unauthenticated_client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'new_user')
        self.assertNotIn('password', response.data)

    def test_retrieve_user(self):
        url = reverse('users-detail', args=(self.user1.id))
        response = self.unauthenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user1')

    def test_subscribe_and_unsubscribe_user(self):
        url = reverse('users-subscribe', args=(self.user2.id))

        response = self.unauthenticated_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authenticated_client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.unauthenticated_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authenticated_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SubscribersViewSetTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1', password='password')
        self.user2 = User.objects.create(username='user2', password='password')
        self.user3 = User.objects.create(username='user3', password='password')
        Follow.objects.create(user=self.user2, following=self.user1)
        Follow.objects.create(user=self.user3, following=self.user1)

        self.authenticated_client1 = APIClient()
        token = Token.objects.create(user=self.user1)
        self.authenticated_client1.credentials(
            HTTP_AUTHORIZATION=f'Token {token.key}')
        self.authenticated_client2 = APIClient()
        token = Token.objects.create(user=self.user2)
        self.authenticated_client2.credentials(
            HTTP_AUTHORIZATION=f'Token {token.key}')
        self.unauthenticated_client = APIClient()

    def test_list_subscribers(self):
        url = reverse('subscribers-list', args=(self.user1.id))
        response = self.unauthenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authenticated_client1.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['username'], 'user2')
        self.assertEqual(response.data['results'][1]['username'], 'user3')

    def test_destroy_subscriber(self):
        url = reverse('subscribers-detail',
                      args=(self.user1.id, self.user2.id))
        response = self.unauthenticated_client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authenticated_client2.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.authenticated_client1.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class SubscriptionsViewSetTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1', password='password')
        self.user2 = User.objects.create(username='user2', password='password')
        self.user3 = User.objects.create(username='user3', password='password')
        Follow.objects.create(user=self.user1, following=self.user2)
        Follow.objects.create(user=self.user1, following=self.user3)

        self.authenticated_client = APIClient()
        token = Token.objects.create(user=self.user1)
        self.authenticated_client.credentials(
            HTTP_AUTHORIZATION=f'Token {token.key}')
        self.unauthenticated_client = APIClient()

    def test_list_subscriptions(self):
        url = reverse('subscriptions-list', args=(self.user1.id))
        response = self.unauthenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['username'], 'user2')
        self.assertEqual(response.data['results'][1]['username'], 'user3')


class FriendsViewSetTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1', password='password')
        self.user2 = User.objects.create(username='user2', password='password')
        Follow.objects.create(user=self.user1, following=self.user2)
        Follow.objects.create(user=self.user2, following=self.user1)

        self.authenticated_client = APIClient()
        token = Token.objects.create(user=self.user1)
        self.authenticated_client.credentials(
            HTTP_AUTHORIZATION=f'Token {token.key}')
        self.unauthenticated_client = APIClient()

    def test_list_friends(self):
        url = reverse('friends-list', args=(self.user1.id))
        response = self.unauthenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.authenticated_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['username'], 'user2')
