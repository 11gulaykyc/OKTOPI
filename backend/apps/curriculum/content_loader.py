"""`content/` klasöründeki JSON dosyalarını okur, Pydantic ile doğrular ve bellekte tutar.

Şema doğrulamasına ek olarak dosyalar arası tutarlılık (çapraz referans) denetlenir:
önerilen alt konuların, kazanımların ve pekiştirme sorularının gerçekten var olması gibi.
"""

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from pydantic import ValidationError

from content.schemas import GradeCurriculumSchema, OyssSchema, QuestionFileSchema, TopicSchema

GRADES = (9, 10, 11, 12)


class ContentValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        lines = "\n".join(f"  - {path}: {message}" for path, message in errors)
        super().__init__(f"İçerik doğrulaması {len(errors)} hata ile başarısız oldu:\n{lines}")


@dataclass
class ContentRepository:
    curricula: dict = field(default_factory=dict)  # grade -> GradeCurriculumSchema
    topics: dict = field(default_factory=dict)  # topic_id -> TopicSchema (anlatımı olanlar)
    questions: dict = field(default_factory=dict)  # question_id -> QuestionSchema
    oyss: OyssSchema | None = None
    # Hızlı arama tabloları
    topic_refs: dict = field(default_factory=dict)  # topic_id -> (grade, ThemeSchema, TopicRef)
    subtopic_parent: dict = field(default_factory=dict)  # subtopic_id -> topic_id

    def topic_ref(self, topic_id):
        return self.topic_refs.get(topic_id)

    def questions_for(self, grade=None, topic_id=None, subtopic_id=None, difficulty=None):
        result = []
        for q in self.questions.values():
            if grade is not None and q.grade != grade:
                continue
            if topic_id is not None and q.topic_id != topic_id:
                continue
            if subtopic_id is not None and q.subtopic_id != subtopic_id:
                continue
            if difficulty is not None and q.difficulty != difficulty:
                continue
            result.append(q)
        return sorted(result, key=lambda q: q.id)

    def question_counts_by_topic(self):
        counts = {}
        for q in self.questions.values():
            counts[q.topic_id] = counts.get(q.topic_id, 0) + 1
        return counts


def _read_json(path, errors):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append((path, f"Geçersiz JSON (satır {exc.lineno}, sütun {exc.colno}): {exc.msg}"))
    except OSError as exc:
        errors.append((path, f"Dosya okunamadı: {exc}"))
    return None


def _validate(schema, data, path, errors):
    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        for err in exc.errors():
            location = ".".join(str(part) for part in err["loc"]) or "(kök)"
            errors.append((path, f"{location}: {err['msg']}"))
    return None


