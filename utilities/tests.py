# test_middleware.py
import json
from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.urls import reverse

from utilities.middleware import IsUserRobot


class IsUserRobotMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = IsUserRobot(get_response=self.get_response)

    def get_response(self, request):
        return JsonResponse({'message': 'OK'}, status=200)

    def test_bot_user_agent(self):
        request = self.factory.get(
            reverse('sample-view'),
            HTTP_USER_AGENT='Googlebot/2.1 (+http://www.google.com/bot.html)'
        )
        response = self.middleware(request)

        self.assertEqual(response.status_code, 423)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json['status']['code'], 'LOCKED'
        )
        self.assertEqual(
            response_json['message']['field'], 'Bot Detected'
        )

    def test_non_bot_user_agent(self):
        request = self.factory.get(
            reverse("sample-view"),
            HTTP_USER_AGENT=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/58.0.3029.110 Safari/537.3"
            )
        )

        response = self.middleware(request)

        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.content)
        self.assertEqual(response_json['message'], 'OK')

    def test_invalid_user_agent(self):
        request = self.factory.get(
            reverse("sample-view"), HTTP_USER_AGENT=""
        )

        response = self.middleware(request)

        self.assertEqual(response.status_code, 423)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json["status"]["code"], "LOCKED"
        )
        self.assertEqual(
            response_json["message"]["field"], "Bot Detected"
        )

    def test_exception_handling(self):
        try:
            response = self.middleware.raise_error(
                code="INTERNAL_SERVER_ERROR", status_code=500,
                field_error="Unable To Read Device Properties",
                for_developer="Test Exception"
            )
        except Exception:
            response = JsonResponse(
                {
                    "message": "Exception handled"
                }, status=500
            )

        self.assertEqual(response.status_code, 500)
        response_json = json.loads(response.content)
        self.assertEqual(
            response_json["status"]["code"],
            "INTERNAL_SERVER_ERROR"
        )
        self.assertEqual(
            response_json["message"]["field"],
            "Unable To Read Device Properties"
        )
