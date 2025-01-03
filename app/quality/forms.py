# quality/forms.py
from django import forms
from .models import Feat, QualityPDFDocument, RedRabbitType
from plant.models.setupfor_models import Part

class FeatForm(forms.ModelForm):
    part = forms.ModelChoiceField(queryset=Part.objects.all(), label="Part Number")

    class Meta:
        model = Feat
        fields = ['part', 'name', 'order', 'alarm']  # Include the alarm field


from django import forms
from .models import QualityPDFDocument
from plant.models.setupfor_models import Part

class PDFUploadForm(forms.ModelForm):
    associated_parts = forms.ModelMultipleChoiceField(
        queryset=Part.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = QualityPDFDocument
        fields = ['title', 'pdf_file', 'category', 'associated_parts']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }




from django import forms
from .models import RedRabbitType
from plant.models.setupfor_models import Part

class RedRabbitTypeForm(forms.ModelForm):
    class Meta:
        model = RedRabbitType
        fields = ['name', 'description', 'part']  # Include the part field
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'part': forms.Select(attrs={'class': 'form-control'}),  # Dropdown for parts
        }




# ==============================================================================
# ==============================================================================
# =============================== QA Tags ======================================
# ==============================================================================
# ==============================================================================

# Common Tag Information Form
class TagInformationForm(forms.Form):
    reason = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Reason"
    )
    customer = forms.ChoiceField(
        choices=[
            ('chrysler_itp', 'Chrysler ITP'),
            ('chrysler_tipton', 'Chrysler Tipton'),
            # Add remaining options here...
        ],
        label="Customer",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    internal_external = forms.ChoiceField(
        choices=[('internal', 'Internal'), ('external', 'External')],
        widget=forms.RadioSelect,
        label="Internal or External"
    )
    # Add remaining fields from Tag Information...





# Hold Form
class HoldForm(forms.Form):
    hold_quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Hold Quantity"
    )
    hold_reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Hold Reason"
    )




# TPC Form
class TPCForm(forms.Form):
    tpc_current_process = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="TPC Current Process"
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Expiry"
    )




# Special Instructions Form
class SpecialInstructionsForm(forms.Form):
    special_instructions = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Special Instructions"
    )