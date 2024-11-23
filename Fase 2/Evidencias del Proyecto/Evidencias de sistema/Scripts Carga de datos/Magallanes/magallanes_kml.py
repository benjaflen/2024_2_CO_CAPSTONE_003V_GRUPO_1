import xml.etree.ElementTree as ET
import re
import pandas as pd
import mysql.connector
import datetime
import time

# Ruta del archivo KML
kml_path = 'proyectos_magallanes.kml' #Por seguridad de decidió ocultar la ruta

# Inicializar variables de log
datos_procesados = 0
datos_insertados = 0
datos_erroneos = 0
mensaje = ""

# Parsear el archivo KML
print("Parseando el archivo KML...")
inicio_procesamiento = time.time()

try:
    tree = ET.parse(kml_path)
    root = tree.getroot()
    namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}

    # Extraer información detallada y utilizar id_expediente como e_code y name como nombre
    placemarks = []

    for placemark in root.findall(".//kml:Placemark", namespaces):
        datos_procesados += 1  # Incrementar el contador de datos procesados

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

    # Conectar a la base de datos MariaDB
    print("\nConectando a la base de datos MariaDB...")
    connection = mysql.connector.connect(
        host='',  
        port='',
        user='',
        password='',
        database=''
    )

    # Obtener el usuario responsable de la conexión
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
        try:
            cursor.execute(insert_query, (placemark['e_code'], placemark['nombre'], placemark['lat'], placemark['lon']))
            datos_insertados += 1  # Incrementar contador de datos insertados
            print(f"Insertado: {placemark['e_code']}, nombre: {placemark['nombre']}, lat: {placemark['lat']}, lon: {placemark['lon']}")
        except mysql.connector.Error as err:
            datos_erroneos += 1  # Incrementar contador de datos erróneos
            print(f"Error al insertar {placemark['e_code']}: {err}")

    # Confirmar cambios y cerrar conexión
    connection.commit()
    cursor.close()
    connection.close()
    print("\nDatos insertados exitosamente en la base de datos.")

except Exception as e:
    mensaje = str(e)
    print(f"Error al procesar el archivo: {mensaje}")

finally:
    # Calcular tiempo de procesamiento
    tiempo_procesamiento = time.time() - inicio_procesamiento

    # Registrar log en la base de datos
    print("\nRegistrando log del proceso...")
    log_query = """
        INSERT INTO log (fecha_hora, archivo_nombre, tipo_archivo, datos_procesados, datos_insertados, datos_erroneos, 
                         tiempo_procesamiento, usuario_responsable, mensaje, archivo_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        connection = mysql.connector.connect(
            host='',
            port='',
            user='',
            password='',
            database=''
        )
        cursor = connection.cursor()
        cursor.execute(log_query, (
            datetime.datetime.now(),  # fecha_hora
            kml_path.split("\\")[-1],  # archivo_nombre
            "KML",  # tipo_archivo
            datos_procesados,  # datos_procesados
            datos_insertados,  # datos_insertados
            datos_erroneos,  # datos_erroneos
            tiempo_procesamiento,  # tiempo_procesamiento
            usuario_responsable,  # usuario_responsable
            mensaje,  # mensaje
            kml_path  # archivo_path
        ))
        connection.commit()
        print("Log registrado exitosamente.")
    except mysql.connector.Error as err:
        print(f"Error al registrar log: {err}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
