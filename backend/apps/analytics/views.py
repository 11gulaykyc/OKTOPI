from rest_framework import serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.curriculum.content_loader import GRADES, get_repository
from apps.gamification import engine

from .models import TopicProgress
from .services import (
    complete_topic,
    dashboard_summary,
    default_grade,
    error_analysis,
    mastery_map,
    save_last_section,
    serialize_progress,
)


def _grade_param(request):
    """?grade=9 değerini okur; verilmezse öğrencinin kendi sınıfı kullanılır."""
    grade = request.query_params.get("grade")
    if grade is None:
        return default_grade(request.user)
    if not grade.isdigit() or int(grade) not in GRADES:
        raise ValidationError({"grade": "Geçerli sınıf düzeyleri: 9, 10, 11, 12."})
    return int(grade)


def _topic_or_404(topic_id):
    entry = get_repository().topic_ref(topic_id)
    if not entry:
        raise NotFound("Konu bulunamadı.")
    return entry


class DashboardSummaryView(APIView):
    """Öğrenci paneli özeti. Her zaman isteği yapan kullanıcının kendi verisi döner."""

    def get(self, request):
        return Response(dashboard_summary(request.user))


class MasteryMapView(APIView):
    """Gelişim Haritası: ?grade=9. Yalnızca isteği yapan kullanıcının verisi."""

    def get(self, request):
        return Response(mastery_map(request.user, _grade_param(request)))


class ErrorAnalysisView(APIView):
    """Kavram yanılgısı örüntüleri ve düzeltilmemiş yanlışlar: ?grade=9. Cevap anahtarı içermez."""

    def get(self, request):
        return Response(error_analysis(request.user, _grade_param(request)))


class TopicProgressListView(APIView):
    """Kullanıcının konu ilerlemeleri: ?grade=9"""

    def get(self, request):
        qs = TopicProgress.objects.filter(user=request.user)
        grade = request.query_params.get("grade")
        if grade is not None:
            if not grade.isdigit() or int(grade) not in GRADES:
                raise ValidationError({"grade": "Geçerli sınıf düzeyleri: 9, 10, 11, 12."})
            qs = qs.filter(grade=int(grade))
        return Response([serialize_progress(p) for p in qs.order_by("-updated_at")])


class LastSectionSerializer(serializers.Serializer):
    last_section_id = serializers.CharField(max_length=64)


class TopicProgressDetailView(APIView):
    """Bir konudaki ilerleme. PATCH ile "son kalınan yer" kaydedilir."""

    def get(self, request, topic_id):
        _topic_or_404(topic_id)
        progress = TopicProgress.objects.filter(user=request.user, topic_id=topic_id).first()
        if progress is None:
            return Response({"topic_id": topic_id, "status": TopicProgress.Status.NOT_STARTED, "last_section_id": ""})
        return Response(serialize_progress(progress))

    def patch(self, request, topic_id):
        grade, _, ref = _topic_or_404(topic_id)
        serializer = LastSectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        section_id = serializer.validated_data["last_section_id"]
        if section_id not in {s.id for s in ref.subtopics}:
            raise ValidationError({"last_section_id": "Bu bölüm konuya ait değil."})
        progress = save_last_section(request.user, topic_id, grade, section_id)
        rewards = engine.on_topic_activity(request.user)
        return Response({**serialize_progress(progress), "rewards": rewards.as_dict()})


class TopicCompleteView(APIView):
    """Konuyu tamamlandı olarak işaretler. Tekrarlanan istek ikinci kez puan kazandırmaz."""

    def post(self, request, topic_id):
        grade, _, _ = _topic_or_404(topic_id)
        progress, points_awarded = complete_topic(request.user, topic_id, grade)
        rewards = engine.on_topic_activity(request.user)
        rewards.points += points_awarded
        return Response({**serialize_progress(progress), "points_awarded": points_awarded, "rewards": rewards.as_dict()})
