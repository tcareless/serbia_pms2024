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
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='questions_answers')
    question = models.CharField(max_length=255)
    answer = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Question: {self.question} - Form: {self.form.name}"