# quality/forms.py
from django import forms
from .models import Feat, QualityPDFDocument, RedRabbitType
from plant.models.setupfor_models import Part
from .models import QualityTagDropdownOptions, QualityTag


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




class QualityTagForm(forms.ModelForm):
    """
    Dynamic Form for creating a Quality Tag. All choices are fetched dynamically from the database.
    Dropdown fields are used instead of checkboxes.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dropdown_options = QualityTagDropdownOptions.objects.first()  # Fetch dropdown options from DB

        if dropdown_options:
            # Single-select dropdown
            self.fields["quality_tag_type"] = forms.ChoiceField(
                choices=[("", "Select Quality Tag Type")] + [(opt, opt) for opt in dropdown_options.data.get("quality_tag_type", [])],
                widget=forms.Select,  # Normal dropdown
                required=True
            )
            
            self.fields["customer"] = forms.MultipleChoiceField(
                choices=[(opt, opt) for opt in dropdown_options.data.get("customer", [])],
                widget=forms.SelectMultiple,  # Multi-select dropdown
                required=False
            )

            self.fields["parts"] = forms.MultipleChoiceField(
                choices=[(p["part_name"], p["part_name"]) for p in dropdown_options.data.get("parts", [])],
                widget=forms.SelectMultiple,  # Multi-select dropdown
                required=False
            )

            self.fields["cell"] = forms.MultipleChoiceField(
                choices=[(opt, opt) for opt in dropdown_options.data.get("cell", [])],
                widget=forms.SelectMultiple,  # Multi-select dropdown
                required=False
            )

            self.fields["quality_engineer"] = forms.MultipleChoiceField(
                choices=[(opt, opt) for opt in dropdown_options.data.get("quality_engineer", [])],
                widget=forms.SelectMultiple,  # Multi-select dropdown
                required=False
            )

            self.fields["factory_focus_leader"] = forms.MultipleChoiceField(
                choices=[(opt, opt) for opt in dropdown_options.data.get("factory_focus_leader", [])],
                widget=forms.SelectMultiple,  # Multi-select dropdown
                required=False
            )

            self.fields["quality_manager"] = forms.ChoiceField(
                choices=[("", "Select Quality Manager")] + [(opt, opt) for opt in dropdown_options.data.get("quality_manager", [])],
                widget=forms.Select,  # Single dropdown
                required=True
            )

    class Meta:
        model = QualityTag
        fields = []  # Fields are generated dynamically
