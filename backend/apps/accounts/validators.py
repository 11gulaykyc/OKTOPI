"""Kayıt ve profil alanları için ortak doğrulayıcılar (serializer, model ve şifre ayarları kullanır)."""
import re

import dns.exception
import dns.name
import dns.resolver
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email
from django.utils.deconstruct import deconstructible

FIRST_NAME_MIN_LETTERS = 3
LAST_NAME_MIN_LETTERS = 2
USERNAME_MIN_LENGTH = 2

# Ad/soyad: harfler, aralarında boşluk, kesme işareti veya tire ("Ayşe Nur", "D'Angelo", "Kaya-Demir").
_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ '\-’][^\W\d_]+)*$")

# Bilinen tek kullanımlık (geçici) e-posta servisleri.
DISPOSABLE_EMAIL_DOMAINS = frozenset(
    {
        "mailinator.com", "guerrillamail.com", "guerrillamail.net", "10minutemail.com", "tempmail.com",
        "temp-mail.org", "yopmail.com", "trashmail.com", "sharklasers.com", "getnada.com",
        "dispostable.com", "maildrop.cc", "throwawaymail.com", "fakeinbox.com", "mailnesia.com",
    }
)


def clean_person_name(value, *, min_letters, label):
    value = " ".join(value.split())
    if not _NAME_RE.match(value):
        raise ValidationError(f"{label} yalnızca harflerden oluşmalı.")
    if sum(ch.isalpha() for ch in value) < min_letters:
        raise ValidationError(f"{label} en az {min_letters} harf olmalı.")
    return value


@deconstructible
class UsernameValidator:
    """En az 2 karakter; harf, rakam ve sembol serbest, boşluk yok. E-posta biçiminde olamaz
    (girişte e-posta ile kullanıcı adı karışmasın)."""

    def __call__(self, value):
        if len(value) < USERNAME_MIN_LENGTH:
            raise ValidationError(f"Kullanıcı adı en az {USERNAME_MIN_LENGTH} karakter olmalı.")
        if any(ch.isspace() for ch in value) or not value.isprintable():
            raise ValidationError("Kullanıcı adında boşluk olamaz.")
        if re.fullmatch(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValidationError("Kullanıcı adı e-posta adresi biçiminde olamaz.")

    def __eq__(self, other):
        return isinstance(other, UsernameValidator)


def _domain_accepts_mail(domain):
    """Alan adının MX (yoksa A/AAAA) kaydı var mı? DNS'e ulaşılamıyorsa kaydı engellememek için True."""
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 4
    for record in ("MX", "A", "AAAA"):
        try:
            answer = resolver.resolve(domain, record)
        except (dns.resolver.NXDOMAIN, dns.name.EmptyLabel, dns.name.LabelTooLong):
            return False
        except dns.resolver.NoAnswer:
            continue
        except (dns.resolver.NoNameservers, dns.exception.Timeout):
            return True
        # "Null MX" (RFC 7505): alan adı açıkça e-posta kabul etmiyor.
        if record == "MX" and all(str(r.exchange) == "." for r in answer):
            return False
        return True
    return False


def validate_real_email(value):
    value = value.strip().lower()
    django_validate_email(value)
    domain = value.rsplit("@", 1)[1]
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        raise ValidationError("Geçici e-posta adresleri kabul edilmiyor.")
    if not _domain_accepts_mail(domain):
        raise ValidationError(f"“{domain}” e-posta alamayan bir alan adı. Adresini kontrol et.")
    return value


class UppercasePasswordValidator:
    """AUTH_PASSWORD_VALIDATORS içinde: şifrede en az bir büyük harf."""

    def validate(self, password, user=None):
        if not any(ch.isupper() for ch in password):
            raise ValidationError("Şifre en az bir büyük harf içermeli.", code="password_no_upper")

    def get_help_text(self):
        return "Şifre en az bir büyük harf içermeli."
