from rest_framework import serializers
from app.models.pizza import Pizza
from app.models.size import Size
from app.models.typecake import TypeCake
from django.contrib.auth.models import User



class PizzaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pizza
        fields = "__all__"


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = "__all__"


class TypeCakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeCake
        fields = "__all__"


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user