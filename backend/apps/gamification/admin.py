from django.contrib import admin

from .models import Badge, DailyTask, PersonalGoal, PointLedger, UserBadge


@admin.register(PointLedger)
class PointLedgerAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "reason", "idempotency_key", "created_at")
    list_filter = ("reason",)
    search_fields = ("user__username", "idempotency_key")


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "points_reward", "order", "is_active")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "awarded_at")


@admin.register(DailyTask)
class DailyTaskAdmin(admin.ModelAdmin):
    list_display = ("user", "period", "period_start", "task_type", "progress", "target", "completed_at")
    list_filter = ("period", "task_type")


@admin.register(PersonalGoal)
class PersonalGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "goal_type", "target", "valid_from", "valid_until")
    list_filter = ("goal_type",)
