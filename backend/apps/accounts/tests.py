from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import StudentProfile
from .validators import UsernameValidator, validate_real_email

User = get_user_model()


def years_ago(years, today=None):
    today = today or date.today()
    try:
        return today.replace(year=today.year - years)
    except ValueError:  # 29 Şubat
        return today.replace(year=today.year - years, day=28)


VALID_REGISTRATION = {
    "username": "ayse",
    "email": "Ayse@Example.com",
    "password": "GucluSifre!2026",
    "first_name": "Ayşe",
    "last_name": "Yılmaz",
    "birth_date": years_ago(15).isoformat(),
    "school_type": "anadolu",
    "grade_level": 9,
}


def make_student(username="ali", email="ali@example.com", password="GucluSifre!2026", grade=10):
    user = User.objects.create_user(username=username, email=email, password=password)
    StudentProfile.objects.create(user=user, birth_date=years_ago(16), school_type="fen", grade_level=grade)
    return user


def setUpModule():
    # Testler ağ erişimine bağlı olmasın: alan adı DNS kontrolü varsayılan olarak "geçerli" döner.
    global _dns_patch
    _dns_patch = mock.patch("apps.accounts.validators._domain_accepts_mail", return_value=True)
    _dns_patch.start()


def tearDownModule():
    _dns_patch.stop()


class RegisterTests(APITestCase):
    url = reverse("auth-register")

    def post(self, **changes):
        return self.client.post(self.url, {**VALID_REGISTRATION, **changes}, format="json")

    def test_register_creates_user_profile_and_returns_tokens(self):
        response = self.client.post(self.url, VALID_REGISTRATION, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        user = User.objects.get(username="ayse")
        self.assertEqual(user.email, "ayse@example.com")
        self.assertTrue(user.check_password("GucluSifre!2026"))
        self.assertEqual(user.profile.grade_level, 9)
        self.assertEqual(user.profile.initial_level_status, StudentProfile.InitialLevel.NOT_ASSESSED)
        self.assertNotIn("password", response.data["user"])

    def test_register_rejects_duplicate_email_case_insensitive(self):
        make_student(email="ayse@example.com")
        response = self.client.post(self.url, VALID_REGISTRATION, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["fields"])

    def test_register_rejects_invalid_grade_and_school_type(self):
        payload = {**VALID_REGISTRATION, "grade_level": 8, "school_type": "meslek"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("grade_level", response.data["fields"])
        self.assertIn("school_type", response.data["fields"])

    def test_register_rejects_weak_password(self):
        response = self.post(password="12345678")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="ayse").exists())

    def test_password_needs_8_chars_and_an_uppercase_letter(self):
        short = self.post(password="Kisa!1")
        self.assertIn("password", short.data["fields"])
        no_upper = self.post(password="kucukharf!2026")
        self.assertEqual(no_upper.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("büyük harf", str(no_upper.data["fields"]["password"]))

    def test_first_name_needs_3_letters_and_last_name_is_required(self):
        self.assertIn("first_name", self.post(first_name="Al").data["fields"])
        self.assertIn("first_name", self.post(first_name="Ali3").data["fields"])
        payload = {k: v for k, v in VALID_REGISTRATION.items() if k != "last_name"}
        self.assertIn("last_name", self.client.post(self.url, payload, format="json").data["fields"])
        self.assertIn("last_name", self.post(last_name="K").data["fields"])

    def test_names_are_normalized(self):
        response = self.post(first_name="  Ayşe   Nur ", last_name="Kaya-Demir")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["first_name"], "Ayşe Nur")

    def test_username_rules(self):
        self.assertIn("username", self.post(username="a").data["fields"])
        self.assertIn("username", self.post(username="ay se").data["fields"])
        self.assertIn("username", self.post(username="ayse@example.com").data["fields"])
        response = self.post(username="a1_*!")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_rejects_duplicate_username_case_insensitive(self):
        make_student(username="Ayse", email="baska@example.com")
        response = self.post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("alınmış", str(response.data["fields"]["username"]))

    def test_register_rejects_undeliverable_email(self):
        self.assertIn("email", self.post(email="ayse@").data["fields"])
        self.assertIn("email", self.post(email="ayse@mailinator.com").data["fields"])
        with mock.patch("apps.accounts.validators._domain_accepts_mail", return_value=False):
            response = self.post(email="ayse@olmayan-alan-adi.xyz")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("olmayan-alan-adi.xyz", str(response.data["fields"]["email"]))


