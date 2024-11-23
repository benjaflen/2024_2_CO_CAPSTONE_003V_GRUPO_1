import mysql.connector  # Asegúrate de tener este módulo instalado
import pandas as pd
import openpyxl
import re
import datetime
import time

# Ruta del archivo Excel
excel_path = 'Concesiones_Los_Lagos_SEIA.xlsx' #Por seguridad se decidió ocultar la ruta

# Leer el archivo Excel omitiendo la primera fila y usando la segunda como encabezado
df = pd.read_excel(excel_path, engine='openpyxl', header=1)

# Ignorar la fila 2 y otras filas que no tengan un nombre válido
df = df.iloc[2:].dropna(subset=["Nombre"])

# Columna de la WEB (URL)
web_col_idx = df.columns.get_loc("WEB") + 1  # +1 porque openpyxl indexa columnas desde 1

# Abrir el archivo con openpyxl para acceder a los hipervínculos
wb = openpyxl.load_workbook(excel_path)
ws = wb.active

# Extraer las columnas necesarias
nombres = df['Nombre']
latitudes = df['Latitud ']  # Latitud (con espacio extra al final)
longitudes = df['Longitud ']  # Longitud (con espacio extra al final)

# Extraer los hipervínculos de la columna 'WEB'
urls = []
print("Extracción de URLs:")
for row in ws.iter_rows(min_row=3, max_row=len(df)+2, min_col=web_col_idx, max_col=web_col_idx):
    for cell in row:
        if cell.hyperlink:
            urls.append(cell.hyperlink.target)
        else:
            urls.append("Sin_URL")

# Limitar la lista de urls a la cantidad de filas en el DataFrame
urls = urls[:len(df)]

# Extraer el número de expediente de las URLs y depurar
expedientes = []
for url in urls:
    if url != "Sin_URL" and isinstance(url, str):
        expediente_match = re.search(r'id_expediente=(\d+)', url)
        if expediente_match:
            expedientes.append(expediente_match.group(1))
        else:
            expedientes.append("Sin_expediente")
    else:
        expedientes.append("Sin_expediente")

# Crear un DataFrame con los datos extraídos
data = pd.DataFrame({
    'nombre': nombres,
    'latitud': latitudes,
    'longitud': longitudes,
    'url': urls,
    'e_code': expedientes
})

print("\nDataFrame creado con nombre, latitud, longitud, URL y e_code formateados correctamente:")
print(data.head())

# Variables para log
datos_procesados = 0
datos_insertados = 0
datos_erroneos = 0
mensaje = ""
usuario_responsable = "desconocido"  # Valor predeterminado si no se conecta correctamente
inicio_procesamiento = time.time()

# Conectar a la base de datos MariaDB
print("\nConectando a la base de datos MariaDB...")
try:
    connection = mysql.connector.connect(
        host='',
        port='',
        user='',
        password='',
        database=''
    )
    print('Conexión exitosa')

    # Obtener usuario conectado
    usuario_responsable = connection.user

    # Crear el cursor y la sentencia SQL
    cursor = connection.cursor()
    insert_query = """
    INSERT INTO estacion (e_code, lat, lon, nombre, url)
    VALUES (%s, %s, %s, %s, %s)
    """

    # Insertar cada fila en la tabla desde el DataFrame
    print("\nInsertando datos en la base de datos...")
    for _, row in data.iterrows():
        datos_procesados += 1
        e_code = row['e_code']
        lat = row['latitud']
        lon = row['longitud']
        nombre = row['nombre']
        url = row['url']
        
        # Insertar solo si e_code no es 'Sin_expediente'
        if e_code != "Sin_expediente":
            try:
                cursor.execute(insert_query, (e_code, lat, lon, nombre, url))
                print(f"Insertado: e_code={e_code}, lat={lat}, lon={lon}, nombre={nombre}, url={url}")
                datos_insertados += 1
            except mysql.connector.Error as err:
                print(f"Error al insertar e_code={e_code}: {err}")
                datos_erroneos += 1

    # Confirmar cambios
    connection.commit()

except Exception as e:
    mensaje = str(e)
    print(f"Error durante el procesamiento: {mensaje}")

finally:
    tiempo_procesamiento = time.time() - inicio_procesamiento

    # Registrar log del proceso
    print("\nRegistrando log del proceso...")
    log_query = """
        INSERT INTO log (fecha_hora, archivo_nombre, tipo_archivo, datos_procesados, datos_insertados, datos_erroneos, 
                         tiempo_procesamiento, usuario_responsable, mensaje, archivo_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        if connection and connection.is_connected():
            cursor.execute(log_query, (
                datetime.datetime.now(),
                excel_path.split("\\")[-1],
                "Excel",
                datos_procesados,
                datos_insertados,
                datos_erroneos,
                tiempo_procesamiento,
                usuario_responsable,
                mensaje,
                excel_path
            ))
            connection.commit()
            print("Log registrado exitosamente.")
    except mysql.connector.Error as err:
        print(f"Error al registrar log: {err}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("Conexión cerrada correctamente.")

print("\nProceso finalizado. Datos insertados y log registrado.")
