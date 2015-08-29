from __future__ import unicode_literals
from django.shortcuts import render
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from push_notifications.models import APNSDevice
from rest_framework import mixins, status, viewsets
from .serializers import APNSDeviceSerializer


class APNSDeviceViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = APNSDeviceSerializer
    queryset = APNSDevice.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            # If this user has already created a device return a 200 response.
            if e.detail == {'registration_id': [u'This field must be unique.']}:
                headers = self.get_success_headers(serializer.data)
                return Response(status=status.HTTP_200_OK, headers=headers)
            return Response(status=status.HTTP_400_BAD_REQUEST)
