from django.core.management.base import BaseCommand, CommandError

from apps.curriculum.content_loader import ContentValidationError, load_content


class Command(BaseCommand):
    help = "content/ altındaki tüm JSON dosyalarını şema ve çapraz referans kurallarına göre doğrular."
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument("--content-dir", help="Varsayılan settings.CONTENT_DIR yerine kullanılacak klasör.")

    def handle(self, *args, **options):
        try:
            repo = load_content(options.get("content_dir"))
        except ContentValidationError as exc:
            for path, message in exc.errors:
                self.stderr.write(self.style.ERROR(f"✗ {path}: {message}"))
            raise CommandError(f"İçerik doğrulaması başarısız: {len(exc.errors)} hata bulundu.")

        topic_count = sum(len(t.topics) for c in repo.curricula.values() for t in c.themes)
        misconceptions = {
            o.misconception_tag for q in repo.questions.values() for o in q.options if o.misconception_tag
        }
        self.stdout.write(self.style.SUCCESS("✓ İçerik doğrulaması başarılı."))
        self.stdout.write(f"  Sınıf müfredatı : {len(repo.curricula)}")
        self.stdout.write(f"  Konu            : {topic_count} ({len(repo.topics)} tanesinin anlatımı var)")
        self.stdout.write(f"  Soru            : {len(repo.questions)}")
        self.stdout.write(f"  Kavram yanılgısı: {len(misconceptions)} farklı etiket")
        self.stdout.write(f"  OYSS            : {'var' if repo.oyss else 'yok'}")
