from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyStudyTotal
from .services import end_session, record_heartbeat


class HeartbeatSerializer(serializers.Serializer):
    context = serializers.CharField(max_length=100, required=False, allow_blank=True)


class HeartbeatView(APIView):
    """İstemci, kullanıcı aktifken 60 sn'de bir çağırır. Süre hesabı tamamen sunucudadır."""

    def post(self, request):
        serializer = HeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = record_heartbeat(request.user, context=serializer.validated_data.get("context", ""))
        today = DailyStudyTotal.objects.filter(user=request.user, date=timezone.localdate()).aggregate(
            total=Sum("active_seconds")
        )["total"] or 0
        return Response(
            {
                "session_id": result.session.id,
                "session_active_seconds": result.session.active_seconds,
                "credited_seconds": result.credited_seconds,
                "new_session": result.new_session,
                "today_active_seconds": today,
            }
        )


class EndSessionView(APIView):
    def post(self, request):
        session = end_session(request.user)
        if session is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"session_id": session.id, "session_active_seconds": session.active_seconds})
