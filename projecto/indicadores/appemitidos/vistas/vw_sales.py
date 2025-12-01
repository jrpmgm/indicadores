from appemitidos.models import Factura, Partner
from django.shortcuts import render
from django.db.models.functions import ExtractMonth, ExtractYear # La forma correcta
from django.db.models import Sum

from django.core.paginator import Paginator

def summarysales(request):
    #year = request.GET.get('year')
    #month = request.GET.get('month')
    years = [2023, 2024, 2025]  # Lista de años disponibles
    year = request.GET.get('year', years[0])  # Por defecto, el
    months = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
        (4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
        (7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
        (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    month = request.GET.get('month', 1)  # Por defecto, el primer
    
    partner_id = request.GET.get('partner')
    
    facturas = Factura.objects.all()
    if year:
        facturas = facturas.annotate(y=ExtractYear('date')).filter(y=year)
    if month:
        facturas = facturas.annotate(m=ExtractMonth('date')).filter(m=month)
    if partner_id:
        facturas = facturas.filter(partner_id=partner_id)

    resumen = facturas.annotate(
        year=ExtractYear('date'),
        month=ExtractMonth('date'),
    ).values('year', 'month', 'partner__name').annotate(
        total=Sum('total'),
        subtotal=Sum('subtotal'),
        iva=Sum('iva'),
    ).order_by('-year', '-month')

    paginator = Paginator(resumen, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    #print(f"Anio: {year}, Mes: {month}, Partner ID: {partner_id}")
    context = {
        'page_obj': page_obj,
        'partners': Partner.objects.all(),
        'years': years,
        'months': months,
    }
    return render(request, 'sales/summarysales.html', context)

def update_filters(request):
    return summarysales(request)
