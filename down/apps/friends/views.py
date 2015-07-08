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
from down.apps.events.models import AllFriendsInvitation, Invitation


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

    def perform_create(self, serializer):
        super(FriendshipViewSet, self).perform_create(serializer)

        # Invite the new friend to any events with an all friends invitation.
        user_id = serializer.data['user']
        friend_id = serializer.data['friend']
        all_friends_invitations = AllFriendsInvitation.objects.filter(
                from_user_id=user_id)
        for all_friends_invitation in all_friends_invitations:
            event = all_friends_invitation.event
            invitation = Invitation(from_user_id=user_id, to_user_id=friend_id,
                                    event=event, open=True)
            invitation.save()

            # Update the event so that users see the friend as invited.
            event.save()

    @list_route(methods=['delete'])
    def friend(self, request):
        serializer = FriendSerializer(data=request.data)
        serializer.is_valid()

        Friendship.objects.filter(user=request.user,
                                  friend_id=serializer.data['friend']).delete()

        return Response()
