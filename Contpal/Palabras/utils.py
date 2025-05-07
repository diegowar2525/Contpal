import re
import docx
import nltk
import pandas as pd
from nltk.corpus import stopwords
from collections import Counter
from django.db import transaction
from .models import Palabras, Conteo, Provincia, Empresa

nltk.download('stopwords')

def count_frequent_words(doc_paths):
    # Inicializar contador global
    total_word_counts = Counter()

    # Iterar sobre cada documento
    for doc_path in doc_paths:
        # Verificar extensión del archivo
        if doc_path.lower().endswith('.docx'):
            # Leer documento Word
            doc = docx.Document(doc_path)

            # Extraer texto del documento
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + " "

        elif doc_path.lower().endswith('.txt'):
            # Leer archivo de texto
            with open(doc_path, 'r', encoding='utf-8') as file:
                text = file.read()
        else:
            raise ValueError(f"Formato de archivo no soportado para {doc_path}. Use .docx o .txt")

        # Convertir a minúsculas y eliminar caracteres especiales (excepto letras)
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)

        # Filtrar las palabras que contengan solo letras (eliminar números)
        text = re.sub(r'\b\d+\b', '', text)

        # Obtener lista de stop words en español
        spanish_stop_words = set(stopwords.words('spanish'))

        # Dividir el texto en palabras
        words = text.split()

        # Filtrar stop words y palabras vacías
        meaningful_words = [word for word in words if word not in spanish_stop_words and word.isalpha()]

        # Actualizar el contador global con las palabras del documento actual
        total_word_counts.update(meaningful_words)

    # Convertir a diccionario con las palabras más comunes
    most_common_dict = dict(total_word_counts.most_common())

    return most_common_dict


def guardar_conteo_en_bd(reporte, word_counts):
    """
    Guarda el conteo de palabras en la base de datos, acumulando
    para palabras del mismo año (sin importar la empresa).
    """
    with transaction.atomic():
        for palabra, cantidad in word_counts.items():
            palabra_obj, _ = Palabras.objects.get_or_create(descripcion=palabra)

            # Buscar si ya existe conteo para esta palabra en este año
            conteos_previos = Conteo.objects.filter(
                reporte__anio=reporte.anio,
                palabra=palabra_obj
            )

            if conteos_previos.exists():
                # Sumamos al primer conteo encontrado
                conteo = conteos_previos.first()
                conteo.cantidad += cantidad
                conteo.save()
            else:
                # Si no existe, creamos uno nuevo vinculado al reporte actual
                Conteo.objects.create(
                    reporte=reporte,
                    palabra=palabra_obj,
                    cantidad=cantidad
                )


def insertar_provincias(archivo_excel):
    # Leer el archivo Excel
    df = pd.read_excel(archivo_excel)

    # Insertar las provincias en la base de datos
    for _, row in df.iterrows():
        nombre_provincia = row['provincia']
        # Verificar si la provincia ya existe, si no, crearla
        if not Provincia.objects.filter(nombre=nombre_provincia).exists():
            Provincia.objects.create(nombre=nombre_provincia)

    print("Provincias importadas correctamente.")



def insertar_empresas(archivo_excel):
    # Leer el archivo Excel
    df = pd.read_excel(archivo_excel)

    for _, row in df.iterrows():
        nombre_empresa = row['NOMBRE DE LA ENTIDAD']
        ruc_empresa = row['IDENTIFICACIÓN']
        nombre_provincia = row['provincia']

        # Obtener o crear la provincia
        provincia, _ = Provincia.objects.get_or_create(nombre=nombre_provincia)

        # Verificar si la empresa ya existe por nombre o por ruc
        if not Empresa.objects.filter(nombre=nombre_empresa).exists() and not Empresa.objects.filter(ruc=ruc_empresa).exists():
            Empresa.objects.create(
                nombre=nombre_empresa,
                ruc=ruc_empresa,
                provincia=provincia
            )
        else:
            print(f"Empresa '{nombre_empresa}' con RUC '{ruc_empresa}' ya existe. No se insertó.")

    print("Empresas importadas correctamente.")


#insertar_provincias(r'C:\Users\USUARIO\Downloads\Empresas.xlsx')
#insertar_empresas(r'C:\Users\USUARIO\Downloads\Empresas.xlsx')
