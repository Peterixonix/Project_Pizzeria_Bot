from django.contrib import admin
from app.models.pizza import Pizza
from app.models.size import Size
from app.models.typecake import TypeCake
from app.models.price import Price
from app.models.order import Order
from app.models.shopping import Shopping
from app.models.posorder import OrderItem 


admin.site.register(Pizza)
admin.site.register(Size)
admin.site.register(TypeCake)
admin.site.register(Price)
admin.site.register(Order)
admin.site.register(Shopping)
admin.site.register(OrderItem)