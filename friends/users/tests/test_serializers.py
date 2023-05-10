from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Subquery
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from users.models import Follow
from users.serializers import UserCreateSerializer, UserSerializer

User = get_user_model()


class UserSerializerTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user1 = User.objects.create_user(username='testuser1',
                                              password='testpassword')
        self.user2 = User.objects.create_user(username='testuser2',
                                              password='testpassword')

    def test_friendship_status(self):
        annotated_users_for_user2 = User.objects.annotate(
            is_follower=Exists(Subquery(
                Follow.objects.filter(user=OuterRef('pk'),
                                      following=self.user2)
            )),
            is_following=Exists(Subquery(
                Follow.objects.filter(user=self.user2,
                                      following=OuterRef('pk'))
            )),
        )
        annotated_users_for_user1 = User.objects.annotate(
            is_follower=Exists(Subquery(
                Follow.objects.filter(user=OuterRef('pk'),
                                      following=self.user1)
            )),
            is_following=Exists(Subquery(
                Follow.objects.filter(user=self.user1,
                                      following=OuterRef('pk'))
            )),
        )

        user1_request = self.factory.get(reverse('users-list'))
        user1_request.user = self.user1
        user1_context = {'request': user1_request}

        user2_request = self.factory.get(reverse('users-list'))
        user2_request.user = self.user2
        user2_context = {'request': user2_request}

        serializer = UserSerializer(instance=self.user2, context=user1_context)
        self.assertEqual(serializer.data['friendship_status'], 'нет ничего')
        serializer = UserSerializer(instance=annotated_users_for_user1.get(
            id=self.user2.id), context=user1_context)
        self.assertEqual(serializer.data['friendship_status'], 'нет ничего')
        serializer = UserSerializer(instance=annotated_users_for_user2.get(
            id=self.user1.id), context=user2_context)
        self.assertEqual(serializer.data['friendship_status'], 'нет ничего')

        # user1 subscribe to user2
        Follow.objects.create(user=self.user1, following=self.user2)
        serializer = UserSerializer(instance=self.user2, context=user1_context)
        self.assertEqual(
            serializer.data['friendship_status'], 'есть исходящая заявка'
        )
        serializer = UserSerializer(instance=annotated_users_for_user1.get(
            id=self.user2.id), context=user1_context)
        self.assertEqual(
            serializer.data['friendship_status'], 'есть исходящая заявка'
        )
        serializer = UserSerializer(instance=self.user1, context=user2_context)
        self.assertEqual(
            serializer.data['friendship_status'], 'есть входящая заявка'
        )
        serializer = UserSerializer(instance=annotated_users_for_user2.get(
            id=self.user1.id), context=user2_context)
        self.assertEqual(
            serializer.data['friendship_status'], 'есть входящая заявка'
        )

        # user2 subscribe user1
        Follow.objects.create(user=self.user2, following=self.user1)
        serializer = UserSerializer(instance=self.user2, context=user1_context)
        self.assertEqual(serializer.data['friendship_status'], 'уже друзья')
        serializer = UserSerializer(instance=annotated_users_for_user1.get(
            id=self.user2.id), context=user1_context)
        self.assertEqual(serializer.data['friendship_status'], 'уже друзья')
        serializer = UserSerializer(instance=self.user1, context=user2_context)
        self.assertEqual(serializer.data['friendship_status'], 'уже друзья')
        serializer = UserSerializer(instance=annotated_users_for_user2.get(
            id=self.user1.id), context=user2_context)
        self.assertEqual(serializer.data['friendship_status'], 'уже друзья')

    def test_user_create_serializer(self):
        # Test successful user creation
        serializer = UserCreateSerializer(data={
            'username': 'newuser',
            'password': 'supersecretpassword1337gg'
        })
        self.assertTrue(serializer.is_valid(raise_exception=True))
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertTrue(user.check_password('supersecretpassword1337gg'))

        # Test invalid password
        serializer = UserCreateSerializer(data={
            'username': 'invaliduser',
            'password': '1234'
        })
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

        # Test username uniqueness constraint
        serializer = UserCreateSerializer(data={
            'username': 'testuser1',
            'password': 'testpassword'
        })
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
