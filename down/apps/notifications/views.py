from __future__ import unicode_literals
from django.shortcuts import render
from push_notifications.models import APNSDevice
from rest_framework import viewsets
from .serializers import APNSDeviceSerializer


# TODO: Security
class APNSDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = APNSDeviceSerializer
    queryset = APNSDevice.objects.all()
