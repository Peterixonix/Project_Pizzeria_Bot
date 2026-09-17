from decimal import Decimal

from django.contrib.auth.models import User
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.models.order import Order
from app.models.pizza import Pizza
from app.models.posorder import OrderItem
from app.models.price import Price
from app.models.shopping import Shopping
from app.models.size import Size
from app.models.typecake import TypeCake
from app.serializers import (
    PizzaSerializer,
    RegisterSerializer,
    SizeSerializer,
    TypeCakeSerializer,
)



class RegisterView(generics.CreateAPIView):
    """Obsługuje rejestrację nowych użytkowników."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer



class PizzaViewSet(viewsets.ModelViewSet):
    """Obsługuje operacje API związane z pizzami."""
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer



class SizeViewSet(viewsets.ModelViewSet):
    """Obsługuje operacje API związane z rozmiarami pizzy."""
    queryset = Size.objects.all()
    serializer_class = SizeSerializer



class TypeCakeViewSet(viewsets.ModelViewSet):
    """Obsługuje operacje API związane z rodzajami ciasta."""
    queryset = TypeCake.objects.all()
    serializer_class = TypeCakeSerializer


def validate_quantity(quantity):
    """Sprawdza, czy podana ilość jest prawidłową liczbą większą od zera."""
    
    # Próbuje zamienić podaną ilość na liczbę całkowitą.
    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        return None, "The quantity must be a number."

    # Sprawdza, czy ilość jest większa od zera.
    if quantity < 1:
        return None, "The quantity must be greater than 0."

    return quantity, None


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    """Dodaje wybraną pizzę do koszyka zalogowanego użytkownika."""
    
    # Pobiera i sprawdza ilość produktu.
    quantity, error = validate_quantity(
        request.data.get("quantity", 1)
    )

    if error:
        return Response(
            {"quantity": error},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Pobiera z bazy wybraną pizzę, rozmiar i rodzaj ciasta.
    try:
        pizza = Pizza.objects.get(id=request.data.get("pizza"))
        size = Size.objects.get(id=request.data.get("size"))
        typecake = TypeCake.objects.get(id=request.data.get("typecake"))
    except (Pizza.DoesNotExist, Size.DoesNotExist, TypeCake.DoesNotExist):
        return Response(
            {"error": "Wrong pizza, size or type of cake."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Tworzy nową pozycję w koszyku użytkownika.
    Shopping.objects.create(
        user=request.user,
        pizza=pizza,
        size=size,
        typecake=typecake,
        quantity=quantity
    )

    # Zwraca informację o poprawnym dodaniu produktu do koszyka.
    return Response(
        {"message": "Added to cart."},
        status=status.HTTP_201_CREATED
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(request):
    """Pobiera zawartość koszyka zalogowanego użytkownika."""

    # Pobiera z bazy wszystkie pozycje koszyka zalogowanego użytkownika.
    cart_items = Shopping.objects.filter(user=request.user)

    # Przygotowuje listę danych, która zostanie zwrócona przez API.
    data = []

    for item in cart_items:
        data.append({
            "id": item.id,
            "pizza": str(item.pizza),
            "size": str(item.size),
            "typecake": str(item.typecake),
            "quantity": int(item.quantity)
        })

    # Zwraca zawartość koszyka.
    return Response(data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    """Usuwa wybraną pozycję z koszyka zalogowanego użytkownika."""
    
    # Wyszukuje pozycję należącą do zalogowanego użytkownika.
    try:
        item = Shopping.objects.get(
            id=item_id,
            user=request.user
        )
    except Shopping.DoesNotExist:
        return Response(
            {"error": "Position not found in this cart."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Usuwa znalezioną pozycję z koszyka.
    item.delete()

    return Response(
        {"message": "Position deleted from this cart."},
        status=status.HTTP_200_OK
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    """Zmienia ilość wybranej pozycji w koszyku."""
    
    # Wyszukuje pozycję należącą do zalogowanego użytkownika.
    try:
        item = Shopping.objects.get(
            id=item_id,
            user=request.user
        )
    except Shopping.DoesNotExist:
        return Response(
            {"error": "Position not found in this cart."},
            status=status.HTTP_404_NOT_FOUND
        )

    # Sprawdza, czy w żądaniu została podana ilość.
    if "quantity" not in request.data:
        return Response(
            {"quantity": "This field is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Sprawdza poprawność nowej ilości.
    quantity, error = validate_quantity(request.data.get("quantity"))

    if error:
        return Response(
            {"quantity": error},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Zmienia ilość produktu i zapisuje zmianę w bazie.
    item.quantity = quantity
    item.save()

    return Response(
        {
            "message": "The quantity has been changed.",
            "id": item.id,
            "quantity": item.quantity
        },
        status=status.HTTP_200_OK
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    """Tworzy zamówienie na podstawie zawartości koszyka użytkownika."""
    
    # Pobiera użytkownika, adres i numer telefonu.
    user = request.user
    address = request.data.get("address")
    phone = request.data.get("phone")

    # Sprawdza, czy podano adres.
    if not address:
        return Response(
            {"address": "This field is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Sprawdza, czy podano numer telefonu.
    if not phone:
        return Response(
            {"phone": "This field is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Pobiera wszystkie produkty z koszyka użytkownika.
    cart_items = Shopping.objects.filter(user=user)

    # Sprawdza, czy koszyk nie jest pusty.
    if not cart_items.exists():
        return Response(
            {"error": "Your cart is empty."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Tworzy nowe zamówienie.
    order = Order.objects.create(
        user=user,
        adres=address,
        phone=phone,
        value=0
    )

    # Ustawia początkową wartość całego zamówienia.
    total_value = Decimal("0.00")

    # Przechodzi przez wszystkie produkty znajdujące się w koszyku.
    for item in cart_items:

        # Wyszukuje cenę dla wybranej pizzy, rozmiaru i rodzaju ciasta.
        try:
            price = Price.objects.get(
                pizza=item.pizza,
                size=item.size,
                typecake=item.typecake
            )
        except Price.DoesNotExist:
             # Usuwa utworzone zamówienie, jeśli nie znaleziono ceny.
            order.delete()

            return Response(
                {
                    "error": (
                        f"No price for: "
                        f"{item.pizza}, {item.size}, {item.typecake}"
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Dodaje cenę pozycji pomnożoną przez jej ilość do wartości zamówienia.
        total_value += price.price * item.quantity

        # Tworzy pozycję należącą do zamówienia.
        OrderItem.objects.create(
            order=order,
            pizza=item.pizza,
            size=item.size,
            typecake=item.typecake,
            quantity=item.quantity,
            price=price.price
        )

    # Zapisuje obliczoną wartość całego zamówienia.
    order.value = total_value
    order.save()

    # Po poprawnym utworzeniu zamówienia opróżnia koszyk użytkownika.
    cart_items.delete()

    # Zwraca informację o utworzonym zamówieniu.
    return Response(
        {
            "message": "The order has been placed.",
            "order_id": order.id,
            "value": order.value
        },
        status=status.HTTP_201_CREATED
    )