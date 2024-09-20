from django.db import models

class PDFUpload(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='pdfs/')

    def __str__(self):
        return self.title
