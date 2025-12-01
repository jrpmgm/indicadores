# ubicaciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from appemitidos.models.forms import LocationForm
from appemitidos.models import Location

def location_create(request):
    """
    Vista para crear una nueva ubicación.
    Maneja la visualización del formulario (GET) y el guardado (POST).
    """
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirige a una página de éxito o a la lista de ubicaciones
            # Asume que tienes una URL llamada 'location_list' o similar
            return redirect(reverse('location_list')) # Cambia 'location_list' a tu URL de lista
    else:
        form = LocationForm()
    
    context = {
        'form': form,
        'page_title': 'Agregar Nueva Ubicación'
    }
    return render(request, 'locations/location_form.html', context)

def location_edit(request, pk):
    """
    Vista para editar una ubicación existente.
    """
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect(reverse('location_list')) # Cambia 'location_list' a tu URL de lista
    else:
        form = LocationForm(instance=location)
    
    context = {
        'form': form,
        'page_title': f'Editar Ubicación: {location.name}'
    }
    return render(request, 'locations/location_form.html', context)

def location_list(request):
    """
    Vista para mostrar todas las ubicaciones.
    """
    # Puedes obtener todas las ubicaciones o filtrarlas por nivel si es necesario
    locations = Location.objects.all().order_by('level', 'name')
    context = {
        'locations': locations,
        'page_title': 'Lista de Ubicaciones'
    }
    return render(request, 'locations/location_list.html', context)

def location_delete(request, pk):
    """
    Vista para eliminar una ubicación.
    Muestra una página de confirmación (GET) y realiza la eliminación (POST).
    """
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        # Asegúrate de que no tenga hijos antes de eliminar, si es necesario
        if location.children.exists():
            # Si tiene hijos, puedes redirigir con un mensaje de error o manejarlo de otra forma
            # Por ahora, simplemente no permitiremos la eliminación
            return redirect(reverse('location_list')) 
        
        location.delete()
        return redirect(reverse('location_list'))
    
    context = {
        'location': location,
        'page_title': f'Confirmar Eliminación: {location.name}'
    }
    return render(request, 'locations/location_confirm_delete.html', context)


# --- Funcionalidad Adicional (Opcional) ---
# Si quisieras agregar una ubicación con un padre pre-seleccionado, por ejemplo,
# al hacer clic en "Añadir hijo" desde la vista de detalle de un padre.
def location_create_child(request, parent_pk):
    parent_location = get_object_or_404(Location, pk=parent_pk)
    initial_data = {
        'parent': parent_location.pk,
        'level': parent_location.level + 1
    }

    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            #return redirect(reverse('location_list', args=[parent_location.pk])) # O a la lista
            return redirect(reverse('location_list')) # O a la lista
    else:
        form = LocationForm(initial=initial_data)

    context = {
        'form': form,
        'page_title': f'Agregar Ubicación bajo: {parent_location.name}',
        'parent_location': parent_location
    }
    return render(request, 'locations/location_form.html', context)

def children_options(request):
    parent_id = None
    for key in ["continents", "countries", "regions", "provinces", "cities", "establishments"]:
        val = request.GET.get(key)
        if val:  # si no está vacío
            parent_id = val
            break
    if parent_id:
        children = Location.objects.filter(parent_id=parent_id).order_by("name")
    else:
        children = Location.objects.filter(level=1).order_by("name")

    return render(request, "partials/location_options.html", {"children": children})

