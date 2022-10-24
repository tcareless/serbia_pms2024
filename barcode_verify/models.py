from django.db import models

# Create your models here.
class LaserMark(models.Model):
    part_number = models.CharField(max_length=7)
    bar_code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duplicate_scan_at = models.DateTimeField(null=True)
    quality_scan_at = models.DateTimeField(null=True)


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.bar_code


class LaserMarkMeasurementData(models.Model):
    laser_mark = models.OneToOneField(LaserMark, on_delete=models.CASCADE, primary_key=True)
    measurement_data = models.TextField()

    class Meta:
        ordering = ['laser_mark']

    def __str__(self):
       return self.laser_mark.bar_code


class BarCodePUN(models.Model):
    name = models.CharField(max_length=50)
    part_number = models.CharField(max_length=50)
    regex = models.CharField(max_length=120)

    class Meta:
        ordering = ['part_number']

    def __str__(self):
        return self.name
