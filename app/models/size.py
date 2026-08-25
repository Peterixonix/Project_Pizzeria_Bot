from django.db import models as m

class Size(m.Model):
    name = m.CharField(max_length=100)
    diameter = m.IntegerField()
    def __str__(self):
        return self.name



