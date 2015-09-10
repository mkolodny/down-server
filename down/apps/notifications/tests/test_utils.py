from __future__ import unicode_literals
from django.conf import settings
from django.test import TestCase
import mock
from push_notifications.models import APNSDevice, GCMDevice
from down.apps.auth.models import User, UserPhone
from down.apps.notifications import utils


class SendMessageTests(TestCase):

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('push_notifications.gcm.gcm_send_bulk_message')
    @mock.patch('down.apps.notifications.utils.TwilioRestClient')
    def test_send_message(self, mock_twilio, mock_gcm, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        # Mock three users: 1) an iphone user; 2) an android user; 3) a user added
        # from contacts.
        ios_user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                        username='tdog')
        ios_user.save()
        registration_id = ('1ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        ios_user_device = APNSDevice(registration_id=registration_id,
                                     device_id=device_id, name='iPhone, 8.2',
                                     user=ios_user)
        ios_user_device.save()

        android_user = User(email='jclarke@gmail.com', name='Joan Clarke',
                            username='jcke')
        android_user.save()
        registration_id = ('APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvP'
                           'VGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7h'
                           'H5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMC'
                           'g2ZXKqpc8FXKmhX94kIxQaa')
        device_id = int('490154203237518', 16)
        android_user_device = GCMDevice(registration_id=registration_id,
                                        device_id=device_id, name='Galaxy S6',
                                        user=android_user)
        android_user_device.save()

        sms_user = User(name='Bruce Lee') # SMS users don't have a username.
        sms_user.save()
        sms_user_phone = UserPhone(user=sms_user, phone='+12036227310')
        sms_user_phone.save()

        user_ids = [ios_user.id, android_user.id, sms_user.id]
        message = 'Bars?!?!?!'
        utils.send_message(user_ids, message)

        # It should send push notifications to users with ios devices.
        token = ios_user_device.registration_id
        mock_apns.assert_any_call(registration_ids=[token], alert=message,
                                  badge=1)

        # It should send push notifications to users with android devices.
        token = android_user_device.registration_id
        data = {'message': message}
        mock_gcm.assert_any_call(registration_ids=[token], data=data)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(sms_user_phone.phone)
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)
