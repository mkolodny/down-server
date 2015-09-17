from __future__ import unicode_literals
from django.conf import settings
from django.test import TestCase
import mock
from push_notifications.models import APNSDevice, GCMDevice
from down.apps.auth.models import User, UserPhone
from down.apps.events.models import Event, LinkInvitation
from down.apps.notifications import utils


class SendMessageTests(TestCase):

    def setUp(self):
        # Mock three users: 1) an iphone user; 2) an android user; 3) a user added
        # from contacts.
        self.user = User(email='aturing@gmail.com', name='Alan Tdog Turing',
                         username='tdog')
        self.user.save()
        registration_id = ('1ed202ac08ea9033665e853a3dc8bc4c5e78f7a6cf8d559'
                           '10df230567037dcc4')
        device_id = 'E621E1F8-C36C-495A-93FC-0C247A3E6E5F'
        self.ios_device = APNSDevice(registration_id=registration_id,
                                     device_id=device_id, name='iPhone, 8.2',
                                     user=self.user)
        self.ios_device.save()

        registration_id = ('APA91bHPRgkF3JUikC4ENAHEeMrd41Zxv3hVZjC9KtT8OvP'
                           'VGJ-hQMRKRrZuJAEcl7B338qju59zJMjw2DELjzEvxwYv7h'
                           'H5Ynpc1ODQ0aT4U4OFEeco8ohsN5PjL1iC2dNtk2BAokeMC'
                           'g2ZXKqpc8FXKmhX94kIxQaa')
        device_id = int('490154203237518', 16)
        self.android_device = GCMDevice(registration_id=registration_id,
                                        device_id=device_id, name='Galaxy S6',
                                        user=self.user)
        self.android_device.save()

        self.contact = User(name='Bruce Lee') # SMS users don't have a username.
        self.contact.save()
        self.contact_phone = UserPhone(user=self.contact, phone='+12036227310')
        self.contact_phone.save()

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('push_notifications.gcm.gcm_send_bulk_message')
    @mock.patch('down.apps.notifications.utils.TwilioRestClient')
    def test_send_message(self, mock_twilio, mock_gcm, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        user_ids = [self.user.id, self.contact.id]
        message = 'Bars?!?!?!'
        utils.send_message(user_ids, message)

        # It should send push notifications to users with ios devices.
        token = self.ios_device.registration_id
        mock_apns.assert_any_call(registration_ids=[token], alert=message,
                                  badge=1)

        # It should send push notifications to users with android devices.
        token = self.android_device.registration_id
        data = {'title': 'Down.', 'message': message}
        mock_gcm.assert_any_call(registration_ids=[token], data=data)

        # It should init the Twilio client with the proper params.
        mock_twilio.assert_called_with(settings.TWILIO_ACCOUNT,
                                       settings.TWILIO_TOKEN)

        # It should send SMS to users without devices.
        phone = unicode(self.contact_phone.phone)
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('push_notifications.gcm.gcm_send_bulk_message')
    def test_send_message_devices_only(self, mock_gcm, mock_apns):
        user_ids = [self.user.id, self.contact.id]
        message = 'Bars?!?!?!'
        utils.send_message(user_ids, message, sms=False)

        # It should send push notifications to users with ios devices.
        token = self.ios_device.registration_id
        mock_apns.assert_any_call(registration_ids=[token], alert=message,
                                  badge=1)

        # It should send push notifications to users with android devices.
        token = self.android_device.registration_id
        data = {'title': 'Down.', 'message': message}
        mock_gcm.assert_any_call(registration_ids=[token], data=data)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('push_notifications.gcm.gcm_send_bulk_message')
    @mock.patch('down.apps.notifications.utils.TwilioRestClient')
    def test_send_message_invitation(self, mock_twilio, mock_gcm, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        # Mock an event.
        event = Event(title='Ball?', creator=self.user)
        event.save()

        user_ids = [self.user.id, self.contact.id]
        message = 'from Barack Obama'
        from_user = self.user
        utils.send_message(user_ids, message, from_user=from_user,
                           event_id=event.id)

        # It should send push notifications to users with ios devices.
        token = self.ios_device.registration_id
        mock_apns.assert_any_call(registration_ids=[token], alert=message,
                                  badge=1)

        # It should send push notifications to users with android devices.
        token = self.android_device.registration_id
        data = {'title': 'Down.', 'message': message}
        mock_gcm.assert_any_call(registration_ids=[token], data=data)

        # It should create a link invitation.
        link_invitation = LinkInvitation.objects.get(event=event,
                                                     from_user=from_user)

        # It should send SMS to users without devices.
        emoji = '\U0001f447'
        link = 'http://{emoji}.ws/e/{link_id}'.format(
                emoji=emoji, link_id=link_invitation.link_id)
        name = link_invitation.from_user.name
        message = '{name} sent you a down - {link}'.format(name=name, link=link)
        phone = unicode(self.contact_phone.phone)
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('push_notifications.gcm.gcm_send_bulk_message')
    @mock.patch('down.apps.notifications.utils.TwilioRestClient')
    def test_send_message_invitation_link_exists(self, mock_twilio, mock_gcm,
                                                 mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        # Mock an event with a link invitation.
        event = Event(title='Ball?', creator=self.user)
        event.save()
        from_user = self.user
        link_invitation = LinkInvitation(event=event, from_user=from_user)
        link_invitation.save()

        user_ids = [self.user.id, self.contact.id]
        message = 'from Barack Obama'
        utils.send_message(user_ids, message, from_user=from_user,
                           event_id=event.id)

        # It should send push notifications to users with ios devices.
        token = self.ios_device.registration_id
        mock_apns.assert_any_call(registration_ids=[token], alert=message,
                                  badge=1)

        # It should send push notifications to users with android devices.
        token = self.android_device.registration_id
        data = {'title': 'Down.', 'message': message}
        mock_gcm.assert_any_call(registration_ids=[token], data=data)

        # It should send SMS to users without devices.
        emoji = '\U0001f447'
        link = 'http://{emoji}.ws/e/{link_id}'.format(
                emoji=emoji, link_id=link_invitation.link_id)
        name = link_invitation.from_user.name
        message = '{name} sent you a down - {link}'.format(name=name, link=link)
        phone = unicode(self.contact_phone.phone)
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)

    @mock.patch('push_notifications.apns.apns_send_bulk_message')
    @mock.patch('push_notifications.gcm.gcm_send_bulk_message')
    @mock.patch('down.apps.notifications.utils.TwilioRestClient')
    def test_send_message_added_friend(self, mock_twilio, mock_gcm, mock_apns):
        # Mock the Twilio SMS API.
        mock_client = mock.MagicMock()
        mock_twilio.return_value = mock_client

        # Mock an event.
        event = Event(title='Ball?', creator=self.user)
        event.save()

        user_ids = [self.user.id, self.contact.id]
        message = 'Barack Obama (@bobama) added you as a friend!'
        from_user = self.user
        utils.send_message(user_ids, message, added_friend=True)

        # It should send push notifications to users with ios devices.
        token = self.ios_device.registration_id
        mock_apns.assert_any_call(registration_ids=[token], alert=message,
                                  badge=1)

        # It should send push notifications to users with android devices.
        token = self.android_device.registration_id
        data = {'title': 'Down.', 'message': message}
        mock_gcm.assert_any_call(registration_ids=[token], data=data)

        # It should send SMS to users without devices.
        message = message[:-1] # remove the exclamation point at the end.
        emoji = '\U0001f447'
        url = 'http://{emoji}.ws/app'.format(emoji=emoji)
        message = '{message} on Down! - {url}'.format(message=message, url=url)
        phone = unicode(self.contact_phone.phone)
        mock_client.messages.create.assert_called_with(to=phone, 
                                                       from_=settings.TWILIO_PHONE,
                                                       body=message)
