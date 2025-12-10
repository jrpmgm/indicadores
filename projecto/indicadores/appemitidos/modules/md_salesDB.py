from ..models import Factura
from datetime import datetime
from django.utils.timezone import make_aware
from django.db.models import Q, Sum
from django.http import JsonResponse

def norm(val):
    return None if val in ("null", "", None, "None") else val

def sales_dashboard(request):
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
        .order_by("-total")[:5]
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
    
    """ Aplica TODOS los filtros comunes:
      - date_from / date_to
      - type_doc (ALL, FAC, NC)
      - partner_id
      - localización jerárquica (continent, country, region, province, city, establishment, point)
    Asumiendo que Factura.location SIEMPRE apunta a un Location de level=7 (Punto).
    """
    qs = Factura.objects.select_related("partner", "location")

    # Filtros básicos
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

    # --- Fechas (timezone-aware) ---
    if date_from:
        dt_from = make_aware(datetime.strptime(date_from, "%Y-%m-%d"))
        qs = qs.filter(date__gte=dt_from)

    if date_to:
        dt_to = make_aware(datetime.strptime(date_to, "%Y-%m-%d"))
        qs = qs.filter(date__lte=dt_to)

    # --- Tipo de documento ---
    # ALL -> no filtra
    if type_doc == "FAC":
        qs = qs.filter(total__gt=0)
    elif type_doc == "NC":
        qs = qs.filter(total__lt=0)

    # --- Partner ---
    if partner_id != "ALL":
        qs = qs.filter(partner_id=partner_id)

    # --- Localización jerárquica ---
    # Recordatorio:
    # Factura.location -> level 7 (Punto)
    # Punto (7) -> parent (6) -> parent (5) -> parent (4) -> parent (3) -> parent (2) -> parent (1)
    # Entonces:
    #   continent id = location.parent^6.id
    #   country   id = location.parent^5.id
    #   region    id = location.parent^4.id
    #   province  id = location.parent^3.id
    #   city      id = location.parent^2.id
    #   establish id = location.parent.id
    #   point     id = location.id

    if continent != "ALL":
        qs = qs.filter(location__parent__parent__parent__parent__parent__parent_id=continent)

    if country != "ALL":
        qs = qs.filter(location__parent__parent__parent__parent__parent_id=country)

    if region != "ALL":
        qs = qs.filter(location__parent__parent__parent__parent_id=region)

    if province != "ALL":
        qs = qs.filter(location__parent__parent__parent_id=province)

    if city != "ALL":
        qs = qs.filter(location__parent__parent_id=city)

    if establishment != "ALL":
        qs = qs.filter(location__parent_id=establishment)

    if point != "ALL":
        qs = qs.filter(location_id=point)

    return qs

def datatables_sales(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    # Query base con filtros reutilizables
    qs = apply_sales_filters(request)

    # 🔍 Búsqueda global DataTables
    search_value = (request.GET.get("search[value]", "") or "").strip()
    if search_value:
        qs = qs.filter(
            Q(number__icontains=search_value) |
            Q(identification__icontains=search_value) |
            Q(partner__name__icontains=search_value)
        )

    # Totales globales filtrados
    total_filtered = qs.count()
    totals = qs.aggregate(total_sum=Sum("total"))
    total_sum = totals.get("total_sum") or 0

    # Ordenamiento DataTables
    order_column_index = request.GET.get("order[0][column]", "0")
    order_dir = request.GET.get("order[0][dir]", "asc")

    column_map = {
        "0": "date",
        "1": "number",
        "2": "identification",
        "3": "partner__name",
        "4": "location__code_segment",
        "5": "total",
    }

    order_field = column_map.get(order_column_index, "date")
    if order_dir == "desc":
        order_field = "-" + order_field

    # Paginación
    page_qs = qs.order_by(order_field)[start:start + length]

    data = [
        [
            obj.date.strftime("%d/%m/%Y"),
            obj.number,
            obj.identification,
            obj.partner.name if obj.partner else "",
            obj.location.code_segment if obj.location else "",
            float(obj.total or 0),
        ]
        for obj in page_qs
    ]

    return JsonResponse({
        "draw": draw,
        "recordsTotal": Factura.objects.count(),
        "recordsFiltered": total_filtered,
        "data": data,
        "totals": {"total_sum": total_sum},
    })
