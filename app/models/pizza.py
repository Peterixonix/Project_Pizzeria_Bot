from django.db import models as m

class Pizza(m.Model):
    name = m.CharField(max_length=100)
    content = m.TextField()
    def __str__(self):
        return self.name


