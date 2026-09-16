import pytest
from decimal import Decimal
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from app.models.pizza import Pizza
from app.models.size import Size
from app.models.typecake import TypeCake
from app.models.shopping import Shopping
from app.models.price import Price
from app.models.order import Order


@pytest.mark.django_db
def test_create_order():
    """Sprawdza utworzenie zamówienia, obliczenie jego wartości i opróżnienie koszyka."""
    user = User.objects.create_user(username="test", password="test123")
    pizza = Pizza.objects.create(name="Margherita", content="Cheese")
    size = Size.objects.create(name="Large", diameter=40)
    cake = TypeCake.objects.create(name="Thin")

    Price.objects.create(
        pizza=pizza, size=size, typecake=cake, price=Decimal("25.00")
    )

    Shopping.objects.create(
        user=user, pizza=pizza, size=size, typecake=cake, quantity=2
    )

    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/order/create/",
        {"address": "Street", "phone": "123456789"},
        format="json"
    )

    assert response.status_code == 201
    assert Order.objects.get(user=user).value == Decimal("50.00")
    assert not Shopping.objects.filter(user=user).exists()