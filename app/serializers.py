from rest_framework import serializers
from app.models.pizza import Pizza
from app.models.size import Size
from app.models.typecake import TypeCake
from django.contrib.auth.models import User


# Serializuje dane modelu Pizza.
class PizzaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pizza
        fields = "__all__"

# Serializuje dane modelu Size.
class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = "__all__"

# Serializuje dane modelu TypeCake.
class TypeCakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeCake
        fields = "__all__"

# Obsługuje dane potrzebne do rejestracji nowego użytkownika.
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    # Tworzy nowego użytkownika na podstawie przesłanych danych.
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user