from django.urls import path

from .views import QuestionDetailView, QuestionListView

urlpatterns = [
    path("", QuestionListView.as_view(), name="question-list"),
    path("<str:question_id>/", QuestionDetailView.as_view(), name="question-detail"),
]
