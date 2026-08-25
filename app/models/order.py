from django.db import models as m
from django.contrib.auth.models import User

class Order(m.Model):
    STATUS = [
        ("new", "New"),
        ("in_realization", "In_realization"),
        ("delivered", "Delivered")
    ]
    user = m.ForeignKey(User, on_delete=m.CASCADE)
    date = m.DateTimeField(auto_now_add=True)
    status = m.CharField(max_length=20, choices=STATUS, default="new")
    adres = m.CharField(max_length=200)
    phone = m.CharField(max_length=20)
    value = m.DecimalField(max_digits=10, decimal_places=2)
    def __str__(self):
        return f"Order {self.id}"

