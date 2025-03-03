"""
ASGI config for LaLouge project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter

from django.core.asgi import get_asgi_application

django_application = get_asgi_application()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "LaLouge.settings")

from . import routing  # noqa: E402


application = ProtocolTypeRouter(
    {
        "http": django_application,
        "websocket": URLRouter(routing.websocket_urlpatterns)
    }
)
