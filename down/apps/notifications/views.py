from __future__ import unicode_literals
from django.shortcuts import render
from push_notifications.models import APNSDevice
from rest_framework import mixins, viewsets
from .serializers import APNSDeviceSerializer


class APNSDeviceViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = APNSDeviceSerializer
    queryset = APNSDevice.objects.all()
