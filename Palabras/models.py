from django.db import models
import datetime

# Create your models here.
class Provincia(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Empresa(models.Model):
    ruc = models.CharField(max_length=13, unique=True)
    nombre = models.CharField(max_length=100)
    provincia = models.ForeignKey(Provincia, on_delete=models.CASCADE)  # Relación agregada

    def __str__(self):
        return self.nombre


class Reporte(models.Model):
    nombre = models.CharField(max_length=150, editable=False)  # editable=False para que no se muestre en el admin
    empresa = models.ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
    archivo = models.FileField(upload_to='reportes/', blank=True, null=True)
    anio = models.IntegerField(default=datetime.datetime.now().year)

    def save(self, *args, **kwargs):
        if not self.nombre:
            base_nombre = self.archivo.name if self.archivo else "SinArchivo"
            base_nombre = base_nombre.split('/')[-1]  # Solo el nombre del archivo
            self.nombre = base_nombre
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    def top_palabras(self, cantidad=5):
        conteos = self.conteototal_set.order_by('-cantidad')[:cantidad]
        return ', '.join([f"{c.palabra.descripcion} ({c.cantidad})" for c in conteos])

    top_palabras.short_description = "Top palabras"


class Palabras(models.Model):
    descripcion = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.descripcion
    

class ConteoTotal(models.Model):
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE)
    palabra = models.ForeignKey(Palabras, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    class Meta:
        unique_together = ('reporte', 'palabra')  # Opcional, evita duplicados

    def __str__(self):
        return f"{self.palabra.descripcion} ({self.cantidad}) en {self.reporte}"

