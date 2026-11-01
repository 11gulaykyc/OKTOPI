from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import StudentProfile
from .validators import (
    FIRST_NAME_MIN_LETTERS,
    LAST_NAME_MIN_LETTERS,
    UsernameValidator,
    clean_person_name,
    validate_real_email,
)

User = get_user_model()


def validate_birth_date(value):
    if value > timezone.localdate():
        raise serializers.ValidationError("Doğum tarihi gelecekte olamaz.")
    if value.year < StudentProfile.MIN_BIRTH_YEAR:
        raise serializers.ValidationError("Doğum tarihini kontrol et.")
    return value


def _django_to_drf(func, value, **kwargs):
    try:
        return func(value, **kwargs)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.messages) from exc


class StudentProfileSerializer(serializers.ModelSerializer):
    school_type_display = serializers.CharField(source="get_school_type_display", read_only=True)
    initial_level_display = serializers.CharField(source="get_initial_level_status_display", read_only=True)
    age = serializers.SerializerMethodField()
    is_birthday_today = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = (
            "birth_date",
            "age",
            "is_birthday_today",
            "school_type",
            "school_type_display",
            "grade_level",
            "initial_level_status",
            "initial_level_display",
            "initial_level_assessed_at",
        )
        # Başlangıç seviyesi yalnızca sunucudaki tanılama testiyle güncellenir.
        read_only_fields = ("initial_level_status", "initial_level_assessed_at")
        extra_kwargs = {"birth_date": {"validators": [validate_birth_date]}}

    def get_age(self, obj):
        return obj.age_on(timezone.localdate())

    def get_is_birthday_today(self, obj):
        # Doğum günü kontrolü sunucu saatine (Europe/Istanbul) göre yapılır.
        return obj.is_birthday_on(timezone.localdate())


class PersonFieldsMixin:
    """Ad, soyad ve e-posta kuralları kayıt ile profil güncellemede aynıdır."""

    def validate_first_name(self, value):
        return _django_to_drf(clean_person_name, value, min_letters=FIRST_NAME_MIN_LETTERS, label="Ad")

    def validate_last_name(self, value):
        return _django_to_drf(clean_person_name, value, min_letters=LAST_NAME_MIN_LETTERS, label="Soyad")

    def validate_email(self, value):
        value = _django_to_drf(validate_real_email, value)
        others = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            others = others.exclude(pk=self.instance.pk)
        if others.exists():
            raise serializers.ValidationError("Bu e-posta adresiyle zaten bir hesap var.")
        return value


class UserSerializer(PersonFieldsMixin, serializers.ModelSerializer):
    profile = StudentProfileSerializer()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined", "profile")
        read_only_fields = ("id", "username", "date_joined")
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        return instance


class RegisterSerializer(PersonFieldsMixin, serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    email = serializers.CharField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={"input_type": "password"})
    birth_date = serializers.DateField(validators=[validate_birth_date])
    school_type = serializers.ChoiceField(choices=StudentProfile.SchoolType.choices)
    grade_level = serializers.IntegerField(min_value=9, max_value=12)

    def validate_username(self, value):
        _django_to_drf(UsernameValidator(), value)
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu kullanıcı adı alınmış.")
        return value

    def validate(self, attrs):
        candidate = User(
            username=attrs["username"], email=attrs["email"], first_name=attrs["first_name"], last_name=attrs["last_name"]
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        profile_fields = {k: validated_data.pop(k) for k in ("birth_date", "school_type", "grade_level")}
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        try:
            with transaction.atomic():
                user.save()
                StudentProfile.objects.create(user=user, **profile_fields)
        except IntegrityError as exc:
            # Aynı anda gelen iki kayıt isteği ön kontrolü geçse bile veritabanı kısıtı yakalar.
            if User.objects.filter(username__iexact=user.username).exists():
                raise serializers.ValidationError({"username": ["Bu kullanıcı adı alınmış."]}) from exc
            raise serializers.ValidationError({"email": ["Bu e-posta adresiyle zaten bir hesap var."]}) from exc
        return user


class EmailOrUsernameTokenSerializer(TokenObtainPairSerializer):
    """Kullanıcı adı alanına e-posta yazılırsa ilgili kullanıcı adına çevirir."""

    default_error_messages = {
        "no_active_account": "Kullanıcı adı/e-posta veya şifre hatalı.",
    }

    def validate(self, attrs):
        login = attrs.get(self.username_field, "")
        if "@" in login:
            user = User.objects.filter(email__iexact=login).only("username").first()
            if user:
                attrs[self.username_field] = user.username
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
