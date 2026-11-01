from django.urls import path

from .views import CheckAnswerView, QuestionDetailView, QuestionListView

urlpatterns = [
    path("", QuestionListView.as_view(), name="question-list"),
    path("<str:question_id>/", QuestionDetailView.as_view(), name="question-detail"),
    path("<str:question_id>/check/", CheckAnswerView.as_view(), name="question-check"),
]
