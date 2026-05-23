# COMMENT-HEADER
# File: nyondogeneralhardware/asgi.py
# Simple review note: use this file for code logic and Django app behavior.
"""
ASGI config for nyondogeneralhardware project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nyondogeneralhardware.settings')

application = get_asgi_application()
