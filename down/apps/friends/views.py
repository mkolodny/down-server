from __future__ import unicode_literals
from django.shortcuts import render
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from down.apps.notifications.utils import send_message
from .models import Friendship
from .serializers import (
    FriendshipSerializer,
    FriendSerializer,
    MessageSerializer,
)
from down.apps.events.models import Invitation, Invitation


class FriendshipViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                        viewsets.GenericViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Friendship.objects.all()
    serializer_class = FriendshipSerializer

    # TODO: Only expect the friend when creating a friendship.

    def get_object(self):
        obj = super(FriendshipViewSet, self).get_object()

        # Make sure that the current user created the friendship.
        if obj.user != self.request.user:
            raise PermissionDenied()

        return obj

    @list_route(methods=['delete'])
    def friend(self, request):
        """
        Delete the user's friendship with the given friend.
        """
        serializer = FriendSerializer(data=request.data)
        serializer.is_valid()

        Friendship.objects.filter(user=request.user,
                                  friend_id=serializer.data['friend']) \
                .delete()

        return Response()

    @detail_route(methods=['post'])
    def messages(self, request, pk=None):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid() # TODO: Handle bad data

        user_ids = [int(pk)]
        text = serializer.data['text']
        message = '{name}: {text}'.format(name=request.user.name, text=text)
        send_message(user_ids, message, sms=False)

        return Response(status=status.HTTP_201_CREATED)
