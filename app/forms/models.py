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


class Form(models.Model):
    name = models.CharField(max_length=255)
    form_type = models.ForeignKey(FormType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Form {self.name} - {self.form_type.name}"


class FormQuestionAnswer(models.Model):
    ANSWER_TYPE_CHOICES = [
        ('textarea', 'Textarea'),
        ('number', 'Number Input'),
        ('dropdown', 'Dropdown'),
        ('radio', 'Radio Button'),
        ('checkbox', 'Checkbox'),
        ('time', 'Time Input'),
    ]

    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='questions_answers')
    question = models.CharField(max_length=255)
    answer_type = models.CharField(max_length=50, choices=ANSWER_TYPE_CHOICES, default='textarea')
    options = models.JSONField(blank=True, null=True)  # Store options as a JSON array if needed

    def __str__(self):
        return f"Question: {self.question} - Form: {self.form.name}"
