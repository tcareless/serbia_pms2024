from django.db import models

class serbia_FormSubmission(models.Model):
    payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    form_type = models.ForeignKey('serbia_FormType', on_delete=models.CASCADE)

    def __str__(self):
        return f"Submission {self.id} - {self.form_type.name}"


class serbia_FormType(models.Model):
    name = models.CharField(max_length=255)
    template_name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class serbia_Form(models.Model):
    name = models.CharField(max_length=255)
    form_type = models.ForeignKey(serbia_FormType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)  # Add the metadata field


    def __str__(self):
        return f"Form {self.name} - {self.form_type.name}"


class serbia_FormQuestion(models.Model):
    form = models.ForeignKey(serbia_Form, on_delete=models.CASCADE, related_name='questions')
    question = models.JSONField()  # Store the question details as a JSON object
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Question for Form: {self.form.name}"


class FormAnswer(models.Model):
    question = models.ForeignKey(serbia_FormQuestion, on_delete=models.CASCADE, related_name='answers')
    answer = models.JSONField()  # Storing the answer as a JSON object for flexibility
    operator_number = models.CharField(max_length=255)  # New field to store operator number
    created_at = models.DateTimeField()  # No auto_now_add

    def __str__(self):
        return f"Answer by {self.operator_number} for Question ID: {self.question.id} - Form: {self.question.form.name}"
