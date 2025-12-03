from django.db.models import Sum, Case, When, IntegerField
from django.http import JsonResponse
from django.db.models.functions import ExtractYear, ExtractMonth
from ..models import Factura, Location  # ajusta el import a tu app real
from ..generalsdata import functions
import calendar

def invoiced_by_location(pyears, pmonths, pgrouptype, ptypedocument, locationFilters):
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
    if ptypedocument == 'FAC':
        base_query = base_query.filter(subtotal__gt=0)
    elif ptypedocument == 'NC':
        base_query = base_query.filter(subtotal__lt=0)
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

def _format_period_for_output(pgrouptype, year, month_or_bucket=None):
    """
    Formatea legiblemente el periodo según tipo de agrupación.
    - mensual: month_or_bucket = month (1..12) -> "Marzo 2025"
    - trimestral: month_or_bucket = quarter (1..4) -> "Q1 2025" (o "T1 2025")
    - semestral: month_or_bucket = semester (1..2) -> "1° Semestre 2025"
    - anual: month_or_bucket ignored -> "2025"
    """
    gt = pgrouptype.lower().strip()
    if gt == "mensual":
        if not month_or_bucket:
            return str(year)
        nombre = calendar.month_name[int(month_or_bucket)]
        return f"{nombre}"
    if gt == "trimestral":
        return f"{int(month_or_bucket)}° Trimestre"
    if gt == "semestral":
        return f"{int(month_or_bucket)}° Semestre"
    if gt == "anual":
        return str(year)
    return str(year)


def invoiced_location_details_by_id(request, level, locId, pyears, pmonths, pgrouptype, ptypedocument):
    """
    Devuelve detalles facturación para la localización (id) agrupados por pgrouptype.
    pgrouptype: 'Mensual','Trimestral','Semestral','Anual' (cualquier case).
    """

    # 1) nodo
    try:
        node = Location.objects.get(id=locId)
    except Location.DoesNotExist:
        return JsonResponse({"error": "Location not found"}, status=404)

    # 2) descendientes
    descendants = Location.objects.filter(path__startswith=node.path)

    # 3) filtros (tu función obtain_filters)
    filtros = functions.obtain_filters(None, pyears, pmonths)

    # 4) preparar queryset base
    qs = Factura.objects.filter(location__in=descendants, **filtros)

    if ptypedocument == 'FAC':
        qs = qs.filter(subtotal__gt=0)
    elif ptypedocument == 'NC':
        qs = qs.filter(subtotal__lt=0)

    # 5) según tipo de agrupación agregar anotaciones y agrupar
    pg = (pgrouptype or "").lower().strip()
    results = None

    if pg == "mensual":
        # agregar year y month, agrupar por ambos
        qs = qs.annotate(month=ExtractMonth("date"))
        results = (
            qs.values("month")
              .annotate(subtotal=Sum("subtotal"), iva=Sum("iva"), total=Sum("total"))
              .order_by("month")
        )

    elif pg == "trimestral":
        # calcular trimestre a partir del mes
        qs = qs.annotate(month=ExtractMonth("date"))
        quarter_case = Case(
            When(month__in=[1,2,3], then=1),
            When(month__in=[4,5,6], then=2),
            When(month__in=[7,8,9], then=3),
            When(month__in=[10,11,12], then=4),
            output_field=IntegerField(),
        )
        qs = qs.annotate(quarter=quarter_case)
        results = (
            qs.values("quarter")
              .annotate(subtotal=Sum("subtotal"), iva=Sum("iva"), total=Sum("total"))
              .order_by("quarter")
        )

    elif pg == "semestral":
        # semestre 1: meses 1-6, semestre 2: meses 7-12
        qs = qs.annotate(month=ExtractMonth("date"))
        sem_case = Case(
            When(month__in=[1,2,3,4,5,6], then=1),
            When(month__in=[7,8,9,10,11,12], then=2),
            output_field=IntegerField(),
        )
        qs = qs.annotate(semester=sem_case)
        results = (
            qs.values("semester")
              .annotate(subtotal=Sum("subtotal"), iva=Sum("iva"), total=Sum("total"))
              .order_by("semester")
        )

    elif pg == "anual" or pg == "año":
        qs = qs.annotate(year=ExtractYear("date"))
        results = (
            qs.values("year")
              .annotate(subtotal=Sum("subtotal"), iva=Sum("iva"), total=Sum("total"))
              .order_by("year")
        )

    else:
        return JsonResponse({"error": f"Tipo de agrupación inválido: {pgrouptype}"}, status=400)

    # 6) formatear resultados y totales
    detalles = []
    for row in results:
        year = row.get("year")
        if pg == "mensual":
            bucket = row.get("month")
        elif pg == "trimestral":
            bucket = row.get("quarter")
        elif pg == "semestral":
            bucket = row.get("semester")
        else:  # anual
            bucket = None

        periodo_text = _format_period_for_output(pgrouptype, year, bucket)
        detalles.append({
            "periodo": periodo_text,
            "subtotal": float(row.get("subtotal") or 0),
            "iva": float(row.get("iva") or 0),
            "total": float(row.get("total") or 0),
        })

    totals = {
        "subtotal": sum(d["subtotal"] for d in detalles),
        "iva": sum(d["iva"] for d in detalles),
        "total": sum(d["total"] for d in detalles),
    }

    return JsonResponse({
        "level": level,
        "location": node.name,
        "tipo_agrupacion": pgrouptype,
        "detalles": detalles,
        "totales": totals,
    })

def consolidado_emitidos_localizacion_data(request, pyears, pmonths, pgrouptype, ptypedocument):
    
    locationFilters = functions.get_only_location(request)

    datos = invoiced_by_location(pyears, pmonths, pgrouptype, ptypedocument, locationFilters)

    return JsonResponse({"resultados": datos})