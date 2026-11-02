from django.urls import path

from .views import (
    DashboardSummaryView,
    ErrorAnalysisView,
    MasteryMapView,
    TopicCompleteView,
    TopicProgressDetailView,
    TopicProgressListView,
)

urlpatterns = [
    path("dashboard-summary/", DashboardSummaryView.as_view(), name="analytics-dashboard-summary"),
    path("mastery-map/", MasteryMapView.as_view(), name="analytics-mastery-map"),
    path("error-analysis/", ErrorAnalysisView.as_view(), name="analytics-error-analysis"),
    path("topic-progress/", TopicProgressListView.as_view(), name="analytics-topic-progress-list"),
    path("topic-progress/<str:topic_id>/", TopicProgressDetailView.as_view(), name="analytics-topic-progress"),
    path("topic-progress/<str:topic_id>/complete/", TopicCompleteView.as_view(), name="analytics-topic-complete"),
]
