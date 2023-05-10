from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import (FriendsViewSet, SubscribersViewSet,
                         SubscriptionsViewSet, UserViewSet)

router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register(r'users/(?P<user_id>\d+)/subscribers', SubscribersViewSet,
                basename='subscribers')
router.register(r'users/(?P<user_id>\d+)/subscriptions', SubscriptionsViewSet,
                basename='subscriptions')
router.register(r'users/(?P<user_id>\d+)/friends', FriendsViewSet,
                basename='friends')

api_urls = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urls)),
]
