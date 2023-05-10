from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from users.serializers import UserCreateSerializer, UserSerializer
from users.services import (SubscriptionQuerySet, SubsriptionCreateDelete,
                            annotate_follower_and_following_on_request_user,
                            destroy_from_subscribers)
from users.viewsets import CreateListRetrieveModelViewSet, ListModelViewSet

User = get_user_model()


class UserViewSet(CreateListRetrieveModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_anonymous:
            return queryset
        return annotate_follower_and_following_on_request_user(
            queryset, self.request.user
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        if self.action in ('list', 'create'):
            return (AllowAny(),)
        return super().get_permissions()

    @action(methods=('post', 'delete'), detail=True)
    def subscribe(self, request, *args, **kwargs):
        subscription = SubsriptionCreateDelete(
            request, self.get_queryset(),
            self.kwargs.get(self.lookup_url_kwarg)
        )
        if request.method == 'POST':
            return subscription.create_subscribe()
        return subscription.delete_subscribe()


class SubscribersViewSet(ListModelViewSet):
    serializer_class = UserSerializer
    lookup_url_kwarg = 'subscriber_id'

    def destroy(self, request, user_id, subscriber_id):
        return destroy_from_subscribers(request.user, user_id, subscriber_id)

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs.get('user_id'))
        queryset = SubscriptionQuerySet(user).get_user_subscribers()
        queryset = queryset.order_by('id')
        if self.request.user.is_anonymous:
            return queryset
        return annotate_follower_and_following_on_request_user(
            queryset, self.request.user
        )


class SubscriptionsViewSet(ListModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs.get('user_id'))
        queryset = SubscriptionQuerySet(user).get_user_subscriptions()
        queryset = queryset.order_by('id')
        if self.request.user.is_anonymous:
            return queryset
        return annotate_follower_and_following_on_request_user(
            queryset, self.request.user
        )


class FriendsViewSet(ListModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = get_object_or_404(User, id=self.kwargs.get('user_id'))
        queryset = SubscriptionQuerySet(user).get_user_friends()
        queryset = queryset.order_by('id')
        if self.request.user.is_anonymous:
            return queryset
        return annotate_follower_and_following_on_request_user(
            queryset, self.request.user
        )
