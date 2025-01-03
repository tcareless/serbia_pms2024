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

from django import forms

# Common Tag Information Form
class TagInformationForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Reason"
    )
    customer = forms.ChoiceField(
        choices=[
            ('chrysler_itp', 'Chrysler ITP'),
            ('chrysler_tipton', 'Chrysler Tipton'),
            ('ford_livonia', 'Ford Motor Co Livonia'),
            ('ford_sharonville', 'Ford Motor Co Sharonville'),
            ('gm_bay_city', 'GM Bay City'),
            ('gm_romulus', 'GM Romulus'),
            ('gm_silao', 'GM Silao'),
            ('gm_slp', 'GM SLP'),
            ('gm_st_catherines', 'GM St Catherines'),
            ('gm_toledo', 'GM Toledo'),
            ('magna_msm', 'Magna MSM'),
            ('magna_ramos', 'Magna Ramos'),
            ('magna_roitzsch', 'Magna Roitzsch'),
            ('melling_tool', 'Melling Tool Jackson'),
            ('punch_powerglide', 'Punch Powerglide'),
            ('rpm_industries', 'RPM Industries'),
            ('seastar_solutions', 'Seastar Solutions (Teleflex) BC'),
            ('zf_germany', 'ZF Germany'),
        ],
        label="Customer",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    internal_external = forms.ChoiceField(
        choices=[('internal', 'Internal'), ('external', 'External')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Internal / External"
    )

    part_lookup = forms.MultipleChoiceField(
        choices=[
            ('50-9341', '50-9341'),
            ('50-8670', '50-8670'),
            ('51-1234', '51-1234'),
            ('51-5678', '51-5678'),
            ('52-1111', '52-1111'),
            ('52-2222', '52-2222'),
            ('53-3333', '53-3333'),
            ('53-4444', '53-4444'),
            ('54-5555', '54-5555'),
            ('54-6666', '54-6666'),
            ('55-7777', '55-7777'),
            ('55-8888', '55-8888'),
            ('56-9999', '56-9999'),
            ('56-0000', '56-0000'),
            ('57-1122', '57-1122'),
            ('57-3344', '57-3344'),
            ('58-5566', '58-5566'),
            ('58-7788', '58-7788'),
            ('59-9900', '59-9900'),
            ('59-0011', '59-0011'),
            ('60-1234', '60-1234'),
            ('60-5678', '60-5678'),
            ('61-9101', '61-9101'),
            ('61-1121', '61-1121'),
            ('62-3141', '62-3141'),
            ('62-5161', '62-5161'),
            ('63-7181', '63-7181'),
            ('63-9202', '63-9202'),
        ],
        label="Part Lookup",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    is_compact_pellet = forms.ChoiceField(
        choices=[
            ('search', 'Search'),
            ('non_compact', 'Non-Compact'),
            ('compact_plate', 'Compact-Plate'),
            ('compact_pedestal', 'Compact-Pedestal'),
            ('pellet', 'Pellet'),
        ],
        label="Is Part a Compact or Pellet?",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cell = forms.ChoiceField(
        choices=[
            ('search', 'Search'),
            ('10r140', '10R140'),
            ('10r60', '10R60'),
            ('10r80', '10R80'),
            ('6l_input', '6L Input'),
            ('6l_output', '6L Output'),
            ('9hp', '9HP'),
            ('ab1v_input', 'AB1V Input'),
            ('ab1v_overdrive', 'AB1V Overdrive'),
            ('ab1v_reaction', 'AB1V Reaction'),
            ('blending', 'Blending'),
            ('compact', 'Compact'),
            ('gf6_input', 'GF6 Input'),
            ('gf6_reaction', 'GF6 Reaction'),
            ('gf9', 'GF9'),
            ('not_cell_specific', 'Not Cell Specific'),
            ('optimized', 'Optimized'),
            ('tesma', 'Tesma'),
            ('trilobe', 'Trilobe'),
        ],
        label="Cell",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    machine = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Machine"
    )
    operations = forms.ChoiceField(
        choices=[
            ('search', 'Search'),
            ('all_processes', 'All Processes'),
            ('assembler', 'Assembler'),
            ('autogauge', 'Autogauge'),
            ('balancing', 'Balancing'),
            ('bearing_press', 'Bearing Press'),
            ('blending', 'Blending'),
            ('broaching', 'Broaching'),
            ('care', 'Care'),
            ('compacting', 'Compacting'),
            ('deburr', 'Deburr'),
            ('final_audit', 'Final Audit'),
            ('finished', 'Finished'),
            ('gp12', 'GP12'),
            ('high_pressure_wash', 'High Pressure Wash'),
            ('induction', 'Induction'),
            ('laser_marking', 'Laser Marking'),
            ('machining', 'Machining'),
            ('media_detect', 'Media Detect'),
            ('mpi', 'MPI'),
            ('not_operation_specific', 'Not Operation Specific'),
            ('op10', 'OP10'),
            ('op10_20', 'OP10/20'),
            ('op10_20_30', 'OP10/20/30'),
            ('op100', 'OP100'),
            ('op110', 'OP110'),
            ('op120', 'OP120'),
            ('op130', 'OP130'),
            ('op20', 'OP20'),
            ('op25', 'OP25'),
            ('op30', 'OP30'),
            ('op35', 'OP35'),
            ('op40', 'OP40'),
            ('op40_50', 'OP40/50'),
            ('op50', 'OP50'),
            ('op60', 'OP60'),
            ('op7', 'OP7'),
            ('op70', 'OP70'),
            ('op80', 'OP80'),
            ('op90', 'OP90'),
            ('packing', 'Packing'),
            ('secondary', 'Secondary'),
            ('shipping', 'Shipping'),
            ('sintering', 'Sintering'),
            ('sizing', 'Sizing'),
            ('turning', 'Turning'),
            ('vision_system', 'Vision System'),
            ('wash', 'Wash'),
        ],
        label="Operations",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quality_engineer = forms.ChoiceField(
        choices=[
            ('romario_antony', 'Romario Antony (Romario.Antony@johnsonelectric.com)'),
            ('terry_clarke', 'Terry Clarke (Terry.Clarke@johnsonelectric.com)'),
            ('arun_janardhan', 'Arun Janardhan (Arun.Janardhan@johnsonelectric.com)'),
            ('nikhil_jindal', 'Nikhil Jindal (Nikhil.Jindal@johnsonelectric.com)'),
            ('lakshmi_kurukuri', 'Lakshmi Kurukuri (lakshmi.kurukuri@johnsonelectric.com)'),
            ('geoff_perrier', 'Geoff Perrier (Geoff.Perrier@johnsonelectric.com)'),
        ],
        label="Quality Engineer",
        widget=forms.Select(attrs={'class': 'form-control'})
    )






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
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Expiry"
    )
    has_process_been_bypassed = forms.ChoiceField(
        choices=[('yes', 'Yes'), ('no', 'No')],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Has any part of the process been bypassed?"
    )
    tpc_current_process = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="TPC Current Process",
        help_text="Describe the Current Process. Please be as descriptive as possible."
    )
    changed = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        label="Changed",
    )
    risk_analysis = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        label="Risk Analysis: To be completed by Quality Engineer",
        help_text="Will the TPC: Require extra inspection? Require inspection frequency change? Effect downstream operations? Customer end use?",
    )




# Special Instructions Form
class SpecialInstructionsForm(forms.Form):
    special_instructions = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label="Special Instructions"
    )