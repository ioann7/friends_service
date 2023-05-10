from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet


class CreateListRetrieveModelViewSet(mixins.CreateModelMixin,
                                     mixins.ListModelMixin,
                                     mixins.RetrieveModelMixin,
                                     GenericViewSet):
    '''
    A viewset that provides `create`, `list` and `retrieve` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    '''


class ListModelViewSet(mixins.ListModelMixin,
                       GenericViewSet):
    '''
    A viewset that provides `list` action.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    '''
