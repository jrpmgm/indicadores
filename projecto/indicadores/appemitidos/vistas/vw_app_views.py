import csv
import datetime
from django.utils.timezone import make_aware, get_default_timezone
from decimal import Decimal
import json
import os
from django.shortcuts import render
from django.conf import settings

from ..models import Partner, Emitido, Factura, Location
import calendar
from django.http import JsonResponse
import pandas as pd
import re
from django.db.models import Q
from django.db import transaction
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt # ¡Importante! Lee la nota abajo
from django.db.models.functions import ExtractYear, ExtractMonth
from django.db.models import Sum
from ..modules import md_invoiced
from appemitidos.generalsdata.constants import TYPE_DOCUMENT_CHOICES
import random

PATH_FILES = os.path.join(settings.BASE_DIR, 'appemitidos', 'static', 'resources/docelectronicos')
PATH_FILESEXCEL = os.path.join(settings.BASE_DIR, 'appemitidos', 'static', 'resources/docfacturas')
#TYPEGRAPH =   {'bar': 'bar','barH': 'barH', 'line': 'line', 'pie':'pie','doughnut':'doughnut','polarArea': 'polarArea'}  # Cambia esto a 'line' si prefieres un gráfico de líneas

def home(request):
    return render(request, "home.html")

def guardar_csv_en_modelos(request):
    
    emitidos = {}

    partners = {}
    ructmp = ""
    mestmp = ""
    nrodocumento = 0
    for key in request.POST:
        if key.startswith('data_'):
            if key.endswith('_1'):
                ructmp = request.POST[key]
            elif key.endswith('_2'):
                partners[key] = {'ruc': ructmp, 'razonsocial': request.POST[key], 'email': ructmp+"@gmail.com", 'telefono': "S/T"}
            elif key.endswith('_3'):
                mestmp = request.POST[key]
            elif key.endswith('_4'):
                nrodocumento = int(request.POST[key])
                emitidos[key] = {
                    'partner': ructmp,
                    'year': int(mestmp.split('/')[1]),
                    'month': int(mestmp.split('/')[0]),
                    'issued': nrodocumento
                }

    # Guardar los partners en la base de datos
    for key, partner in partners.items():
        if not Partner.objects.filter(identification=partner['ruc']).exists():
            p = Partner.objects.create(
                identification=partner['ruc'],
                name=partner['razonsocial'],
                email=partner['email'],
                phone=partner['telefono']
            )
            print(f"Partner {p.name} creado.")
        else:
            print(f"Partner con RUC {partner['ruc']} ya existe.")
    
    # Guardar los emitidos en la base de datos
    for key, emitido in emitidos.items():
        partner = Partner.objects.get(identification=emitido['partner'])
        # Verificar si ya existe un Emitido con el mismo partner, year y month
        if not Emitido.objects.filter(partner_id=partner.id, year=emitido['year'], month=emitido['month']).exists():
            Emitido.objects.create(
                partner_id=partner.id,
                year=emitido['year'],
                month=emitido['month'],
                issued=emitido['issued']
            )
            print(f"Emitido para {partner.name} creado.")
        else:
            print(f"Emitido para {partner.name}, año {emitido['year']}, mes {emitido['month']} ya existe.")

def mostrar_csv(request):
    
    if request.method == 'POST':
        guardar_csv_en_modelos(request)
        return render(request, 'appemitidos/issued.html', {'message': 'CSV guardado exitosamente.'})
    
    #csv_path = os.path.join(settings.BASE_DIR, 'appemitidos', 'static', 'resources', 'emitidos.csv')
    #PATH_FILES
    with open(PATH_FILES + "/emitidos.csv", newline='', encoding='latin1') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        rows = list(reader)

    headers = rows[0]
    data_rows = rows[1:]

    return render(request, 'appemitidos/issued.html', {
        'headers': headers,
        'rows': data_rows
    })

def dataobtained(request, pyears, pmonths):
    """
    Obtiene los datos emitidos para un año y mes específicos.
    """
    data = Emitido.objects.filter(year=pyears, month=pmonths).order_by('partner__identification')
    
    emitidos = []
    for emitido in data:
        emitidos.append({
            'partner_ruc': emitido.partner.identification,
            'partner_name': emitido.partner.name,
            'year': emitido.year,
            'month': emitido.month,
            'issued': emitido.issued
        })
    
    return JsonResponse(emitidos, safe=False)

def loadissued(request):
    numero_mes = Emitido.objects.values_list('month', flat=True).distinct().order_by('month')
    meses = [(m, calendar.month_name[m]) for m in numero_mes]

    years = Emitido.objects.values_list('year', flat=True).distinct().order_by('year')

    return render(request, 'appemitidos/showissued.html', {
            'months': meses, 'years': years,
        })

