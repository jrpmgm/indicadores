# appemitidos/vistas/vw_sales.py

from django.shortcuts import render
from ..generalsdata import functions
from ..generalsdata.constants import TYPE_DOCUMENT_CHOICES, GROUPING_TYPE
from ..models import Factura  # 👈 importar Factura


def sales(request):
    typedocuments = [('ALL', 'Todos')] + [
        choice for choice in TYPE_DOCUMENT_CHOICES if choice[0] in ['FAC', 'NC']
    ]

    # Filtros genéricos que ya tenías
    context = functions.get_filtros_context()

    # Determinar último mes/año disponible en la BD
    last_invoice = Factura.objects.order_by("-date").first()
    default_year = last_invoice.date.year if last_invoice else None
    default_month = last_invoice.date.month if last_invoice else None

    return render(request, 'appemitidos/sales.html', {
        'years': context["years"],
        'months': context["months"],
        'groupingtype': GROUPING_TYPE,
        'typedocuments': typedocuments,
        'default_year': default_year,
        'default_month': default_month,
    })


def update_filters(request):
    return sales(request)
