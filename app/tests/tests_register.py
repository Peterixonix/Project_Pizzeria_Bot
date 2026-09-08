import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient




@pytest.mark.django_db
def test_register_user():
    client = APIClient()

    data = {
        "username": "test1",
        "password": "testuser",
        "email": "testuser@gmail.com"
    }

    response = client.post(
        "/api/register/",
        data,
        format="json"
    )

    assert response.status_code == 201

    user = User.objects.get(username="test1")

    assert user.email == "testuser@gmail.com"
    assert user.check_password("testuser")