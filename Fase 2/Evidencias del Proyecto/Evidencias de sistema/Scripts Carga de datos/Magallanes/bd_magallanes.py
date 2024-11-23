import mysql.connector
import pandas as pd
import openpyxl
import datetime
import time

# Inicializar conexión
connection = None

# Cargar el archivo Excel
file_path = 'Base_de_datos_Magallanes_SEIA.xlsx' #Por Seguridad se decidió ocultar la ruta
df_clean = pd.read_excel(file_path, sheet_name='Magallanes_TOTAL', skiprows=1)

# Verificar columnas y dimensiones
print(f"Columnas encontradas en el archivo: {df_clean.columns}")
print(f"Dimensiones del DataFrame: {df_clean.shape}")

# Inicializar variables para el registro de log
datos_procesados = 0
urls_actualizadas = 0
errores = 0
mensaje = ""
usuario_responsable = "desconocido"  # Valor por defecto si la conexión falla

# Marcar inicio del procesamiento
inicio_procesamiento = time.time()

try:
    # Seleccionar y renombrar columnas necesarias
    df_clean = df_clean[[
        'Nombre', 'CPS disponible', 'archivo', 'tipo de fondo', 'Bat', 'MO', 
        'Gra', 'Macro', 'Ph, Re', 'Corr', 'Colum', 'Región', 'Comunas', 
        'Titular', 'Inversión', 'Estado', 'Fecha calificación', 'Latitud ', 'Longitud '
    ]]
    df_clean.columns = [
        'Nombre', 'CPS disponible', 'archivo', 'tipo de fondo', 'Bat', 'MO', 
        'Gra', 'Macro', 'Ph_Re', 'Corr', 'Colum', 'Región', 'Comunas', 
        'Titular', 'Inversión', 'Estado', 'Fecha calificación', 'Latitud', 'Longitud'
    ]

    # Convertir latitud y longitud a float
    df_clean['Latitud'] = df_clean['Latitud'].astype(float)
    df_clean['Longitud'] = df_clean['Longitud'].astype(float)

    # Reemplazar valores en columnas de disponibilidad
    availability_columns = ['Bat', 'MO', 'Gra', 'Macro', 'Ph_Re', 'Corr', 'Colum']
    df_clean[availability_columns] = df_clean[availability_columns].replace({'/': 'Disponible', '_': 'No Disponible'})

    # Cargar el archivo con openpyxl para extraer hipervínculos
    wb = openpyxl.load_workbook(file_path)
    ws = wb['Magallanes_TOTAL']

    # Obtener el índice de la columna "archivo"
    archivo_col_idx = df_clean.columns.get_loc("archivo") + 1

    # Extraer los hipervínculos de la columna 'archivo'
    urls = []
    for row in ws.iter_rows(min_row=4, max_row=len(df_clean) + 3, min_col=archivo_col_idx, max_col=archivo_col_idx):
        for cell in row:
            if cell.hyperlink:
                urls.append(cell.hyperlink.target)
            else:
                urls.append(None)

    # Agregar las URLs extraídas al DataFrame
    df_clean['archivo_url'] = urls

    print(f"URLs extraídas: {len(urls)}")

    # Conectar a la base de datos MariaDB
    print("\nConectando a la base de datos MariaDB...")
    connection = mysql.connector.connect(
        host='',
        port='',
        user='',
        password='',
        database=''
    )

    # Obtener el usuario conectado
    usuario_responsable = connection.user
    print('Conexión exitosa')

    # Crear el cursor con buffered=True
    cursor = connection.cursor(buffered=True)

    # Consultas SQL
    select_query = """
    SELECT archivo_url FROM estacion WHERE lat = %s AND lon = %s
    """
    update_query = """
    UPDATE estacion SET archivo_url = %s, fecha = %s WHERE lat = %s AND lon = %s
    """

    # Insertar URLs y fechas cuando hay coincidencia de latitud y longitud
    print("\nInsertando URLs y fechas cuando hay coincidencia de latitud y longitud...")
    for _, row in df_clean.iterrows():
        datos_procesados += 1
        lat = row['Latitud']
        lon = row['Longitud']
        url = row['archivo_url']
        fecha_calificacion = row['Fecha calificación']

        # Convertir 'Fecha calificación' al formato YYYY-MM-DD
        if not pd.isnull(fecha_calificacion):  # Validar que no sea NaN
            fecha = pd.to_datetime(fecha_calificacion).strftime('%Y-%m-%d')
        else:
            fecha = None

        if url or fecha:
            try:
                # Verificar coincidencia
                cursor.execute(select_query, (lat, lon))
                result = cursor.fetchone()

                if result is not None:
                    print(f"Coincidencia encontrada para lat={lat}, lon={lon}. Actualizando URL y Fecha.")
                    cursor.execute(update_query, (url, fecha, lat, lon))
                    urls_actualizadas += 1
                else:
                    print(f"No se encontró coincidencia para lat={lat}, lon={lon}.")
            except mysql.connector.Error as err:
                errores += 1
                print(f"Error al actualizar URL y Fecha para lat={lat}, lon={lon}: {err}")

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
                file_path.split("\\")[-1],
                "Excel",
                datos_procesados,
                urls_actualizadas,
                errores,
                tiempo_procesamiento,
                usuario_responsable,
                mensaje,
                file_path
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

print("\nProceso finalizado. URLs insertadas y log registrado.")
