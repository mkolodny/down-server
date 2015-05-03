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


class Versioning(object):

    def process_request(self, request):
        '''
        Requests should have a version string, anything without a version string 
        is assumed to be from before the beginning of down time
        '''

        accept_header = request.META['HTTP_ACCEPT']

        if accept_header != 'version == ""':
            content = {'HTTP 406 Version Error': 
                    'Your request did not contain a valid version number'}
            return HttpResponse(content, status=status.HTTP_406_NOT_ACCEPTABLE)
