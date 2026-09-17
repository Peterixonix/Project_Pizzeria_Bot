from django.contrib import admin
from app.models.pizza import Pizza
from app.models.size import Size
from app.models.typecake import TypeCake
from app.models.price import Price
from app.models.order import Order
from app.models.shopping import Shopping
from app.models.posorder import OrderItem 


# Rejestruje modele w panelu administracyjnym Django.
admin.site.register(Pizza)
admin.site.register(Size)
admin.site.register(TypeCake)
admin.site.register(Price)
admin.site.register(Shopping)
admin.site.register(OrderItem)


# Rejestruje model Order i pozwala dostosować sposób jego wyświetlania w panelu admina.
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    # Określa kolumny wyświetlane na liście zamówień.
    list_display = (
        "id",
        "user",
        "date",
        "status",
        "phone",
        "value",
    )


    # Pozwala filtrować zamówienia według statusu i daty.
    list_filter = (
        "status",
        "date",
    )


    # Pozwala wyszukiwać zamówienia po użytkowniku, telefonie i adresie.
    search_fields = (
        "user__username",
        "phone",
        "adres",
    )


    # Dodaje własną akcję do panelu administracyjnego.
    actions = (
        "mark_as_delivered",
    )

    # Ustawia nazwę akcji widoczną w panelu administracyjnym.
    @admin.action(description="Mark selected orders as delivered")
    def mark_as_delivered(self, request, queryset):
        # Zmienia status zaznaczonych zamówień na dostarczone.
        queryset.update(status="delivered")