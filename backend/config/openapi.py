"""OpenAPI (drf-spectacular) açıklamaları.

Uygulamaların çoğu düz `APIView` kullandığı için drf-spectacular istek/yanıt gövdelerini
kendisi çıkaramaz. Açıklamalar, uygulama dosyalarına dokunmadan (3 admin çakışma kuralı)
burada merkezî olarak eklenir; `config/urls.py` bu modülü içe aktarır.

Yeni bir uç nokta eklediğinizde buraya da bir satır ekleyin ve şemayı doğrulayın
(hata/uyarı varsa komut başarısız olur):
    python manage.py spectacular --validate --fail-on-warn --file openapi.yaml
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import serializers

from apps.accounts import views as accounts
from apps.analytics import views as analytics
from apps.curriculum import views as curriculum
from apps.exams import views as exams
from apps.gamification import views as gamification
from apps.questions import views as questions
from apps.study_sessions import views as study_sessions


class ApiErrorSerializer(serializers.Serializer):
    """config/exceptions.py: tüm hatalar bu biçimde döner."""

    detail = serializers.CharField(help_text="Kullanıcıya gösterilebilir Türkçe mesaj")
    code = serializers.CharField(help_text="Makine okur kod: invalid, not_authenticated, not_found, conflict, time_up …")
    fields = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField()), required=False, help_text="Alan hataları"
    )


ERRORS = {
    400: OpenApiResponse(ApiErrorSerializer, description="Geçersiz istek"),
    401: OpenApiResponse(ApiErrorSerializer, description="Giriş gerekli / token geçersiz"),
    404: OpenApiResponse(ApiErrorSerializer, description="Bulunamadı"),
}
CONFLICT = {409: OpenApiResponse(ApiErrorSerializer, description="Oturum bu işleme uygun değil (ör. süre doldu: code=time_up)")}

GRADE = OpenApiParameter("grade", OpenApiTypes.INT, enum=[9, 10, 11, 12], description="Sınıf düzeyi")
GRADE_DEFAULT_OWN = OpenApiParameter(
    "grade", OpenApiTypes.INT, enum=[9, 10, 11, 12], description="Sınıf düzeyi; verilmezse öğrencinin profilindeki sınıf"
)
SESSION_KIND = OpenApiParameter("kind", OpenApiTypes.STR, OpenApiParameter.PATH, enum=["practice", "timed"])


def ok(description, status=200):
    return {status: OpenApiResponse(OpenApiTypes.OBJECT, description=description), **ERRORS}


def document(view, **methods):
    """`document(View, get=extend_schema(...))` → görünüme açıklamayı uygular."""
    extend_schema_view(**methods)(view)


# --- Kimlik ---
document(
    accounts.RegisterView,
    post=extend_schema(summary="Kayıt ol", responses=ok("Oluşturulan kullanıcı ile `access` / `refresh` token'ları", 201)),
)
document(accounts.ProfileOptionsView, get=extend_schema(summary="Kayıt formu seçenekleri (okul türü, sınıf)", responses=ok("Seçenek listeleri")))
document(
    accounts.DiagnosticView,
    get=extend_schema(summary="Başlangıç seviye testi soruları (cevap anahtarı içermez)", responses=ok("Sorular ve test durumu")),
    post=extend_schema(summary="Başlangıç seviye testini gönder", responses={**ok("Belirlenen seviye ve soru bazında sonuç"), **CONFLICT}),
)

# --- Müfredat (herkese açık) ---
document(curriculum.GradeListView, get=extend_schema(operation_id="curriculum_grades_list", summary="Sınıf düzeyleri ve konu sayıları", responses=ok("Sınıf listesi")))
document(curriculum.GradeDetailView, get=extend_schema(summary="Bir sınıfın tema → konu → alt konu ağacı", responses=ok("Müfredat ağacı")))
document(
    curriculum.TopicDetailView,
    get=extend_schema(
        summary="Konu anlatımı",
        description="Bölümler, formüller, çözümlü örnekler, pekiştirme soru kimlikleri ve etkileşimli grafik (`visualizations`) parametreleri.",
        responses=ok("Konu ve (varsa) anlatım içeriği"),
    ),
)
document(curriculum.OyssView, get=extend_schema(summary="OYSS bilgilendirme ve sınav takvimi", responses=ok("OYSS içeriği")))

# --- Soru havuzu ---
document(
    questions.QuestionListView,
    get=extend_schema(
        operation_id="questions_list",
        summary="Soru listesi (cevap anahtarı içermez)",
        parameters=[
            GRADE,
            OpenApiParameter("topic_id", OpenApiTypes.STR),
            OpenApiParameter("subtopic_id", OpenApiTypes.STR),
            OpenApiParameter("difficulty", OpenApiTypes.STR, enum=["easy", "medium", "hard"]),
        ],
        responses=ok("Sorular"),
    ),
)
document(questions.QuestionDetailView, get=extend_schema(summary="Tek soru (cevap anahtarı içermez)", responses=ok("Soru")))
document(
    questions.CheckAnswerView,
    post=extend_schema(
        summary="Pekiştirme sorusu cevabını kontrol et",
        request=questions.CheckAnswerSerializer,
        responses=ok("Doğruluk, doğru şık, çözüm ve (yanlışsa) kavram yanılgısı ile önerilen konu"),
    ),
)

# --- Soru çözümü ve süreli test ---
document(
    exams.StartPracticeView,
    post=extend_schema(summary="Soru çözümü başlat", request=exams.StartPracticeSerializer, responses=ok("Oturum ve sorular", 201)),
)
document(
    exams.StartTimedExamView,
    post=extend_schema(
        summary="Süreli test başlat",
        description="Başlangıç ve bitiş zamanı sunucuda belirlenir (`deadline`, `server_now`).",
        request=exams.StartTimedSerializer,
        responses=ok("Oturum, sorular ve süre bilgisi", 201),
    ),
)
document(
    exams.SubmitAnswerView,
    post=extend_schema(
        summary="Cevap gönder",
        description="Soru çözümünde değerlendirme hemen döner; süreli testte cevap yalnızca kaydedilir.",
        request=exams.SubmitAnswerSerializer,
        responses={**ok("Değerlendirme (soru çözümü) veya kayıt onayı (süreli test)"), **CONFLICT},
    ),
)
document(
    exams.FinishExamView,
    post=extend_schema(summary="Oturumu bitir ve sonucu al", request=exams.SessionRefSerializer, responses=ok("Sonuç")),
)
document(
    exams.SessionListView,
    get=extend_schema(
        operation_id="exams_sessions_list",
        summary="Son oturumlar",
        parameters=[OpenApiParameter("limit", OpenApiTypes.INT, description="1–50, varsayılan 10")],
        responses=ok("Oturum listesi"),
    ),
)
document(exams.SessionDetailView, get=extend_schema(summary="Oturum durumu", parameters=[SESSION_KIND], responses=ok("Oturum ve sorular")))
document(
    exams.SessionResultView,
    get=extend_schema(summary="Oturum sonucu", parameters=[SESSION_KIND], responses={**ok("Soru bazında sonuç ve yanılgı özeti"), **CONFLICT}),
)

# --- Çalışma süresi ---
document(
    study_sessions.HeartbeatView,
    post=extend_schema(
        summary="Heartbeat (60 sn)",
        description="Yalnızca kullanıcı etkileşimdeyken gönderilir. 120 sn'den uzun sessizlikten sonra süre eklenmez.",
        request=study_sessions.HeartbeatSerializer,
        responses=ok("Oturum ve bugünkü aktif süre"),
    ),
)
document(
    study_sessions.EndSessionView,
    post=extend_schema(summary="Çalışma oturumunu kapat", request=None, responses={**ok("Kapanan oturum"), 204: OpenApiResponse(description="Açık oturum yok")}),
)

# --- Analitik ---
document(analytics.DashboardSummaryView, get=extend_schema(summary="Öğrenci paneli özeti", responses=ok("Çalışma süresi, soru, konu, puan, görev ve hedef özetleri")))
document(
    analytics.MasteryMapView,
    get=extend_schema(
        summary="Gelişim Haritası",
        description="Konu başına düzey: mastered / developing / needs_review / insufficient (yeterli veri yok) / not_started.",
        parameters=[GRADE_DEFAULT_OWN],
        responses=ok("Temalara göre konu düzeyleri ve tekrar listesi"),
    ),
)
document(
    analytics.ErrorAnalysisView,
    get=extend_schema(
        summary="Hata Analizi",
        description="Kavram yanılgısı örüntüleri ve düzeltilmemiş yanlışlar. Doğru cevap anahtarı içermez.",
        parameters=[GRADE_DEFAULT_OWN],
        responses=ok("Örüntüler, yanlışlar ve eşik değerleri"),
    ),
)
document(analytics.TopicProgressListView, get=extend_schema(operation_id="analytics_topic_progress_list", summary="Konu ilerlemeleri", parameters=[GRADE], responses=ok("İlerleme listesi")))
document(
    analytics.TopicProgressDetailView,
    get=extend_schema(summary="Bir konudaki ilerleme", responses=ok("İlerleme")),
    patch=extend_schema(summary="Son kalınan bölümü kaydet", request=analytics.LastSectionSerializer, responses=ok("Güncel ilerleme ve ödüller")),
)
document(
    analytics.TopicCompleteView,
    post=extend_schema(summary="Konuyu tamamlandı olarak işaretle (puan bir kez verilir)", request=None, responses=ok("İlerleme, kazanılan puan ve ödüller")),
)

# --- Oyunlaştırma ---
document(gamification.GamificationSummaryView, get=extend_schema(summary="Puan, seviye, rozet, görev ve hedef özeti", responses=ok("Özet")))
document(gamification.BadgeListView, get=extend_schema(summary="Rozetler ve kazanılma durumu", responses=ok("Rozet listesi")))
document(gamification.TaskListView, get=extend_schema(summary="Günlük / haftalık görevler", responses=ok("Görev listesi")))
document(
    gamification.GoalsView,
    get=extend_schema(summary="Kişisel hedefler", responses=ok("Hedefler ve geçmiş")),
    put=extend_schema(
        summary="Hedef belirle / güncelle",
        description="Eski hedef kapatılır, yenisi açılır; geçmiş günlerin değerlendirmesi değişmez.",
        request=gamification.GoalSerializer,
        responses=ok("Güncel hedefler ve ödüller"),
    ),
)
document(
    gamification.GoalDetailView,
    delete=extend_schema(summary="Hedefi kaldır", responses={204: OpenApiResponse(description="Kaldırıldı"), **ERRORS}),
)
