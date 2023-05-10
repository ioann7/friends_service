from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Q, Subquery
from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import Follow
from users.serializers import UserSerializer

User = get_user_model()


ERRORS_KEY: str = 'errors'


def annotate_follower_and_following_on_request_user(
        queryset: QuerySet, request_user: User) -> QuerySet:
    return queryset.annotate(
        is_follower=Exists(Subquery(
            Follow.objects.filter(user=OuterRef('pk'), following=request_user)
        )),
        is_following=Exists(Subquery(
            Follow.objects.filter(user=request_user, following=OuterRef('pk'))
        )),
    )


def destroy_from_subscribers(request_user: User, user_id: int,
                             subscriber_id: int) -> Response:
    not_enough_rights: str = 'Недостаточно прав!'
    cannot_unsubscribe_if_not_subscribed: str = (
        'Пользователь {subscriber}, не является подписчиком {user}!'
    )

    user = get_object_or_404(User, id=user_id)
    subscriber = get_object_or_404(User,
                                   id=subscriber_id)
    subscribers = SubscriptionQuerySet(user).get_user_subscribers()
    if request_user != user:
        error_message = {ERRORS_KEY: not_enough_rights}
        return Response(error_message, status.HTTP_403_FORBIDDEN)
    if not subscribers.filter(id=subscriber_id).exists():
        error_message = {
            ERRORS_KEY: cannot_unsubscribe_if_not_subscribed.format(
                subscriber=subscriber.username, user=user.username
            )
        }
        return Response(error_message, status.HTTP_400_BAD_REQUEST)
    Follow.objects.get(user=subscriber_id, following=user_id).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionQuerySet:
    def __init__(self, user: User) -> None:
        self.user = user

    def get_user_subscribers(self) -> QuerySet:
        user_all_subscriptions = self.user.follower.values('following')
        subscribers = self.user.following.filter(
            ~Q(user__in=user_all_subscriptions)
        ).values('user')
        return User.objects.filter(id__in=subscribers)

    def get_user_subscriptions(self) -> QuerySet:
        user_all_subscribers = self.user.following.values('user')
        subscriptions = self.user.follower.filter(
            ~Q(following__in=user_all_subscribers)
        ).values('following')
        return User.objects.filter(id__in=subscriptions)

    def get_user_friends(self) -> QuerySet:
        user_all_subscribers = self.user.following.values('user')
        friends = self.user.follower.filter(
            Q(following__in=user_all_subscribers)
        ).values('following')
        return User.objects.filter(id__in=friends)


class SubsriptionCreateDelete:
    CANNOT_SUBSCRIBE_TO_YOURSELF: str = 'Нельзя подписаться на самого себя!'
    CANNOT_SUBSCRIBE_TWICE: str = 'Нельзя подписаться дважды!'
    CANNOT_UNSUBSCRIBED_IF_NOT_SUBSCRIBED: str = (
        'Нельзя отписаться, если не подписан!'
    )

    def __init__(self, request: Request, user_queryset: QuerySet,
                 following_user_id: Optional[int]) -> None:
        self.request: Request = request
        self.user: User = request.user
        self.user_queryset: QuerySet = user_queryset
        self.following_user_id: Optional[int] = following_user_id

    def create_subscribe(self) -> Response:
        following = self._get_following_or_404()
        if self.user == following:
            return Response(
                {ERRORS_KEY: self.CANNOT_SUBSCRIBE_TO_YOURSELF},
                status.HTTP_400_BAD_REQUEST,
            )
        if self._is_follow_exists(following):
            return Response(
                {ERRORS_KEY: self.CANNOT_SUBSCRIBE_TWICE},
                status.HTTP_400_BAD_REQUEST,
            )

        Follow.objects.create(user=self.user, following=following)
        following = self._get_following_or_404()
        serializer = UserSerializer(instance=following,
                                    context={'request': self.request})
        return Response(serializer.data, status.HTTP_201_CREATED)

    def delete_subscribe(self) -> Response:
        following = self._get_following_or_404()
        if not self._is_follow_exists(following):
            return Response(
                {ERRORS_KEY: self.CANNOT_UNSUBSCRIBED_IF_NOT_SUBSCRIBED},
                status.HTTP_400_BAD_REQUEST,
            )
        Follow.objects.get(user=self.user, following=following).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _is_follow_exists(self, following: User) -> bool:
        return Follow.objects.filter(
            user=self.user,
            following=following
        ).exists()

    def _get_following_or_404(self) -> User:
        return get_object_or_404(
            self.user_queryset,
            id=self.following_user_id,
        )
