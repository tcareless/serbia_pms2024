# password_models.py
from django.db import models
from django.utils import timezone
from ..models.setupfor_models import Asset  # Import the Asset model

class Password(models.Model):
    password_asset = models.ForeignKey(Asset, on_delete=models.CASCADE, default=1)  # Changed from machine to password_asset
    label = models.CharField(max_length=100)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.password_asset.asset_number} - {self.label} - {self.username or 'No Username'}"

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save()
