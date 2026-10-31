import json
import shutil
import tempfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APISimpleTestCase

from .content_loader import ContentValidationError, load_content


class ContentCopyMixin:
    """Gerçek içeriğin geçici bir kopyası üzerinde bozma senaryoları dener."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(settings.CONTENT_DIR, self.tmp / "content")
        self.root = self.tmp / "content"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def edit_json(self, relative, mutate):
        path = self.root / relative
        data = json.loads(path.read_text(encoding="utf-8"))
        mutate(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def assert_error_contains(self, text):
        with self.assertRaises(ContentValidationError) as ctx:
            load_content(self.root)
        messages = " | ".join(m for _, m in ctx.exception.errors)
        self.assertIn(text, messages)


class RealContentTests(SimpleTestCase):
    def test_repository_content_is_valid(self):
        repo = load_content()
        self.assertEqual(sorted(repo.curricula), [9, 10, 11, 12])
        self.assertGreaterEqual(len(repo.questions), 15)
        self.assertIn("top-9-exp", repo.topics)

    def test_every_wrong_option_has_misconception(self):
        repo = load_content()
        for q in repo.questions.values():
            for option in q.options:
                if not option.is_correct:
                    self.assertTrue(option.misconception_tag, f"{q.id} {option.key}")


class ValidateContentBrokenTests(ContentCopyMixin, SimpleTestCase):
    Q = "questions/grade-9/top-9-exp.json"

    def test_invalid_json_syntax(self):
        (self.root / self.Q).write_text("{ bozuk json", encoding="utf-8")
        self.assert_error_contains("Geçersiz JSON")

    def test_two_correct_options(self):
        def mutate(d):
            opt = d["questions"][0]["options"][0]
            opt.update(is_correct=True, misconception_tag=None, misconception_detail=None, recommended_subtopic_id=None)
        self.edit_json(self.Q, mutate)
        self.assert_error_contains("tam olarak bir doğru şık")

    def test_wrong_option_without_misconception_tag(self):
        self.edit_json(self.Q, lambda d: d["questions"][0]["options"][0].update(misconception_tag=None))
        self.assert_error_contains("zorunludur")

    def test_correct_option_with_misconception_tag(self):
        self.edit_json(self.Q, lambda d: d["questions"][0]["options"][2].update(misconception_tag="MISC_X"))
        self.assert_error_contains("null olmalıdır")

    def test_unknown_recommended_subtopic(self):
        self.edit_json(
            self.Q, lambda d: d["questions"][0]["options"][0].update(recommended_subtopic_id="top-9-yok")
        )
        self.assert_error_contains("müfredatta yok")

    def test_learning_outcome_not_in_topic(self):
        self.edit_json(self.Q, lambda d: d["questions"][0].update(learning_outcome="MAT.9.4.1"))
        self.assert_error_contains("konuda tanımlı değil")

    def test_unknown_field_is_rejected(self):
        self.edit_json(self.Q, lambda d: d["questions"][0].update(answer="C"))
        self.assert_error_contains("Extra inputs are not permitted")

    def test_missing_reinforcement_question(self):
        self.edit_json(
            "curriculum/grade-9/topics/top-9-exp.json",
            lambda d: d["reinforcement_question_ids"].append("q-9-exp-999"),
        )
        self.assert_error_contains("Pekiştirme sorusu 'q-9-exp-999' bulunamadı")

    def test_command_fails_loudly(self):
        (self.root / self.Q).write_text("[]", encoding="utf-8")
        err = StringIO()
        with self.assertRaises(CommandError):
            call_command("validate_content", content_dir=str(self.root), stderr=err, stdout=StringIO())
        self.assertIn("top-9-exp.json", err.getvalue())

    def test_command_success_output(self):
        out = StringIO()
        call_command("validate_content", content_dir=str(self.root), stdout=out)
        self.assertIn("başarılı", out.getvalue())


class CurriculumApiTests(APISimpleTestCase):
    def test_grade_list(self):
        response = self.client.get(reverse("curriculum-grades"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([g["grade"] for g in response.data], [9, 10, 11, 12])

    def test_grade_detail_tree(self):
        response = self.client.get(reverse("curriculum-grade-detail", args=[9]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        topics = {t["id"]: t for th in response.data["themes"] for t in th["topics"]}
        self.assertTrue(topics["top-9-exp"]["has_content"])
        self.assertEqual(topics["top-9-exp"]["question_count"], 7)

    def test_invalid_grade_404(self):
        self.assertEqual(self.client.get(reverse("curriculum-grade-detail", args=[8])).status_code, 404)
        self.assertEqual(self.client.get(reverse("curriculum-grade-detail", args=["abc"])).status_code, 404)

    def test_topic_detail_with_content(self):
        response = self.client.get(reverse("curriculum-topic-detail", args=["top-9-exp"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["theme"]["id"], "th-9-1")
        self.assertGreater(len(response.data["content"]["sections"]), 0)

    def test_topic_without_content(self):
        response = self.client.get(reverse("curriculum-topic-detail", args=["top-12-integ"]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_content"])
        self.assertIsNone(response.data["content"])

    def test_unknown_topic_404(self):
        self.assertEqual(self.client.get(reverse("curriculum-topic-detail", args=["top-9-yok"])).status_code, 404)

    def test_oyss(self):
        response = self.client.get(reverse("curriculum-oyss"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["calendar_is_official"])
        self.assertIn("title", response.data["calendar"][0]["topics"][0])
