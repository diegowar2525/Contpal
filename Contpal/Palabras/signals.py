# Palabras/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reporte
from .utils import count_frequent_words, guardar_conteo_en_bd
import os
from django.conf import settings

@receiver(post_save, sender=Reporte)
def procesar_reporte(sender, instance, created, **kwargs):
    if created and instance.archivo:
        # Obtener la ruta completa del archivo
        doc_path = os.path.join(settings.MEDIA_ROOT, instance.archivo.name)
        
        # Procesar el archivo y contar palabras
        word_counts = count_frequent_words([doc_path])
        
        # Guardar en base de datos
        guardar_conteo_en_bd(instance, word_counts)
