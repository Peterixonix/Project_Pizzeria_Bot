from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status




class LoginTest(APITestCase):

    def setUp(self):
        User.objects.create_user(
            username="test2",
            password="testuser",
            email="testuser@example.com"
        )

    def test_login_user(self):
        data = {
            "username": "test2",
            "password": "testuser"

        }

        response = self.client.post(
            "/api/login/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)