class UniquenessConstraintTests(APITestCase):
    def test_database_rejects_case_insensitive_duplicates(self):
        make_student(username="ali", email="ali@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username="ALI", email="yeni@example.com", password="x")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(username="yeni", email="ALI@example.com", password="x")


class ValidatorUnitTests(SimpleTestCase):
    def test_username_validator_allows_symbols_and_digits(self):
        UsernameValidator()("x9")
        UsernameValidator()("mat.kurdu#7")

    def test_null_mx_and_missing_domain_are_rejected(self):
        from django.core.exceptions import ValidationError

        with mock.patch("apps.accounts.validators._domain_accepts_mail", return_value=False):
            with self.assertRaises(ValidationError):
                validate_real_email("biri@yok.example")
        with mock.patch("apps.accounts.validators._domain_accepts_mail", return_value=True):
            self.assertEqual(validate_real_email(" Biri@Gmail.com "), "biri@gmail.com")


class LoginTests(APITestCase):
    url = reverse("auth-login")

    def setUp(self):
        make_student()

    def test_login_with_username(self):
        response = self.client.post(self.url, {"username": "ali", "password": "GucluSifre!2026"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["profile"]["grade_level"], 10)

    def test_login_with_email(self):
        response = self.client.post(
            self.url, {"username": "ALI@example.com", "password": "GucluSifre!2026"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_wrong_password(self):
        response = self.client.post(self.url, {"username": "ali", "password": "yanlis"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        login = self.client.post(self.url, {"username": "ali", "password": "GucluSifre!2026"}, format="json")
        response = self.client.post(reverse("auth-token-refresh"), {"refresh": login.data["refresh"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class MeTests(APITestCase):
    url = reverse("auth-me")

    def setUp(self):
        self.user = make_student()
        self.other = make_student(username="veli", email="veli@example.com", grade=12)

    def test_requires_authentication(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_returns_own_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "ali")
        self.assertEqual(response.data["profile"]["school_type_display"], "Fen Lisesi")

    def test_patch_updates_grade_and_name(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            self.url, {"first_name": "Alican", "profile": {"grade_level": 11}}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alican")
        self.assertEqual(self.user.profile.grade_level, 11)
        self.assertEqual(self.user.profile.school_type, "fen")

    def test_patch_cannot_change_initial_level_or_username(self):
        self.client.force_authenticate(self.user)
        self.client.patch(
            self.url,
            {"username": "hacker", "profile": {"initial_level_status": "advanced"}},
            format="json",
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "ali")
        self.assertEqual(self.user.profile.initial_level_status, "not_assessed")

    def test_patch_rejects_invalid_grade(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, {"profile": {"grade_level": 13}}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_rejects_short_or_blank_names(self):
        self.client.force_authenticate(self.user)
        self.assertIn("first_name", self.client.patch(self.url, {"first_name": "Al"}, format="json").data["fields"])
        self.assertIn("last_name", self.client.patch(self.url, {"last_name": ""}, format="json").data["fields"])

    def test_patch_rejects_email_of_another_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(self.url, {"email": "veli@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileOptionsTests(APITestCase):
    def test_options_are_public(self):
        response = self.client.get(reverse("auth-profile-options"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([g["value"] for g in response.data["grade_levels"]], [9, 10, 11, 12])


class BirthDateValidationTests(APITestCase):
    url = reverse("auth-register")

    def register(self, birth_date):
        return self.client.post(self.url, {**VALID_REGISTRATION, "birth_date": birth_date}, format="json")

    def test_birth_date_is_required(self):
        payload = {k: v for k, v in VALID_REGISTRATION.items() if k != "birth_date"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("birth_date", response.data["fields"])

    def test_future_birth_date_rejected(self):
        response = self.register(date(date.today().year + 1, 1, 1).isoformat())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gelecekte", str(response.data["fields"]["birth_date"]))

    def test_no_age_limit(self):
        response = self.register(years_ago(100).isoformat())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["profile"]["age"], 100)

    def test_obviously_mistyped_year_rejected(self):
        self.assertEqual(self.register("0201-05-05").status_code, status.HTTP_400_BAD_REQUEST)

    def test_age_and_birth_date_returned(self):
        response = self.register(years_ago(15).isoformat())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["profile"]["age"], 15)

    def test_profile_birth_date_update_is_validated(self):
        user = make_student()
        self.client.force_authenticate(user)
        bad = self.client.patch(reverse("auth-me"), {"profile": {"birth_date": "2099-01-01"}}, format="json")
        self.assertEqual(bad.status_code, status.HTTP_400_BAD_REQUEST)
        good = self.client.patch(reverse("auth-me"), {"profile": {"birth_date": years_ago(17).isoformat()}}, format="json")
        self.assertEqual(good.status_code, status.HTTP_200_OK)
        self.assertEqual(good.data["profile"]["age"], 17)


class BirthdayTests(APITestCase):
    def profile(self, birth_date):
        return StudentProfile(birth_date=birth_date)

    def test_birthday_matches_month_and_day(self):
        p = self.profile(date(2010, 11, 1))
        self.assertTrue(p.is_birthday_on(date(2026, 11, 1)))
        self.assertFalse(p.is_birthday_on(date(2026, 10, 31)))

    def test_leap_day_birthday_celebrated_on_feb_28_in_common_years(self):
        p = self.profile(date(2008, 2, 29))
        self.assertTrue(p.is_birthday_on(date(2027, 2, 28)))
        self.assertFalse(p.is_birthday_on(date(2028, 2, 28)))
        self.assertTrue(p.is_birthday_on(date(2028, 2, 29)))

    def test_age_before_and_after_birthday(self):
        p = self.profile(date(2010, 11, 1))
        self.assertEqual(p.age_on(date(2026, 10, 31)), 15)
        self.assertEqual(p.age_on(date(2026, 11, 1)), 16)

    def test_me_reports_birthday_using_server_date(self):
        user = User.objects.create_user(username="dogum", email="d@example.com", password="x")
        StudentProfile.objects.create(user=user, birth_date=date(2010, 11, 1), school_type="anadolu", grade_level=10)
        self.client.force_authenticate(user)
        with mock.patch("django.utils.timezone.localdate", return_value=date(2026, 11, 1)):
            response = self.client.get(reverse("auth-me"))
        self.assertTrue(response.data["profile"]["is_birthday_today"])
        self.assertEqual(response.data["profile"]["age"], 16)
        with mock.patch("django.utils.timezone.localdate", return_value=date(2026, 11, 2)):
            self.assertFalse(self.client.get(reverse("auth-me")).data["profile"]["is_birthday_today"])
