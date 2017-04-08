# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from pygments import highlight
from pygments.lexers.data import JsonLexer
from pygments.formatters import HtmlFormatter
from django.contrib import admin
from . import models
import json

class LogAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_id', 'request_method', 'request_url',
                    'response_code', 'datetime', 'ip_address')
    date_hierarchy = 'datetime'
    list_filter = ('request_method', 'response_code')
    search_fields = ('user', 'request_url')
    readonly_fields = ('user_id','user','request_url','request_method','response_code','datetime','data_prettified','ip_address')
    exclude = ('extra_data',)

    def data_prettified(self, instance):
        """Function to display pretty version of our data"""

        # Convert the data to sorted, indented JSON
        response = json.dumps(instance.extra_data, sort_keys=True, indent=2)

        # Truncate the data. Alter as needed
        response = response[:5000]

        # Get the Pygments formatter
        formatter = HtmlFormatter(style='colorful')

        # Highlight the data
        response = highlight(response, JsonLexer(), formatter)

        # Get the stylesheet
        style = "<style>" + formatter.get_style_defs() + "</style><br>"

        # Safe the output
        return mark_safe(style + response)

    data_prettified.short_description = _('extra data')

admin.site.register(models.ActivityLog, LogAdmin)
