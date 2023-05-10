from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIRequestFactory

from users.models import Follow
from users.serializers import UserSerializer
from users.services import (SubscriptionQuerySet, SubsriptionCreateDelete,
                            annotate_follower_and_following_on_request_user,
                            destroy_from_subscribers)

User = get_user_model()


class SubscriptionCreateDeleteTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user1 = User.objects.create_user(username='user1',
                                              password='user1password')
        self.user2 = User.objects.create_user(username='user2',
                                              password='user2password')

    def test_create_subscribe(self):
        request = self.factory.post('/subscribe/', {'user_id': self.user2.id})
        request.user = self.user1
        response = SubsriptionCreateDelete(request, User.objects.all(),
                                           self.user2.id).create_subscribe()
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Follow.objects.filter(
            user=self.user1, following=self.user2
        ).exists())
        serializer = UserSerializer(instance=self.user2,
                                    context={'request': request})
        self.assertEqual(response.data, serializer.data)

    def test_create_subscribe_cannot_subscribe_twice(self):
        Follow.objects.create(user=self.user1, following=self.user2)
        request = self.factory.post('/subscribe/', {'user_id': self.user2.id})
        request.user = self.user1
        response = SubsriptionCreateDelete(request, User.objects.all(),
                                           self.user2.id).create_subscribe()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'errors': 'Нельзя подписаться дважды!'})

    def test_create_subscribe_cannot_subscribe_to_yourself(self):
        request = self.factory.post('/subscribe/', {'user_id': self.user1.id})
        request.user = self.user1
        response = SubsriptionCreateDelete(request, User.objects.all(),
                                           self.user1.id).create_subscribe()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'errors': 'Нельзя подписаться на самого себя!'})

    def test_delete_subscribe(self):
        Follow.objects.create(user=self.user1, following=self.user2)
        request = self.factory.delete('/subscribe/',
                                      {'user_id': self.user2.id})
        request.user = self.user1
        response = SubsriptionCreateDelete(request, User.objects.all(),
                                           self.user2.id).delete_subscribe()
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Follow.objects.filter(user=self.user1,
                                               following=self.user2).exists())

    def test_delete_subscribe_cannot_unsubscribe_if_not_subscribed(self):
        request = self.factory.delete('/subscribe/',
                                      {'user_id': self.user2.id})
        request.user = self.user1
        response = SubsriptionCreateDelete(request, User.objects.all(),
                                           self.user2.id).delete_subscribe()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data,
                         {'errors': 'Нельзя отписаться, если не подписан!'})


class AnnotateFollowerAndFollowingOnRequestUserTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass1'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass2'
        )

    def test_annotate_follower_and_following_on_request_user(self):
        queryset = User.objects.all()
        annotated_queryset1 = (
            annotate_follower_and_following_on_request_user(queryset,
                                                            self.user1)
        )
        annotated_queryset2 = (
            annotate_follower_and_following_on_request_user(queryset,
                                                            self.user2)
        )
        self.assertIn('is_follower', annotated_queryset1[0].__dict__)
        self.assertIn('is_following', annotated_queryset1[0].__dict__)

        # user1 subscribe on user2
        Follow.objects.create(user=self.user1, following=self.user2)
        self.assertTrue(annotated_queryset1.get(id=self.user2.id).is_following)
        self.assertFalse(annotated_queryset1.get(id=self.user2.id).is_follower)
        self.assertTrue(annotated_queryset2.get(id=self.user1.id).is_follower)
        self.assertFalse(annotated_queryset2.get(
            id=self.user1.id).is_following)

        # user2 subscribe on user1
        Follow.objects.create(user=self.user2, following=self.user1)
        self.assertTrue(annotated_queryset1.get(id=self.user2.id).is_following)
        self.assertTrue(annotated_queryset1.get(id=self.user2.id).is_follower)
        self.assertTrue(annotated_queryset2.get(id=self.user1.id).is_follower)
        self.assertTrue(annotated_queryset2.get(id=self.user1.id).is_following)


class SubscriptionQuerySetTestCase(TestCase):
    def setUp(self):
        '''
        Subscribers model:
        user1 <-> user2     user1 and user2 friends
        user1 <- user3      user3 subscriber of user1
        '''
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        self.user4 = User.objects.create(username='user4')
        Follow.objects.create(user=self.user1, following=self.user2)
        Follow.objects.create(user=self.user2, following=self.user1)
        Follow.objects.create(user=self.user3, following=self.user1)

    def test_get_user_subscribers(self):
        subscription_queryset = SubscriptionQuerySet(self.user1)
        subscribers = subscription_queryset.get_user_subscribers()
        self.assertQuerysetEqual(subscribers, [self.user3])

    def test_get_user_subscriptions(self):
        subscription_queryset = SubscriptionQuerySet(self.user1)
        subscriptions = subscription_queryset.get_user_subscriptions()
        self.assertQuerysetEqual(subscriptions, [])

    def test_get_user_friends(self):
        subscription_queryset = SubscriptionQuerySet(self.user1)
        friends = subscription_queryset.get_user_friends()
        self.assertQuerysetEqual(friends, [self.user2])


class DestroyFromSubscribersTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        Follow.objects.create(user=self.user1, following=self.user2)

    def test_destroy_from_subscribers(self):
        response = destroy_from_subscribers(self.user2, self.user2.id,
                                            self.user1.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = destroy_from_subscribers(self.user2, self.user2.id,
                                            self.user3.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_destroy_from_subscribers_forbidden(self):
        '''
        Test case 403 Forbidden error.
        This test checks if a 403 Forbidden error
        is returned when the request_user
        is not the same as the user specified by user_id.
        '''
        response = destroy_from_subscribers(self.user1, self.user2.id,
                                            self.user1.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
