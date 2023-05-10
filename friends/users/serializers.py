from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.db import IntegrityError
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Be sure to annotate `is_follower` and `is_following`
    when many=True for optimized queries.
    """
    FRIENDSHIP_STATUSES = {
        'friends': 'уже друзья',
        'outgoing_request': 'есть исходящая заявка',
        'incoming_request': 'есть входящая заявка',
        'nothing': 'нет ничего',
    }

    friendship_status = serializers.SerializerMethodField()

    class Meta:
        fields = ('id', 'username', 'friendship_status')
        model = User

    def get_friendship_status(self, obj):
        user = self.context['request'].user
        if hasattr(obj, 'is_follower'):
            is_follower = obj.is_follower
        else:
            is_follower = (
                user.is_authenticated
                and obj.follower.filter(following=user).exists()
            )
        if hasattr(obj, 'is_following'):
            is_following = obj.is_following
        else:
            is_following = (
                user.is_authenticated
                and obj.following.filter(user=user).exists()
            )
        if is_follower and is_following:
            return self.FRIENDSHIP_STATUSES['friends']
        if is_following:
            return self.FRIENDSHIP_STATUSES['outgoing_request']
        if is_follower:
            return self.FRIENDSHIP_STATUSES['incoming_request']
        return self.FRIENDSHIP_STATUSES['nothing']


class UserCreateSerializer(UserSerializer):
    password = serializers.CharField(write_only=True)

    default_error_messages = {
        'cannot_create_user': 'Не получается создать пользователя!',
    }

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'friendship_status')
        read_only_fields = ('id', 'friendship_status')

    def validate(self, attrs):
        user = User(**attrs)
        password = attrs.get('password')

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {'password': serializer_error['non_field_errors']}
            )

        return attrs

    def create(self, validated_data):
        try:
            return self.perform_create(validated_data)
        except IntegrityError:
            self.fail('cannot_create_user')

    def perform_create(self, validated_data):
        return User.objects.create_user(**validated_data)
