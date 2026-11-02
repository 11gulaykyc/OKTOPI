from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.curriculum.content_loader import get_repository

from . import services
from .models import PracticeSession, TimedExamSession

SESSION_MODELS = {"practice": PracticeSession, "timed": TimedExamSession}
DIFFICULTIES = ("easy", "medium", "hard")


def get_session(user, kind, session_id):
    """Oturumu YALNIZCA isteği yapan kullanıcının kayıtları arasında arar (IDOR koruması).

    Başka bir öğrencinin oturumu "yok" gibi davranır (404); varlığı bile sızdırılmaz.
    """
    model = SESSION_MODELS.get(kind)
    if model is None:
        raise NotFound("Oturum bulunamadı.")
    session = model.objects.filter(user=user, pk=session_id).first()
    if session is None:
        raise NotFound("Oturum bulunamadı.")
    if kind == "timed":
        session = services.expire_if_needed(session)
    return session


class StartSessionSerializer(serializers.Serializer):
    grade = serializers.IntegerField(min_value=9, max_value=12)
    topic_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    subtopic_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")
    difficulty = serializers.ChoiceField(choices=DIFFICULTIES, required=False, allow_blank=True, default="")
    count = serializers.IntegerField(min_value=1, max_value=services.MAX_QUESTIONS, default=services.DEFAULT_QUESTIONS)

    def validate(self, attrs):
        repo = get_repository()
        if attrs["topic_id"]:
            entry = repo.topic_ref(attrs["topic_id"])
            if not entry or entry[0] != attrs["grade"]:
                raise ValidationError({"topic_id": "Bu konu seçilen sınıfta yok."})
        if attrs["subtopic_id"]:
            parent = repo.subtopic_parent.get(attrs["subtopic_id"])
            if not parent or (attrs["topic_id"] and parent != attrs["topic_id"]):
                raise ValidationError({"subtopic_id": "Bu alt konu seçilen konuda yok."})
        return attrs


class StartPracticeSerializer(StartSessionSerializer):
    mistakes_only = serializers.BooleanField(default=False)


class StartTimedSerializer(StartSessionSerializer):
    duration_minutes = serializers.IntegerField(min_value=1, max_value=120, required=False)


class StartPracticeView(APIView):
    def post(self, request):
        serializer = StartPracticeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = services.start_practice(request.user, **serializer.validated_data)
        return Response(services.session_state(session), status=status.HTTP_201_CREATED)


class StartTimedExamView(APIView):
    def post(self, request):
        serializer = StartTimedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data.pop("subtopic_id", None)
        session = services.start_timed_exam(request.user, **data)
        return Response(services.session_state(session), status=status.HTTP_201_CREATED)


class SessionRefSerializer(serializers.Serializer):
    session_type = serializers.ChoiceField(choices=tuple(SESSION_MODELS))
    session_id = serializers.IntegerField(min_value=1)


class SubmitAnswerSerializer(SessionRefSerializer):
    question_id = serializers.CharField(max_length=64)
    # Süreli testte boş/null göndermek cevabı temizler (soru boş bırakılır).
    selected_option = serializers.ChoiceField(choices=("A", "B", "C", "D", "E"), allow_null=True, allow_blank=True, required=False)


class SubmitAnswerView(APIView):
    """POST /api/exams/submit-answer/

    - Soru çözümü: cevap kesinleşir; doğru şık, çözüm ve (yanlışsa) kavram yanılgısı hemen döner.
    - Süreli test: cevap kaydedilir/güncellenir; doğruluk bilgisi test bitene kadar dönmez.
    """

    def post(self, request):
        serializer = SubmitAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session = get_session(request.user, data["session_type"], data["session_id"])
        option = data.get("selected_option") or ""
        if data["session_type"] == "practice":
            return Response(services.submit_practice_answer(session, data["question_id"], option))
        return Response(services.submit_timed_answer(session, data["question_id"], option))


class FinishExamView(APIView):
    """POST /api/exams/finish-exam/: oturumu bitirir ve sonucu döner. Tekrarlanan istek güvenlidir."""

    def post(self, request):
        serializer = SessionRefSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        session = get_session(request.user, data["session_type"], data["session_id"])
        if data["session_type"] == "practice":
            session = services.finish_practice(session)
        else:
            session = services.finish_timed_exam(session)
        return Response(services.session_result(session))


class SessionDetailView(APIView):
    def get(self, request, kind, session_id):
        return Response(services.session_state(get_session(request.user, kind, session_id)))


class SessionResultView(APIView):
    def get(self, request, kind, session_id):
        return Response(services.session_result(get_session(request.user, kind, session_id)))


class SessionListView(APIView):
    """Kullanıcının son oturumları (en yeni önce): ?limit=10"""

    def get(self, request):
        try:
            limit = min(max(int(request.query_params.get("limit", 10)), 1), 50)
        except ValueError:
            raise ValidationError({"limit": "Sayı olmalı."}) from None
        sessions = [
            *PracticeSession.objects.filter(user=request.user)[:limit],
            *TimedExamSession.objects.filter(user=request.user)[:limit],
        ]
        sessions.sort(key=lambda s: s.started_at, reverse=True)
        return Response([services.session_summary(s) for s in sessions[:limit]])
