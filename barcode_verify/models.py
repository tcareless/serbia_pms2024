from django.db import models

# Create your models here.
class LaserMark(models.Model):
    part_number = models.CharField(max_length=7)
    bar_code = models.CharField(max_length=50, unique=True)
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scanned_at']

    def __str__(self):
        return self.bar_code


class BarCodePUN(models.Model):
    name = models.CharField(max_length=50)
    part = models.CharField(max_length=50)
    regex = models.CharField(max_length=120)

    class Meta:
        ordering = ['part']

    def __str__(self):
        return self.name
