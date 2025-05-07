from django.contrib import admin
from django.core.files.base import ContentFile
import zipfile
import os
import io 
import re 
from docx import Document 
from django.conf import settings
from .models import Empresa, Reporte, Palabras, Conteo, Provincia, ArchivoZip, ZipArchivo



class AnioListFilter(admin.SimpleListFilter):
    title = 'Año'
    parameter_name = 'anio'

    def lookups(self, request, model_admin):
        anios = Reporte.objects.order_by().values_list('anio', flat=True).distinct()
        return [(str(anio), str(anio)) for anio in anios]

    def queryset(self, request, queryset):
        anio = self.value()
        if anio:
            return queryset.filter(reporte__anio=anio)
        return queryset
        

@admin.register(Conteo)
class ConteoAdmin(admin.ModelAdmin):
    list_display = ('reporte', 'palabra', 'cantidad')
    list_filter = (AnioListFilter,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        anio = request.GET.get('anio')
        if anio:
            qs = qs.filter(reporte__anio=anio)
        return qs.order_by('-cantidad')


@admin.register(Palabras)
class PalabrasAdmin(admin.ModelAdmin):
    list_display = ('descripcion',)
    search_fields = ('descripcion',)


@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'empresa', 'anio', 'top_palabras')
    readonly_fields = ('top_palabras', 'nombre')
    autocomplete_fields = ['empresa'] # Autocompletar el campo empresa



@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia', 'ruc')
    list_filter = ('provincia',)
    search_fields = ('nombre',)
    fieldsets = (
        (None, {
            'fields': ('nombre', 'ruc', 'provincia'),  # Aquí especificas el orden de los campos
        }),
    )


@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(ArchivoZip)
class ArchivoZipAdmin(admin.ModelAdmin):
    list_display = ['archivo', 'fecha_subida']
    
    
    

@admin.register(ZipArchivo)
class ZipArchivoAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        zip_file = obj.archivo
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for filename in zip_ref.namelist():
                if filename.endswith(('.docx', '.txt')):
                    file_data = zip_ref.read(filename)

                    # Leer texto del archivo
                    texto = ''
                    if filename.endswith('.docx'):
                        with io.BytesIO(file_data) as f:
                            doc = Document(f)
                            texto = '\n'.join([p.text for p in doc.paragraphs])
                    elif filename.endswith('.txt'):
                        texto = file_data.decode('utf-8', errors='ignore')

                    # Detectar año
                    match_anio = re.search(r'\b(20\d{2}|19\d{2})\b', texto)
                    anio = int(match_anio.group()) if match_anio else 0  # Si no hay, guarda 0

                    # Detectar empresa
                    empresa_asignada = Empresa.objects.filter(nombre__iexact='Desconocido').first()
                    for empresa in Empresa.objects.exclude(nombre__iexact='Desconocido'):
                        if empresa.nombre.lower() in texto.lower():
                            empresa_asignada = empresa
                            break

                    # Guardar archivo en Reporte
                    reporte = Reporte(
                        empresa=empresa_asignada,
                        anio=anio
                    )
                    reporte.archivo.save(os.path.basename(filename), ContentFile(file_data))
                    reporte.save()