import xml.etree.ElementTree as ET
import re
import pandas as pd
import mysql.connector
import datetime
import time

# Ruta del archivo KML
kml_path = 'proyectos_aysen.kml' #Por seguridad se decidió ocultar la ruta

# Parsear el archivo KML
print("Parseando el archivo KML...")
tree = ET.parse(kml_path)
root = tree.getroot()
namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}

# Extraer información detallada y utilizar id_expediente como e_code y name como nombre
placemarks = []

for placemark in root.findall(".//kml:Placemark", namespaces):
    # Procesar el nombre base
    nombre = placemark.find("kml:name", namespaces).text if placemark.find("kml:name", namespaces) is not None else "Sin_nombre"
    
    # Extraer el id_expediente del link dentro de la descripción
    description_elem = placemark.find("kml:description", namespaces)
    description = description_elem.text if description_elem is not None else ""
    
    # Buscar el id_expediente en la URL
    id_expediente_match = re.search(r'id_expediente=(\d+)', description)
    if id_expediente_match:
        e_code = id_expediente_match.group(1)
    else:
        print(f"No se encontró id_expediente en description: {description}")
        e_code = "sin_id"

    # Extraer coordenadas
    coordinates = placemark.find(".//kml:coordinates", namespaces)
    if coordinates is not None and coordinates.text:
        lon, lat, *_ = coordinates.text.strip().split(",")
        lat = float(lat)
        lon = float(lon)
    else:
        lat = lon = 0.0  # Coordenadas no válidas

    placemarks.append({'e_code': e_code, 'nombre': nombre, 'lat': lat, 'lon': lon})

# Mostrar el DataFrame para revisar los resultados antes de la inserción
placemarks_df = pd.DataFrame(placemarks)
print("\nDataFrame con e_code (id_expediente) y nombre:")
print(placemarks_df)

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
        INSERT INTO estacion (e_code, nombre, lat, lon)
        VALUES (%s, %s, %s, %s)
    """

    # Insertar cada fila en la tabla
    print("\nInsertando datos en la base de datos...")
    for placemark in placemarks:
        datos_procesados += 1
        try:
            cursor.execute(insert_query, (placemark['e_code'], placemark['nombre'], placemark['lat'], placemark['lon']))
            print(f"Insertado: {placemark['e_code']}, nombre: {placemark['nombre']}, lat: {placemark['lat']}, lon: {placemark['lon']}")
            datos_insertados += 1
        except mysql.connector.Error as err:
            print(f"Error al insertar {placemark['e_code']}: {err}")
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
                kml_path.split("\\")[-1],
                "KML",
                datos_procesados,
                datos_insertados,
                datos_erroneos,
                tiempo_procesamiento,
                usuario_responsable,
                mensaje,
                kml_path
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
