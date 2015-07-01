from __future__ import unicode_literals
from storages.backends.s3boto import S3BotoStorage
from django.contrib.staticfiles.storage import CachedFilesMixin


class S3CachedStorage(CachedFilesMixin, S3BotoStorage):
    pass
