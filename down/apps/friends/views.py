from __future__ import unicode_literals
from django.shortcuts import render
from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Friendship
from .permissions import UserIsCurrentUser
from .serializers import FriendshipSerializer, FriendSerializer


class FriendshipViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        mixins.DestroyModelMixin, mixins.UpdateModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('user', 'friend')
    permission_classes = (IsAuthenticated, UserIsCurrentUser)
    queryset = Friendship.objects.all()
    serializer_class = FriendshipSerializer

    def get_object(self):
        obj = super(FriendshipViewSet, self).get_object()

        # Make sure that the current user created the friendship.
        if obj.user != self.request.user:
            raise PermissionDenied()

        return obj

    @list_route(methods=['delete'])
    def friend(self, request):
        serializer = FriendSerializer(data=request.data)
        serializer.is_valid()

        Friendship.objects.filter(user=request.user,
                                  friend_id=serializer.data['friend']).delete()

        return Response()