""" def load_location(request, level, parent_id):
    if (parent_id == "-1" or parent_id == "undefined" or parent_id == "null"):
        locations = Location.objects.filter(level=level).values_list('id', 'name').distinct()
    else:
        locations = Location.objects.filter(level=level, parent_id=int(parent_id)).values_list('id', 'name').distinct()
    return JsonResponse(list(locations), safe=False) """

def star_parameters(request):
    data = {"months": list(Factura.objects.annotate(month=ExtractMonth('date')).values_list('month', flat=True).distinct().order_by('month')),
            "years": list(Factura.objects.annotate(year=ExtractYear('date')).values_list('year', flat=True).distinct().order_by('year'))}
    
    return JsonResponse(data, safe=False)

def consolidado_emitidos_local(pyears, pmonths):
    filtros = {}

    #Permitir varios años separados por coma
    years = [int(m) for m in str(pyears).split(',') if m.strip()]
    if len(years) == 1:
        filtros['year'] = years[0]
    else:
        filtros['year__in'] = years

    # Permitir varios meses separados por coma
    months = [int(m) for m in str(pmonths).split(',') if m.strip()]
    if len(months) == 1:
        filtros['month'] = months[0]
    else:
        filtros['month__in'] = months

    datos = (
        Emitido.objects
        .values('year', 'month')
        .annotate(total_emitidos=Sum('issued'))
        .filter(**filtros)
        .order_by('year', 'month')
    )
    # Agregar el nombre del mes a cada registro
    for d in datos:
        d['month_name'] = calendar.month_name[d['month']]
    return datos

def consolidate(request):
    
    numero_mes = Emitido.objects.values_list('month', flat=True).distinct().order_by('month')
    meses = [(m, calendar.month_name[m]) for m in numero_mes]
    numero_mes = [m[0] for m in meses]  # Extraer solo los números de mes
    data_str = ', '.join(str(item) for item in numero_mes)
    years = Emitido.objects.values_list('year', flat=True).distinct().order_by('year')

    consolidated_data = consolidado_emitidos_local(years[0], data_str)
    return render(request, 'appemitidos/consolidate.html', {'data': consolidated_data, 'months': meses, 'years': years, 'typegraph': md_invoiced.TYPEGRAPH})

@csrf_exempt # Quita esto y maneja los tokens CSRF si es un entorno de producción
def upload_and_process_excel(request):
    if request.method == 'POST':
        # Verifica que el archivo exista en la solicitud
        if 'archivo_excel' in request.FILES:
            excel_file = request.FILES['archivo_excel']

            # Validar el tipo de archivo (opcional pero muy recomendado)
            if not (excel_file.name.endswith('.xlsx') or
                    excel_file.name.endswith('.xls') or
                    excel_file.name.endswith('.csv')):
                return JsonResponse(
                    {'error': 'Tipo de archivo no soportado. Por favor, sube un archivo Excel o CSV.'},
                    status=400
                )

            try:
                # Determinar cómo leer el archivo según su extensión
                if excel_file.name.endswith('.csv'):
                    # pd.read_csv puede necesitar 'encoding' dependiendo del archivo
                    df = pd.read_csv(excel_file)
                else: # Asumimos .xlsx o .xls
                    df = pd.read_excel(excel_file)

                # --- Tu lógica de procesamiento del DataFrame ---
                # Eliminar filas donde la primera columna es NaN
                df = df[df.iloc[:, 0].notna()]

                # Establecer la primera fila como encabezado y eliminarla
                # Asegúrate de que esta lógica sea robusta para tus archivos
                df.columns = df.iloc[0]
                df = df[1:]
                df = df.reset_index(drop=True)

                # Eliminar columnas que se llamen 'nan' (resultado de columnas vacías)
                df = df.loc[:, ~df.columns.astype(str).str.startswith('nan')]

                # Filtrar filas que no comiencen con 'Total' en la primera columna
                data_rows = [row for row in df.values.tolist() if not str(row[0]).strip().startswith('Total')]
                # --- Fin de tu lógica de procesamiento ---

                # Devolver los datos procesados como JSON
                return JsonResponse(data_rows, safe=False) # safe=False permite devolver una lista directamente

            except Exception as e:
                # Capturar errores durante el procesamiento del archivo
                return JsonResponse({'error': f'Error al procesar el archivo: {str(e)}'}, status=500)
        else:
            return JsonResponse({'error': 'No se encontró el archivo "archivo_excel" en la solicitud.'}, status=400)
    else:
        # Si no es una solicitud POST, devuelve un error de método no permitido
        return JsonResponse({'error': 'Método no permitido. Solo se acepta POST.'}, status=405)
    
