from ..models import Factura, Location # Asegurar importación de Location para claridad
from datetime import datetime
from django.utils.timezone import make_aware
from django.db.models import Q, Sum, Min, Max
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
import json
import logging
logger = logging.getLogger(__name__)

def norm(val):
    return None if val in ("null", "", None, "None") else val

# --- Nueva Función para Fechas ---
def get_date_range(request):
    """
    Retorna la fecha más antigua (Min) y la más reciente (Max) de la tabla Factura.
    """
    range_data = Factura.objects.aggregate(
        min_date=Min("date"),
        max_date=Max("date")
    )
    date_min = range_data.get("min_date")
    date_max = range_data.get("max_date")
    
    return JsonResponse({
        "min_date": date_min.strftime("%Y-%m-%d") if date_min else "", 
        "max_date": date_max.strftime("%Y-%m-%d") if date_max else "",
    })

# --- Dashboard & Filters ---
def sales_dashboard(request):
    # ... (Se mantiene igual) ...
    qs = apply_sales_filters(request)

    # KPIs
    total_ventas = qs.aggregate(Sum("total"))["total__sum"] or 0
    facturas = qs.filter(total__gt=0).count()
    notas = qs.filter(total__lt=0).count()
    partners = qs.values("partner_id").distinct().count()

    # Ventas por mes para gráfico
    ventas_mes = (
        qs.values("date__year", "date__month")
        .annotate(total=Sum("total"))
        .order_by("date__year", "date__month")
    )

    # Top 5 partners
    top_partners = (
        qs.values("partner__name")
        .annotate(total=Sum("total"))
        .order_by("-total")[:10]
    )

    return JsonResponse({
        "total_ventas": total_ventas,
        "facturas": facturas,
        "notas": notas,
        "partners": partners,
        "ventas_mes": list(ventas_mes),
        "top_partners": list(top_partners),
    })

def apply_sales_filters(request):
    
    qs = Factura.objects.select_related("partner", "location")

    # Filtros básicos (Se mantienen igual)
    date_from = norm(request.GET.get("date_from"))
    date_to = norm(request.GET.get("date_to"))
    type_doc = norm(request.GET.get("type_doc")) or "ALL"
    partner_id = norm(request.GET.get("partner_id")) or "ALL"

    continent = norm(request.GET.get("continent")) or "ALL"
    country = norm(request.GET.get("country")) or "ALL"
    region = norm(request.GET.get("region")) or "ALL"
    province = norm(request.GET.get("province")) or "ALL"
    city = norm(request.GET.get("city")) or "ALL"
    establishment = norm(request.GET.get("establishment")) or "ALL"
    point = norm(request.GET.get("point")) or "ALL"

    # --- Fechas ---
    if date_from:
        dt_from = make_aware(datetime.strptime(date_from, "%Y-%m-%d"))
        qs = qs.filter(date__gte=dt_from)

    if date_to:
        dt_to = make_aware(datetime.strptime(date_to, "%Y-%m-%d"))
        qs = qs.filter(date__lte=dt_to)

    # --- Tipo de documento y Partner ---
    if type_doc == "FAC":
        qs = qs.filter(total__gt=0)
    elif type_doc == "NC":
        qs = qs.filter(total__lt=0)

    if partner_id != "ALL":
        qs = qs.filter(partner_id=partner_id)

    # --- Localización jerárquica CORREGIDA (Aplica el filtro más específico) ---
    applied_location_filter = None
    applied_location_id = None

    location_filters = [
        ("point", point, 7),
        ("establishment", establishment, 6),
        ("city", city, 5),
        ("province", province, 4),
        ("region", region, 3),
        ("country", country, 2),
        ("continent", continent, 1),
    ]

    for name, value, level in location_filters:
        if value != "ALL":
            applied_location_filter = name
            applied_location_id = value
            break 

    if applied_location_filter and applied_location_id != "ALL":
        # Mapeo de __parent necesarios (Nivel 7 - Nivel Aplicado)
        level_map = {
            "point": 0, "establishment": 1, "city": 2, "province": 3,
            "region": 4, "country": 5, "continent": 6
        }
        
        num_parents = level_map.get(applied_location_filter, 0)
        
        if num_parents == 0:
            qs = qs.filter(location_id=applied_location_id)
        else:
            parent_lookup = "__parent" * num_parents
            lookup_field = f"location{parent_lookup}__id"
            qs = qs.filter(**{lookup_field: applied_location_id})

    return qs

def datatables_sales(request):
    try:
        draw = int(request.GET.get("draw", 1))
        start = int(request.GET.get("start", 0))
        length = int(request.GET.get("length", 10))

        # --- 1. Obtener QS y aplicar filtros (SIN AGREGACIONES AÚN) ---
        qs = apply_sales_filters(request)
        
        # --- 2. Búsqueda global DataTables ---
        search_value = (request.GET.get("search[value]", "") or "").strip()
        if search_value:
            qs = qs.filter(
                Q(number__icontains=search_value) |
                Q(identification__icontains=search_value) |
                Q(partner__name__icontains=search_value)
            )

        # --- 3. Ordenamiento ---
        order_column_index = request.GET.get("order[0][column]", "0")
        order_dir = request.GET.get("order[0][dir]", "asc")

        column_map = {
            "0": "date", "1": "number", "2": "identification",
            "3": "partner__name", "4": "location__code_segment", "5": "total",
        }
        order_field = column_map.get(order_column_index, "date")
        if order_dir == "desc":
            order_field = "-" + order_field

        # 4. Paginación y obtención de datos (PRIORIZANDO LA VELOCIDAD)
        # Obtenemos solo los N registros de la página antes de contar
        page_qs = qs.order_by(order_field, 'pk')[start:start + length]
        
        # 5. CONTEO (EJECUTADO DESPUÉS DE OBTENER LOS DATOS DE LA PÁGINA)
        # ESTE PUNTO SIGUE SIENDO EL MÁS LENTO, pero es necesario.
        # Podríamos mover el cálculo del total sumado después del conteo también.
        
        # El .count() se ejecuta con la misma Query, lo que puede ser lento.
        total_filtered = qs.count() 
        
        # Suma Total (También costoso, pero necesario para el footer)
        totals = qs.aggregate(total_sum=Sum("total"))
        total_sum = totals.get("total_sum") or 0


        data = []
        for obj in page_qs:
            # ... (Lógica de llenado de 'data' se mantiene) ...
            data.append([
                obj.date.strftime("%d/%m/%Y"),
                obj.identification,
                obj.partner.name if obj.partner else "",
                obj.number,
                obj.location.code_segment if obj.location else "",
                float(obj.subtotal or 0),
                float(obj.iva or 0),
                float(obj.total or 0),
            ])

        # 6. Respuesta Final
        return JsonResponse({
            "draw": draw,
            "recordsTotal": total_filtered, 
            "recordsFiltered": total_filtered,
            "data": data,
            "totals": {"total_sum": total_sum},
        })

    except Exception as e:
        logger.error(f"FALLO DE TIMEOUT/DB EN DATATABLES: {e}", exc_info=True)
        
        return JsonResponse({
            "draw": int(request.GET.get("draw", 1)),
            "recordsTotal": 0, 
            "recordsFiltered": 0,
            "data": [],
            "error": "Error interno: la consulta excedió el tiempo límite."
        })