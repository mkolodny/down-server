from __future__ import unicode_literals
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rallytap.apps.auth.models import User
from rallytap.apps.auth.permissions import IsMeteor
from rallytap.apps.notifications.utils import send_message
from .models import Friendship
from .serializers import (
    FriendshipSerializer,
    FriendSerializer,
    MessageSerializer,
)


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

    @detail_route(methods=['post'], permission_classes=(IsMeteor,))
    def message(self, request, pk=None):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid() # TODO: Handle bad data

        from_user = User.objects.get(id=pk)
        user_ids = [serializer.data['to_user']]
        text = serializer.data['text']
        message = '{name}: {text}'.format(name=from_user.name, text=text)
        send_message(user_ids, message)

        return Response(status=status.HTTP_201_CREATED)
