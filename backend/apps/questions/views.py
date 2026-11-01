from rest_framework import permissions, serializers
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import MisconceptionLog
from apps.analytics.services import record_attempt
from apps.curriculum.content_loader import GRADES, get_repository

from .serializers import evaluation_result, public_question

DIFFICULTIES = ("easy", "medium", "hard")


class QuestionListView(APIView):
    """Filtrelenebilir soru listesi: ?grade=9&topic_id=top-9-exp&subtopic_id=...&difficulty=medium
    Cevap anahtarı içermediği için giriş yapmamış ziyaretçilere de açıktır."""

    permission_classes = (permissions.AllowAny,)

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
    permission_classes = (permissions.AllowAny,)

    def get(self, request, question_id):
        question = get_repository().questions.get(question_id)
        if not question:
            raise NotFound("Soru bulunamadı.")
        return Response(public_question(question))


class CheckAnswerSerializer(serializers.Serializer):
    selected_option = serializers.ChoiceField(choices=("A", "B", "C", "D", "E"))


class CheckAnswerView(APIView):
    """Konu sonu pekiştirme sorusunu sunucuda değerlendirir.

    Cevap anahtarı ve çözüm yalnızca öğrenci cevabını gönderdikten sonra döner. Yanlış şıkkın
    kavram yanılgısı MisconceptionLog'a yazılır ve öğrenci önerilen alt konuya yönlendirilir.
    (Süreli test ve soru çözümü oturumları Faz 3'te `exams` uygulamasındadır.)

    Giriş gerektirir: ziyaretçiler soruları görebilir ama cevap anahtarına (deneme yoluyla bile) erişemez.
    """

    def post(self, request, question_id):
        repo = get_repository()
        question = repo.questions.get(question_id)
        if not question:
            raise NotFound("Soru bulunamadı.")
        serializer = CheckAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["selected_option"]
        option = next((o for o in question.options if o.key == key), None)
        if option is None:
            raise ValidationError({"selected_option": "Bu soruda böyle bir şık yok."})

        _, first_try = record_attempt(request.user, question, option, source=MisconceptionLog.Source.REINFORCEMENT)
        return Response(evaluation_result(question, option, first_try))
