from django.db import models

# Create your models here.


class LaserMark(models.Model):
    part_number = models.CharField(max_length=20)
    bar_code = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=1, null=True)
    asset = models.CharField(max_length=8, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.bar_code


class LaserMarkMeasurementData(models.Model):
    laser_mark = models.OneToOneField(
        LaserMark, on_delete=models.CASCADE, primary_key=True)
    measurement_data = models.TextField()

    class Meta:
        ordering = ['laser_mark']

    def __str__(self):
        return self.laser_mark.bar_code


class LaserMarkDuplicateScan(models.Model):
    laser_mark = models.OneToOneField(
        LaserMark, on_delete=models.CASCADE, primary_key=True)
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scanned_at']

    def __str__(self):
        return f'{self.laser_mark.bar_code} scanned at {self.scanned_at}'


class BarCodePUN(models.Model):
    name = models.CharField(max_length=50)
    part_number = models.CharField(max_length=50)
    regex = models.CharField(max_length=120)
    active = models.BooleanField()
    parts_per_tray = models.IntegerField(default=0)

    class Meta:
        ordering = ['part_number']

    def __str__(self):
        return self.name


class DuplicateBarcodeEvent(models.Model):
    barcode = models.CharField(max_length=50)
    part_number = models.CharField(max_length=50)
    scan_time = models.DateTimeField()
    unlock_code = models.CharField(max_length=3)
    employee_id = models.CharField(max_length=10, null=True)
    event_time = models.DateTimeField()
    user_reason = models.CharField(max_length=255, null=True)  # Add this field


    class Meta:
        ordering = ['-event_time']

    def __str__(self):
        return f"{self.barcode} scanned at {self.scan_time} with unlock code {self.unlock_code}"
