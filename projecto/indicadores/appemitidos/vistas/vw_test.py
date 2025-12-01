from django.shortcuts import render
from ..models import Factura
from django.http import HttpResponse
# app/views.py
from django.shortcuts import render
from django.http import HttpResponseBadRequest
from ..models import Location
from django.db.models import Sum, F, Value, IntegerField

LEVEL_LABELS = {
    1: "Continente",
    2: "País",
    3: "Región",
    4: "Provincia",
    5: "Ciudad",
    6: "Establecimiento",
}

def children_options(request):
    """
    Devuelve <option> para un select de localidades.
    Parámetros GET:
      - parent_id  -> id del padre (si viene, devuelve hijos directos)
      - level      -> si no viene parent_id, devuelve items con este level
    """
    parent_id = request.GET.get("parent_id") or request.GET.get("parent")
    level = request.GET.get("level")
    try:
        if parent_id:
            children = Location.objects.filter(parent_id=int(parent_id)).order_by("name")
            this_level = None
        elif level:
            this_level = int(level)
            children = Location.objects.filter(level=this_level).order_by("name")
        else:
            this_level = 1
            children = Location.objects.filter(level=1).order_by("name")
    except (ValueError, TypeError):
        return HttpResponseBadRequest("Parámetros inválidos")

    return render(request, "partials/location_options.html", {
        "children": children,
        "level": this_level,
        "labels": LEVEL_LABELS
    })

def test(request, mes):
    """
    Vista para manejar la solicitud AJAX.
    Recupera los detalles del mes especificado.
    """
    try:

        # Filtrar Factura por mes y año del campo 'date'
        consolidacion_obj = Factura.objects.filter(date__month=mes)
        # Recupera las transacciones detalladas
        # Consolidar la información de Factura por año
        consolidado_por_anio = (
            Factura.objects
            .values('date__year')
            .annotate(valor_consolidado=Sum('subtotal'))
            .order_by('date__year')
        )
        #print(consolidado_por_anio)  # Para depuración: muestra la consulta SQL generada
        transacciones_detalle = consolidacion_obj

    except Exception as e:
        return HttpResponse(f"<p>Detalles no encontrados.{e}</p>" , status=404)
        
    # 2. Renderizar solo el fragmento HTML de los detalles
    context = {
        'detalles': transacciones_detalle,
    }
    # Renderiza una plantilla parcial, solo con el contenido de la sub-tabla
    return render(request, 'appemitidos/test.html', context)
