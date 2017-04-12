# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.module_loading import import_string as _load
from django.core.exceptions import DisallowedHost
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from .models import ActivityLog
from . import conf
try:
    from rest_framework.authtoken.models import Token
except:
    pass

def get_ip_address(request):
    for header in conf.IP_ADDRESS_HEADERS:
        addr = request.META.get(header)
        if addr:
            return addr.split(',')[0].strip()


def get_user_from_token(request):
    # check if meta has HTTP_AUTH
    try:
        token_string = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
    except:
        token_string = None

    if not token_string:
        return None
    try:
        token = Token.objects.get(pk=token_string)
    except:
        token = None

    if not token:
        return None

    try:
        return token.user
    except:
        return None

def get_extra_data(request, response, body):
    if not conf.GET_EXTRA_DATA:
        return
    return _load(conf.GET_EXTRA_DATA)(request, response, body)

class ActivityLogMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_request(self, request):
        request.saved_body = request.body
        if conf.LAST_ACTIVITY and request.user.is_authenticated():
            getattr(request.user, 'update_last_activity', lambda: 1)()

    def process_response(self, request, response):

        try:
            self._write_log(request, response, getattr(request, 'saved_body', ''))
        except DisallowedHost:
            return HttpResponseForbidden()

        return response

    def _write_log(self, request, response, body):
        miss_log = [
            not(conf.ANONIMOUS or request.user.is_authenticated()),
            request.method not in conf.METHODS,
            any(url in request.path for url in conf.EXCLUDE_URLS)
        ]
        if conf.STATUSES:
            miss_log.append(response.status_code not in conf.STATUSES)

        if conf.EXCLUDE_STATUSES:
            miss_log.append(response.status_code in conf.EXCLUDE_STATUSES)

        if any(miss_log):
            return

        user_obj = getattr(request, 'user', None)
        if not user_obj.pk:
            # Try to get user_obj from token
            user_obj = get_user_from_token(request)

        print user_obj, user_obj.get_username(), user_obj.pk

        if user_obj and user_obj.pk:
            user, user_id = user_obj.get_username(), user_obj.pk
        elif getattr(request, 'session', None):
            user, user_id = 'anon_{}'.format(request.session.session_key), 0
        else:
            user, user_id = 'unknown', 0
        #print "end"
        ActivityLog.objects.create(
            user_id=user_id,
            user=user,
            request_url=request.build_absolute_uri()[:255],
            request_method=request.method,
            response_code=response.status_code,
            ip_address=get_ip_address(request),
            extra_data=get_extra_data(request, response, body)
        )
        return

    # def process_request(self, request):
    #     request.saved_body = request.body
    #     print dir(request)
    #     if conf.LAST_ACTIVITY and request.user.is_authenticated():
    #         getattr(request.user, 'update_last_activity', lambda: 1)()
    #
    # def process_response(self, request, response):
    #     try:
    #         self._write_log(request, response, getattr(request, 'saved_body', ''))
    #         pass
    #     except DisallowedHost:
    #         return HttpResponseForbidden()
    #     return response
    #

    #
    # def __call__(self, request):
    #     response = self.get_response(request)
    #     return self.process_response(request, response)
