from __future__ import unicode_literals
from django.shortcuts import render
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from push_notifications.models import APNSDevice, GCMDevice
from rest_framework import mixins, status, viewsets
from .serializers import APNSDeviceSerializer, GCMDeviceSerializer


class APNSDeviceViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = APNSDeviceSerializer
    queryset = APNSDevice.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            try:
                # Check whether a device with the given device id already
                # exists.
                device_id = serializer.data['device_id']
                apnsdevice = APNSDevice.objects.get(device_id=device_id)
                
                # Update the device.
                apnsdevice.registration_id = serializer.data['registration_id']
                apnsdevice.user_id = serializer.data['user']
                apnsdevice.save()

                headers = self.get_success_headers(serializer.data)
                return Response(status=status.HTTP_200_OK, headers=headers)
            except APNSDevice.DoesNotExist:
                self.perform_create(serializer)
                headers = self.get_success_headers(serializer.data)
                return Response(status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            # If this user has already created a device return a 200 response.
            if e.detail == {'registration_id': [u'This field must be unique.']}:
                headers = self.get_success_headers(serializer.data)
                return Response(status=status.HTTP_200_OK, headers=headers)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class GCMDeviceViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = GCMDeviceSerializer
    queryset = GCMDevice.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            registration_id = serializer.data['registration_id']
            GCMDevice.objects.get(registration_id=registration_id)
            headers = self.get_success_headers(serializer.data)
            return Response(status=status.HTTP_200_OK, headers=headers)
        except GCMDevice.DoesNotExist:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(status=status.HTTP_201_CREATED, headers=headers)
