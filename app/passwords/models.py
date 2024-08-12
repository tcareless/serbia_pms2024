# passwords/models.py
from django.db import models

class Password(models.Model):
    machine = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.machine} - {self.label} - {self.username or 'No Username'}"

class DeletedPassword(models.Model):
    machine = models.CharField(max_length=100)
    label = models.CharField(max_length=100)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=255)
    deleted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.machine} - {self.label} - {self.username or 'No Username'}"
