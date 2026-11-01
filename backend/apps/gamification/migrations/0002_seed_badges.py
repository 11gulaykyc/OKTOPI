"""Yedi rozetin tanımı. Kazanım kuralları sunucuda: apps/gamification/engine.py"""

from django.db import migrations

BADGES = (
    # (code, name, description, icon [Lucide], points_reward)
    ("ilk-adim", "İlk Adım", "İlk sorunu çözdün.", "footprints", 10),
    ("merakli-zihin", "Meraklı Zihin", "3 farklı konuya başladın.", "lightbulb", 20),
    ("istikrarli-ogrenci", "İstikrarlı Öğrenci", "Art arda 3 gün, her gün en az 5 dakika çalıştın.", "flame", 30),
    ("hata-avcisi", "Hata Avcısı", "Daha önce yanlış yaptığın bir soruyu doğru çözdün.", "crosshair", 20),
    ("hiz-ustasi", "Hız Ustası", "En az 5 soruluk süreli testi, sürenin yarısından kısa sürede %80 başarıyla bitirdin.", "zap", 30),
    ("matematik-kasifi", "Matematik Kaşifi", "3 farklı konuda doğru cevap verdin.", "compass", 25),
    ("hedef-tamamlandi", "Hedef Tamamlandı", "Kendi koyduğun bir günlük hedefe ulaştın.", "target", 20),
)


def seed(apps, schema_editor):
    Badge = apps.get_model("gamification", "Badge")
    for order, (code, name, description, icon, points) in enumerate(BADGES, start=1):
        Badge.objects.update_or_create(
            code=code,
            defaults={"name": name, "description": description, "icon": icon, "points_reward": points, "order": order},
        )


def unseed(apps, schema_editor):
    Badge = apps.get_model("gamification", "Badge")
    Badge.objects.filter(code__in=[b[0] for b in BADGES], awards__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("gamification", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
