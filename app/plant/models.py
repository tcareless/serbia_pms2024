# plant/models.py

from django.db import models

class Asset(models.Model):
    asset_number = models.CharField(max_length=100)  

    def __str__(self):
        return self.asset_number

class Part(models.Model):
    part_number = models.CharField(max_length=100)

    def __str__(self):
        return self.part_number

class SetupFor(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    since = models.DateTimeField()

    def __str__(self):
        return f'{self.asset.asset_number} setup for {self.part.part_number}'
