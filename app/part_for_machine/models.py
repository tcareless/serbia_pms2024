from django.db import models

# Create your models here.
class PartForMachineEvent(models.Model):
    datetime = models.DateTimeField()
    part = models.CharField(max_length=30)
    line = models.CharField(max_length=30)
    asset = models.CharField(max_length=10)