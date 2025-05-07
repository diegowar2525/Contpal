# forms.py

from django import forms
from .models import Reporte

class ReporteAdminForm(forms.ModelForm):
    zip_masivo = forms.FileField(required=False, help_text="Sube un ZIP para cargar múltiples reportes", label="Carga masiva ZIP")

    class Meta:
        model = Reporte
        fields = '__all__'
