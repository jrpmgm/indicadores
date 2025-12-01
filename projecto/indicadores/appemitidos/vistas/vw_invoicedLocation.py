from django.shortcuts import render
from ..generalsdata import functions

def consolidado_emitidos_localizacion_load(request):
    context = functions.get_filtros_context()
    return render(request, 'appemitidos/invoicedLocation.html', context)