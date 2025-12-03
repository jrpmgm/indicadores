from django.http import JsonResponse
from django.shortcuts import render
from ..models import Factura, Location
from appemitidos.generalsdata.constants import TYPE_DOCUMENT_CHOICES, GROUPING_TYPE
import calendar
import json
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractQuarter, ExtractDay
from django.db.models import Case, Sum, When, Value, IntegerField
from ..generalsdata import functions

TYPEGRAPH =   {'bar': 'bar','barH': 'barH', 'line': 'line', 'pie':'pie','doughnut':'doughnut','polarArea': 'polarArea'}  # Cambia esto a 'line' si prefieres un gráfico de líneas

def load_location(request, level, parent_id):
    if (parent_id == "-1" or parent_id == "undefined" or parent_id == "null"):
        locations = Location.objects.filter(level=level).values_list('id', 'name').distinct()
    else:
        locations = Location.objects.filter(level=level, parent_id=int(parent_id)).values_list('id', 'name').distinct()
    return JsonResponse(list(locations), safe=False)

def invoiced_local(request, pyears, pmonths, pgrouptype, ptypedocument, locationFilters):

    # ✅ Validar el parámetro de agrupación
    if pgrouptype not in ['Mensual', 'Trimestral', 'Semestral', 'Anual']:
        raise ValueError("El parámetro groupingtype debe ser 'Mensual', 'Trimestral', 'Semestral' o 'Anual'.")
    
    filtros = functions.obtain_filters(request, pyears, pmonths)

    # ------------------ CONSULTA BASE ------------------
    base_query = Factura.objects.filter(**filtros).filter(type_doc__in=['FAC', 'NC'])
    if ptypedocument == 'FAC':
        base_query = base_query.filter(subtotal__gt=0)
    elif ptypedocument == 'NC':
        base_query = base_query.filter(subtotal__lt=0)

    # ------------------ AGRUPACIÓN SEGÚN TIPO ------------------
    if pgrouptype == 'Mensual':
        datos = (
            base_query
            .annotate(
                month=ExtractMonth('date')
            )
            .values('month')
            .annotate(
                subtotal=Sum('subtotal'),
                iva=Sum('iva'),
                total=Sum('total')
            )
            .order_by('month')
        )

        # Formatear salida
        datos_list = [
            {
                'periodo': f"{calendar.month_name[d['month']]}",
                'month': d['month'],
                'subtotal': d['subtotal'],
                'iva': d['iva'],
                'total': d['total'],
            }
            for d in datos
        ]

    elif pgrouptype == 'Trimestral':
        datos = (
            base_query
            .annotate(
                quarter=ExtractQuarter('date')
            )
            .values('quarter')
            .annotate(
                subtotal=Sum('subtotal'),
                iva=Sum('iva'),
                total=Sum('total')
            )
            .order_by('quarter')
        )

        datos_list = [
            {
                'periodo': f"Trimestre {d['quarter']}",
                'quarter': d['quarter'],
                'subtotal': d['subtotal'],
                'iva': d['iva'],
                'total': d['total'],
            }
            for d in datos
        ]

    elif pgrouptype == 'Semestral':
        datos = (
            base_query
            .annotate(
                year=ExtractYear('date'),
                semester=Case(
                    When(date__month__lte=6, then=Value(1)),
                    When(date__month__gte=7, then=Value(2)),
                    output_field=IntegerField(),
                )
            )
            .values('semester')
            .annotate(
                subtotal=Sum('subtotal'),
                iva=Sum('iva'),
                total=Sum('total')
            )
            .order_by('semester')
        )

        datos_list = [
            {
                'periodo': f"Semestre {d['semester']}",
                'semester': d['semester'],
                'subtotal': d['subtotal'],
                'iva': d['iva'],
                'total': d['total'],
            }
            for d in datos
        ]

    elif pgrouptype == 'Anual':
        datos = (
            base_query
            .annotate(year=ExtractYear('date'))
            .values('year')
            .annotate(
                subtotal=Sum('subtotal'),
                iva=Sum('iva'),
                total=Sum('total')
            )
            .order_by('year')
        )

        datos_list = [
            {
                'periodo': f"{d['year']}",
                'year': d['year'],
                'subtotal': d['subtotal'],
                'iva': d['iva'],
                'total': d['total'],
            }
            for d in datos
        ]

    # ------------------ CÁLCULO DE PERIODO ANTERIOR ------------------
    for i, d in enumerate(datos_list):
        d['periodoanterior'] = datos_list[i - 1]['subtotal'] if i > 0 else None

    return datos_list

def consolidado_emitidos(request, pyears, pmonths, pgrouptype, ptypedocument):
    """ continente = request.GET.get('continents')
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
    } """

    locationFilters = functions.get_only_location(request)
    
    datos = invoiced_local(request, pyears, pmonths, pgrouptype, ptypedocument, locationFilters)
    return JsonResponse({'resultados': list(datos)})

