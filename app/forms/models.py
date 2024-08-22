from django.db import models

class FormSubmission(models.Model):
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    form_type = models.ForeignKey('FormType', on_delete=models.CASCADE)

    def __str__(self):
        return f"Submission {self.id} - {self.form_type.name}"


class FormType(models.Model):
    name = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
