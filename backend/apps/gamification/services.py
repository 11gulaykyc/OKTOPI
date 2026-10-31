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
