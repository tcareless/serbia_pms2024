from django.db import models
from django.utils import timezone

class Asset(models.Model):
    asset_number = models.CharField(max_length=100)

    def __str__(self):
        return self.asset_number

class Part(models.Model):
    part_number = models.CharField(max_length=100)

    def __str__(self):
        return self.part_number

class SetupForManager(models.Manager):
    def get_part_at_time(self, asset_number, timestamp):
        try:
            setup = self.filter(asset__asset_number=asset_number, since__lte=timestamp).order_by('-since').first()
            return setup.part if setup else None
        except self.model.DoesNotExist:
            return None

class SetupFor(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    since = models.DateTimeField()

    objects = models.Manager()  # The default manager.
    setupfor_manager = SetupForManager()  # Our custom manager.

    def __str__(self):
        return f'{self.asset.asset_number} setup for {self.part.part_number}'
