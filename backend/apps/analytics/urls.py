from django.urls import path

from .views import DashboardSummaryView, TopicCompleteView, TopicProgressDetailView, TopicProgressListView

urlpatterns = [
    path("dashboard-summary/", DashboardSummaryView.as_view(), name="analytics-dashboard-summary"),
    path("topic-progress/", TopicProgressListView.as_view(), name="analytics-topic-progress-list"),
    path("topic-progress/<str:topic_id>/", TopicProgressDetailView.as_view(), name="analytics-topic-progress"),
    path("topic-progress/<str:topic_id>/complete/", TopicCompleteView.as_view(), name="analytics-topic-complete"),
]
