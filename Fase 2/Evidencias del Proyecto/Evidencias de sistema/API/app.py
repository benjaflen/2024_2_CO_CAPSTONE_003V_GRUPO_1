from flask import Flask, request, Response, jsonify, url_for
import mariadb
from datetime import datetime
import os
import pandas as pd
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from flask_cors import CORS  # Importar CORS

app = Flask(__name__)
CORS(app)  # Permitir CORS para todas las rutas
load_dotenv("/archivos/.env")
# Obtener configuración de la base de datos de variables de entorno
db_config = {
    'user': '',
    'password': '',
    'host': '',
    'database': '',
    'port': ''#int(os.getenv("DBPORT")),
}

def get_db_connection():
    try:
        conn = mariadb.connect(**db_config)
        return conn
    except mariadb.Error as e:
        app.logger.error(f"Error connecting to the database: {e}")
        return None

def validar_usuario(user, p_cod, e_code=None, check_equipos=False, check_metadatos=False):
    conn = get_db_connection()
    if conn is None:
        return False, "Error de conexión a la base de datos"
    
    try:
        cursor = conn.cursor(dictionary=True)
        # Verificar usuario y contraseña
        query = "SELECT * FROM usuarios WHERE user = ? AND p_cod = ?"
        cursor.execute(query, (user, p_cod))
        result = cursor.fetchone()

        if result is None:
            return False, "Credenciales inválidas"
        
        # Verificar permisos sobre la estación, si se especifica e_code
        if e_code:
            query = "SELECT * FROM permisos_estacion WHERE user = ? AND e_code = ?"
            cursor.execute(query, (user, e_code))
            permiso_estacion = cursor.fetchone()
            if permiso_estacion is None:
                return False, "Acceso denegado a la estación especificada"
        
        # Verificar permisos adicionales
        if check_equipos and not result.get('can_view_equipos'):
            print(f'result: {result}, check_equipos: {check_equipos}')
            return False, "No tiene permiso para ver equipos"
        
        if check_metadatos and not result.get('can_view_metadatos'):
            return False, "No tiene permiso para ver metadatos"
        
        return True, "Usuario autorizado"
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return False, "Error de base de datos"
    finally:
        cursor.close()
        conn.close()



##inicio
@app.route('/', methods=['GET'])
def inicio():
    response_lines = [
        "# Bienvenido a la aplicación CDOMCOPAS",
        "# Sistema desarrollado para la consulta y gestión de datos oceanográficos y meteorológicos.",
        "# Fecha de generación: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        "",
        "# Si tienes alguna consulta, no dudes en contactarnos en lofec@oceanografia.udec.cl",
        "# Para más información sobre el uso y condiciones del sistema, visita lofec.oceanografia.udec.cl",
        "",
        "### Ejemplos de uso de la API:",
        "",
        "1. Obtener la lista de estaciones disponibles:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetEstaciones?user=lofec&p_cod=pide_la_clave",
        "   Descripción: Devuelve una lista de estaciones, incluyendo su código, latitud y longitud.",
        "",
        "2. Ver equipos de una estación específica:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetEquipos?user=lofec&p_cod=pide_la_clave&e_code=DCHT",
        "   Descripción: Muestra todos los equipos registrados en la estación especificada por su código.",
        "",
        "3. Consultar sensores de un equipo:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetSensoresPorEquipo?user=lofec&p_cod=pide_la_clave&eq_code=HOBOTRTL",
        "   Descripción: Lista todos los sensores de un equipo, incluyendo su código, nombre, unidad de medición, y las fechas de inicio y fin de los datos registrados.",
        "",
        "4. Obtener los últimos datos de un sensor:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetUltimosDatosSensor?user=lofec&p_cod=pide_la_clave&s_code=WINDSPEED_MS_CO&limit=10",
        "   Descripción: Devuelve los últimos datos registrados por un sensor, limitado a un número específico de registros.",
        "",
        "5. Consultar datos de un sensor en un rango de fechas:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetDatosSensor?user=lofec&p_cod=pide_la_clave&s_code=WINDSPEED_MS_CO&fecha_inicio=2024-08-01&fecha_fin=2024-08-30",
        "   Descripción: Devuelve todos los datos de un sensor específico dentro del rango de fechas proporcionado.",
        "",
        "6. Ver dirección y velocidad del viento en una estación:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetWindData?user=lofec&p_cod=pide_la_clave&e_code=DCHT&fecha_inicio=2024-08-01&fecha_fin=2024-08-30",
        "   Descripción: Muestra la dirección y velocidad del viento en una estación específica dentro del rango de fechas indicado.",
        "",
        "7. Obtener metadatos de muestreo de estaciones:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetMetadatos?user=lofec&p_cod=pide_la_clave&e_code=EST18",
        "   Descripción: Lista los metadatos de muestreo disponibles por estación, permitiendo acceder a los datos y descargarlos en formato XML.",
        "",
        "8. Agregar una nueva predicción meteorológica, oceánica o de oleaje:",
        "   URL: POST http://api.lofec.oceanografia.udec.cl/AgregarPrediccion",
        "   Descripción: Permite agregar predicciones para modelos meteorológicos, oceánicos o de oleaje. El cuerpo de la solicitud debe estar en formato JSON.",
        "",
        "9. Obtener predicciones registradas:",
        "   URL: http://api.lofec.oceanografia.udec.cl/GetPredicciones?user=lofec&p_cod=pide_la_clave&forecast_type=FORECAST_WEATHER&fecha_inicio=2024-08-01&fecha_fin=2024-08-30",
        "   Descripción: Recupera predicciones de diferentes tipos (meteorológicas, oceánicas, de oleaje) en un rango de fechas específico.",
        "",
        "### Nota:",
        "   Para todas las solicitudes, es necesario proporcionar los parámetros 'user' y 'p_cod' para la autenticación."
    ]
    response_text = "\n".join(response_lines)
    return Response(response_text, mimetype='text/plain')




