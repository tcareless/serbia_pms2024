from django.shortcuts import render
from .models import QueryLog
import time

def recentqueries_view(request):
    tic = time.time()
    return render(request, 'query_tracking/recent.html', 
        {
            'result': QueryLog.objects.order_by("-id")[:50],
            'time': f'Elapsed: {time.time()-tic:.3f} seconds'
        })
