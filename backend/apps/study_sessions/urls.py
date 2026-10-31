from django.urls import path

from .views import EndSessionView, HeartbeatView

urlpatterns = [
    path("heartbeat/", HeartbeatView.as_view(), name="study-heartbeat"),
    path("end/", EndSessionView.as_view(), name="study-end"),
]
