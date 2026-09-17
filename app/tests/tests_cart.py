import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from app.models import Pizza, Size, TypeCake, Shopping


@pytest.mark.django_db
def test_add_pizza_to_cart():
    """Sprawdza, czy zalogowany użytkownik może poprawnie dodać pizzę do koszyka."""
    # Tworzy użytkownika testowego.
    user = User.objects.create_user(
        username="testuser",
        password="test123"
    )

    # Tworzy klienta API i uwierzytelnia go na potrzeby testu.
    client = APIClient()
    client.force_authenticate(user=user)

    # Tworzy pizzę, rozmiar i rodzaj ciasta.
    pizza = Pizza.objects.create(
        name="Margherita",
        content="Tomato sauce, cheese, mushrooms"
    )

    size = Size.objects.create(
        name="Large",
        diameter=40
    )

    typecake = TypeCake.objects.create(
        name="Thin"
    )

    # Przygotowuje dane, które zostaną wysłane do endpointu.
    data = {
        "pizza": pizza.id,
        "size": size.id,
        "typecake": typecake.id,
        "quantity": 2
    }

    # Wysyła dane do API w formacie JSON.
    response = client.post(
        "/api/cart/add/",
        data,
        format="json"
    )

    # Sprawdza, czy endpoint zadziałał poprawnie 201 = Created.
    assert response.status_code == 201


    # Sprawdza, czy powstała prawidłowa pozycja w koszyku.
    cart_item = Shopping.objects.get(user=user)

    assert cart_item.pizza == pizza
    assert cart_item.size == size
    assert cart_item.typecake == typecake
    assert cart_item.quantity == 2