from django.conf import settings
from importlib import import_module
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import HttpRequest, HttpResponse

def login_view(request: HttpRequest) -> HttpResponse:
    """
    Custom login view that uses the CustomLDAPBackend for authentication.

    Args:
        request: The HTTP request object.

    Returns:
        HTTP Response: Renders the login page or redirects on successful login.
    """
    if request.method == 'POST':
        # Get the username and password from the form
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user using Django's authenticate function
        user = authenticate(request, username=username, password=password)

        if user:
            # If authentication succeeds, log the user in and redirect
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect('pms_index')  # Redirect to the index page
        else:
            # If authentication fails, display an error message
            messages.error(request, "Invalid username or password. Please try again.")

    # Render the login page with any messages
    return render(request, 'login.html')



def pms_index_view(request):
    context = {}
    context["main_heading"] = "PMDSData12 Index"
    context["title"] = "Index - pmdsdata12"
    
    app_infos = []
    for app in settings.INSTALLED_APPS:
        if app.startswith('django.') or app in ['whitenoise.runserver_nostatic', 'debug_toolbar', 'django_bootstrap5', 'widget_tweaks', 'corsheaders']:
            continue

        try:
            app_info_module = import_module(f"{app}.app_info")
            if hasattr(app_info_module, 'get_app_info'):
                app_info = app_info_module.get_app_info()
                app_infos.append(app_info)
        except ModuleNotFoundError:
            pass
        except AttributeError as e:
            pass

    context["app_infos"] = app_infos
    
    return render(request, 'index_pms.html', context)


