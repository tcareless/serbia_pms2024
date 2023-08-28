from django.shortcuts import render
from .models import QueryLog

# Create your views here.
def recentqueries_view(request):
    context = {}
    context["title"] = "Prod Query Index - pmsdata12"
    context["main_heading"] = "Prod Query Index"
    context["result"] = QueryLog.objects.order_by("id")[:50]
    return render(request, 'query_tracking/recent.html', context)
