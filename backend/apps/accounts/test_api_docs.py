"""OpenAPI / Swagger dokümantasyonu (/api/docs/) testleri."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ApiDocsTests(APITestCase):
    def test_schema_is_public_and_lists_endpoints(self):
        response = self.client.get(reverse("api-schema"), HTTP_ACCEPT="application/vnd.oai.openapi+json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        schema = response.json()
        self.assertTrue(schema["openapi"].startswith("3."))
        for path in ("/api/auth/login/", "/api/exams/submit-answer/", "/api/analytics/error-analysis/", "/api/study-sessions/heartbeat/"):
            self.assertIn(path, schema["paths"])
        # JWT taşıyıcı token şeması tanımlı: Swagger'daki "Authorize" düğmesi bununla çalışır.
        self.assertIn("jwtAuth", schema["components"]["securitySchemes"])

    def test_request_bodies_are_documented(self):
        schema = self.client.get(reverse("api-schema"), HTTP_ACCEPT="application/vnd.oai.openapi+json").json()
        body = schema["paths"]["/api/exams/practice/start/"]["post"]["requestBody"]
        ref = body["content"]["application/json"]["schema"]["$ref"].rsplit("/", 1)[-1]
        self.assertIn("mistakes_only", schema["components"]["schemas"][ref]["properties"])

    def test_swagger_ui_page(self):
        response = self.client.get(reverse("api-docs"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"swagger", response.content.lower())
