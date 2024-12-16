from django.db import models
from django.utils import timezone
from .setupfor_models import Asset
import time

# Model from setupfor
# class Asset(models.Model):
#     asset_number = models.CharField(max_length=100)
#     asset_name = models.CharField(max_length=256, null=True, blank=True)  # Updated to varchar(256)

#     def __str__(self):
#         return f"{self.asset_number} - {self.asset_name}"

def get_current_epoch():
    return int(time.time())

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
        return int(self.effective_date.timestamp())  # Fixed to refer to effective_date


class Questions(models.Model):
    QUESTION_TYPES = [
        ('YN', 'Yes/No'),
        ('NUM', 'Numeric Input'),
    ]
    question = models.TextField()
    question_group = models.CharField(
        max_length=50,
        choices=[
            ('TPM', 'TPM'),
            ('Process Machine Checks', 'Process Machine Checks'),
            ('6S Checks', '6S Checks'),
        ]
    )
    type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        default='YN'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)  # New field

    def __str__(self):
        return f"Question: {self.question[:50]}"  # Prints first 50 chars of question
    
    def created_at_epoch(self):
        return int(self.created_at.timestamp())


class QuestionaireQuestion(models.Model):
    questionaire = models.ForeignKey(
        TPM_Questionaire,
        on_delete=models.CASCADE,
        related_name='questionaire_questions'
    )
    question = models.ForeignKey(
        Questions,
        on_delete=models.CASCADE,
        related_name='questionaire_questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.FloatField(default=0.0)  # Allow floating-point order values

    class Meta:
        ordering = ['order']  # Default ordering by the 'order' field

    def __str__(self):
        return f"Link: {self.question} to {self.questionaire} (Order: {self.order})"











    

class TPM_Answers(models.Model):
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    operator_number = models.PositiveIntegerField()
    shift = models.PositiveIntegerField(choices=[(1, 'Shift 1'), (2, 'Shift 2'), (3, 'Shift 3')])
    date = models.DateField()
    answers = models.JSONField()  # Stores question-answer pairs as a JSON blob
    submitted_at = models.BigIntegerField(default=get_current_epoch)  # Use the callable function

    def __str__(self):
        return f"Answers for Asset {self.asset.asset_number} on {self.date} by Operator {self.operator_number}"