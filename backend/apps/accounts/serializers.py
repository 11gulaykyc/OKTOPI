from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import StudentProfile

User = get_user_model()


def validate_birth_date(value):
    today = timezone.localdate()
    if value > today:
        raise serializers.ValidationError("Doğum tarihi gelecekte olamaz.")
    probe = StudentProfile(birth_date=value)
    age = probe.age_on(today)
    if not StudentProfile.MIN_AGE <= age <= StudentProfile.MAX_AGE:
        raise serializers.ValidationError(
            f"Doğum tarihini kontrol et; yaşın {StudentProfile.MIN_AGE}–{StudentProfile.MAX_AGE} arasında olmalı."
        )
    return value


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
        )
        # Başlangıç seviyesi yalnızca sunucudaki tanılama testiyle (Faz 3) güncellenir.
        read_only_fields = ("initial_level_status",)
        extra_kwargs = {"birth_date": {"validators": [validate_birth_date]}}

    def get_age(self, obj):
        return obj.age_on(timezone.localdate())

    def get_is_birthday_today(self, obj):
        # Doğum günü kontrolü sunucu saatine (Europe/Istanbul) göre yapılır.
        return obj.is_birthday_on(timezone.localdate())


class UserSerializer(serializers.ModelSerializer):
    profile = StudentProfileSerializer()

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined", "profile")
        read_only_fields = ("id", "username", "date_joined")

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("Bu e-posta adresi başka bir hesapta kullanılıyor.")
        return value

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


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    birth_date = serializers.DateField(validators=[validate_birth_date])
    school_type = serializers.ChoiceField(choices=StudentProfile.SchoolType.choices)
    grade_level = serializers.IntegerField(min_value=9, max_value=12)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Bu kullanıcı adı alınmış.")
        return value

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Bu e-posta adresiyle zaten bir hesap var.")
        return value

    def validate(self, attrs):
        candidate = User(username=attrs["username"], email=attrs["email"])
        validate_password(attrs["password"], user=candidate)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_fields = {k: validated_data.pop(k) for k in ("birth_date", "school_type", "grade_level")}
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        StudentProfile.objects.create(user=user, **profile_fields)
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
