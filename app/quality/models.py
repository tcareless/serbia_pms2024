from django.db import models
from plant.models.setupfor_models import Part  # Importing the Part model

class Feat(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='feat_set')
    name = models.CharField(max_length=256)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('part', 'name')
        ordering = ['order']

    def __str__(self):
        return f'{self.name} ({self.part})'
