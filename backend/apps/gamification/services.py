from django.db import transaction
from django.db.models import Sum

from .models import PointLedger


def award_points(user, amount, reason, idempotency_key, description=""):
    """Puan yazar. Aynı idempotency_key ile tekrar çağrılırsa yeni kayıt oluşturmaz.

    Döner: (kayıt, oluşturuldu_mu)
    """
    with transaction.atomic():
        return PointLedger.objects.get_or_create(
            user=user,
            idempotency_key=idempotency_key,
            defaults={"amount": amount, "reason": reason, "description": description},
        )


def total_points(user):
    return PointLedger.objects.filter(user=user).aggregate(total=Sum("amount"))["total"] or 0


# Konu tamamlama ödülü (konu başına bir kez; idempotency_key ile korunur).
TOPIC_COMPLETION_POINTS = 20


def level_threshold(level):
    """`level` seviyesine ulaşmak için gereken toplam puan: 1→0, 2→100, 3→300, 4→600 ..."""
    return 50 * level * (level - 1)


def level_info(points):
    """Toplam puandan seviyeyi ve bir sonraki seviyeye ilerlemeyi hesaplar."""
    level = 1
    while points >= level_threshold(level + 1):
        level += 1
    floor, next_at = level_threshold(level), level_threshold(level + 1)
    return {
        "level": level,
        "points": points,
        "level_floor": floor,
        "next_level_at": next_at,
        "progress": (points - floor) / (next_at - floor),
    }
