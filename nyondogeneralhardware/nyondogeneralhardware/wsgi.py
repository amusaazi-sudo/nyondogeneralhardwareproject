# COMMENT-HEADER
# File: nyondogeneralhardware/wsgi.py
# Simple review note: use this file for code logic and Django app behavior.
"""
WSGI config for nyondogeneralhardware project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nyondogeneralhardware.settings')

application = get_wsgi_application()
