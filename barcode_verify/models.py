from django.db import models

# Create your models here.
class LaserMark(models.Model):
    part_number = models.CharField(max_length=7)
    bar_code = models.CharField(max_length=50, unique=True)
    scanned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scanned_at']

    def __str__(self):
        return self.bar_code

    @classmethod
    def extract_part_number(cls, bar_code):
        if bar_code[:1:] == 'V':
            if bar_code[1:2:] == '3':
              return 'input'
        else:
            return None
