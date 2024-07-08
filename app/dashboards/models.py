from django.db import models

# Create your models here.

class ShiftPoint(models.Model):
    tv_number = models.IntegerField()
    location = models.CharField(max_length=100)
    points = models.JSONField(default=list)  # Storing points as a list of strings
    last_updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.points:
            self.points = [
                "This is shift point 1.",
                "This is shift point 2.",
                "This is shift point 3.",
                "This is shift point 4."
            ]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"TV {self.tv_number} at {self.location}"
