from django.db import models as m
from app.models.shopping import Shopping
from app.models.pizza import Pizza
from app.models.size import Size 
from app.models.typecake import TypeCake


class PosisionShopping(m.Model):
    quantity = m.IntegerField()
    shopping = m.ForeignKey(Shopping, on_delete=m.CASCADE)
    pizza = m.ForeignKey(Pizza, on_delete=m.CASCADE)
    size = m.ForeignKey(Size, on_delete=m.CASCADE)
    typecake = m.ForeignKey(TypeCake, on_delete=m.CASCADE)
    def __str__(self):
        return f"{self.pizza} x{self.quantity}"
    