import os
import pandas as pd
import re
import mysql.connector
import datetime
import time

# Ruta del directorio a recorrer
directorio = 'CPS' #Por seguridad se decidió ocultar la ruta
contador = 0
inicio_procesamiento = time.time()

# Recorre todos los archivos en el directorio
for root, dirs, files in os.walk(directorio):
    for file in files:
        # Verifica si el archivo tiene extensión .xlsx o .xls
        if file.endswith((".xlsx", ".xls")):
            contador += 1

print(f'Hay {contador} archivos con extensión .xlsx y .xls en el directorio.')

# Cargar el archivo de Excel
file_path = 'Base_de_datos_Magallanes_SEIA.xlsx' #Por seguridad se decidió ocultar la ruta
df_clean = pd.read_excel(file_path, sheet_name='Magallanes', skiprows=2)

# Eliminar filas con NaN en la columna 'Gra'
df_clean = df_clean.dropna(subset=['Gra'])

# Reemplazar '/' con 'Disponible' y '_' con 'No disponible' en la columna 'Gra'
df_clean['Gra'] = df_clean['Gra'].replace({"/": "Disponible", "_": "No disponible"})

# Seleccionar solo la columna "Nombre"
estaciones = df_clean['Nombre']

# Filtrar nombres que contienen las palabras "Solicitud" o "PERT"
filtro_estaciones = estaciones[estaciones.str.contains("Solicitud|PERT", case=False, na=False)]

# Expresión regular ajustada para capturar números en diversos formatos
numeros_extraidos = filtro_estaciones.apply(
    lambda x: re.search(
        r"(Solicitud|PERT)\s*(N*°*∫*∞*\.?:?\s*)*(\d[\d\s]*)",
        x, re.IGNORECASE
    )
)

# Crear una lista con los números limpios (sin espacios)
numeros_limpios = [
    re.sub(r"\s+", "", match.group(3)) if match else None for match in numeros_extraidos
]

# Extraer las columnas Latitud, Longitud y Gra (Granulometría)
lat_long_gra = df_clean[['Latitud ', 'Longitud ', 'Gra']].loc[filtro_estaciones.index]

# Crear DataFrame de resultado para visualizar
resultado_df = pd.DataFrame({
    "Nombre": filtro_estaciones,
    "Numero Extraido": numeros_limpios,
    "Latitud ": lat_long_gra['Latitud '],
    "Longitud ": lat_long_gra['Longitud '],
    "Granulometria (Gra)": lat_long_gra['Gra']
})

# Conectar a la base de datos MariaDB
print("\nConectando a la base de datos MariaDB...")
connection = mysql.connector.connect(
    host='',
    port='',
    user='',
    password='',
    database=''
)

print('Conexión exitosa')

# Crear el cursor con buffered=True para evitar errores de resultados no leídos
cursor = connection.cursor(buffered=True)

# Consulta SQL para verificar coincidencia de latitud y longitud
select_query = """
SELECT e_code FROM estacion WHERE lat = %s AND lon = %s
"""

# Consulta para actualizar numero_pert y granulometria cuando hay coincidencia de latitud y longitud
update_query = """
UPDATE estacion 
SET numero_pert = %s, granulometria = %s 
WHERE lat = %s AND lon = %s
"""

# Consulta para registrar en la tabla log
log_query = """
INSERT INTO log (fecha_hora, archivo_nombre, tipo_archivo, datos_procesados, datos_insertados, datos_erroneos, 
                 tiempo_procesamiento, usuario_responsable, mensaje, archivo_path)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

# Variables para log
actualizados = 0
errores = 0
mensaje = ""
usuario_responsable = connection.user  # Obtener el usuario conectado

# Insertar datos solo cuando hay coincidencia de latitud y longitud
print("\nInsertando datos de numero_pert y granulometria cuando hay coincidencia de latitud y longitud...")
for _, row in resultado_df.iterrows():
    lat = row['Latitud ']
    lon = row['Longitud ']
    numero_pert = row['Numero Extraido']
    granulometria = row['Granulometria (Gra)']
    
    # Continuar solo si numero_pert y granulometria están presentes
    if numero_pert and granulometria:
        # Ejecutar la consulta para verificar si existe coincidencia
        cursor.execute(select_query, (lat, lon))
        result = cursor.fetchone()
        
        # Actualizar solo si se encontró coincidencia en latitud y longitud
        if result is not None:
            print(f"Coincidencia encontrada para lat={lat}, lon={lon}. Procediendo a actualizar.")
            try:
                cursor.execute(update_query, (numero_pert, granulometria, lat, lon))
                print(f"Datos actualizados para lat={lat}, lon={lon} con numero_pert={numero_pert} y granulometria={granulometria}")
                actualizados += 1
            except mysql.connector.Error as err:
                print(f"Error al actualizar datos para lat={lat}, lon={lon}: {err}")
                errores += 1
        else:
            print(f"No se encontró coincidencia en la base de datos para lat={lat}, lon={lon}.")
            errores += 1

# Confirmar cambios y cerrar conexión
connection.commit()

# Medir tiempo de procesamiento
tiempo_procesamiento = time.time() - inicio_procesamiento

# Registrar log del proceso
print("\nRegistrando log del proceso...")
try:
    cursor.execute(log_query, (
        datetime.datetime.now(),  # fecha_hora
        file_path.split("\\")[-1],  # archivo_nombre
        "Excel",  # tipo_archivo
        len(resultado_df),  # datos_procesados
        actualizados,  # datos_insertados
        errores,  # datos_erroneos
        tiempo_procesamiento,  # tiempo_procesamiento
        usuario_responsable,  # usuario_responsable
        mensaje,  # mensaje
        file_path  # archivo_path
    ))
    connection.commit()
    print("Log registrado exitosamente.")
except mysql.connector.Error as err:
    print(f"Error al registrar log: {err}")

cursor.close()
connection.close()
print("\nProceso finalizado. Datos de numero_pert y granulometria insertados en la base de datos.")
print(f'Filas actualizadas: {actualizados} Filas No actualizadas: {errores}')
