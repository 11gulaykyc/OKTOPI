from django.urls import path

from .views import BadgeListView, GamificationSummaryView, GoalDetailView, GoalsView, TaskListView

urlpatterns = [
    path("summary/", GamificationSummaryView.as_view(), name="gamification-summary"),
    path("badges/", BadgeListView.as_view(), name="gamification-badges"),
    path("tasks/", TaskListView.as_view(), name="gamification-tasks"),
    path("goals/", GoalsView.as_view(), name="gamification-goals"),
    path("goals/<str:goal_type>/", GoalDetailView.as_view(), name="gamification-goal-detail"),
]
