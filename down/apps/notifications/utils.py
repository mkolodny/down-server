from __future__ import unicode_literals
from push_notifications.models import APNSDevice


def notify_users(user_ids, message, extra=None):
    devices = APNSDevice.objects.filter(user_id__in=user_ids)
    devices.send_message(message)
    extra = {'message': message}
    devices.send_message(None, extra=extra)
