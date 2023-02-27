from django.db import models

# Create your models here.
class SiteVariableModel(models.Model):

    variable_name = models.CharField(max_length=128)
    variable_value = models.CharField(max_length=128)

    def __str__(self):
        return self.variable_name