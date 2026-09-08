from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status



class RegisterTests(APITestCase):

    def test_register_user(self):
        data = {
            "username": "test1",
            "password": "testuser",
            "email": "testuser@gmail.com"
        }

        response = self.client.post(
            "/api/register/",
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertTrue(
            User.objects.filter(username="test1").exists()
        )