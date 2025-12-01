from django.db import models
from appemitidos.generalsdata.constants import TYPE_DOCUMENT_CHOICES

# Create your models here.
class Partner(models.Model):
    id = models.AutoField(primary_key=True)
    identification = models.CharField(max_length=20, null=False)
    name = models.CharField(max_length=150, null=False)
    email = models.EmailField(max_length=254, null=False)
    phone = models.CharField(max_length=15, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Partner'
        verbose_name_plural = 'Partners'

    def __str__(self):
        return self.name

class Emitido(models.Model):
    id = models.AutoField(primary_key=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='emitidos')
    year = models.IntegerField(null=False)
    month = models.IntegerField(null=False)
    issued = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'App Emitidos'
        verbose_name_plural = 'Apps Emitidos'

    def __str__(self):
        return self.app_name
    
class Factura(models.Model):
    id = models.AutoField(primary_key=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, related_name='facturas')
    number = models.CharField(max_length=20, null=False)
    identification = models.CharField(max_length=20, null=False)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    base_0 = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    base_no_objeto = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    base_ex = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    base_iva = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    base_ice = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    iva = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    ice = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    total = models.DecimalField(max_digits=10, decimal_places=2, null=False)
    date = models.DateTimeField(null=False)
    type_doc = models.CharField(max_length=10, choices=TYPE_DOCUMENT_CHOICES, default='FAC', verbose_name='Tipo de Documento', null=False)
    location = models.ForeignKey('Location', on_delete=models.CASCADE, related_name='facturas', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        unique_together = ('partner', 'number')

    def __str__(self):
        if self.partner:
            return f"Factura {self.id} - {self.partner.name}"
    
    def str_summary(self):
        return f"{self.get_type_doc_display()} - {self.number if hasattr(self, 'number') else ''} ({self.date})"
