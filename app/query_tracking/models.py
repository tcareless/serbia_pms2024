from django.db.models import Model
from django.db.models import DecimalField
from django.db.models import CharField

class QueryLog(Model):
    source = CharField(max_length=48)
    query = CharField(max_length=1024)
    time = DecimalField(max_digits=5, decimal_places=2)

def record_execution_time(name, sql, duration):
    querylog = QueryLog.objects.create(
        source = name,
        query = sql,
        time = duration,
    )
    querylog.save()