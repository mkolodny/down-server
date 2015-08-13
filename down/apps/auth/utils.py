from __future__ import unicode_literals
from urllib import urlencode
import requests
from rest_framework import status
from rest_framework.exceptions import ParseError
from .models import SocialAccount, User
from .exceptions import ServiceUnavailable


def get_facebook_friends(user):
    user_facebook_account = SocialAccount.objects.get(user=user)
    params = {'access_token': user_facebook_account.profile['access_token']}
    url = 'https://graph.facebook.com/v2.2/me/friends?' + urlencode(params)
    facebook_friend_ids = []
    while True:
        response = requests.get(url)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            raise ParseError(response.content)
        elif response.status_code != status.HTTP_200_OK:
            raise ServiceUnavailable(response.content)
        try:
            facebook_json = response.json()
        except ValueError:
            raise ServiceUnavailable('Facebook response data was not JSON.')
        try:
            new_friend_ids = [
                facebook_friend['id']
                for facebook_friend in facebook_json['data']
            ]
            facebook_friend_ids.extend(new_friend_ids)
            paging = facebook_json['paging']
            if len(new_friend_ids) < 25 or 'next' not in paging:
                break
            url = paging['next']
        except KeyError:
            raise ServiceUnavailable('Facebook response did not contain data.')

    # Use the list of the user's Facebook friends to create a queryset of the
    # user's friends on Down.
    social_accounts = SocialAccount.objects.filter(uid__in=facebook_friend_ids)
    friend_ids = [account.user_id for account in social_accounts]
    friends = User.objects.filter(id__in=friend_ids)
    return friends
