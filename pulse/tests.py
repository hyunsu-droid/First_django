from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .views import FALLBACK


class DashboardTests(TestCase):
    def test_dashboard_page_renders_information_board(self):
        response = self.client.get(reverse("pulse:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "시장 정보 게시판")
        self.assertContains(response, "세계정세 브리핑")

    @patch("pulse.views._market_snapshot", return_value=FALLBACK)
    def test_market_api_returns_server_side_snapshot(self, _snapshot):
        response = self.client.get(reverse("pulse:market_api"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "fallback")
        self.assertEqual(len(response.json()["coins"]), 3)
