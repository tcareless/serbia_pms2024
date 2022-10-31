from django.shortcuts import render

from prod_query.forms import ShiftLineForm

def shift_line(request):
	if request.method == 'GET':
		form = ShiftLineForm()


	context = {
		'form': form,
	}

	return render(request, 'prod_query/prod_query.html')