def _rel(path, root):
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def load_content(content_dir=None):
    """Tüm içeriği yükler. Hata varsa tüm hataları toplayıp ContentValidationError fırlatır."""
    root = Path(content_dir or settings.CONTENT_DIR)
    errors = []
    repo = ContentRepository()

    # 1) Müfredat ağaçları
    for grade in GRADES:
        path = root / "curriculum" / f"grade-{grade}" / "index.json"
        if not path.exists():
            errors.append((_rel(path, root), "Müfredat dosyası bulunamadı."))
            continue
        data = _read_json(path, errors)
        curriculum = data and _validate(GradeCurriculumSchema, data, _rel(path, root), errors)
        if not curriculum:
            continue
        if curriculum.grade != grade:
            errors.append((_rel(path, root), f"grade alanı ({curriculum.grade}) klasörle ({grade}) uyuşmuyor."))
            continue
        repo.curricula[grade] = curriculum
        for theme in curriculum.themes:
            for topic in theme.topics:
                repo.topic_refs[topic.id] = (grade, theme, topic)
                for sub in topic.subtopics:
                    repo.subtopic_parent[sub.id] = topic.id

    # 2) Konu anlatımları
    for topic_id, (grade, theme, ref) in repo.topic_refs.items():
        if not ref.content_file:
            continue
        path = root / "curriculum" / f"grade-{grade}" / ref.content_file
        rel = _rel(path, root)
        if not path.exists():
            errors.append((rel, f"{topic_id} için belirtilen anlatım dosyası bulunamadı."))
            continue
        data = _read_json(path, errors)
        topic = data and _validate(TopicSchema, data, rel, errors)
        if not topic:
            continue
        if topic.id != topic_id or topic.grade != grade or topic.theme_id != theme.id:
            errors.append((rel, f"id/grade/theme_id müfredat ağacıyla uyuşmuyor (beklenen {topic_id}, {grade}, {theme.id})."))
            continue
        subtopic_ids = {s.id for s in ref.subtopics}
        for section in topic.sections:
            if section.id not in subtopic_ids:
                errors.append((rel, f"Bölüm '{section.id}', {topic_id} konusunun alt konuları arasında yok."))
        repo.topics[topic_id] = topic

    # 3) Sorular
    questions_root = root / "questions"
    for path in sorted(questions_root.glob("grade-*/*.json")):
        rel = _rel(path, root)
        data = _read_json(path, errors)
        qfile = data and _validate(QuestionFileSchema, data, rel, errors)
        if not qfile:
            continue
        if path.stem != qfile.topic_id or path.parent.name != f"grade-{qfile.grade}":
            errors.append((rel, "Dosya adı/klasörü, topic_id ve grade ile uyuşmalıdır."))
        ref_entry = repo.topic_refs.get(qfile.topic_id)
        if not ref_entry:
            errors.append((rel, f"topic_id '{qfile.topic_id}' müfredat ağacında yok."))
            continue
        _, _, ref = ref_entry
        outcomes = {o.code for o in ref.learning_outcomes}
        for q in qfile.questions:
            if q.id in repo.questions:
                errors.append((rel, f"{q.id}: soru kimliği başka bir dosyada da kullanılmış."))
                continue
            if repo.subtopic_parent.get(q.subtopic_id) != q.topic_id:
                errors.append((rel, f"{q.id}: subtopic_id '{q.subtopic_id}' bu konunun alt konusu değil."))
            if q.learning_outcome not in outcomes:
                errors.append((rel, f"{q.id}: kazanım '{q.learning_outcome}' konuda tanımlı değil."))
            for option in q.options:
                target = option.recommended_subtopic_id
                if target and target not in repo.subtopic_parent and target not in repo.topic_refs:
                    errors.append((rel, f"{q.id} {option.key}: recommended_subtopic_id '{target}' müfredatta yok."))
            repo.questions[q.id] = q

    # 4) Pekiştirme sorusu referansları
    for topic in repo.topics.values():
        for qid in topic.reinforcement_question_ids:
            if qid not in repo.questions:
                errors.append((f"curriculum/grade-{topic.grade}/topics/{topic.id}.json", f"Pekiştirme sorusu '{qid}' bulunamadı."))

    # 5) OYSS
    oyss_path = root / "curriculum" / "oyss" / "oyss.json"
    if oyss_path.exists():
        rel = _rel(oyss_path, root)
        data = _read_json(oyss_path, errors)
        oyss = data and _validate(OyssSchema, data, rel, errors)
        if oyss:
            for exam in oyss.calendar:
                for tid in exam.topic_ids:
                    entry = repo.topic_refs.get(tid)
                    if not entry or entry[0] != exam.grade:
                        errors.append((rel, f"Takvimdeki konu '{tid}' {exam.grade}. sınıf müfredatında yok."))
            repo.oyss = oyss
    else:
        errors.append((_rel(oyss_path, root), "OYSS dosyası bulunamadı."))

    if errors:
        raise ContentValidationError([(str(p), m) for p, m in errors])
    return repo


_lock = threading.Lock()
_repository = None


def get_repository():
    """Önbellekteki içerik deposunu döner; ilk çağrıda yükler."""
    global _repository
    if _repository is None:
        with _lock:
            if _repository is None:
                _repository = load_content()
    return _repository


def reload_repository():
    global _repository
    with _lock:
        _repository = load_content()
    return _repository
