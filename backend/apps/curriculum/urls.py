from django.urls import path

from .views import GradeDetailView, GradeListView, OyssView, TopicDetailView

urlpatterns = [
    path("grades/", GradeListView.as_view(), name="curriculum-grades"),
    path("grades/<str:grade>/", GradeDetailView.as_view(), name="curriculum-grade-detail"),
    path("topics/<str:topic_id>/", TopicDetailView.as_view(), name="curriculum-topic-detail"),
    path("oyss/", OyssView.as_view(), name="curriculum-oyss"),
]
