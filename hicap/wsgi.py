import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_production'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()
