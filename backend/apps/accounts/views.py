from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.questions.serializers import public_question

from .diagnostic import DiagnosticAlreadyDone, diagnostic_questions, submit_diagnostic
from .models import StudentProfile
from .serializers import EmailOrUsernameTokenSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.GenericAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    serializer_class = EmailOrUsernameTokenSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """Oturumdaki kullanıcının profili. Her zaman request.user döner; başka kullanıcıya erişim yoktur."""

    serializer_class = UserSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


class ProfileOptionsView(generics.GenericAPIView):
    """Kayıt/profil formlarındaki seçim listeleri (tek kaynak backend'dir)."""

    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        def as_list(choices):
            return [{"value": value, "label": label} for value, label in choices]

        return Response(
            {
                "min_birth_year": StudentProfile.MIN_BIRTH_YEAR,
                "school_types": as_list(StudentProfile.SchoolType.choices),
                "grade_levels": [{"value": g, "label": f"{g}. Sınıf"} for g in (9, 10, 11, 12)],
            }
        )


class DiagnosticAnswerSerializer(serializers.Serializer):
    question_id = serializers.CharField(max_length=64)
    selected_option = serializers.ChoiceField(choices=("A", "B", "C", "D", "E"), allow_blank=True, allow_null=True, required=False)


class DiagnosticSubmitSerializer(serializers.Serializer):
    answers = DiagnosticAnswerSerializer(many=True, allow_empty=True)

    def validate_answers(self, value):
        ids = [a["question_id"] for a in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Aynı soru birden fazla kez gönderildi.")
        return value


class DiagnosticView(generics.GenericAPIView):
    """Başlangıç seviye testi. GET: sorular (cevap anahtarı olmadan). POST: cevapları değerlendirip profile işler.

    Test bir kez yapılır; sonuç yalnızca sunucuda hesaplanır ve `initial_level_status` alanına yazılır.
    """

    serializer_class = DiagnosticSubmitSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Öğrenci profili olmayan hesaplar (ör. yönetici) için test yoktur.
        if getattr(request.user, "profile", None) is None:
            raise NotFound("Öğrenci profili bulunamadı.")

    def get(self, request):
        profile = request.user.profile
        questions = diagnostic_questions(profile.grade_level)
        return Response(
            {
                "completed": profile.initial_level_assessed_at is not None,
                "level": profile.initial_level_status,
                "level_display": profile.get_initial_level_status_display(),
                "assessed_at": profile.initial_level_assessed_at,
                "grade": profile.grade_level,
                # Kendi sınıfında soru yoksa (veya azsa) önceki sınıfların temel soruları kullanılır.
                "includes_lower_grades": any(q.grade < profile.grade_level for q in questions),
                "questions": [public_question(q) for q in questions],
            }
        )

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = {a["question_id"]: a.get("selected_option") or "" for a in serializer.validated_data["answers"]}
        try:
            result = submit_diagnostic(request.user, answers)
        except DiagnosticAlreadyDone:
            return Response(
                {"detail": "Başlangıç seviyen zaten belirlendi.", "code": "already_completed"}, status=status.HTTP_409_CONFLICT
            )
        request.user.profile.refresh_from_db()
        return Response({**result, "user": UserSerializer(request.user).data})
