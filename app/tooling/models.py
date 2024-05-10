from django.db import models

# Create your models here.
class SiteVariableModel(models.Model):

    variable_name = models.CharField(max_length=128)
    variable_value = models.CharField(max_length=128)

    def __str__(self):
        return self.variable_name
    

# original sql table create statement:
    # CREATE TABLE tool_datatab
    # id INT AUTO_INCREMENT PRIMARY KEY,
    # macnum VARCHAR(255),
    # operation VARCHAR(255),
    # Shift VARCHAR(255),
    # operator VARCHAR(255),
    # tool_type VARCHAR(255),
    # toolstatus VARCHAR(255),
    # tool_issue VARCHAR(255),
    # Rated_toollife INT,
    # acttoollife INT,
    # toolserial VARCHAR(255),
    # comments TEXT,
    # insert_datetime DATETIME

class MachineList(models.Model):
    asset_number = models.CharField(max_length=20)
    asset_name = models.CharField(max_length=128)

    def __str__(self):
        return f'{self.asset_number}: {self.asset_name}'


class ToolLifeData(models.Model):
    MACHINE_NUMBER_CHOICES = [
        (788,"788"),
        (789,"789"),
        (790,"790"),
        (791,"791"),
        (792,"792"),
        (793,"793"),
        (794,"794"),
    ]
    OPERATION_CHOICES = [
        (10, "OP-10"),
        (20, "OP-20"),
        (30, "OP-30"),
    ]

    SHIFT_CHOICES = [
        ("Mornings","Mornings"),
        ("Afternoons","Afternoons"),
        ("Midnights","Midnights"),
        ("Continental-A","Continental-A"),
        ("Continental-B","Continental-B"),
    ]

    TOOL_TYPE_CHOICES = [
        ("Drill","Drill"),
        ("Reamer","Reamer"),
    ]

    TOOL_ISSUE_CHOICES = [
        ("Machine Issue", "Machine Issue"),
        ("Oversize Holes", "Oversize Holes"),
        ("Undersize Holes", "Undersize Holes"),
        ("Hole Positions", "Hole Positions are out"),
        ("Burnt Holes", "Burnt Holes"),
        ("Insufficient Coolant", "Insufficient Coolant"),
        ("Dropped", "Tool Dropped"),
        ("Wrong Offset", "Wrong Offset"),
        ("Incorrect Part Load", "Incorrect Part Load"),
        ("Tooling Issue", "Wrong Setup by Toolroom"),
        ("Other", "Other"),
    ]

    machine = models.CharField(
        max_length = 128,
        choices = MACHINE_NUMBER_CHOICES,
    )
    operation = models.CharField(
        max_length = 128,
        choices = OPERATION_CHOICES,
    )
    shift = models.CharField(
        max_length = 128,
        choices = SHIFT_CHOICES
    )

    operator = models.CharField(
        max_length=128,
    )

    tool_type = models.CharField(
        max_length = 128,
        choices = TOOL_TYPE_CHOICES,
    )

    tool_status = models.CharField(
        max_length=128,
    )

    tool_issue = models.CharField(
        max_length=128,
        choices = TOOL_ISSUE_CHOICES,
    )

    # Conditional default for expected_tool_life based on tool_type
    def get_expected_tool_life_default(self):
        return 750 if self.tool_type == 'Drill' else 250 if self.tool_type == 'Reamer' else 0

    expected_tool_life = models.IntegerField()
    actual_tool_life = models.IntegerField()
    tool_serial_number = models.CharField(
        max_length=128
    )
    comments = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )




