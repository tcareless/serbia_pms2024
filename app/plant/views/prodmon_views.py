from django.shortcuts import render

def prodmon_ping(request):
    """
    View to handle prodmon_ping requests.
    Renders an HTML template to verify server status.
    """
    return render(request, 'prodmon_ping.html')
