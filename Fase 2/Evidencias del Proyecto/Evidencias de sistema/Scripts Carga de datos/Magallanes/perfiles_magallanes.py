import pandas as pd
import mysql.connector
import time
from datetime import datetime

# Cargar datos del archivo Excel, incluyendo la columna "estación"
file_path = 'Planilla_Perfiles_Magallanes.xlsx' #Por seguridad se decidió ocultar la ruta
df = pd.read_excel(file_path, sheet_name='T-S-O')

print(df.head())
# Reemplazar comas por puntos y convertir a tipo float para las columnas relevantes
df['latitud'] = df['latitud'].astype(str).str.replace(',', '.').astype(float)
df['longitud'] = df['longitud'].astype(str).str.replace(',', '.').astype(float)
df['temperatura (°C)'] = pd.to_numeric(df['temperatura (°C)'].astype(str).str.replace(',', '.'), errors='coerce')
df['salinidad (PSU)'] = pd.to_numeric(df['salinidad (PSU)'].astype(str).str.replace(',', '.'), errors='coerce')
df['oxigeno disuelto (mg/L)'] = pd.to_numeric(df['oxigeno disuelto (mg/L)'].astype(str).str.replace(',', '.'), errors='coerce')

# Convertir profundidad a tipo float y luego aplicar valor absoluto (sin el signo negativo)
df['profundidad perfil (m)'] = pd.to_numeric(df['profundidad perfil (m)'].astype(str).str.replace(',', '.'), errors='coerce')
df['profundidad perfil (m)'] = df['profundidad perfil (m)'].apply(lambda x: abs(x))

# Conectar a la base de datos
print("\nConectando a la base de datos MariaDB...")
connection = mysql.connector.connect(
    host='',
    port='',
    user='',
    password='',
    database=''
)
print('Conexión exitosa')

# Crear cursor y obtener el mapeo de e_code por latitud y longitud
cursor = connection.cursor()
cursor.execute("SELECT e_code, lat, lon FROM estacion")
estaciones = cursor.fetchall()

# Crear un diccionario para buscar e_code según latitud y longitud
estacion_map = {
    (float(lat), float(lon)): e_code
    for e_code, lat, lon in estaciones
}

# Función para encontrar e_code correspondiente
def obtener_e_code(lat, lon):
    return estacion_map.get((float(lat), float(lon)), None)

# Añadir una columna 'e_code' al DataFrame basado en latitud y longitud
df['e_code'] = df.apply(lambda row: obtener_e_code(row['latitud'], row['longitud']), axis=1)

# Filtrar solo filas con coincidencia de e_code y valores válidos en 'temperatura', 'salinidad', 'oxigeno disuelto' y 'estación'
df_filtrado = df.dropna(subset=['e_code', 'temperatura (°C)', 'salinidad (PSU)', 'oxigeno disuelto (mg/L)', 'estacion'])

# Variables para log
start_time = time.time()
total_datos = len(df)
datos_insertados = 0
datos_erroneos = 0

# Definir la consulta de inserción en la tabla `perfiles`
insert_query = """
INSERT INTO perfiles (e_code, estacion, profundidad, temperatura, salinidad, oxigeno_disuelto)
VALUES (%s, %s, %s, %s, %s, %s)
"""

# Insertar cada fila en la base de datos
for index, row in df_filtrado.iterrows():
    try:
        values = (
            row['e_code'],
            row['estacion'],                 # Extrae la columna "estación" del archivo
            row['profundidad perfil (m)'],       # Ahora es el valor absoluto
            row['temperatura (°C)'],
            row['salinidad (PSU)'],
            row['oxigeno disuelto (mg/L)']
        )
        cursor.execute(insert_query, values)
        datos_insertados += 1
    except Exception as e:
        datos_erroneos += 1
        print(f"Error al insertar fila {index}: {e}")

# Confirmar los cambios en la base de datos
connection.commit()

# Calcular tiempo de procesamiento
end_time = time.time()
processing_time = end_time - start_time

# Consulta para obtener el usuario conectado
cursor.execute("SELECT USER()")
usuario_conectado = cursor.fetchone()[0]

print(f"Usuario conectado: {usuario_conectado}")


# Insertar registro en la tabla log
log_query = """
INSERT INTO log (fecha_hora, archivo_nombre, tipo_archivo, datos_procesados, datos_insertados, datos_erroneos, tiempo_procesamiento, usuario_responsable, mensaje, archivo_path)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

log_values = (
    datetime.now(),
    'Planilla_Perfiles_Magallanes.xlsx',
    'Excel',
    total_datos,
    datos_insertados,
    datos_erroneos,
    processing_time,
    usuario_conectado,  # Cambia esto según el usuario responsable
    'Carga exitosa con algunos errores' if datos_erroneos > 0 else 'Carga exitosa',
    file_path
)

cursor.execute(log_query, log_values)
connection.commit()

print("Inserción de datos y registro en log completados.")

# Mostrar las filas donde 'estacion' tiene valores que están causando problemas
print("Contenido de la columna 'estacion' en las filas problemáticas:")
for index, row in df_filtrado.iterrows():
    estacion_value = row['estacion']
    if len(str(estacion_value)) > 100:
        print(f"Fila {index}: {estacion_value} (longitud: {len(str(estacion_value))})")


# Cerrar cursor y conexión
cursor.close()
connection.close()
