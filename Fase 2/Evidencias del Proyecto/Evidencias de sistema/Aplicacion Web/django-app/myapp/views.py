from bs4 import BeautifulSoup
from django.shortcuts import render
import requests
import json

def estaciones_view(request):
    # URL de la API
    api_url = "http://127.0.0.1:9091/GetEstaciones?user=lofec&p_cod=1234"
    
    # Realiza la solicitud a la API
    response = requests.get(api_url)
    data = response.text

    # Usar BeautifulSoup para procesar el HTML
    soup = BeautifulSoup(data, 'html.parser')

    # Extraer la tabla de estaciones
    table = soup.find('table')
    if not table:
        print("No se encontró ninguna tabla en la respuesta HTML.")
        return render(request, 'index.html', {'estaciones': json.dumps([])})

    # Buscar todas las filas (<tr>) de la tabla, omitiendo el encabezado (<thead>)
    estaciones = []
    rows = table.find_all('tr')[1:]  # Omitimos la primera fila que es la cabecera

    for row in rows:
        columns = row.find_all('td')  # Extraer todas las celdas (<td>) de la fila
        
        # Asegúrate de que tienes suficientes columnas para evitar errores de índice
        if len(columns) >= 6:  # Aseguramos que haya al menos seis columnas
            codigo_estacion = columns[0].get_text().strip()  # Código de la estación
            latitud = columns[1].get_text().strip()          # Latitud
            longitud = columns[2].get_text().strip()         # Longitud
            url = columns[3].get_text().strip()              # URL
            nombre = columns[4].get_text().strip()           # Nombre
            archivo_url = columns[5].get_text().strip()      # archivo_url
            fecha = columns[6].get_text().strip()

            # Verifica si URL y archivo_url son enlaces válidos
            url = url if url.lower().startswith("http") else None
            archivo_url = archivo_url if archivo_url.lower().startswith("http") else None
            
            # Agregar la estación a la lista
            estaciones.append({
                'codigo_estacion': codigo_estacion,
                'nombre': nombre,
                'lat': latitud,
                'lng': longitud,
                'url': url,
                'archivo_url': archivo_url,
                'fecha': fecha
            })

    # Usar json.dumps para serializar las estaciones a JSON
    return render(request, 'index.html', {'estaciones': json.dumps(estaciones)})
