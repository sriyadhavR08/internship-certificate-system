import logging
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler


def exception_handler(exc, context):
    response = drf_handler(exc, context)
    if response is not None:
        response.data = {'success': False, 'message': 'Please check your request.', 'errors': response.data}
        return response
    if isinstance(exc, IntegrityError):
        return Response({'success': False, 'message': 'A record with these details already exists. Refresh and try again.'}, status=409)
    logging.getLogger(__name__).exception('API request failed')
    return Response({'success': False, 'message': 'Unable to complete the request. Please try again.'}, status=500)
