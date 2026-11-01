from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import engine
from .models import Badge, PersonalGoal, UserBadge
from .services import level_info, total_points

# Alt sınırlar, hedefi 1'e çekip ödülü anında almayı anlamsız kılar.
GOAL_LIMITS = {
    PersonalGoal.GoalType.DAILY_QUESTIONS: (5, 200),
    PersonalGoal.GoalType.DAILY_MINUTES: (10, 600),
}


def badge_list(user):
    earned = dict(UserBadge.objects.filter(user=user).values_list("badge_id", "awarded_at"))
    return [
        {
            "code": b.code,
            "name": b.name,
            "description": b.description,
            "icon": b.icon,
            "points_reward": b.points_reward,
            "earned": b.id in earned,
            "awarded_at": earned.get(b.id),
        }
        for b in Badge.objects.filter(is_active=True)
    ]


def active_goals(user):
    today = timezone.localdate()
    goals = {g.goal_type: g for g in PersonalGoal.objects.filter(user=user, valid_until__isnull=True)}
    result = []
    for goal_type, label in PersonalGoal.GoalType.choices:
        goal = goals.get(goal_type)
        low, high = GOAL_LIMITS[goal_type]
        result.append(
            {
                "goal_type": goal_type,
                "label": label,
                "target": goal.target if goal else None,
                "current": engine.goal_progress(user, goal_type, today),
                "valid_from": goal.valid_from if goal else None,
                "min": low,
                "max": high,
            }
        )
    return result


class GamificationSummaryView(APIView):
    """Puan/seviye, rozetler, güncel görevler ve hedefler. Her zaman isteği yapan kullanıcının verisi."""

    def get(self, request):
        rewards = engine.Rewards()
        tasks = engine.refresh_tasks(request.user, rewards)
        return Response(
            {
                "points": level_info(total_points(request.user)),
                "badges": badge_list(request.user),
                "tasks": [engine.serialize_task(t) for t in tasks],
                "goals": active_goals(request.user),
                "rewards": rewards.as_dict(),
            }
        )


class BadgeListView(APIView):
    def get(self, request):
        return Response(badge_list(request.user))


class TaskListView(APIView):
    def get(self, request):
        rewards = engine.Rewards()
        tasks = engine.refresh_tasks(request.user, rewards)
        return Response({"tasks": [engine.serialize_task(t) for t in tasks], "rewards": rewards.as_dict()})


class GoalSerializer(serializers.Serializer):
    goal_type = serializers.ChoiceField(choices=PersonalGoal.GoalType.choices)
    target = serializers.IntegerField()

    def validate(self, attrs):
        low, high = GOAL_LIMITS[attrs["goal_type"]]
        if not low <= attrs["target"] <= high:
            raise serializers.ValidationError({"target": f"Hedef {low} ile {high} arasında olmalı."})
        return attrs


class GoalsView(APIView):
    """GET: aktif hedefler + son 14 gün. PUT: hedefi güncelle (eski hedef kapatılır, geçmiş korunur)."""

    def get(self, request):
        return Response({"goals": active_goals(request.user), "history": engine.goal_history(request.user)})

    def put(self, request):
        serializer = GoalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        engine.set_goal(request.user, **serializer.validated_data)
        # Yeni hedef bugün zaten karşılanıyorsa ödül hemen verilir.
        rewards = engine.on_goal_changed(request.user)
        return Response(
            {"goals": active_goals(request.user), "history": engine.goal_history(request.user), "rewards": rewards.as_dict()}
        )


class GoalDetailView(APIView):
    def delete(self, request, goal_type):
        if goal_type not in PersonalGoal.GoalType.values:
            return Response({"detail": "Böyle bir hedef türü yok.", "code": "not_found"}, status=status.HTTP_404_NOT_FOUND)
        engine.clear_goal(request.user, goal_type)
        return Response(status=status.HTTP_204_NO_CONTENT)
