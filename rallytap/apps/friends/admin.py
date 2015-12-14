from __future__ import unicode_literals
from django.contrib import admin
from .models import Friendship


@admin.register(Friendship)
class FriendsAdmin(admin.ModelAdmin):
    pass
