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



@pytest.mark.django_db
def test_add_pizza_to_cart_invalid_quantity():
    """Sprawdza błąd, gdy ilość produktu nie jest liczbą."""

    # Tworzy użytkownika testowego.
    user = User.objects.create_user(
        username="testuser2",
        password="test123"
    )

    # Tworzy klienta API i uwierzytelnia użytkownika.
    client = APIClient()
    client.force_authenticate(user=user)

    # Tworzy dane potrzebne do dodania pizzy.
    pizza = Pizza.objects.create(
        name="Pepperoni",
        content="Tomato sauce, cheese, pepperoni"
    )

    size = Size.objects.create(
        name="Medium",
        diameter=32
    )

    typecake = TypeCake.objects.create(
        name="Thick"
    )

    # Podaje błędną ilość.
    data = {
        "pizza": pizza.id,
        "size": size.id,
        "typecake": typecake.id,
        "quantity": "abc"
    }

    response = client.post(
        "/api/cart/add/",
        data,
        format="json"
    )

    # Sprawdza, czy API zwróciło błąd walidacji.
    assert response.status_code == 400
    assert response.data["quantity"] == "The quantity must be a number."



@pytest.mark.django_db
def test_add_pizza_to_cart_zero_quantity():
    """Sprawdza błąd, gdy ilość produktu wynosi zero."""

    # Tworzy użytkownika testowego.
    user = User.objects.create_user(
        username="testuser3",
        password="test123"
    )

    # Tworzy klienta API i uwierzytelnia użytkownika.
    client = APIClient()
    client.force_authenticate(user=user)

    # Tworzy pizzę, rozmiar i rodzaj ciasta.
    pizza = Pizza.objects.create(
        name="Hawaii",
        content="Tomato sauce, cheese, ham, pineapple"
    )

    size = Size.objects.create(
        name="Small",
        diameter=25
    )

    typecake = TypeCake.objects.create(
        name="Thin"
    )

    # Podaje błędną ilość równą zero.
    data = {
        "pizza": pizza.id,
        "size": size.id,
        "typecake": typecake.id,
        "quantity": 0
    }

    response = client.post(
        "/api/cart/add/",
        data,
        format="json"
    )

    # Sprawdza, czy API zwróciło właściwy błąd walidacji.
    assert response.status_code == 400
    assert response.data["quantity"] == "The quantity must be greater than 0."