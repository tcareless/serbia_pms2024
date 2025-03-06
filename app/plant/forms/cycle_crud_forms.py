from django import forms

class AssetCycleTimeForm(forms.Form):
    ASSET_CHOICES = [
        ('asset_1', 'Asset 1'),
        ('asset_2', 'Asset 2'),
        ('asset_3', 'Asset 3'),
    ]
    
    PART_CHOICES = [
        ('part_1', 'Part 1'),
        ('part_2', 'Part 2'),
        ('part_3', 'Part 3'),
    ]

    asset = forms.ChoiceField(choices=ASSET_CHOICES, label="Select Asset")
    part = forms.ChoiceField(choices=PART_CHOICES, label="Select Part")
    cycle_time = forms.FloatField(label="Cycle Time", min_value=0)
    datetime = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), label="Date & Time")
