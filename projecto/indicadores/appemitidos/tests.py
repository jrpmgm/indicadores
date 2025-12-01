# app/views.py
from django.shortcuts import render
from django.http import HttpResponse
from .models import Factura

def test(request, mes):
    """
    Vista para manejar la solicitud AJAX.
    Recupera los detalles del mes especificado.
    """
    try:

        # Filtrar Factura por mes y año del campo 'date'
        consolidacion_obj = Factura.objects.filter(date__month=mes).first()
        if not consolidacion_obj:
            return HttpResponse("<p>No se encontró información para ese mes.</p>", status=404)
        
        # Recupera las transacciones detalladas
        transacciones_detalle = Factura.objects.filter(date__year=consolidacion_obj.date.year).order_by('id')
        
    except transacciones_detalle.DoesNotExist:
        return HttpResponse("<p>Detalles no encontrados.</p>", status=404)
        
    # 2. Renderizar solo el fragmento HTML de los detalles
    context = {
        'detalles': transacciones_detalle,
    }
    # Renderiza una plantilla parcial, solo con el contenido de la sub-tabla
    return render(request, 'test.html', context)