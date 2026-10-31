from rest_framework import permissions
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .content_loader import GRADES, get_repository


def _parse_grade(value):
    try:
        grade = int(value)
    except (TypeError, ValueError):
        grade = None
    if grade not in GRADES:
        raise NotFound("Geçerli sınıf düzeyleri: 9, 10, 11, 12.")
    return grade


class CurriculumView(APIView):
    """Müfredat içeriği gizli değildir; giriş yapmamış ziyaretçiler de konu ağacını görebilir."""

    permission_classes = (permissions.AllowAny,)


class GradeListView(CurriculumView):
    def get(self, request):
        repo = get_repository()
        data = []
        for grade in GRADES:
            curriculum = repo.curricula[grade]
            topics = [t for theme in curriculum.themes for t in theme.topics]
            data.append(
                {
                    "grade": grade,
                    "title": curriculum.title,
                    "theme_count": len(curriculum.themes),
                    "topic_count": len(topics),
                    "topics_with_content": sum(1 for t in topics if t.id in repo.topics),
                }
            )
        return Response(data)


class GradeDetailView(CurriculumView):
    def get(self, request, grade):
        grade = _parse_grade(grade)
        repo = get_repository()
        curriculum = repo.curricula[grade]
        question_counts = repo.question_counts_by_topic()
        themes = []
        for theme in sorted(curriculum.themes, key=lambda t: t.order):
            themes.append(
                {
                    "id": theme.id,
                    "order": theme.order,
                    "title": theme.title,
                    "description": theme.description,
                    "topics": [
                        {
                            "id": topic.id,
                            "title": topic.title,
                            "learning_outcomes": [o.model_dump() for o in topic.learning_outcomes],
                            "subtopics": [s.model_dump() for s in topic.subtopics],
                            "has_content": topic.id in repo.topics,
                            "question_count": question_counts.get(topic.id, 0),
                        }
                        for topic in theme.topics
                    ],
                }
            )
        return Response(
            {
                "grade": grade,
                "version": curriculum.version,
                "title": curriculum.title,
                "program": curriculum.program,
                "themes": themes,
            }
        )


class TopicDetailView(CurriculumView):
    def get(self, request, topic_id):
        repo = get_repository()
        entry = repo.topic_ref(topic_id)
        if not entry:
            raise NotFound("Konu bulunamadı.")
        grade, theme, ref = entry
        topic = repo.topics.get(topic_id)
        return Response(
            {
                "id": ref.id,
                "grade": grade,
                "theme": {"id": theme.id, "title": theme.title},
                "title": ref.title,
                "learning_outcomes": [o.model_dump() for o in ref.learning_outcomes],
                "subtopics": [s.model_dump() for s in ref.subtopics],
                "has_content": topic is not None,
                "question_count": len(repo.questions_for(topic_id=topic_id)),
                # Anlatım yalnızca öğretici içerik (çözümlü örnekler) taşır; soru cevap anahtarı içermez.
                "content": topic.model_dump(mode="json", exclude={"id", "grade", "theme_id", "title"}) if topic else None,
            }
        )


class OyssView(CurriculumView):
    def get(self, request):
        repo = get_repository()
        if not repo.oyss:
            raise NotFound("OYSS içeriği bulunamadı.")
        data = repo.oyss.model_dump(mode="json")
        for exam in data["calendar"]:
            exam["topics"] = [
                {"id": tid, "title": repo.topic_refs[tid][2].title} for tid in exam.pop("topic_ids")
            ]
        return Response(data)
