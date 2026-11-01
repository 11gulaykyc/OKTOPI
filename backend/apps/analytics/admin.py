from django.contrib import admin

from .models import MisconceptionLog, QuestionAttempt, TopicProgress


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "grade", "topic_id", "status", "questions_answered", "correct_answers", "updated_at")
    list_filter = ("grade", "status")
    search_fields = ("user__username", "topic_id")


@admin.register(MisconceptionLog)
class MisconceptionLogAdmin(admin.ModelAdmin):
    list_display = ("user", "question_id", "misconception_tag", "subtopic_id", "source", "created_at")
    list_filter = ("source",)
    search_fields = ("user__username", "misconception_tag", "question_id")


@admin.register(QuestionAttempt)
class QuestionAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "question_id", "topic_id", "selected_option", "is_correct", "source", "created_at")
    list_filter = ("source", "is_correct", "grade")
    search_fields = ("user__username", "question_id", "topic_id")
