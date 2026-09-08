from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status



class CartTests(APITestCase):

    def test_cart_authentication(self):
        response = self.client.get(
            "/api/cart/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )