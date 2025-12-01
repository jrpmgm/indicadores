# ubicaciones/forms.py
from django import forms
from appemitidos.models import Location

class LocationForm(forms.ModelForm):
    """
    Formulario para crear o editar instancias del modelo Location.
    """
    class Meta:
        model = Location
        fields = ['name', 'code_segment', 'level', 'parent']
        labels = {
            'name': 'Nombre de la Ubicación',
            'code_segment': 'Código del Segmento',
            'level': 'Nivel Jerárquico',
            'parent': 'Ubicación Padre',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: América, Ecuador, Loja'}),
            'code_segment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 001, 002'}),
            'level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1 (Continente), 2 (País)'}),
            # Para el campo 'parent', ModelChoiceField usará un select HTML
            # Puedes personalizar el queryset para mostrar solo ciertos tipos de padres
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }

    """ def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Opcional: Personalizar el queryset para el campo 'parent'
        # Por ejemplo, para que solo se muestren ubicaciones que sean padres válidos
        # self.fields['parent'].queryset = Location.objects.filter(level__lt=self.initial.get('level', 100))
        
        # Si estamos creando un nuevo Location, y no se ha especificado un padre
        # y no estamos en el nivel 1, entonces el padre debe ser obligatorio
        if 'instance' not in kwargs or kwargs['instance'] is None:
            if 'level' in self.initial and self.initial['level'] > 1:
                self.fields['parent'].required = True
            elif self.data.get('level') and int(self.data['level']) > 1:
                 self.fields['parent'].required = True
            else:
                self.fields['parent'].required = False # Nivel 1 (continente) no tiene padre
        
        # Si existe un parent, asegura que solo se muestren padres con un nivel menor al actual
        if self.instance.pk: # Si es una instancia existente (editando)
            if self.instance.level > 1:
                self.fields['parent'].queryset = Location.objects.filter(level=self.instance.level - 1)
            else: # Si el nivel es 1, no hay padre
                self.fields['parent'].queryset = Location.objects.none() # Opciones vacías
                self.fields['parent'].required = False
        else: # Si es una nueva instancia (creando)
            # Puedes limitar los padres a ciertos niveles si lo deseas
            self.fields['parent'].queryset = Location.objects.all().order_by('level', 'name')
            # Si el nivel es 1, el padre no es requerido
            if self.data.get('level') == '1':
                self.fields['parent'].required = False
            else:
                self.fields['parent'].required = True # Para niveles > 1, el padre es requerido """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Por defecto, el campo parent del modelo permite null=True y blank=True,
        # lo que lo hace no requerido por defecto en el formulario.
        # Solo lo haremos requerido si el nivel de la ubicación es mayor a 1.

        current_level = None
        
        # 1. Si es una instancia existente (editando):
        if self.instance and self.instance.pk:
            current_level = self.instance.level
        # 2. Si es un POST request (cuando el usuario envía el formulario):
        elif self.data and 'level' in self.data:
            try:
                current_level = int(self.data['level'])
            except (ValueError, TypeError):
                # El campo 'level' podría no ser un número válido, la validación del campo lo manejará.
                pass
        # 3. Si es un GET request con datos iniciales (ej. desde location_create_child):
        elif self.initial and 'level' in self.initial:
            current_level = self.initial['level']

        # Determinar si el campo 'parent' debe ser requerido
        if current_level is not None and current_level > 1:
            self.fields['parent'].required = True
            # Limitar las opciones de 'parent' a ubicaciones del nivel inmediatamente superior
            self.fields['parent'].queryset = Location.objects.filter(level=current_level - 1).order_by('name')
        else:
            # Si el nivel es 1 (Continente) o si el nivel aún no se ha determinado,
            # el campo 'parent' no es requerido.
            self.fields['parent'].required = False
            # Para nivel 1, no debería haber opciones para seleccionar padre
            # Puedes mostrar ubicaciones sin padre (si eso tiene sentido para selección)
            # o simplemente no mostrar ninguna opción.
            self.fields['parent'].queryset = Location.objects.filter(parent__isnull=True).order_by('name')
            # O si no quieres que se pueda seleccionar nada si es nivel 1:
            # self.fields['parent'].queryset = Location.objects.none()

        # Al editar, la ubicación actual no debe ser una opción para su propio padre
        if self.instance and self.instance.pk and self.fields['parent'].queryset is not None:
            self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(pk=self.instance.pk)
