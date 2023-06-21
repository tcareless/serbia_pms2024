from django.db.models import Model
from django.db.models import DurationField
from django.db.models import CharField
from django.db.models import CharField

class QueryLog(Model):
    source = CharField(max_length=48)
    query = CharField(max_length=1024)
    time = DurationField()