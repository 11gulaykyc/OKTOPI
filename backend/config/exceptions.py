"""API genelinde tek tip, kullanıcı dostu Türkçe hata yanıtı.

Her hata şu biçimde döner:
    {"detail": "Ekranda gösterilebilecek Türkçe mesaj", "code": "makine_okur_kod", "fields": {...}}

- `fields` yalnızca doğrulama hatalarında bulunur: {"alan": ["mesaj", ...]} (iç içe olabilir).
- Teknik ayrıntılar (yığın izi, token iç yapısı, SQL hataları) istemciye gönderilmez; sunucu günlüğüne yazılır.
"""

import logging

from django.conf import settings
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger("oktopi.api")

MESSAGES = {
    status.HTTP_401_UNAUTHORIZED: "Bu işlem için giriş yapmalısın.",
    status.HTTP_403_FORBIDDEN: "Bu işlem için yetkin yok.",
    status.HTTP_404_NOT_FOUND: "Aradığın kayıt bulunamadı.",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Bu işlem desteklenmiyor.",
    status.HTTP_429_TOO_MANY_REQUESTS: "Çok sık istek gönderdin. Biraz bekleyip tekrar dene.",
}
SERVER_ERROR = "Sunucuda beklenmeyen bir sorun oluştu. Lütfen biraz sonra tekrar dene."
SESSION_EXPIRED = "Oturumunun süresi doldu. Lütfen tekrar giriş yap."


def _first_message(data):
    """İç içe hata yapısındaki ilk okunabilir mesajı bulur."""
    if isinstance(data, dict):
        # Alana bağlı olmayan hatalar önce gelir.
        for key in ("non_field_errors", *data.keys()):
            if key in data:
                found = _first_message(data[key])
                if found:
                    return found
        return None
    if isinstance(data, list):
        for item in data:
            found = _first_message(item)
            if found:
                return found
        return None
    return str(data) if data else None


def _code(exc):
    codes = exc.get_codes()
    return codes if isinstance(codes, str) else getattr(exc, "default_code", "error")


def api_exception_handler(exc, context):
    if isinstance(exc, (InvalidToken, TokenError)):
        # SimpleJWT, token ayrıntılarını ("messages") yanıta koyar; bunlar kullanıcıya gösterilmez.
        return Response({"detail": SESSION_EXPIRED, "code": "token_not_valid"}, status=status.HTTP_401_UNAUTHORIZED)

    response = drf_exception_handler(exc, context)

    if response is None:
        # Beklenmeyen hata: geliştirmede Django'nun hata sayfası görünsün, aksi halde ayrıntı gizlenir.
        if settings.DEBUG:
            return None
        view = context.get("view")
        logger.exception("Beklenmeyen API hatası (%s)", view.__class__.__name__ if view else "?", exc_info=exc)
        return Response({"detail": SERVER_ERROR, "code": "server_error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if isinstance(exc, exceptions.ValidationError):
        data = response.data
        body = {"detail": _first_message(data) or "Gönderilen bilgileri kontrol et.", "code": "invalid"}
        if isinstance(data, dict):
            body["fields"] = data
        response.data = body
        return response

    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    if isinstance(exc, exceptions.NotAuthenticated):
        detail = MESSAGES[status.HTTP_401_UNAUTHORIZED]
    elif not detail:
        detail = MESSAGES.get(response.status_code, SERVER_ERROR)
    response.data = {"detail": str(detail), "code": _code(exc)}
    return response
