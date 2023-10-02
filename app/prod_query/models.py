from django.db import models

# Create your models here.
#id, part, week, year, goal

class Weekly_Production_Goals(models.Model):
    part_number = models.CharField(max_length=20)
    week = models.IntegerField()
    year = models.IntegerField()
    goal = models.IntegerField()
