from __future__ import unicode_literals
from django.conf import settings
from push_notifications.models import APNSDevice, GCMDevice
from twilio.rest import TwilioRestClient
from down.apps.auth.models import UserPhone

def send_message(user_ids, message, sms=True, is_invitation=False):
    # Notify users with iOS devices.
    apnsdevices = APNSDevice.objects.filter(user_id__in=user_ids)
    apnsdevices.send_message(message, badge=1)

    # Notify users with Android devices.
    gcmdevices = GCMDevice.objects.filter(user_id__in=user_ids)
    extra = {'title': 'Down.', 'message': message}
    gcmdevices.send_message(None, extra=extra)

    if sms:
        # Notify users who were added from contacts.
        if is_invitation:
            message = 'Down. {og_message}'.format(og_message=message)
        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        userphones = UserPhone.objects.filter(user_id__in=user_ids,
                                              user__username__isnull=True)
        for userphone in userphones:
            phone = unicode(userphone.phone)
            client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                                   body=message)
