import graphene
from graphene_django import DjangoObjectType

from .models import Pizza


class PizzaType(DjangoObjectType):
    class Meta:
        model = Pizza
        fields = ("id", "name", "content")


class Query(graphene.ObjectType):
    pizzas = graphene.List(PizzaType)

    def resolve_pizzas(root, info):
        return Pizza.objects.all()


schema = graphene.Schema(query=Query)