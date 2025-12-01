from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Value
from ..models import Factura, Location
import calendar

def get_filtros_context():
    """Devuelve los años y meses para los modales de filtro."""
    years_lst = Factura.objects.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct().order_by('year')
    years = [(str(y)) for y in years_lst]
    years.insert(0, 'All')

    numero_mes = Factura.objects.annotate(month=ExtractMonth('date')).values_list('month', flat=True).distinct().order_by('month')
    months = [(i, calendar.month_name[i]) for i in numero_mes]
    
    star_element = (0, 'All')
    months.insert(0, star_element)

    return {"years": years, "months": months}

def obtain_filters(request = None, pyears = None, pmonths = None):
  
    locationFilters = {}
    
    
    filtros = {}

    # Permitir varios años separados por coma
    if pyears:
        years = [int(m) for m in str(pyears).split(',') if m.strip() and m != 'All']
        if years:
            filtros['date__year__in'] = years

    # Permitir varios meses separados por coma
    if pmonths:
        months = [int(m) for m in str(pmonths).split(',') if m.strip() and m != '0' and m != 'All']
        if months:
            filtros['date__month__in'] = months
    # ------------------ SECCIÓN DE FILTRO DE UBICACIÓN CORREGIDA ------------------
    # Construye el diccionario de filtros para la tabla Location de forma dinámica
    if request:
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
        location_filters_dict = {}

        if locationFilters.get("continent") and locationFilters["continent"] != -1:
            location_filters_dict['parent__parent__parent__parent__parent__parent'] = locationFilters["continent"]
        
        if locationFilters.get("country") and locationFilters["country"] != -1:
            location_filters_dict['parent__parent__parent__parent__parent'] = locationFilters["country"]

        if locationFilters.get("region") and locationFilters["region"] != -1:
            location_filters_dict['parent__parent__parent__parent'] = locationFilters["region"]

        if locationFilters.get("province") and locationFilters["province"] != -1:
            location_filters_dict['parent__parent__parent'] = locationFilters["province"]

        if locationFilters.get("city") and locationFilters["city"] != -1:
            location_filters_dict['parent__parent'] = locationFilters["city"]

        if locationFilters.get("establishment") and locationFilters["establishment"] != -1:
            location_filters_dict['parent'] = locationFilters["establishment"]

        if locationFilters.get("point") and locationFilters["point"] != -1:
            location_filters_dict['id'] = locationFilters["point"]

        # Si hay filtros de ubicación, encuentra los IDs de las ubicaciones que coinciden
        if location_filters_dict:
            # Encuentra los IDs de todas las ubicaciones que cumplen con el filtro de jerarquía
            valid_location_ids = Location.objects.filter(**location_filters_dict).values_list('id', flat=True)
            # Filtra las facturas usando el conjunto de IDs de ubicación válidos
            filtros['location_id__in'] = valid_location_ids

    return filtros