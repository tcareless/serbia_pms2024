"""pms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.views import LogoutView

from pms.views import pms_index_view, login_view

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('dashboard/',include('dashboards.urls')),
    # path('barcode/',include('barcode.urls')),
    # path('prod-query/',include('prod_query.urls')),
    # path('query-time/',include('query_tracking.urls')),
    path('admin/', admin.site.urls),
    path('__debug__/', include('debug_toolbar.urls')),
    path('index/', pms_index_view, name='pms_index'),
    path('', pms_index_view, name='pms_index'),
    # path('quality/', include('quality.urls')),
    # path('plant/', include('plant.urls')),
    path('forms/', include('serbia_forms.urls')),

    # Custom login URL
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),

]



if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
