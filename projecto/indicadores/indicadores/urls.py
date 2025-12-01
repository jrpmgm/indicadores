"""
URL configuration for indicadores project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.http import HttpResponse
#from projecto.indicadores.appemitidos import vistas as vw_app_views
from appemitidos.vistas import vw_app_views

def home(request):
    return HttpResponse("Bienvenido a la página principal")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', vw_app_views.home, name='home'),
    path('', include('appemitidos.urls')),
]