def consolidado_emitidos_filtrado(request, pyears, pmonths, pgrouptype, param_filter, ptypedocument):
   
    filters = functions.obtain_filters(request, pyears, pmonths)
    label_param_filter = ""
    match pgrouptype:
        case 'Anual':
            datos = invoiced_by_year_month(filters, param_filter, ptypedocument)
            label_param_filter = param_filter
        case 'Mensual':
            datos = invoiced_by_month_year(filters, param_filter, ptypedocument)
            # devolver nombre del mes en español
            try:
                month_idx = int(param_filter)
                months_es = [None, 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
                label_param_filter = months_es[month_idx] if 1 <= month_idx <= 12 else str(param_filter)
            except (TypeError, ValueError):
                label_param_filter = str(param_filter)
        case 'Trimestral':
            datos = invoiced_by_quarter_year(filters, param_filter, ptypedocument)
            label_param_filter = f"Trimestre {param_filter}"
        case 'Semestral':
            datos = invoiced_by_semester_year(filters, param_filter, ptypedocument)
            label_param_filter = f"Semestre {param_filter}"
    # Filtrar por mes si se proporcionó un parámetro válido y la agrupación es Mensual
    data = {
        "month_name": label_param_filter,
        "details": list(datos)
    }

    return JsonResponse(data)

def api_invoiced(request):

    typedocuments = [('ALL', 'Todos')] + [choice for choice in TYPE_DOCUMENT_CHOICES if choice[0] in ['FAC', 'NC']]
 
    context = functions.get_filtros_context()
    return render(request, 'appemitidos/invoiced.html', {'years': context["years"], 'months': context["months"], 'typegraph': TYPEGRAPH, 'groupingtype': GROUPING_TYPE, 'typedocuments': typedocuments})

def invoiced_by_year_month(filters, year=None, ptypedocument=None):
    """
    Retorna los detalles (por año) de un mes seleccionado.
    Ejemplo: Enero → {2015: ..., 2016: ...}
    """

    if not year:
        return JsonResponse({"error": "Falta el parámetro 'month'."}, status=400)

    try:
        year = int(year)
    except ValueError:
        return JsonResponse({"error": "El parámetro 'month' debe ser numérico."}, status=400)

    # Puedes agregar filtros adicionales (años seleccionados, ubicaciones, etc.)
    if ptypedocument == 'FAC':
        datos = Factura.objects.filter(subtotal__gt=0)
    elif ptypedocument == 'NC':
        datos = Factura.objects.filter(subtotal__lt=0)
    else:
        datos = Factura.objects.all()

    datos = (
        datos
        .filter(**filters, date__year=year)
        .annotate(month=ExtractMonth("date"))
        .values("month")
        .annotate(
            subtotal=Sum("subtotal"),
            iva=Sum("iva"),
            total=Sum("total")
        )
        .order_by("month")
    )
    
    return datos

def invoiced_by_month_year(filters, month=None, ptypedocument=None):
    """
    Retorna los detalles (por año) de un mes seleccionado.
    Ejemplo: Enero → {2015: ..., 2016: ...}
    """
    
    if not month:
        return JsonResponse({"error": "Falta el parámetro 'month'."}, status=400)

    try:
        month = int(month)
    except ValueError:
        return JsonResponse({"error": "El parámetro 'month' debe ser numérico."}, status=400)

    # Puedes agregar filtros adicionales (años seleccionados, ubicaciones, etc.)
    if ptypedocument == 'FAC':
        datos = Factura.objects.filter(subtotal__gt=0)
    elif ptypedocument == 'NC':
        datos = Factura.objects.filter(subtotal__lt=0)
    else:
        datos = Factura.objects.all()

    datos = (
        datos
        .filter(**filters, date__month=month)
        .annotate(year=ExtractYear("date"))
        .values("year")
        .annotate(
            subtotal=Sum("subtotal"),
            iva=Sum("iva"),
            total=Sum("total")
        )
        .order_by("year")
    )
 
    return datos

def invoiced_by_quarter_year(filters, quarter=None, ptypedocument=None):
    """
    Retorna los detalles (por año) de un mes seleccionado.
    Ejemplo: Enero → {2015: ..., 2016: ...}
    """
    
    if not quarter:
        return JsonResponse({"error": "Falta el parámetro 'quarter'."}, status=400)

    try:
        quarter = int(quarter)
    except ValueError:
        return JsonResponse({"error": "El parámetro 'month' debe ser numérico."}, status=400)

    # Puedes agregar filtros adicionales (años seleccionados, ubicaciones, etc.)
    if ptypedocument == 'FAC':
        datos = Factura.objects.filter(subtotal__gt=0)
    elif ptypedocument == 'NC':
        datos = Factura.objects.filter(subtotal__lt=0)
    else:
        datos = Factura.objects.all()

    datos = (
        datos
        .filter(**filters, date__quarter=quarter)
        .annotate(year=ExtractYear("date"))
        .values("year")
        .annotate(
            subtotal=Sum("subtotal"),
            iva=Sum("iva"),
            total=Sum("total")
        )
        .order_by("year")
    )

    return datos

def invoiced_by_semester_year(filters, semester=None, ptypedocument=None):
    """
    Retorna los detalles (por año) de un mes seleccionado.
    Ejemplo: Enero → {2015: ..., 2016: ...}
    """
    
    if not semester:
        return JsonResponse({"error": "Falta el parámetro 'semester'."}, status=400)

    try:
        semester = int(semester)
    except ValueError:
        return JsonResponse({"error": "El parámetro 'month' debe ser numérico."}, status=400)

    # Puedes agregar filtros adicionales (años seleccionados, ubicaciones, etc.)
    if ptypedocument == 'FAC':
        datos = Factura.objects.filter(subtotal__gt=0)
    elif ptypedocument == 'NC':
        datos = Factura.objects.filter(subtotal__lt=0)
    else:
        datos = Factura.objects.all()

    datos = (
        datos
        .annotate(
                year=ExtractYear('date'),
                semester=Case(
                    When(date__month__lte=6, then=Value(1)),
                    When(date__month__gte=7, then=Value(2)),
                    output_field=IntegerField(),
                )
            )
        .filter(**filters, semester=semester)
        .values("year")
        .annotate(
            subtotal=Sum("subtotal"),
            iva=Sum("iva"),
            total=Sum("total")
        )
        .order_by("year")
    )

    return datos