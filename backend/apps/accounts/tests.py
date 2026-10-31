from datetime import date
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import StudentProfile

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
    "birth_date": years_ago(15).isoformat(),
    "school_type": "anadolu",
    "grade_level": 9,
}


def make_student(username="ali", email="ali@example.com", password="GucluSifre!2026", grade=10):
    user = User.objects.create_user(username=username, email=email, password=password)
    StudentProfile.objects.create(user=user, birth_date=years_ago(16), school_type="fen", grade_level=grade)
    return user


class RegisterTests(APITestCase):
    url = reverse("auth-register")

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
        self.assertIn("email", response.data)

    def test_register_rejects_invalid_grade_and_school_type(self):
        payload = {**VALID_REGISTRATION, "grade_level": 8, "school_type": "meslek"}
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("grade_level", response.data)
        self.assertIn("school_type", response.data)

    def test_register_rejects_weak_password(self):
        response = self.client.post(self.url, {**VALID_REGISTRATION, "password": "12345678"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="ayse").exists())


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
            self.url, {"first_name": "Ali", "profile": {"grade_level": 11}}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ali")
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
        self.assertIn("birth_date", response.data)

    def test_future_birth_date_rejected(self):
        response = self.register(date(date.today().year + 1, 1, 1).isoformat())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("gelecekte", str(response.data["birth_date"]))

    def test_too_young_and_too_old_rejected(self):
        self.assertEqual(self.register(years_ago(8).isoformat()).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.register(years_ago(40).isoformat()).status_code, status.HTTP_400_BAD_REQUEST)

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
