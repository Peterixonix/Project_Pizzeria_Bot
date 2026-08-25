from django.db import models as m
from app.models.pizza import Pizza
from app.models.size import Size
from app.models.typecake import TypeCake

class Price(m.Model):
    price = m.DecimalField(max_digits=10, decimal_places=2)
    pizza = m.ForeignKey(Pizza, on_delete=m.CASCADE)
    size = m.ForeignKey(Size, on_delete=m.CASCADE)
    typecake = m.ForeignKey(TypeCake, on_delete=m.CASCADE)
    def __str__(self):
        return f"{self.pizza} - {self.size} - {self.price} zł"

