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
    # A Foreign Key to the Asset model creates a many-to-one relationship.
    # Each TPM_Questionaire is linked to one Asset, but an Asset can have multiple Questionnaires.
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,  # If an Asset is deleted, all associated Questionnaires are also deleted.
        related_name='questionaires'  # Allows reverse access: Asset.questionaires.all() for related Questionnaires.
    )
    version = models.PositiveIntegerField(default=1)  # Tracks versioning for updates or modifications.
    effective_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Provides a human-readable name for the object in admin and queries.
        return f"Questionaire for Asset: {self.asset.asset_number}"

    def created_at_epoch(self):
        # Returns the effective_date as an epoch timestamp, useful for JSON APIs or timestamp comparisons.
        return int(self.effective_date.timestamp())


# Represents individual questions that can belong to various questionaires.
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
        choices=QUESTION_TYPES,  # Ensures type is one of the predefined values
        default='YN'  # Default question type is Yes/No
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)  # Soft delete option for questions without permanent removal

    def __str__(self):
        # Displays the first 50 characters of the question for easy identification.
        return f"Question: {self.question[:50]}"
    
    def created_at_epoch(self):
        # Returns the created_at timestamp as an epoch for APIs or other time-based logic.
        return int(self.created_at.timestamp())


# Represents the many-to-many relationship between TPM_Questionaire and Questions
class QuestionaireQuestion(models.Model):
    questionaire = models.ForeignKey(
        TPM_Questionaire,
        on_delete=models.CASCADE,  # Deleting a questionnaire removes its links to questions.
        related_name='questionaire_questions'  # Reverse access from TPM_Questionaire to its linked questions.
    )
    question = models.ForeignKey(
        Questions,
        on_delete=models.CASCADE,  # Deleting a question removes its links to questionnaires.
        related_name='questionaire_questions'  # Reverse access from Questions to associated questionnaires.
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when this link was created.
    order = models.FloatField(default=0.0)  # Allows precise control over question order (e.g., 1.1, 2.3).

    class Meta:
        ordering = ['order']  # Automatically orders linked questions by their order value.

    def __str__(self):
        # Provides an easy-to-read representation of the link for admin and debugging.
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