from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

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
                "birth_date_age_range": {"min": StudentProfile.MIN_AGE, "max": StudentProfile.MAX_AGE},
                "school_types": as_list(StudentProfile.SchoolType.choices),
                "grade_levels": [{"value": g, "label": f"{g}. Sınıf"} for g in (9, 10, 11, 12)],
            }
        )
