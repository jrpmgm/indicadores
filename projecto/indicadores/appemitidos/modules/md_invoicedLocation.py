from django.db.models import Sum, F
from django.http import JsonResponse
from django.db.models.functions import ExtractYear
from ..models import Factura, Location  # ajusta el import a tu app real
from ..generalsdata import functions
#import calendar

def invoiced_by_location(pyears, pmonths, pgrouptype, locationFilters):
    """
    Devuelve un resumen consolidado de facturas agrupado por jerarquía de localización.
    """
    filtros = {}

    # === Filtros de año y mes ===
    if pyears:
        years = [int(y) for y in str(pyears).split(',') if y.strip()]
        filtros['date__year__in'] = years
    if pmonths:
        months = [int(m) for m in str(pmonths).split(',') if m.strip()]
        filtros['date__month__in'] = months

    # === Filtros de jerarquía de localización ===
    location_filters_dict = {}

    if locationFilters.get("continent"):
        location_filters_dict["parent__parent__parent__parent__parent__parent"] = locationFilters["continent"]
    if locationFilters.get("country"):
        location_filters_dict["parent__parent__parent__parent__parent"] = locationFilters["country"]
    if locationFilters.get("region"):
        location_filters_dict["parent__parent__parent__parent"] = locationFilters["region"]
    if locationFilters.get("province"):
        location_filters_dict["parent__parent__parent"] = locationFilters["province"]
    if locationFilters.get("city"):
        location_filters_dict["parent__parent"] = locationFilters["city"]
    if locationFilters.get("establishment"):
        location_filters_dict["parent"] = locationFilters["establishment"]
    if locationFilters.get("point"):
        location_filters_dict["id"] = locationFilters["point"]

    # IDs válidos
    if location_filters_dict:
        valid_location_ids = Location.objects.filter(**location_filters_dict).values_list('id', flat=True)
        if valid_location_ids:
            filtros['location_id__in'] = valid_location_ids
            
    base_query = Factura.objects.filter(**filtros)
    print("Filtros aplicados:", filtros)
    # === Agrupar ===
    datos = (
        base_query
        .values(
            'location__parent__parent__parent__parent__parent__parent__name',   # Continente
            'location__parent__parent__parent__parent__parent__parent__id',     # Continente Id
            'location__parent__parent__parent__parent__parent__name',           # País
            'location__parent__parent__parent__parent__parent__id',             # País Id
            'location__parent__parent__parent__parent__name',                   # Región
            'location__parent__parent__parent__parent__id',                     # Región Id
            'location__parent__parent__parent__name',                           # Provincia
            'location__parent__parent__parent__id',                             # Provincia Id
            'location__parent__parent__name',                                   # Ciudad
            'location__parent__parent__id',                                     # Ciudad Id
            'location__parent__name',                                           # Establecimiento
            'location__parent__id',                                             # Establecimiento Id
            'location__name',                                                   # Usuario
            'location__id',                                                     # Usuario Id
        )
        .annotate(
            subtotal=Sum('subtotal'),
            iva=Sum('iva'),
            total=Sum('total')
        )
        .order_by(
            'location__parent__parent__parent__parent__parent__parent__name',
            'location__parent__parent__parent__parent__parent__name',
            'location__parent__parent__parent__parent__name',
            'location__parent__parent__parent__name',
            'location__parent__parent__name',
            'location__parent__name',
            'location__name',
        )
    )

    return list(datos)

def location_details(request, level, value):
    # El fullpath es opcional si quieres validar jerarquía exacta
    fullpath = request.GET.get("path", "")

    # Mapa dinámico según el nivel
    level_filters = {
        "continent": {"location__parent__parent__parent__parent__parent__parent__name": value},
        "country":   {"location__parent__parent__parent__parent__parent__name": value},
        "region":    {"location__parent__parent__parent__parent__name": value},
        "province":  {"location__parent__parent__parent__name": value},
        "city":      {"location__parent__parent__name": value},
        "establishment": {"location__parent__name": value},
        "point":     {"location__name": value},
    }
    if level not in level_filters:
        return JsonResponse({"error": "Nivel no válido"}, status=400)

    filtros = level_filters[level]

    datos = (
        Factura.objects
        .filter(**filtros)
        .annotate(year=ExtractYear("date"))
        .values("year")
        .annotate(
            subtotal=Sum("subtotal"),
            iva=Sum("iva"),
            total=Sum("total")
        )
        .order_by("year")
    )

    return JsonResponse({"resultados": list(datos)})

def invoiced_location_details_by_id(request, level, locId, pyears, pmonths):
    
    # 1️⃣ Buscar el nodo seleccionado
    try:
        node = Location.objects.get(id=locId)
    except Location.DoesNotExist:
        return JsonResponse({"error": "Location not found"}, status=404)

    # 2️⃣ Obtener TODOS los descendientes del nodo (de cualquier nivel)
    #    Esto permite que al consultar un país se sumen Costa, Sierra, ciudades, establecimientos, etc.
    descendants = Location.objects.filter(path__startswith=node.path)

    # 3️⃣ Obtener los totales agrupados por NOMBRE DE LOCALIZACIÓN
    filtros = functions.obtain_filters(None, pyears, pmonths)

    data = (
        Factura.objects.filter(location__in=descendants, **filtros)
        .annotate(year=ExtractYear('date'))
        .values("year")
        .annotate(
            subtotal=Sum("subtotal"),
            iva=Sum("iva"),
            total=Sum("total")
        )
        .order_by("year")
    )

    # 4️⃣ Calcular totales generales
    totals = {
        "subtotal": sum((item["subtotal"] or 0) for item in data),
        "iva": sum((item["iva"] or 0) for item in data),
        "total": sum((item["total"] or 0) for item in data),
    }

    return JsonResponse({
        "level": level,
        "location": node.name,
        "detalles": list(data),
        "totales": totals
    })

def consolidado_emitidos_localizacion_data(request, pyears, pmonths, pgrouptype):
    
    continente = request.GET.get('continents')
    pais = request.GET.get('countries')
    region = request.GET.get('regions')
    provincia = request.GET.get('provinces')
    ciudad = request.GET.get('cities')
    establecimiento = request.GET.get('establishments')
    punto = request.GET.get('points')

    locationFilters = {
        "continent": int(continente) if continente else None,
        "country": int(pais) if pais else None,
        "region": int(region) if region else None,
        "province": int(provincia) if provincia else None,
        "city": int(ciudad) if ciudad else None,
        "establishment": int(establecimiento) if establecimiento else None,
        "point": int(punto) if punto else None,
    }

    datos = invoiced_by_location(pyears, pmonths, pgrouptype, locationFilters)

    return JsonResponse({"resultados": datos})