from django.contrib import admin

from .models import DailyStudyTotal, StudySession


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ("user", "started_at", "last_heartbeat_at", "active_seconds", "ended_at", "context")
    list_filter = ("ended_at",)
    search_fields = ("user__username",)


@admin.register(DailyStudyTotal)
class DailyStudyTotalAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "active_seconds")
    search_fields = ("user__username",)