@app.route('/GetSerieSensor', methods=['GET'])
def get_serie_sensor():
    params = ['user', 'p_cod', 'e_code', 's_code', 'fecha_inicio', 'fecha_fin']
    for param in params:
        if not request.args.get(param):
            return Response(f"Falta el parámetro: {param}", status=400, mimetype='text/plain')

    user, p_cod, e_code, s_code, fecha_inicio, fecha_fin = (request.args.get(param) for param in params)

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT s.e_code, s.s_code, s.tf_nombre, s.um_notacion, ds.dato, ds.tiempo_lectura
            FROM sensor s
            JOIN datos_sensor ds ON s.s_code = ds.s_code
            WHERE s.e_code = ? AND s.s_code = ? AND ds.tiempo_lectura BETWEEN ? AND ?
            ORDER BY ds.tiempo_lectura
        """
        cursor.execute(query, (e_code, s_code, fecha_inicio, fecha_fin))
        results = cursor.fetchall()
        response_lines = [
            "#Datos provistos por CDOM a través del sistema CDOMCOPAS, generados el: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "#Para consultas, contactar al mail lofec@udec.cl",
            "#Revisar condiciones de uso en www.cdom.cl",
            "#Params , gmt: gmt-4",
            "#e_code,s_code,tf_nombre,um_notacion,dato,tiempo_lectura,"
        ]
        for row in results:
            line = "{},{},{},{},{},{}".format(
                row['e_code'], row['s_code'], row['tf_nombre'],
                row['um_notacion'], row['dato'],
                row['tiempo_lectura'].strftime('%Y-%m-%d %H:%M:%S')
            )
            response_lines.append(line)
        response_text = "\n".join(response_lines)
        return Response(response_text, mimetype='text/plain')
    except mariadb.Error as e:
        app.logger.error(f"Error executing query: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()


@app.route('/GetEquipos', methods=['GET'])
def get_equipos():
    user, p_cod, e_code = (request.args.get(param) for param in ['user', 'p_cod', 'e_code'])
    if not all([user, p_cod, e_code]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    autorizado, mensaje = validar_usuario(user, p_cod, e_code=e_code, check_equipos=True)
    if not autorizado:
        print(f'usuario no autorizado, usuario: {user}, p_cod: {p_cod}, e_code: {e_code}')
        return Response(mensaje, status=403, mimetype='text/plain')
        

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT e.eq_code, e.e_code, e.nombre, e.numero_serie
            FROM equipo e
            WHERE e.e_code = ?
        """
        cursor.execute(query, (e_code,))
        results = cursor.fetchall()

        df = pd.DataFrame(results)
        df.rename(columns={
            'eq_code': 'Código de Equipo',
            'e_code': 'Código de Estación',
            'nombre': 'Nombre del Equipo',
            'numero_serie': 'Número de Serie'
        }, inplace=True)

        # Agregar columna para los enlaces
        df['Ver Sensores'] = df['Código de Equipo'].apply(
            lambda x: f'<a href="{url_for("get_sensores_por_equipo", user=user, p_cod=p_cod, eq_code=x)}">Ver Sensores</a>'
        )

        html_table = df.to_html(classes='table table-striped', index=False, escape=False)
        return Response(html_table, mimetype='text/html')
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()


