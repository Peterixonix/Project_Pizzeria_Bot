from django.db import models as m
from app.models.order import Order
from app.models.pizza import Pizza
from app.models.size import Size
from app.models.typecake import TypeCake

class OrderItem(m.Model):
    order = m.ForeignKey(Order, on_delete=m.CASCADE)
    pizza = m.ForeignKey(Pizza, on_delete=m.CASCADE)
    size = m.ForeignKey(Size, on_delete=m.CASCADE)
    typecake = m.ForeignKey(TypeCake, on_delete=m.CASCADE)
    quantity = m.PositiveIntegerField(default=1)
    price = m.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.pizza} x{self.quantity}"