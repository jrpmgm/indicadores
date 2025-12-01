import calendar
from django.core.management.base import BaseCommand
from appemitidos.models.generals import Factura
from django.db.models import Sum, Max
from django.db.models.functions import ExtractYear, ExtractMonth

def max_subtotal_por_anio_con_partner():
    # 1) Agregamos por (year, partner)
    partner_totals = (
        Factura.objects
        .annotate(year=ExtractYear('date'), month=ExtractMonth('date'))
        .values('year', 'month', 'partner_id', 'partner__name')
        .annotate(value=Max('subtotal'))
        .order_by('year', 'month', '-value')  # por año, partner con mayor subtotal primero
    )

    # 2) Recorremos y seleccionamos el primer partner de cada año (el mayor)
    resultado = []
    años_vistos = set()

    for row in partner_totals:
        key = (row['year'], row['month'])
        if key in años_vistos:
            continue  # ya elegimos el partner máximo para ese año
        años_vistos.add(key)
        resultado.append({
            'year': row['year'],
            'month': row['month'],
            'month_name': calendar.month_name[row['month']],
            'partner_id': row['partner_id'],
            'partner_name': row['partner__name'],
            'max_value': row['value'],
        })

    return resultado

class Command(BaseCommand):
    help = 'Ejemplo de comando Django'

    def handle(self, *args, **kwargs):
        # Subconsulta que obtiene el máximo subtotal por año (devuelve un solo valor)
        
        for entry in max_subtotal_por_anio_con_partner():
            self.stdout.write(
                f"Año: {entry['year']}, Mes:{entry['month_name']}, Máximo: {entry['max_value']}, Partner: {entry['partner_name']} (id={entry['partner_id']})"
            )

        #self.stdout.write(f"Partner: {myfac.partner}, el valor del subtotal es: {myfac.subtotal}")
        

        # obtener el valor máximo de subtotal
        """ max_sub = myfac.aggregate(max_subtotal=Max('subtotal'))['max_subtotal']

        # obtener una factura con ese subtotal máximo (si hay varias, la primera)
        factura_max = None
        partner_max = None
        if max_sub is not None:
            factura_max = myfac.filter(subtotal=max_sub).select_related('partner').first()
            if factura_max:
                partner_max = getattr(factura_max, 'partner', None)

        # si existe, mostrar info del partner junto al subtotal máximo
        if partner_max is not None:
            self.stdout.write(f'Partner con subtotal máximo: {partner_max} (ID: {getattr(partner_max, "id", "N/A")})')
        if max_sub is None:
            self.stdout.write('No hay facturas.')
        else:
            self.stdout.write(f'Máximo subtotal: {max_sub}') """
        """ for factura in myfac:
            self.stdout.write(f'Factura ID: {factura.id}, Número: {factura.number}, Total: {factura.total}') """