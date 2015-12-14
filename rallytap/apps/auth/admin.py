from __future__ import unicode_literals
from django.contrib import admin
from .models import AuthCode, LinfootFunnel, SocialAccount, User, UserPhone


@admin.register(AuthCode, LinfootFunnel, SocialAccount, User, UserPhone)
class AuthAdmin(admin.ModelAdmin):
    pass