def invoice_excel(request):

    if request.method == 'POST':
        datos = request.POST.getlist('datos')
        # Pero como es una lista de listas, mejor accedemos así:
        datos_completos = request.POST.getlist('datos[]')  # alternativamente
        # Django no estructura bien listas anidadas automáticamente
        # Usaremos mejor request.POST.getlist() + nombres tipo datos[0][1], datos[1][3], etc.

        datos_recibidos = []
        i = 0
        while f"datos[{i}][0]" in request.POST:
            fila = []
            j = 0
            while f"datos[{i}][{j}]" in request.POST:
                fila.append(request.POST[f"datos[{i}][{j}]"])
                j += 1
            datos_recibidos.append(fila)
            i += 1

        # Ahora `datos_recibidos` contiene toda la tabla como listas de filas
        # Puedes guardarlos en la base de datos aquí

        return render(request, 'appemitidos/confirmation.html', {'mensaje': 'Datos guardados correctamente'})
    
    excel_path = os.path.join(settings.BASE_DIR, 'appemitidos', 'static', 'resources/docfacturas', 'TotalJunio2025.xlsx')
    df = pd.read_excel(excel_path)

    #Elimina filas donde la primera columna es NaN
    df = df[df.iloc[:, 0].notna()]

    df.columns = df.iloc[0]
    # Elimina la primera fila que ahora es el encabezado
    df = df[1:]
    df = df.reset_index(drop=True)

    df = df.loc[:, ~df.columns.astype(str).str.startswith('nan')]

    #headers = list(df.columns)
    headers = ['Fecha', 'Número', 'CI/RUC', 'Razón Social', 'Tip. Doc.', 'Subtotal', 'Base 0%', 'Base No Objeto', 'Base Exenta', 'Base IVA', 'Base ICE', 'IVA', 'ICE']

    # Filtrar filas que no comiencen con 'Total' en la primera columna
    data_rows = [row for row in df.values.tolist() if not str(row[0]).strip().startswith('Total')]

    return render(request, 'appemitidos/invoice_excel.html', {
        'headers': headers#,
        #'rows': data_rows
    })

@require_POST
def guardar_facturas_ajax(request):
    
    try:
        locations = Location.objects.filter(level=7).values_list('id', 'name')
        payload = json.loads(request.body)
        rows = payload.get('datos', [])

        creadas, duplicadas = 0, 0
        
        with transaction.atomic():
            for fila in rows:
                
                fecha_str, num, ci, partner_name, type_doc = fila[0:5]
                montos = fila[5:]

                # reemplaza cualquier variante de "a.m.", "a. m.", "a .m.", etc.
                fecha_str = re.sub(r'a\.?\s*m\.?', 'AM', fecha_str, flags=re.IGNORECASE)
                fecha_str = re.sub(r'p\.?\s*m\.?', 'PM', fecha_str, flags=re.IGNORECASE)
                # Convertir fecha
                try:
                    # Intenta con formato 'dd-mm-YYYY HH:MM:SS'
                    # Soporta formato 'd/m/YYYY HH:MM:SS AM/PM'
                    fecha_dt = datetime.datetime.strptime(fecha_str, '%d/%m/%Y %I:%M:%S %p')
                except ValueError as ve:
                    # Imprime el error específico y luego intenta con otro formato
                    fecha_dt = datetime.datetime.strptime(fecha_str, '%b %d, %Y, %I:%M %p')

                fecha_dt = make_aware(fecha_dt, get_default_timezone())
                
                # Convertir montos a Decimal
                subt, base0, base_no, base_ex, base_iva, base_ice, iva, ice, total = \
                    [Decimal(val or '0') for val in montos]

                # Obtener o crear partner
                
                partner, _ = Partner.objects.get_or_create(
                    identification=ci,
                    defaults={'name': partner_name}
                )

                # Validar si ya existe una factura con los mismos valores
                locs = list(locations)
                if not locs:
                    existe = False
                else:
                    random_loc_id = random.choice(locs)[0]
                    existe = Factura.objects.filter(
                        partner=partner,
                        number=num,
                        date=fecha_dt,
                        type_doc=type_doc,
                        location_id=random_loc_id
                    ).exists()

                if existe:
                    duplicadas += 1
                    continue  # Saltar esta fila

                # Crear la factura
                Factura.objects.create(
                    partner=partner,
                    number=num,
                    identification=ci,
                    subtotal=subt,
                    base_0=base0,
                    base_no_objeto=base_no,
                    base_ex=base_ex,
                    base_iva=base_iva,
                    base_ice=base_ice,
                    iva=iva,
                    ice=ice,
                    total=total,
                    date=fecha_dt,
                    type_doc=type_doc,
                    location_id=random_loc_id
                )
                creadas += 1

        return JsonResponse({
            'mensaje': f'Guardado completo ✅  {creadas} nuevas, {duplicadas} duplicadas (omitidas)'
        })

    except Exception as e:
        print(f"Error al guardar facturas: {e}")
        return JsonResponse({'mensaje': f'Error: {e}'}, status=400)