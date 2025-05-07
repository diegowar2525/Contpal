from django.contrib import admin
from django.conf import settings
from django.urls import path
from django.http import JsonResponse
from django.utils.html import format_html
from .models import Empresa, Reporte, Palabras, ConteoTotal, Provincia
from .utils import procesar_zip_reportes
from .forms import ReporteAdminForm


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


@admin.register(ConteoTotal)
class ConteoAdmin(admin.ModelAdmin):
    list_display = ('palabra', 'cantidad')
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
    form = ReporteAdminForm
    list_display = ('nombre', 'anio','empresa')  # Se elimina 'top_palabras' de la lista
    readonly_fields = ('top_palabras', 'nombre', 'anio')
    autocomplete_fields = ['empresa']
    change_form_template = 'admin/reporte_change_form.html'  # Plantilla personalizada

    def save_model(self, request, obj, form, change):
        # Guardar el reporte normal
        super().save_model(request, obj, form, change)

        # Procesar ZIP si fue subido
        zip_file = form.cleaned_data.get('zip_masivo')
        if zip_file:
            procesar_zip_reportes(zip_file)

    def top_palabras(self, obj):
        conteos = obj.conteototal_set.all()
        total = sum(c.cantidad for c in conteos)
        if not total:
            return "Sin datos"
        
        # Limitar a las 10 palabras más frecuentes
        conteos_top_10 = sorted(conteos, key=lambda x: -x.cantidad)[:10]

        # Crear la tabla HTML para las palabras, cantidades y frecuencias
        tabla = '<table style="width: 100%; border: 1px solid #ddd; border-collapse: collapse;">'
        tabla += '<thead><tr><th style="padding: 8px; background-color: #f2f2f2;">Palabra</th><th style="padding: 8px; background-color: #f2f2f2;">Cantidad</th><th style="padding: 8px; background-color: #f2f2f2;">Frecuencia (%)</th></tr></thead>'
        tabla += '<tbody>'
        
        for c in conteos_top_10:
            frecuencia_porcentaje = (c.cantidad / total) * 100
            tabla += f'<tr><td style="padding: 8px; text-align: left;"><strong>{c.palabra.descripcion}</strong></td>'
            tabla += f'<td style="padding: 8px; text-align: right;">{c.cantidad}</td>'
            tabla += f'<td style="padding: 8px; text-align: right;">{frecuencia_porcentaje:.2f}%</td></tr>'
        
        tabla += '</tbody></table>'
        return format_html(tabla)

    top_palabras.short_description = "Palabras y peso relativo"

    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
            path('<int:pk>/chart-data/', self.admin_site.admin_view(self.chart_data), name='reporte_chart_data'),
        ]
        return extra_urls + urls

    def chart_data(self, request, pk):
        reporte = Reporte.objects.get(pk=pk)
        conteos = reporte.conteototal_set.all()
        total = sum(c.cantidad for c in conteos)
        data = {
            "labels": [c.palabra.descripcion for c in conteos],
            "weights": [round((c.cantidad / total) * 100, 2) for c in conteos]
        }
        return JsonResponse(data)

    # Personalizar el formulario para ocultar el campo 'zip_masivo' en ediciones
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Si el objeto ya existe (se está editando), eliminamos 'zip_masivo' del formulario
        if obj:
            form.base_fields.pop('zip_masivo', None)  # Elimina el campo 'zip_masivo' en ediciones
        return form



@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'provincia', 'ruc')
    list_filter = ('provincia',)
    search_fields = ('nombre',)
    fieldsets = (
        (None, {
            'fields': ('nombre', 'ruc', 'provincia'),
        }),
    )


@admin.register(Provincia)
class ProvinciaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)
