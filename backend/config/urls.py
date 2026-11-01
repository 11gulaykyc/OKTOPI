from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(request):
    return JsonResponse({"status": "ok", "service": "oktopi-api"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/curriculum/", include("apps.curriculum.urls")),
    path("api/questions/", include("apps.questions.urls")),
    path("api/study-sessions/", include("apps.study_sessions.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
    path("api/exams/", include("apps.exams.urls")),
    path("api/gamification/", include("apps.gamification.urls")),
]
