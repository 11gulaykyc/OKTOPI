from django.urls import path

from .views import (
    FinishExamView,
    SessionDetailView,
    SessionListView,
    SessionResultView,
    StartPracticeView,
    StartTimedExamView,
    SubmitAnswerView,
)

urlpatterns = [
    path("practice/start/", StartPracticeView.as_view(), name="exams-practice-start"),
    path("timed/start/", StartTimedExamView.as_view(), name="exams-timed-start"),
    path("submit-answer/", SubmitAnswerView.as_view(), name="exams-submit-answer"),
    path("finish-exam/", FinishExamView.as_view(), name="exams-finish"),
    path("sessions/", SessionListView.as_view(), name="exams-session-list"),
    path("sessions/<str:kind>/<int:session_id>/", SessionDetailView.as_view(), name="exams-session-detail"),
    path("sessions/<str:kind>/<int:session_id>/result/", SessionResultView.as_view(), name="exams-session-result"),
]
