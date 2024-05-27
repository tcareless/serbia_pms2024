from django.conf import settings
from importlib import import_module
from django.shortcuts import render
import os

def index(request):
    print("Starting index view...")
    app_infos = []
    for app in settings.INSTALLED_APPS:
        print(f"Checking app: {app}")
        # Skip apps that are not your own
        if app.startswith('django.') or app in ['whitenoise.runserver_nostatic', 'debug_toolbar', 'django_bootstrap5', 'widget_tweaks', 'corsheaders']:
            print(f"Skipping built-in app: {app}")
            continue

        try:
            app_info_module = import_module(f"{app}.app_info")
            print(f"Imported {app}.app_info successfully")
            if hasattr(app_info_module, 'get_app_info'):
                app_info = app_info_module.get_app_info()
                print(f"App info for {app}: {app_info}")
                app_infos.append(app_info)
            else:
                print(f"get_app_info function not found in {app}.app_info")
        except ModuleNotFoundError:
            print(f"ModuleNotFoundError: {app}.app_info not found")
        except AttributeError as e:
            print(f"AttributeError: {e}")

    context = {
        "app_infos": app_infos,
        "title": "App Index",
        "main_heading": "Available Applications"
    }
    print("Finished gathering app info")
    print(f"App infos gathered: {app_infos}")
    return render(request, "index_pms.html", context)
