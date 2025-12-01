# models.py en tu_app_de_ubicaciones
from django.db import models
from django.contrib.auth.models import User  # Si usas el modelo User por defecto

class Location(models.Model):
    """
    Modelo para representar una estructura de ubicación jerárquica en una sola tabla.
    Utiliza el patrón de lista de adyacencia.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre de la Ubicación",
        help_text="Ej: América, Ecuador, Sierra, Loja, Matriz, Sucursal 1"
    )
    
    code_segment = models.CharField(
        max_length=6,
        verbose_name="Segmento de Código",
        help_text="Código de 3 dígitos para este nivel (ej: '001', '002')."
    )
    
    level = models.IntegerField(
        verbose_name="Nivel Jerárquico",
        help_text="Nivel de la ubicación en la jerarquía (1: Continente, 2: País, etc.)."
    )
    
    parent = models.ForeignKey(
        'self',  # Apunta a la misma clase Location
        on_delete=models.CASCADE, # Si se borra un padre, se borran sus hijos
        null=True,                # Los niveles superiores (ej: continentes) no tienen padre
        blank=True,               # Permite que el campo esté vacío en el formulario
        related_name='children',  # Permite acceder a los hijos de una ubicación (ej: location.children.all())
        verbose_name="Ubicación Padre",
        help_text="Ubicación superior en la jerarquía."
    )

    path = models.CharField(
        max_length=300,
        editable=False,
        db_index=True,
        null=True,
        blank=True,
        help_text="Ruta jerárquica (ej: 1/5/23/)"
    )

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        # Opcional: añade una restricción de unicidad para el segmento de código
        # dentro de un mismo padre, y para el nivel.
        unique_together = ('code_segment', 'parent', 'level') 
        # Añade un índice para búsquedas por padre y nivel
        indexes = [
            models.Index(fields=['parent', 'level']),
            models.Index(fields=['level']),
        ]

    def save(self, *args, **kwargs):
        """
        Guarda primero para obtener el ID, luego actualiza el path.
        """
        super().save(*args, **kwargs)

        # Generar path
        if self.parent:
            self.path = f"{self.parent.path}{self.id}/"
        else:
            self.path = f"{self.id}/"

        # Guardar path si cambió
        super().save(update_fields=["path"])
    
    def __str__(self):
        """
        Representación de cadena del objeto Location.
        Puedes personalizarla para mostrar la jerarquía completa si lo deseas.
        """
        if self.parent:
            return f"{self.get_full_path()} ({self.code_segment})"
        return f"{self.name} ({self.code_segment}) ({self.level})"

    def get_full_path(self):
        """
        Retorna la ruta completa de la ubicación (ej: América/Ecuador/Sierra/Loja).
        """
        path = [self.name]
        current = self
        while current.parent:
            current = current.parent
            path.append(current.name)
        return " / ".join(reversed(path))

    @property
    def full_code(self):
        """
        Retorna el código completo jerárquico (ej: '001001001').
        """
        code_parts = [self.code_segment]
        current = self
        while current.parent:
            current = current.parent
            code_parts.append(current.code_segment)
        return "".join(reversed(code_parts))

# Ejemplo de cómo podrías vincular los usuarios a una ubicación (ej. Sucursal)
# Asumiendo que usas el modelo User por defecto de Django o uno personalizado.
# from django.contrib.auth.models import User # Si usas el User por defecto

class CustomUser(models.Model): # Si tienes un modelo de usuario personalizado
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL, # O models.RESTRICT, según la lógica de tu negocio
        null=True,
        blank=True,
        limit_choices_to={'level': 6}, # Limita la elección solo a ubicaciones de nivel 'Sucursal'/'Matriz'
        verbose_name="Ubicación Asignada"
    )
     # Otros campos de usuario personalizados

    def __str__(self):
        return self.user.username
