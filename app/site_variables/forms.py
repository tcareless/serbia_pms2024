from django import forms
from .models import SiteVariableModel


# creating a form
class SiteVariableForm(forms.ModelForm):

	# create meta class
	class Meta:
		# specify model to be used
		model = SiteVariableModel

		# specify fields to be used
		fields = [
			"variable_name",
			"variable_value",
		]
