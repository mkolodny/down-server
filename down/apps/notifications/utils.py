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
    apnsdevice_ids = set(device.user_id for device in apnsdevices)
    remaining_user_ids = [user_id for user_id in user_ids
            if user_id not in apnsdevice_ids]
    gcmdevices = GCMDevice.objects.filter(user_id__in=remaining_user_ids)
    gcmdevices.send_message(message, badge=1)

    if sms:
        # Notify users who were added from contacts.
        gcmdevice_ids = set(device.user_id for device in gcmdevices)
        remaining_user_ids = [user_id for user_id in remaining_user_ids
                if user_id not in gcmdevice_ids]
        userphones = UserPhone.objects.filter(user_id__in=remaining_user_ids)
        client = TwilioRestClient(settings.TWILIO_ACCOUNT, settings.TWILIO_TOKEN)
        if is_invitation:
            message = 'Down. {og_message}'.format(og_message=message)
        for userphone in userphones:
            phone = unicode(userphone.phone)
            client.messages.create(to=phone, from_=settings.TWILIO_PHONE,
                                   body=message)
