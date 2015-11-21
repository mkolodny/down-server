from __future__ import unicode_literals
from django.conf import settings
from push_notifications.gcm import GCMError
from push_notifications.models import APNSDevice, GCMDevice
from twilio.rest import TwilioRestClient
from rallytap.apps.auth.models import UserPhone

def send_message(user_ids, message, sms=True, from_user=None, event_id=None,
                 added_friend=False):
    # Notify users with iOS devices.
    apnsdevices = APNSDevice.objects.filter(user_id__in=user_ids)
    for device in apnsdevices:
        device.send_message(message, badge=1)

    # Notify users with Android devices.
    gcmdevices = GCMDevice.objects.filter(user_id__in=user_ids)
    extra = {'title': 'Rallytap', 'message': message}
    for device in gcmdevices:
        try:
            device.send_message(None, extra=extra)
        except GCMError:
            continue

    if not sms:
        return

    # Notify users who were added from contacts.
    if added_friend:
        # The message is a notification that the user added a contact as a friend
        # on rallytap. Include a link to the app.
        message = message[:-1] # remove the exclamation point at the end.
        url = 'https://rallytap.com/app'
        message = '{message} on Rallytap! - {url}'.format(message=message, url=url)
    client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
    userphones = UserPhone.objects.filter(user_id__in=user_ids,
                                          user__username__isnull=True)
    for userphone in userphones:
        phone = unicode(userphone.phone)
        client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                               body=message)
