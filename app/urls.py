from django.urls import path
from .views import RegisterView, create_order, add_to_cart, get_cart, remove_from_cart, update_cart_item

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("order/create/", create_order, name="create-order"),
    path("cart/", get_cart, name="get-cart"),
    path("cart/add/", add_to_cart, name="add-to-cart"),
    path("cart/remove/<int:item_id>/",remove_from_cart,name="remove-from-cart"),
    path("cart/update/<int:item_id>/", update_cart_item, name="update-cart-item"),
]
