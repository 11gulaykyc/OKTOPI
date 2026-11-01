from django.contrib import admin

from .models import ExamAnswer, PracticeSession, TimedExamSession


class PracticeAnswerInline(admin.TabularInline):
    model = ExamAnswer
    fk_name = "practice_session"
    fields = ("question_id", "selected_option", "is_correct", "answered_at")
    readonly_fields = fields
    extra = 0
    can_delete = False


class TimedAnswerInline(PracticeAnswerInline):
    fk_name = "timed_session"


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "grade", "topic_id", "mistakes_only", "started_at", "finished_at", "correct_count", "incorrect_count")
    list_filter = ("grade", "mistakes_only")
    search_fields = ("user__username", "topic_id")
    readonly_fields = ("question_ids", "rewards")
    inlines = (PracticeAnswerInline,)


@admin.register(TimedExamSession)
class TimedExamSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "grade", "topic_id", "started_at", "deadline", "finished_at", "auto_finished", "correct_count")
    list_filter = ("grade", "auto_finished")
    search_fields = ("user__username", "topic_id")
    readonly_fields = ("question_ids", "rewards")
    inlines = (TimedAnswerInline,)
