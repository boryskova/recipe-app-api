"""
Tests for the healthcheck API.
"""
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

class HealthCheckTests(TestCase):
    """Test the health check."""

    def test_health_check(self):
        """Test health check API."""
        client = APIClient()
        url = reverse('health-check')
        res = client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
