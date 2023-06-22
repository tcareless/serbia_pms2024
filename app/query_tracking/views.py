from django.shortcuts import render
from .models import QueryLog

# Create your views here.
def recentqueries_view(request):
    return render(request, 'query_tracking/recent.html', 
        {
            'result': QueryLog.objects.order_by("id")[:50],
        })
