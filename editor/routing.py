from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/editor/room/(?P<task_id>\d+)/$',
        consumers.UpdateConsumer.as_asgi()
    )
]