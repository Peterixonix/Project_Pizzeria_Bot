from decimal import Decimal
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework import viewsets
from app.models.pizza import Pizza
from app.models.posorder import OrderItem
from app.models.price import Price
from .models.order import Order
from app.models.size import Size
from app.models.typecake import TypeCake
from app.models.shopping import Shopping
from app.serializers import PizzaSerializer, SizeSerializer, TypeCakeSerializer, RegisterSerializer
from rest_framework import generics
from django.contrib.auth.models import User


class PizzaViewSet(viewsets.ModelViewSet):
    queryset = Pizza.objects.all()
    serializer_class = PizzaSerializer

class SizeViewSet(viewsets.ModelViewSet):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

class TypeCakeViewSet(viewsets.ModelViewSet):
    queryset = TypeCake.objects.all()
    serializer_class = TypeCakeSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    user = request.user
    address = request.data.get("address")
    phone = request.data.get("phone")
    if not address:
        return Response(
            {"address": "This field is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not phone:
        return Response(
            {"phone": "This field in required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    cart_items = Shopping.objects.filter(user=user)

    if not cart_items.exists():
        return Response(
            {"error":"Your basket is empty."},
            status=status.HTTP_400_BAD_REQUEST
        )

    total_value = Decimal("0.00")
    order = Order.objects.create(
        user=user,
        address=address,
        phone=phone,
        value=0
    )

    for item in cart_items:
        try:
            price_objects = Price.objects.get(
                pizza=item.pizza,
                size=item.size,
                typecake=item.typecake
            )

        except Price.DoesNotExist:
            order.delete()

            return Response(
                {
                    "error":
                    f"No price for: {item.pizza}, {item.size}, {item.typecake}"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        item_value = price_objects.price * item.quantity

        total_value += item_value

        OrderItem.objects.create(
            order=order,
            pizza=item.pizza,
            size=item.size,
            typecake=item.typecake,
            quantity=item.quantity,
            price=price_objects.price
        )

    order.value = total_value
    order.save()
    cart_items.delete()

    return Response(
        {
            "message": "The order has been placed.",
            "order_id": order.id,
            "value": order.value
        },
        status=status.HTTP_201_CREATED
    )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    user = request.user
    pizza_id = request.data.get("pizza")
    size_id = request.data.get("size")
    typecake_id = request.data.get("typecake")
    quantity = request.data.get("quantity", 1)

    try:
        pizza = Pizza.objects.get(id=pizza_id)
        size = Size.objects.get(id=size_id)
        typecake = TypeCake.objects.get(id=typecake_id)
    except (Pizza.DoesNotExist, Size.DoesNotExist, TypeCake.DoesNotExist):
        return Response(
            {"error": "Wrong pizza, size or type of cake."},
            status=status.HTTP_400_BAD_REQUEST
        )

    Shopping.objects.create(
        user=user,
        pizza=pizza,
        size=size,
        typecake=typecake,
        quantity=quantity
    )
    return Response(
        {"message": "Add to basket"},
        status=status.HTTP_201_CREATED
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(request):
    user = request.user

    cart_items = Shopping.objects.filter(user=user)

    data = []

    for item in cart_items:
        data.append({
            "id": item.id,
            "pizza": str(item.pizza),
            "size": str(item.size),
            "typecake": str(item.typecake),
            "quantity": item.quantity,
        })

    return Response(data, status=status.HTTP_200_OK)

@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    try:
        item = Shopping.objects.get(
            id=item_id,
            user=request.user
        )
    except Shopping.DoesNotExist:
        return Response(
            {"error": "No found posision in this basket"},
            status=status.HTTP_404_NOT_FOUND
        )

    item.delete()

    return Response(
        {"message": "Deleted posision in this basket"},
        status=status.HTTP_200_OK
    )

@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    try:
        item = Shopping.objects.get(
            id=item_id,
            user=request.user
        )
    except Shopping.DoesNotExist:
        return Response(
            {"error": "There are no items in your basket."},
            status=status.HTTP_404_NOT_FOUND
        )
    quantity = request.data.get("quantity")

    if quantity is None:
        return Response(
            {"quantity": "This field is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        quantity = int(quantity)
    except (TypeError,ValueError):
        return Response(
            {"quantity": "The quantity must be a number."},
            status=status.HTTP_400_BAD_REQUEST
        )
    if quantity < 1:
        return Response(
            {quantity: "The quantity must be greater than 0."},
            status=status.HTTP_400_BAD_REQUEST
        )
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