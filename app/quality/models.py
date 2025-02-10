from django.db import models
from plant.models.setupfor_models import Part  # Importing the Part model
from django.core.exceptions import ValidationError



class SupervisorAuthorization(models.Model):
    supervisor_id = models.CharField(max_length=256)
    part_number = models.CharField(max_length=256)
    feat_name = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Authorization by {self.supervisor_id} for {self.feat_name} (Part {self.part_number}) at {self.created_at}'

class Feat(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='feat_set')
    name = models.CharField(max_length=256)
    order = models.PositiveIntegerField(default=1)
    alarm = models.IntegerField(default=0)  # New alarm field
    critical = models.BooleanField(default=False)  # New critical field


    class Meta:
        unique_together = ('part', 'name')
        ordering = ['order']

    def __str__(self):
        return f'{self.name} ({self.part})'


class ScrapForm(models.Model):
    partNumber = models.CharField(max_length=256)
    date = models.DateField()
    operator = models.CharField(max_length=256, blank=True, null=True)
    shift = models.IntegerField(blank=True, null=True)
    qtyPacked = models.IntegerField(blank=True, null=True)  # Updated field name
    totalDefects = models.IntegerField(blank=True, null=True)
    totalInspected = models.IntegerField(blank=True, null=True)  # Updated field name
    comments = models.TextField(blank=True, null=True)
    detailOther = models.TextField(blank=True, null=True)
    tpc_number = models.CharField(max_length=256, blank=True, null=True)  # New field for TPC #
    payload = models.JSONField()  # Storing the entire payload as JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Scrap Form {self.id} for Part {self.partNumber}'


class FeatEntry(models.Model):
    scrap_form = models.ForeignKey(ScrapForm, related_name='feat_entries', on_delete=models.CASCADE)
    featName = models.CharField(max_length=256)
    defects = models.IntegerField()
    partNumber = models.CharField(max_length=256)  # Add the partNumber field

    def __str__(self):
        return f'FeatEntry for {self.featName} with {self.defects} defects, Part Number: {self.partNumber}'





from django.db import models
from plant.models.setupfor_models import Part

class PartMessage(models.Model):
    FONT_SIZE_CHOICES = [
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('xl', 'Extra Large'),
        ('xxl', 'Double Extra Large'),
        ('xxxl', 'Triple Extra Large'),
    ]

    part = models.OneToOneField(Part, on_delete=models.CASCADE, related_name='custom_message')
    message = models.TextField(blank=True, null=True)
    font_size = models.CharField(max_length=10, choices=FONT_SIZE_CHOICES, default='medium')  # Default size

    def __str__(self):
        return f"Message for {self.part.part_number}"



# =====================================================
# ===================== QA V2 =========================
# =====================================================

from django.db import models
from plant.models.setupfor_models import Part
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os


class QualityPDFDocument(models.Model):
    CATEGORY_CHOICES = [
        ('QA', 'Quality Alerts'),
        ('SI', 'Special Instruction'),
        ('TPC', 'TPC'),
        ('VAC', 'Visual Acceptance Criteria'),
        ('PMR', 'Part Marking Requirement'),
        ('CT', 'Certification Tag'),
    ]

    title = models.CharField(max_length=256)
    pdf_file = models.FileField(upload_to='pdfs/')  # Stores the PDF file
    associated_parts = models.ManyToManyField(Part, related_name='pdf_documents')  # Many-to-Many relation with parts
    uploaded_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='QA')

    def __str__(self):
        return self.title

    def is_new(self):
        # Return True if the PDF was uploaded within the last 8 hours
        return timezone.now() - self.uploaded_at < timedelta(hours=4)

# Automatically delete the PDF file from the media folder when a QualityPDFDocument instance is deleted
@receiver(post_delete, sender=QualityPDFDocument)
def delete_file_on_delete(sender, instance, **kwargs):
    if instance.pdf_file:
        if os.path.isfile(instance.pdf_file.path):
            os.remove(instance.pdf_file.path)


class ViewingRecord(models.Model):
    operator_number = models.CharField(max_length=20)  # Operator's clock number (string for flexibility)
    pdf_document = models.ForeignKey(QualityPDFDocument, on_delete=models.CASCADE, related_name='viewing_records')
    viewed_at = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp when viewed

    def __str__(self):
        return f"Operator {self.operator_number} viewed {self.pdf_document.title} on {self.viewed_at}"
    






# =================================================================
# =================================================================
# ====================== Red Rabbits ==============================
# =================================================================
# =================================================================

from django.db import models
from plant.models.setupfor_models import Part

class RedRabbitType(models.Model):
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField(blank=True, null=True)  # Optional description
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name="red_rabbit_types", default=1)  # Default to part ID 1

    def __str__(self):
        return f"{self.name} (Part: {self.part.part_number})"



class RedRabbitsEntry(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='red_rabbits_entries')
    red_rabbit_type = models.ForeignKey(RedRabbitType, on_delete=models.CASCADE, related_name='entries', default=1)
    date = models.DateField(auto_now_add=True)
    clock_number = models.CharField(max_length=20)
    shift = models.PositiveSmallIntegerField()
    verification_okay = models.BooleanField()
    supervisor_comments = models.TextField(blank=True, null=True)
    supervisor_id = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.red_rabbit_type} Entry for {self.part.part_number} by {self.clock_number}'





def default_dropdown_data():
    """
    Returns a dictionary with the expected keys for dropdown options.
    'parts' is a list of dictionaries, where each dictionary represents
    a part and its associated operations.
    """
    return {
        "quality_tag_type": [],
        "customer": [],
        "parts": [],
        "cell": [],
        "quality_engineer": [],
        "factory_focus_leader": [],
        "quality_manager": [],
    }

class QualityTagDropdownOptions(models.Model):
    """
    A singleton model that stores the options for each dropdown as a JSON object.
    'parts' is stored as a list of objects:
      [
        {
          "part_name": "Part A",
          "operations": ["Op1", "Op2", ...]
        },
        ...
      ]
    """
    data = models.JSONField(default=default_dropdown_data, blank=True)

    def clean(self):
        # Ensure the JSON object includes all required keys
        expected_keys = [
            "quality_tag_type",
            "customer",
            "parts",
            "cell",
            "quality_engineer",
            "factory_focus_leader",
            "quality_manager",
        ]
        if not isinstance(self.data, dict):
            raise ValidationError("Data must be a JSON object (dictionary).")

        for key in expected_keys:
            if key not in self.data:
                # For 'parts', default to empty list (each entry is {part_name, operations})
                if key == "parts":
                    self.data[key] = []
                else:
                    self.data[key] = []

        # Validate that parts is a list of dicts with "part_name" and "operations"
        if not isinstance(self.data["parts"], list):
            raise ValidationError("'parts' must be a list.")
        for item in self.data["parts"]:
            if not isinstance(item, dict):
                raise ValidationError("Each item in 'parts' must be a dict.")
            if "part_name" not in item or "operations" not in item:
                raise ValidationError(
                    "Each part must have 'part_name' and 'operations' keys."
                )
            if not isinstance(item["operations"], list):
                raise ValidationError("'operations' must be a list.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return "Quality Tag Dropdown Options"

    class Meta:
        verbose_name = "Quality Tag Dropdown Options"
        verbose_name_plural = "Quality Tag Dropdown Options"





class QualityTag(models.Model):
    """
    Model to store Quality Tags with dynamically selected dropdown options.
    """
    data = models.JSONField()  # Store user-selected dropdown options
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of creation

    def __str__(self):
        return f"Quality Tag {self.id} - Created on {self.created_at}"
