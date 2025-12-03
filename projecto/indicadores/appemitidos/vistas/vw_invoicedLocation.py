from django.shortcuts import render
from ..generalsdata import functions
from ..generalsdata.constants import TYPE_DOCUMENT_CHOICES, GROUPING_TYPE

def consolidado_emitidos_localizacion_load(request):
    context = functions.get_filtros_context()

    typedocuments = [('ALL', 'Todos')] + [choice for choice in TYPE_DOCUMENT_CHOICES if choice[0] in ['FAC', 'NC']]
 
    context = functions.get_filtros_context()

    return render(request, 'appemitidos/invoicedLocation.html', {'years': context["years"], 'months': context["months"], 'groupingtype': GROUPING_TYPE, 'typedocuments': typedocuments})