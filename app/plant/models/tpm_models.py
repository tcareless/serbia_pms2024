from django.db import models
from django.utils import timezone
from .setupfor_models import Asset

# Model from setupfor
# class Asset(models.Model):
#     asset_number = models.CharField(max_length=100)
#     asset_name = models.CharField(max_length=256, null=True, blank=True)  # Updated to varchar(256)

#     def __str__(self):
#         return f"{self.asset_number} - {self.asset_name}"



class TPM_Questionaire(models.Model):
    # Foreign Key is implicitly a many-to-one relationship.
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='questionaires'
    )
    version = models.PositiveIntegerField(default=1)
    effective_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Questionaire for Asset: {self.asset.asset_number}"
    
    def created_at_epoch(self):
        return int(self.created_at.timestamp())


class Questions(models.Model):
    question = models.TextField()
    questionaires = models.ManyToManyField(
        TPM_Questionaire,
        related_name='questions'
    )
    question_group = models.CharField(
        max_length=50,
        choices=[
            ('TPM', 'TPM'),
            ('Safety Check', 'Safety Check'),
            ('Process Machine Checks', 'Process Machine Checks'),
            ('6S Checks', '6S Checks'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)  # New field


    def __str__(self):
        return f"Question: {self.text:50}" #Prints first 50 chars of question
    
    def created_at_epoch(self):
        return int(self.created_at.timestamp())
    
    