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
from app.models.posorder import OrderItem


@pytest.mark.django_db
def test_create_order():
    """Sprawdza utworzenie zamówienia, obliczenie jego wartości i opróżnienie koszyka."""

    # Tworzy użytkownika testowego.
    user = User.objects.create_user(
        username="user", 
        password="user123"
        )
    
    # Tworzy klienta API i uwierzytelnia go na potrzeby testu.
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Tworzy pizzę, rozmiar i rodzaj ciasta.
    pizza = Pizza.objects.create(
        name="Margherita", 
        content="tomato sauce, cheese, mushrooms"
        )
    size = Size.objects.create(
        name="Large", 
        diameter=40
        )
    cake = TypeCake.objects.create(
        name="Thin"
        )

    # Na podstawie powyższych danych tworzy cenę i pozycję w koszyku.
    Price.objects.create(
        pizza=pizza, 
        size=size, 
        typecake=cake, 
        price=Decimal("25.00")
    )


    Shopping.objects.create(
        user=user, 
        pizza=pizza, 
        size=size, 
        typecake=cake, 
        quantity=2
    )


    # Wysyłamy dane do api wraz z adresem i numerem telefonu.
    response = client.post(
        "/api/order/create/",{
        "address": "Street", 
        "phone": "123456789"
        },
        format="json"
    )
   
   
    # Sprawdza czy endpoint zadziałał poprawnie 201 = Created.
    assert response.status_code == 201


    # Sprawdza czy zamówienie powstało i ma prawidłową wartość.
    order = Order.objects.get(user=user)
    assert order.value == Decimal("50.00")


    # Sprawdza czy powstała prawidłowa pozycja zamówienia.
    order_item = OrderItem.objects.get(order=order)

    assert order_item.pizza == pizza
    assert order_item.size == size
    assert order_item.typecake == cake
    assert order_item.quantity == 2
    assert order_item.price == Decimal("25.00")


    # Sprawdza czy po zamówieniu koszyk został opróżniony.
    assert not Shopping.objects.filter(user=user).exists()