from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.curriculum.content_loader import GRADES, get_repository

from .serializers import public_question

DIFFICULTIES = ("easy", "medium", "hard")


class QuestionListView(APIView):
    """Filtrelenebilir soru listesi: ?grade=9&topic_id=top-9-exp&subtopic_id=...&difficulty=medium"""

    def get(self, request):
        params = request.query_params
        filters = {}
        if "grade" in params:
            try:
                filters["grade"] = int(params["grade"])
            except ValueError:
                filters["grade"] = None
            if filters["grade"] not in GRADES:
                raise ValidationError({"grade": "Geçerli sınıf düzeyleri: 9, 10, 11, 12."})
        if "difficulty" in params:
            if params["difficulty"] not in DIFFICULTIES:
                raise ValidationError({"difficulty": "Geçerli değerler: easy, medium, hard."})
            filters["difficulty"] = params["difficulty"]
        for name in ("topic_id", "subtopic_id"):
            if params.get(name):
                filters[name] = params[name]

        questions = get_repository().questions_for(**filters)
        return Response({"count": len(questions), "results": [public_question(q) for q in questions]})


class QuestionDetailView(APIView):
    def get(self, request, question_id):
        question = get_repository().questions.get(question_id)
        if not question:
            raise NotFound("Soru bulunamadı.")
        return Response(public_question(question))
