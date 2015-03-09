from __future__ import unicode_literals
from django.test import TestCase
from down.apps.auth.models import User
from ..models import Friendship


class FriendshipTests(TestCase):
    
    def test_id_order(self):
        """
        Make sure that user1's id is less than user2's id to avoid duplicate
        friendships.
        """
        # Mock two users.
        user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                    username='tdog', image_url='http://imgur.com/tdog')
        user.save()
        friend = User(email='jclarke@gmail.com', name='Joan Clarke',
                      image_url='http://imgur.com/jcke')
        friend.save()

        # Set user1 to have a greater id than user2.
        self.assertGreater(friend.id, user.id)
        friendship = Friendship(user1=friend, user2=user)
        friendship.save()

        # It should set user1 to the user with the lesser id.
        self.assertLess(friendship.user1_id, friendship.user2_id)