@app.route('/GetSensoresPorEquipo', methods=['GET'])
def get_sensores_por_equipo():
    user, p_cod, eq_code = (request.args.get(param) for param in ['user', 'p_cod', 'eq_code'])
    limit = request.args.get('limit', default=100, type=int)  # Parámetro 'limit' con valor por defecto de 100

    if not all([user, p_cod, eq_code]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT s.s_code, s.um_notacion,
                   MIN(ds.tiempo_lectura) AS fecha_minima,
                   MAX(ds.tiempo_lectura) AS fecha_maxima
            FROM sensor s
            LEFT JOIN datos_sensor ds ON s.s_code = ds.s_code
            WHERE s.eq_code = ?
            GROUP BY s.s_code, s.um_notacion
        """
        cursor.execute(query, (eq_code,))
        results = cursor.fetchall()

        df = pd.DataFrame(results)
        df.rename(columns={
            's_code': 'Código de Sensor',
            'um_notacion': 'Unidad de Medición',
            'fecha_minima': 'Fecha Mínima',
            'fecha_maxima': 'Fecha Máxima'
        }, inplace=True)

        # Agregar columna para los enlaces a los últimos elementos, con el límite incluido en la URL
        df['Ver Últimos Datos'] = df['Código de Sensor'].apply(
            lambda x: f'<a href="{url_for("get_ultimos_datos_sensor", user=user, p_cod=p_cod, s_code=x, limit=limit)}">Ver Datos</a>'
        )

        html_table = df.to_html(classes='table table-striped', index=False, escape=False)
        
        return Response(html_table, mimetype='text/html')
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

@app.route('/GetUltimosDatosSensor', methods=['GET'])
def get_ultimos_datos_sensor():
    user, p_cod, s_code = (request.args.get(param) for param in ['user', 'p_cod', 's_code'])
    limit = request.args.get('limit', default=100, type=int)  # Parámetro 'limit' con valor por defecto de 100

    if not all([user, p_cod, s_code]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT ds.s_code, ds.tiempo_lectura, ds.dato, s.tf_nombre, s.um_notacion
            FROM datos_sensor ds
            JOIN sensor s ON ds.s_code = s.s_code
            WHERE ds.s_code = ?
            ORDER BY ds.tiempo_lectura DESC
            LIMIT ?
        """
        cursor.execute(query, (s_code, limit))
        results = cursor.fetchall()

        df = pd.DataFrame(results)
        df.rename(columns={
            's_code': 'Código de Sensor',
            'tf_nombre': 'Nombre del Sensor',
            'um_notacion': 'Unidad de Medición',
            'dato': 'Dato',
            'tiempo_lectura': 'Tiempo de Lectura'
        }, inplace=True)

        html_table = df.to_html(classes='table table-striped', index=False)
        
        return Response(html_table, mimetype='text/html')
    except mariadb.Error as e:
        app.logger.error(f"Error executing query: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()



@app.route('/GetEstaciones', methods=['GET'])
def get_estaciones():
    user, p_cod = request.args.get('user'), request.args.get('p_cod')
    
    if not all([user, p_cod]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT e.e_code, e.lat, e.lon, e.url, e.nombre, e.archivo_url, e.fecha
            FROM estacion e
        """
        cursor.execute(query)
        results = cursor.fetchall()

        df = pd.DataFrame(results)
        df.rename(columns={
            'e_code': 'Código de Estación',
            'nombre': 'Nombre',
            'lat': 'Latitud',
            'lon': 'Longitud',            
            'url': 'URL',
            'archivo_url': 'archivo_url',
            'fecha': 'Fecha'
            
        }, inplace=True)


        html_table = df.to_html(classes='table table-striped', index=False, escape=False)
        
        return Response(html_table, mimetype='text/html')
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

@app.route('/GetDatosSensor', methods=['GET'])
def get_datos_sensor():
    user, p_cod, s_code, fecha_inicio, fecha_fin = (request.args.get(param) for param in ['user', 'p_cod', 's_code', 'fecha_inicio', 'fecha_fin'])

    if not all([user, p_cod, s_code, fecha_inicio, fecha_fin]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT ds.s_code, ds.tiempo_lectura, ds.dato, s.tf_nombre, s.um_notacion
            FROM datos_sensor ds
            JOIN sensor s ON ds.s_code = s.s_code
            WHERE ds.s_code = ? AND ds.tiempo_lectura BETWEEN ? AND ?
            ORDER BY ds.tiempo_lectura
        """
        cursor.execute(query, (s_code, fecha_inicio, fecha_fin))
        results = cursor.fetchall()

        df = pd.DataFrame(results)
        df.rename(columns={
            's_code': 'Código de Sensor',
            'tf_nombre': 'Nombre del Sensor',
            'um_notacion': 'Unidad de Medición',
            'dato': 'Dato',
            'tiempo_lectura': 'Tiempo de Lectura'
        }, inplace=True)

        html_table = df.to_html(classes='table table-striped', index=False)
        
        return Response(html_table, mimetype='text/html')
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

#
@app.route('/GetListaSensores', methods=['GET'])
def get_lista_sensores():
    user, p_cod, e_code = (request.args.get(param) for param in ['user', 'p_cod', 'e_code'])
    if not all([user, p_cod, e_code]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT s.e_code, s.s_code, s.tf_nombre, s.um_notacion, ds.dato, ds.tiempo_lectura
            FROM sensor s
            JOIN datos_sensor ds ON s.s_code = ds.s_code
            WHERE s.e_code = ? AND ds.tiempo_lectura = (
                SELECT MAX(ds2.tiempo_lectura) 
                FROM datos_sensor ds2 
                WHERE ds2.s_code = s.s_code
            )
        """
        cursor.execute(query, (e_code,))
        results = cursor.fetchall()
        response_lines = [
            "#Datos provistos por CDOM a través del sistema CDOMCOPAS, generados el: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "#Para consultas, contactar al mail lofec@udec.cl",
            "#Revisar condiciones de uso en www.cdom.cl",
            "#Params , gmt: gmt-4",
            "#e_code,s_code,tf_nombre,um_notacion,dato,ultima_lectura,"
        ]
        for row in results:
            line = "{},{},{},{},{},{}".format(
                row['e_code'], row['s_code'], row['tf_nombre'],
                row['um_notacion'], row['dato'],
                row['tiempo_lectura'].strftime('%Y-%m-%d %H:%M:%S')
            )
            response_lines.append(line)
        response_text = "\n".join(response_lines)
        return Response(response_text, mimetype='text/plain')
    except mariadb.Error as e:
        app.logger.error(f"Error executing query: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

@app.route('/IngresarEstacion', methods=['GET'])
def ingresar_estacion():
    params = ['user', 'p_cod', 'e_code', 'lat', 'lon']
    for param in params:
        if not request.args.get(param):
            return Response(f"Falta el parámetro: {param}", status=400, mimetype='text/plain')

    user, p_cod, e_code, lat, lon = (request.args.get(param) for param in params)

    if user != 'wodan':
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor()
        query = "INSERT INTO estacion (e_code, lat, lon) VALUES (?, ?, ?)"
        cursor.execute(query, (e_code, lat, lon))
        conn.commit()
        return Response("Estación ingresada correctamente", mimetype='text/plain')
    except mariadb.Error as e:
        app.logger.error(f"Error executing query: {e}")
        return Response(f"Error: {e}", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

@app.route('/AgregarEquipo', methods=['GET'])
def agregar_equipo():
    params = ['user', 'p_cod', 'eq_code', 'nombre', 'numero_serie','e_code']
    for param in params:
        if not request.args.get(param):
            return Response(f"Falta el parámetro: {param}", status=400, mimetype='text/plain')

    user, p_cod, eq_code, nombre, numero_serie,e_code = (request.args.get(param) for param in params)

    if user != 'wodan':
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor()
        query = "INSERT INTO equipo (eq_code, nombre, numero_serie,e_code) VALUES (?, ?, ?,?)"
        cursor.execute(query, (eq_code, nombre, numero_serie,e_code))
        conn.commit()
        return Response("Equipo ingresado correctamente", mimetype='text/plain')
    except mariadb.Error as e:
        app.logger.error(f"Error executing query: {e}")
        return Response(f"Error: {e}", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()



@app.route('/GetMetadatos', methods=['GET'])
def get_metadatos():
    user, p_cod, e_code = request.args.get('user'), request.args.get('p_cod'), request.args.get('e_code')
    if not all([user, p_cod, e_code]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    autorizado, mensaje = validar_usuario(user, p_cod, e_code=e_code, check_metadatos=True)
    if not autorizado:
        return Response(mensaje, status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT m.StartTime, m.e_code
            FROM Metadatos m
            WHERE m.e_code = ?
        """
        cursor.execute(query, (e_code,))
        results = cursor.fetchall()

        df = pd.DataFrame(results)
        df.rename(columns={
            'StartTime': 'Fecha de muestreo',
            'e_code': 'Código de Estación'
        }, inplace=True)

        # Agregar columnas para los enlaces
        df['Tabla de datos'] = df['Fecha de muestreo'].apply(
            lambda x: f'<a href="{url_for("get_datos_medicion", user=user, p_cod=p_cod, start_time=x, e_code=e_code)}">Ver datos</a>'
        )
        df['Get Data'] = df['Fecha de muestreo'].apply(
            lambda x: f'<a href="{url_for("get_datos_medicion_xml", user=user, p_cod=p_cod, start_time=x, e_code=e_code)}">Descargar XML</a>'
        )

        html_table = df.to_html(classes='table table-striped', index=False, escape=False)
        return Response(html_table, mimetype='text/html')
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

@app.route('/GetDatosMedicion', methods=['GET'])
def get_datos_medicion():
    user, p_cod = request.args.get('user'), request.args.get('p_cod')
    start_time = request.args.get('start_time')
    e_code = request.args.get('e_code')
    
    if not all([user, p_cod, start_time, e_code]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT dm.*
            FROM DatosMedicion dm
            JOIN Metadatos m ON dm.StartTime = m.StartTime
            WHERE dm.StartTime = ? AND m.e_code = ?
        """
        cursor.execute(query, (start_time, e_code))
        results = cursor.fetchall()

        if not results:
            return Response("No se encontraron datos para los parámetros proporcionados", status=404, mimetype='text/plain')
        
        # Convertir los resultados a un DataFrame de pandas
        df = pd.DataFrame(results)
        
        # Convertir el DataFrame a una tabla HTML
        html_table = df.to_html(index=False, border=0)
        
        # Devolver la tabla HTML en la respuesta
        return Response(html_table, status=200, mimetype='text/html')
    
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    
    finally:
        cursor.close()
        conn.close()

@app.route('/GetDatosMedicionXML', methods=['GET'])
def get_datos_medicion_xml():
    user, p_cod = request.args.get('user'), request.args.get('p_cod')
    start_time = request.args.get('start_time')
    e_code = request.args.get('e_code')

    if not all([user, p_cod, start_time, e_code]):
        return Response("Faltan parámetros", status=400, mimetype='text/plain')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT dm.*
            FROM DatosMedicion dm
            JOIN Metadatos m ON dm.StartTime = m.StartTime
            WHERE dm.StartTime = ? AND m.e_code = ?
        """
        cursor.execute(query, (start_time, e_code))
        results = cursor.fetchall()

        root = ET.Element("DatosMedicion")
        for row in results:
            item = ET.SubElement(root, "Item")
            for key, val in row.items():
                child = ET.SubElement(item, key)
                child.text = str(val)

        xml_data = ET.tostring(root, encoding='utf-8', method='xml')
        return Response(xml_data, mimetype='application/xml', headers={"Content-Disposition": f"attachment;filename=DatosMedicion_{start_time}_e_code_{e_code}.xml"})
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()




@app.route('/GetWindDirection', methods=['GET'])
def get_wind_direction():
    params = ['user', 'p_cod', 'e_code', 'fecha_inicio', 'fecha_fin']
    for param in params:
        if not request.args.get(param):
            return Response(f"Falta el parámetro: {param}", status=400, mimetype='text/plain')

    user, p_cod, e_code, fecha_inicio, fecha_fin = (request.args.get(param) for param in params)

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT ds.s_code, ds.dato, ds.tiempo_lectura
            FROM datos_sensor ds
            JOIN sensor s ON ds.s_code = s.s_code
            JOIN equipo e ON s.eq_code = e.eq_code
            JOIN estacion est ON e.e_code = est.e_code
            WHERE est.e_code = ? AND s.tf_nombre = 'direction_Avg' AND ds.tiempo_lectura BETWEEN ? AND ?
            ORDER BY ds.tiempo_lectura
        """
        
        # Mostrar los parámetros para depuración
        app.logger.debug(f"Parámetros: e_code={e_code}, fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}")
        
        cursor.execute(query, (e_code, fecha_inicio, fecha_fin))
        results = cursor.fetchall()
        
        # Mostrar resultados obtenidos para depuración
        app.logger.debug(f"Resultados obtenidos: {results}")

        response_lines = [
            "#Datos provistos por CDOM a través del sistema CDOMCOPAS, generados el: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "#Para consultas, contactar al mail lofec@udec.cl",
            "#Revisar condiciones de uso en www.cdom.cl",
            "#Params , gmt: gmt-4",
            "#s_code,dato,tiempo_lectura,"
        ]
        for row in results:
            line = "{},{},{}".format(
                row['s_code'], row['dato'],
                row['tiempo_lectura'].strftime('%Y-%m-%d %H:%M:%S')
            )
            response_lines.append(line)
        response_text = "\n".join(response_lines)
        return Response(response_text, mimetype='text/plain')
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response(f"Error ejecutando la consulta: {e}", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()


@app.route('/GetWindData', methods=['GET'])
def get_wind_data():
    params = ['user', 'p_cod', 'e_code', 'fecha_inicio', 'fecha_fin']
    for param in params:
        if not request.args.get(param):
            return Response(f"Falta el parámetro: {param}", status=400, mimetype='text/plain')

    user, p_cod, e_code, fecha_inicio, fecha_fin = (request.args.get(param) for param in params)

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT ds.tiempo_lectura,
                MAX(CASE 
                    WHEN LOWER(s.tf_nombre) LIKE '%dir%' 
                         AND LOWER(s.s_code) LIKE '%wind%' THEN ds.dato 
                    END) AS direccion,
                MAX(CASE 
                    WHEN LOWER(s.tf_nombre) LIKE '%dir%' 
                         AND LOWER(s.s_code) LIKE '%wind%' THEN s.um_notacion 
                    END) AS um_notacion_direccion,
                MAX(CASE 
                    WHEN LOWER(s.tf_nombre) LIKE '%speed%' 
                         AND LOWER(s.tf_nombre) LIKE '%avg%' 
                         AND LOWER(s.s_code) LIKE '%wind%' THEN ds.dato 
                    END) AS velocidad,
                MAX(CASE 
                    WHEN LOWER(s.tf_nombre) LIKE '%speed%' 
                         AND LOWER(s.tf_nombre) LIKE '%avg%' 
                         AND LOWER(s.s_code) LIKE '%wind%' THEN s.um_notacion 
                    END) AS um_notacion_velocidad
            FROM datos_sensor ds
            JOIN sensor s ON ds.s_code = s.s_code
            JOIN equipo e ON s.eq_code = e.eq_code
            JOIN estacion est ON e.e_code = est.e_code
            WHERE est.e_code = ? AND ds.tiempo_lectura BETWEEN ? AND ?
            GROUP BY ds.tiempo_lectura
            ORDER BY ds.tiempo_lectura
        """

        # Mostrar los parámetros para depuración
        app.logger.debug(f"Parámetros: e_code={e_code}, fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}")
        
        cursor.execute(query, (e_code, fecha_inicio, fecha_fin))
        results = cursor.fetchall()
        
        # Mostrar resultados obtenidos para depuración
        app.logger.debug(f"Resultados obtenidos: {results}")

        response_lines = [
            "#Datos provistos por CDOM a través del sistema CDOMCOPAS, generados el: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "#Para consultas, contactar al mail lofec@oceanografia.udec.cl",
            "#Revisar condiciones de uso en lofec.oceanografia.udec.cl",
            "#Params , gmt: gmt-0",
            "#tiempo_lectura,direccion,um_notacion_direccion,velocidad,um_notacion_velocidad"
        ]
        for row in results:
            line = "{},{},{},{},{}".format(
                row['tiempo_lectura'].strftime('%Y-%m-%d %H:%M:%S'), 
                row['direccion'], 
                row['um_notacion_direccion'], 
                row['velocidad'], 
                row['um_notacion_velocidad']
            )
            response_lines.append(line)
        response_text = "\n".join(response_lines)
        return Response(response_text, mimetype='text/plain')
    except mariadb.Error as e:
        app.logger.error(f"Error ejecutando la consulta: {e}")
        return Response(f"Error ejecutando la consulta: {e}", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

@app.route('/AgregarPrediccion', methods=['POST'])
def agregar_prediccion():
    data = request.get_json()
    if not data:
        return Response("El cuerpo de la solicitud debe ser JSON", status=400, mimetype='text/plain')

    required_params = ['user', 'p_cod', 'timestamp', 'lat', 'lon', 'nombre_modelo', 'forecast_type', 'forecasts']
    for param in required_params:
        if param not in data:
            return Response(f"Falta el parámetro: {param}", status=400, mimetype='text/plain')

    user = data['user']
    p_cod = data['p_cod']
    timestamp = data['timestamp']
    lat = data['lat']
    lon = data['lon']
    nombre_modelo = data['nombre_modelo']
    forecast_type = data['forecast_type']
    forecasts = data['forecasts']

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')

    try:
        cursor = conn.cursor()
        query_pred = "INSERT INTO PREDICTIONS (Timestamp, Lat, Lon, NombreModelo) VALUES (?, ?, ?, ?)"
        cursor.execute(query_pred, (timestamp, lat, lon, nombre_modelo))

        if forecast_type == 'FORECAST_OCEAN':
            query = """
            INSERT INTO FORECAST_OCEAN (Fecha, VelocidadCorriente, DirecciónCorriente, AlturadelMar, TemperaturaMar, SalinidadMar, PREDICTIONS_Timestamp, PREDICTIONS_Lat, PREDICTIONS_Lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        elif forecast_type == 'FORECAST_DOP':
            query = """
            INSERT INTO FORECAST_DOP (Fecha, AlturaSignificativa, DominantWaveFrequency, SeaSurfaceWaveFromDirection, SeaSurfaceWavePeakDirection, DominantWavePeriod, PREDICTIONS_Timestamp, PREDICTIONS_Lat, PREDICTIONS_Lon)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        elif forecast_type == 'FORECAST_WEATHER':
            query = """
            INSERT INTO FORECAST_WEATHER (Fecha, VelocidadViento, DireccionViento, PREDICTIONS_Timestamp, PREDICTIONS_Lat, PREDICTIONS_Lon)
            VALUES (?, ?, ?, ?, ?, ?)
            """
        else:
            return Response("Tipo de previsión no válido", status=400, mimetype='text/plain')

        for forecast in forecasts:
            if forecast_type == 'FORECAST_OCEAN':
                cursor.execute(query, (
                    forecast['Fecha'],
                    forecast.get('VelocidadCorriente'),
                    forecast.get('DirecciónCorriente'),
                    forecast.get('AlturadelMar'),
                    forecast.get('TemperaturaMar'),
                    forecast.get('SalinidadMar'),
                    timestamp,
                    lat,
                    lon
                ))
            elif forecast_type == 'FORECAST_DOP':
                dominant_wave_frequency = forecast.get('DominantWaveFrequency')
                dominant_wave_period = 1 / dominant_wave_frequency if dominant_wave_frequency and dominant_wave_frequency != 0 else None
                cursor.execute(query, (
                    forecast['Fecha'],
                    forecast.get('AlturaSignificativa'),
                    dominant_wave_frequency,
                    forecast.get('SeaSurfaceWaveFromDirection'),
                    forecast.get('SeaSurfaceWavePeakDirection'),
                    dominant_wave_period,
                    timestamp,
                    lat,
                    lon
                ))
            elif forecast_type == 'FORECAST_WEATHER':
                cursor.execute(query, (
                    forecast['Fecha'],
                    forecast.get('VelocidadViento'),
                    forecast.get('DireccionViento'),
                    timestamp,
                    lat,
                    lon
                ))

        conn.commit()
        return Response("Predicción y forecast ingresados correctamente", mimetype='text/plain')
    except mariadb.Error as e:
        conn.rollback()
        app.logger.error(f"Error executing query: {e}")
        return Response(f"Error: {e}", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()

@app.route('/GetPredicciones', methods=['GET'])
def get_predicciones():
    params = ['user', 'p_cod', 'forecast_type']
    for param in params:
        if not request.args.get(param):
            return Response(f"Falta el parámetro: {param}", status=400, mimetype='text/plain')

    user = request.args.get('user')
    p_cod = request.args.get('p_cod')
    forecast_type = request.args.get('forecast_type')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    last_n = request.args.get('last_n')

    if not validar_usuario(user, p_cod):
        return Response("Usuario no autorizado", status=403, mimetype='text/plain')

    conn = get_db_connection()
    if conn is None:
        return Response("Error de conexión a la base de datos", status=500, mimetype='text/plain')

    try:
        cursor = conn.cursor(dictionary=True)
        
        # Determine forecast table and base query based on forecast_type
        if forecast_type == 'FORECAST_OCEAN':
            forecast_table = 'FORECAST_OCEAN'
            base_query = """
                SELECT f.Fecha, f.VelocidadCorriente, f.DirecciónCorriente, f.AlturadelMar, f.TemperaturaMar, f.SalinidadMar,
                       p.Timestamp, p.Lat, p.Lon, p.NombreModelo
                FROM FORECAST_OCEAN f
                JOIN PREDICTIONS p ON f.PREDICTIONS_Timestamp = p.Timestamp AND f.PREDICTIONS_Lat = p.Lat AND f.PREDICTIONS_Lon = p.Lon
            """
        elif forecast_type == 'FORECAST_DOP':
            forecast_table = 'FORECAST_DOP'
            base_query = """
                SELECT f.Fecha, f.AlturaSignificativa, f.DominantWaveFrequency, f.SeaSurfaceWaveFromDirection, f.SeaSurfaceWavePeakDirection, f.DominantWavePeriod,
                       p.Timestamp, p.Lat, p.Lon, p.NombreModelo
                FROM FORECAST_DOP f
                JOIN PREDICTIONS p ON f.PREDICTIONS_Timestamp = p.Timestamp AND f.PREDICTIONS_Lat = p.Lat AND f.PREDICTIONS_Lon = p.Lon
            """
        elif forecast_type == 'FORECAST_WEATHER':
            forecast_table = 'FORECAST_WEATHER'
            base_query = """
                SELECT f.Fecha, f.VelocidadViento, f.DireccionViento,
                       p.Timestamp, p.Lat, p.Lon, p.NombreModelo
                FROM FORECAST_WEATHER f
                JOIN PREDICTIONS p ON f.PREDICTIONS_Timestamp = p.Timestamp AND f.PREDICTIONS_Lat = p.Lat AND f.PREDICTIONS_Lon = p.Lon
            """
        else:
            return Response("Tipo de previsión no válido", status=400, mimetype='text/plain')

        # Add conditions to the query
        conditions = []
        params = []
        if fecha_inicio and fecha_fin:
            conditions.append("f.Fecha BETWEEN ? AND ?")
            params.extend([fecha_inicio, fecha_fin])
        if last_n:
            conditions.append("1=1 ORDER BY f.Fecha DESC LIMIT ?")
            params.append(int(last_n))
        
        # Add conditions to the base query
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Execute the query
        cursor.execute(base_query, tuple(params))
        results = cursor.fetchall()

        response_lines = [
            "#Datos provistos por CDOM a través del sistema CDOMCOPAS, generados el: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            "#Para consultas, contactar al mail lofec@udec.cl",
            "#Revisar condiciones de uso en www.cdom.cl",
            "#Params , gmt: gmt-4"
        ]

        # Add header based on forecast_type
        if forecast_type == 'FORECAST_OCEAN':
            response_lines.append("#Fecha,VelocidadCorriente,DirecciónCorriente,AlturadelMar,TemperaturaMar,SalinidadMar,Timestamp,Lat,Lon,NombreModelo")
        elif forecast_type == 'FORECAST_DOP':
            response_lines.append("#Fecha,AlturaSignificativa,DominantWaveFrequency,SeaSurfaceWaveFromDirection,SeaSurfaceWavePeakDirection,DominantWavePeriod,Timestamp,Lat,Lon,NombreModelo")
        elif forecast_type == 'FORECAST_WEATHER':
            response_lines.append("#Fecha,VelocidadViento,DireccionViento,Timestamp,Lat,Lon,NombreModelo")

        for row in results:
            if forecast_type == 'FORECAST_OCEAN':
                line = "{},{},{},{},{},{},{},{},{},{}".format(
                    row['Fecha'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['VelocidadCorriente'], row['DirecciónCorriente'],
                    row['AlturadelMar'], row['TemperaturaMar'], row['SalinidadMar'],
                    row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['Lat'], row['Lon'], row['NombreModelo']
                )
            elif forecast_type == 'FORECAST_DOP':
                line = "{},{},{},{},{},{},{},{},{},{}".format(
                    row['Fecha'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['AlturaSignificativa'], row['DominantWaveFrequency'],
                    row['SeaSurfaceWaveFromDirection'], row['SeaSurfaceWavePeakDirection'],
                    row['DominantWavePeriod'],
                    row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['Lat'], row['Lon'], row['NombreModelo']
                )
            elif forecast_type == 'FORECAST_WEATHER':
                line = "{},{},{},{},{},{},{}".format(
                    row['Fecha'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['VelocidadViento'], row['DireccionViento'],
                    row['Timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    row['Lat'], row['Lon'], row['NombreModelo']
                )
            response_lines.append(line)

        response_text = "\n".join(response_lines)
        return Response(response_text, mimetype='text/plain')

    except mariadb.Error as e:
        app.logger.error(f"Error executing query: {e}")
        return Response("Error ejecutando la consulta", status=500, mimetype='text/plain')
    finally:
        cursor.close()
        conn.close()




@app.route('/perfiles/<e_code>', methods=['GET'])
def ver_perfiles(e_code):
    """Endpoint para ver perfiles de una estación específica en formato HTML"""
    conn = get_db_connection()
    if conn is None:
        return "Error de conexión a la base de datos", 500

    try:
        cursor = conn.cursor(dictionary=True)
        
        # Consultar el nombre de la estación y sus perfiles asociados al e_code
        query_nombre = "SELECT nombre FROM estacion WHERE e_code = ?"
        cursor.execute(query_nombre, (e_code,))
        nombre_result = cursor.fetchone()
        nombre_estacion = nombre_result['nombre'] if nombre_result else f"Estación {e_code}"
        
        # Consultar perfiles asociados al e_code de la estación
        query_perfiles = """
            SELECT estacion, profundidad, temperatura, salinidad, oxigeno_disuelto
            FROM perfiles
            WHERE e_code = ?
        """
        cursor.execute(query_perfiles, (e_code,))
        perfiles = cursor.fetchall()

        # Generar tabla HTML sin estilo, solo con funcionalidad de ordenación
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Perfiles de la Concesión</title>
        </head>
        <body>  
            <h3>Perfiles de la concesión "{nombre_estacion}"</h3>
            <table border="1" id="perfiles-table" >
                <thead>
                    <tr>
                        <th>Estación <button onclick="window.filterStations()"><i class="bi bi-funnel"></i></button></th>
                        <th>Profundidad <button onclick="window.sortTable(1)"><i class="bi bi-arrow-down-up"></i></button></th>
                        <th>Temperatura <button onclick="window.sortTable(2)"><i class="bi bi-arrow-down-up"></i></button></th>
                        <th>Salinidad <button onclick="window.sortTable(3)"><i class="bi bi-arrow-down-up"></i></button></th>
                        <th>Oxígeno Disuelto <button onclick="window.sortTable(4)"><i class="bi bi-arrow-down-up"></i></button></th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for perfil in perfiles:
            html += "<tr>"
            html += f"<td>{perfil['estacion']}</td>"
            html += f"<td>{perfil['profundidad']}</td>"
            html += f"<td>{perfil['temperatura']}</td>"
            html += f"<td>{perfil['salinidad']}</td>"
            html += f"<td>{perfil['oxigeno_disuelto']}</td>"
            html += "</tr>"
        
        html += """
                    </tbody>
                </table>
            </body>
        </html>
        """

        return Response(html, mimetype="text/html")

    except mariadb.Error as e:
        app.logger.error(f"Error retrieving profiles: {e}")
        return "Error al obtener perfiles", 500

    finally:
        cursor.close()
        conn.close()



@app.route('/perfiles/', methods=['GET'])
def ver_todos_los_perfiles():
    """Endpoint para ver todos los perfiles de todas las estaciones en formato HTML"""
    conn = get_db_connection()
    if conn is None:
        return "Error de conexión a la base de datos", 500

    try:
        cursor = conn.cursor(dictionary=True)
        
        # Consultar todos los perfiles de todas las estaciones
        query = """
            SELECT e_code, profundidad, temperatura, salinidad, oxigeno_disuelto
            FROM perfiles
        """
        cursor.execute(query)
        perfiles = cursor.fetchall()

        # Generar tabla HTML
        html = """
        <h3>Perfiles de todas las estaciones</h3>
        <table border="1">
            <tr>
                <th>Código de Concesión<s (e_code)</th>
                <th>Profundidad</th>
                <th>Temperatura</th>
                <th>Salinidad</th>
                <th>Oxígeno Disuelto</th>
            </tr>
        """
        
        for perfil in perfiles:
            html += "<tr>"
            html += f"<td>{perfil['e_code']}</td>"
            html += f"<td>{perfil['profundidad']}</td>"
            html += f"<td>{perfil['temperatura']}</td>"
            html += f"<td>{perfil['salinidad']}</td>"
            html += f"<td>{perfil['oxigeno_disuelto']}</td>"
            html += "</tr>"
        
        html += "</table>"

        return Response(html, mimetype="text/html")

    except mariadb.Error as e:
        app.logger.error(f"Error retrieving profiles: {e}")
        return "Error al obtener perfiles", 500

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9091, debug=True)
