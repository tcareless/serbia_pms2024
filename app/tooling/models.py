from django.db import models

# Create your models here.
class DefaultTool(models.Model):
    tool_name = models.CharField(max_length=50, unique=True)  # I'm assuming ToolName should be unique
    default_life = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)  # Field for logical deletion

    def __str__(self):
        return self.tool_name
    

class ToolData(models.Model):
    macnum = models.CharField(max_length=255)
    operation = models.CharField(max_length=255)
    shift = models.CharField(max_length=255)
    operator = models.CharField(max_length=255)
    tool_type = models.CharField(max_length=255)
    toolstatus = models.CharField(max_length=255)
    tool_issue = models.CharField(max_length=255)
    rated_toollife = models.IntegerField()
    acttoollife = models.IntegerField()
    toolserial = models.CharField(max_length=255)
    comments = models.TextField()
    insert_datetime = models.DateTimeField()

    def __str__(self):
        return f"{self.toolserial} - {self.operation}"
