from __future__ import unicode_literals
import logging
from django.http import HttpResponse
from rest_framework import status


class LoggingMixin(object):

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(LoggingMixin, self).finalize_response(request, response,
                                                               *args, **kwargs)

        # Log the request data, and response content.
        logger = logging.getLogger('console')
        logger.info(request.data)
        # The response must be rendered before accessing its content.
        response.render()
        logger.info(response.content)

        return response
