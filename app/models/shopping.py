from django.db import models as m
from django.contrib.auth.models import User

from .pizza import Pizza
from .size import Size
from .typecake import TypeCake

class Shopping(m.Model):
    user = m.ForeignKey(User, on_delete=m.CASCADE, null=True)
    pizza = m.ForeignKey(Pizza, on_delete=m.CASCADE, null=True)
    size = m.ForeignKey(Size, on_delete=m.CASCADE, null=True)
    typecake = m.ForeignKey(TypeCake, on_delete=m.CASCADE, null=True)
    quantity = m.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.user} - {self.pizza} - {self.size} - {self.typecake}"