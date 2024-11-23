document.addEventListener("DOMContentLoaded", function () {
    var infoDiv = document.getElementById('station-info');

    var buttonsContainer = document.createElement('div');
    buttonsContainer.id = 'sidebar-buttons';
    infoDiv.insertBefore(buttonsContainer, infoDiv.firstChild);

    var closeButton = document.createElement('button');
    closeButton.classList.add('sidebar-close-btn');
    closeButton.innerHTML = '<i class="bi bi-x"></i>';
    buttonsContainer.appendChild(closeButton);

    var backButton = document.createElement('button');
    backButton.classList.add('back-btn');
    backButton.innerHTML = '<i class="bi bi-arrow-left"></i>';
    backButton.style.display = 'none';
    buttonsContainer.appendChild(backButton);

    var contentContainer = document.createElement('div');
    contentContainer.id = 'sidebar-content';
    infoDiv.appendChild(contentContainer);

    let sidebarHistory = [];
    let currentChart = null; // Variable para almacenar el gráfico actual


    contentContainer.addEventListener('click', function(event) {
        if (event.target.classList.contains('perfiles-btn')) {
            var estacionCode = event.target.getAttribute('data-value');
            obtenerPerfiles(estacionCode);
        }
    });

    function toggleButtonVisibility() {
        closeButton.style.display = 'block';
        backButton.style.display = sidebarHistory.length > 0 ? 'block' : 'none';
    }

    backButton.addEventListener('click', function() {
        backSidebar();
        toggleButtonVisibility();
    });

    closeButton.addEventListener('click', function() {
        closeSidebar();
        toggleButtonVisibility();
    });

    function closeSidebar() {
        contentContainer.innerHTML = "";
        document.getElementById('sidebar').style.display = 'none';
        sidebarHistory = [];
        toggleButtonVisibility();
    }

    function backSidebar() {
        if (sidebarHistory.length > 0) {
            contentContainer.innerHTML = sidebarHistory.pop();
            toggleButtonVisibility();
        } else {
            console.warn("No hay más contenido en el historial para restaurar.");
        }
    }

    var map = L.map('map').setView([-53.163356895455486, -70.9172563422676], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    if (typeof estaciones === 'undefined' || !Array.isArray(estaciones)) {
        console.error("'estaciones' no está definido o no es un array.");
        return;
    }

    estaciones.forEach(function(estacion) {
        var lat = parseFloat(estacion.lat);
        var lng = parseFloat(estacion.lng);
        var nombre = estacion.nombre;
        var archivoUrl = estacion.archivo_url;
        var fecha = estacion.fecha;


        // Generar la URL dinámica usando el código de estación
        var dynamicUrl = `https://seia.sea.gob.cl/expediente/ficha/fichaPrincipal.php?modo=ficha&id_expediente=${estacion.codigo_estacion}`;

        var markerOptions = {
            radius: 10,
            fillColor:"#3388FF",
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        };
    
        if (!isNaN(lat) && !isNaN(lng)) {
            var marker = L.circleMarker([lat, lng], markerOptions).addTo(map);

            marker.on('click', function () {
                mostrarEnlaceArchivo(
                    archivoUrl,
                    nombre,
                    dynamicUrl, // Pasar la URL dinámica
                    estacion.codigo_estacion,
                    estacion.lat,
                    estacion.lng,
                    fecha
                );
                contarPerfiles(estacion.codigo_estacion);
            });
        }
    });

    function mostrarEnlaceArchivo(archivoUrl, nombreEstacion, url, codigoEstacion, latitud, longitud, fecha) {
        contentContainer.innerHTML = "";        

        var nombreEstacionTitulo = document.createElement('h2');
        nombreEstacionTitulo.innerText = nombreEstacion;
        contentContainer.appendChild(nombreEstacionTitulo);
        
        var infoSection = document.createElement('div');
        infoSection.style.marginBottom = '15px';
        
        var infoTitle = document.createElement('h3');
        infoTitle.innerText = "Información de la Concesión";
        infoSection.appendChild(infoTitle);
        
        var infoTable = document.createElement('table');
        infoTable.style.width = '100%';
        infoTable.style.borderCollapse = 'collapse';
        
        var infoData = [
            { label: 'Código de Concesión', value: codigoEstacion },
            { label: 'Latitud', value: latitud },
            { label: 'Longitud', value: longitud },
            { label: 'Perfiles Disponibles', value: "Cargando..." },
            {label: 'Fecha', value: fecha }
        ];
        
        infoData.forEach(function (row) {
            var tr = document.createElement('tr');
            var tdLabel = document.createElement('td');
            tdLabel.innerText = row.label + ":";
            tdLabel.style.fontWeight = 'bold';
            tdLabel.style.padding = '5px';
            tdLabel.style.border = '1px solid #ddd';
            tdLabel.style.width = '50%';
            
            var tdValue = document.createElement('td');
            tdValue.innerText = row.value;
            tdValue.style.padding = '5px';
            tdValue.style.border = '1px solid #ddd';
            tdValue.style.width = '50%';
            tdValue.className = row.label === 'Perfiles Disponibles' ? 'perfiles-disponibles' : '';
            
            tr.appendChild(tdLabel);
            tr.appendChild(tdValue);
            infoTable.appendChild(tr);
        });
        
        infoSection.appendChild(infoTable);
        contentContainer.appendChild(infoSection);
        
        if (archivoUrl) {
            var archivoLink = document.createElement('a');
            archivoLink.href = archivoUrl;
            archivoLink.target = "_blank";
            archivoLink.innerText = "Abrir archivo asociado";
            archivoLink.style.display = 'block';
            archivoLink.style.marginBottom = '10px';
            contentContainer.appendChild(archivoLink);
        } else {
            var mensajeNoArchivo = document.createElement('p');
            mensajeNoArchivo.innerText = "No hay archivo asociado a esta concesión.";
            mensajeNoArchivo.style.color = "#FF0000";
            mensajeNoArchivo.style.fontWeight = "bold";
            contentContainer.appendChild(mensajeNoArchivo);
        }
        
        if (url) {
            var urlLink = document.createElement('a');
            urlLink.href = url;
            urlLink.target = "_blank";
            urlLink.innerText = "Link al proyecto";
            urlLink.style.display = 'block';
            urlLink.style.marginBottom = '10px';
            contentContainer.appendChild(urlLink);
        } else {
            var mensajeNoUrl = document.createElement('p');
            mensajeNoUrl.innerText = "No hay URL disponible para esta concesión.";
            mensajeNoUrl.style.color = "#FF0000";
            mensajeNoUrl.style.fontWeight = "bold";
            contentContainer.appendChild(mensajeNoUrl);
        }
        
        var perfilesButton = document.createElement('button');
        perfilesButton.classList.add('station-btn', 'perfiles-btn');
        perfilesButton.innerText = 'Ver Perfiles';
        perfilesButton.setAttribute('data-value', codigoEstacion);
        perfilesButton.addEventListener('click', function() {
            obtenerPerfiles(codigoEstacion);
        });
        contentContainer.appendChild(perfilesButton);
    
        document.getElementById('sidebar').style.display = 'block';
    
        contarPerfiles(codigoEstacion);
    }
    

    function abrirGraficoPopup(codigoEstacion) {
    
        var modal = document.getElementById('chart-modal');
        if (!modal) {
            console.error("Error: No se encontró el modal para el gráfico.");
            return;
        }
        modal.style.display = 'block';
    
        var closeModal = document.querySelector('.close-btn');
        closeModal.onclick = function () {
            modal.style.display = 'none';
        };
    
        window.onclick = function (event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    
        renderizarGraficoEnCanvas(codigoEstacion); // Pasar el código de estación aquí
    }
    
    
    function renderizarGraficoEnCanvas(estacionCode) {
        console.log(`Renderizando gráfico para la estación: ${estacionCode}`);
    
        const ctx = document.getElementById('chart-canvas');
        if (!ctx) {
            console.error("No se encontró el canvas del gráfico.");
            return;
        }
    
        if (currentChart) {
            currentChart.destroy();
        }
    
        // Obtener datos de la tabla
        const { profundidades, temperaturas } = obtenerDatosTabla();
        console.log('Profundidades:', profundidades);
        console.log('Temperaturas:', temperaturas);
        if (profundidades.length === 0 || temperaturas.length === 0) {
            ctx.getContext('2d').fillText('No hay datos para mostrar', 50, 50);
            return;
        }
    
        currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Relación Temperatura-Profunidad',
                    data: profundidades.map((profundidad, index) => ({
                        x: temperaturas[index], // Temperatura en el eje X
                        y: profundidad // Profundidad en el eje Y
                    })),
                    borderColor: 'blue',
                    borderWidth: 1,
                    pointRadius: 5, // Para resaltar los puntos
                    fill: false
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'top',
                        title: {
                            display: true,
                            text: 'Temperatura (°C)'
                        },
                        min: 0, // Asegura que el eje X comience en 0
                        ticks: {
                            stepSize: 1.0 // Intervalos de 1.0
                        }
                    },
                    y: {
                        reverse: true, // Invierte el eje Y para que las profundidades aumenten hacia abajo
                        title: {
                            display: true,
                            text: 'Profundidad (m)'
                        }
                    }
                }
            }
        });
    }
    


    

    function obtenerDatosTabla() {
        const tabla = document.querySelector("#perfiles-table tbody");
        if (!tabla) {
            console.error("No se encontró la tabla de perfiles.");
            return { profundidades: [], temperaturas: [], salinidades: [] };
        }
    
        const filasVisibles = Array.from(tabla.querySelectorAll("tr:not(.hidden-row)"));
        const profundidades = [];
        const temperaturas = [];
        const salinidades = []; 
        const oxigenos = [];
    
        filasVisibles.forEach(fila => {
            const celdas = fila.querySelectorAll("td");
            if (celdas.length >= 4) { // Verifica si hay suficientes columnas
                const profundidad = parseFloat(celdas[1].innerText.trim());
                const temperatura = parseFloat(celdas[2].innerText.trim());
                const salinidad = parseFloat(celdas[3].innerText.trim()); 
                const oxigeno = parseFloat(celdas[4].innerText.trim());
    
                if (!isNaN(profundidad) && !isNaN(temperatura) && !isNaN(salinidad) && !isNaN(oxigeno)) {
                    profundidades.push(profundidad);
                    temperaturas.push(temperatura);
                    salinidades.push(salinidad);
                    oxigenos.push(oxigeno);
                }
            }
        });
    
        return { profundidades, temperaturas, salinidades, oxigenos};
    }
    
    
    

    
    
    // Función para calcular isolíneas de densidad
    function calcularIsolineasDensidad() {
        var isolineas = [];
        var temperaturas = Array.from({ length: 20 }, (_, i) => 10 + i * 0.5); // Temperaturas entre 10 y 20 °C
        var salinidades = Array.from({ length: 20 }, (_, i) => 30 + i * 0.5); // Salinidades entre 30 y 40 PSU
    
        var densidades = [24, 25, 26, 27]; // Ejemplo de valores de densidad
    
        densidades.forEach(densidad => {
            var points = [];
            temperaturas.forEach(temp => {
                salinidades.forEach(salinidad => {
                    var calcDensidad = calcularDensidad(temp, salinidad);
                    if (Math.abs(calcDensidad - densidad) < 0.1) {
                        points.push({ x: salinidad, y: temp });
                    }
                });
            });
    
            isolineas.push({
                type: 'line',
                borderColor: 'gray',
                borderWidth: 1,
                label: {
                    enabled: true,
                    content: `σ = ${densidad}`
                },
                data: points
            });
        });
    
        return isolineas;
    }
    
    // Función para calcular densidad simplificada
    function calcularDensidad(temperatura, salinidad) {
        return 1000 + (salinidad * 0.8) - (temperatura * 0.2);
    }
    
    // Función para obtener color según oxígeno
    function getColorByOxygen(oxigeno) {
        const gradient = [
            { value: 0, color: 'red' },
            { value: 2, color: 'orange' },
            { value: 4, color: 'yellow' },
            { value: 6, color: 'green' },
            { value: 8, color: 'blue' }
        ];
    
        for (let i = gradient.length - 1; i >= 0; i--) {
            if (oxigeno >= gradient[i].value) {
                return gradient[i].color;
            }
        }
        return 'gray';
    }
    
      
    

    function contarPerfiles(estacionCode) {
        var url = `http://localhost:9091/perfiles/${encodeURIComponent(estacionCode)}`;
    
        fetch(url)
            .then(response => response.text())
            .then(data => {
                var parser = new DOMParser();
                var doc = parser.parseFromString(data, "text/html");
                var rows = doc.querySelectorAll("table tr");
                var numPerfiles = rows.length - 1;

                actualizarNumeroPerfiles(numPerfiles);
            })
            .catch(error => {
                actualizarNumeroPerfiles("Error");
            });
    }

    function actualizarNumeroPerfiles(numPerfiles) {
        var perfilesDisponiblesElement = document.querySelector("#sidebar-content .perfiles-disponibles");
        
        if (perfilesDisponiblesElement) {
            perfilesDisponiblesElement.innerText = numPerfiles;
        } else {
            console.warn("No se encontró el elemento para mostrar el número de perfiles disponibles.");
        }
    }

    function obtenerPerfiles(codigoEstacion) {
        var url = `http://localhost:9091/perfiles/${encodeURIComponent(codigoEstacion)}`;
    
        if (contentContainer.innerHTML.trim() !== "") {
            sidebarHistory.push(contentContainer.innerHTML);
        }
    
        contentContainer.innerHTML = "";
    
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Error en la respuesta de la API: ${response.status}`);
                }
                return response.text();
            })
            .then(data => {
                mostrarPerfilesEnSidebar(data, codigoEstacion); // Pasar el código de estación aquí
                toggleButtonVisibility();
            })
            .catch(error => {
                contentContainer.innerHTML = `<p>Error al cargar los perfiles para la concesión ${codigoEstacion}. Intente nuevamente.</p>`;
                toggleButtonVisibility();
            });
    }
    

    function mostrarPerfilesEnSidebar(htmlContent, codigoEstacion) {
        contentContainer.innerHTML = "";
    
        var perfilesContainer = document.createElement('div');
        perfilesContainer.innerHTML = htmlContent;

        
        var graphTSButton = document.createElement('button');
        graphTSButton.classList.add('station-btn', 'graph-btn-ts');
        graphTSButton.innerText = 'Ver Gráfico TS';
        graphTSButton.style.marginLeft = '10px'; // Espacio entre los botones
        graphTSButton.addEventListener('click', function () {
            abrirGraficoTS(codigoEstacion); // Llama a la función para abrir el gráfico TS
        });
        perfilesContainer.appendChild(graphTSButton);
        
        // Agregar el botón para ver el gráfico
        var graphButton = document.createElement('button');
        graphButton.classList.add('station-btn', 'graph-btn');
        graphButton.innerText = 'Ver Gráfico Temperatura-Profundidad';
        graphButton.style.marginTop = '10px';
        graphButton.addEventListener('click', function () {
            console.log(`Código de estación al abrir gráfico: ${codigoEstacion}`); // Depuración
            abrirGraficoPopup(codigoEstacion); // Pasar el código de estación correctamente
        });
        perfilesContainer.appendChild(graphButton);
    
        contentContainer.appendChild(perfilesContainer);
    
        document.getElementById('sidebar').style.display = 'block';
        toggleButtonVisibility();
    }
    
    function abrirGraficoTS(codigoEstacion) {
        console.log(`Abriendo gráfico TS para la estación: ${codigoEstacion}`);
        var modal = document.getElementById('chart-modal-ts');
        var closeModal = document.querySelector('.close-btn-ts');
        modal.style.display = 'block';
    
        closeModal.onclick = function () {
            modal.style.display = 'none';
        };
    
        window.onclick = function (event) {
            if (event.target == modal) {
                modal.style.display = 'none';
            }
        };
    
        renderizarGraficoTS(codigoEstacion);
    }
    
    function renderizarGraficoTS(estacionCode) {
    
        const ctx = document.getElementById('chart-canvas-ts');
    
        if (currentChart) {
            currentChart.destroy();
        }
    
        // Obtener datos de la tabla
        const { temperaturas, salinidades, oxigenos } = obtenerDatosTabla();
    
        // Validar que hay datos suficientes
        if (temperaturas.length === 0 || salinidades.length === 0 || oxigenos.length === 0) {
            console.warn("No hay datos suficientes para graficar.");
            const ctx2d = ctx.getContext('2d');
            ctx2d.clearRect(0, 0, ctx.width, ctx.height); // Limpiar el canvas
            ctx2d.fillText('No hay datos para mostrar', 50, 50);
            return;
        }
    
        // Crear un gradiente continuo para mapear los colores (invertido)
        function mapOxigenoToColor(oxigenoValue) {
            const minOxigeno = 0.0;
            const maxOxigeno = 14.0;
    
            // Crear un gradiente temporal
            const gradientCanvas = document.createElement('canvas');
            const gradientCtx = gradientCanvas.getContext('2d');
            gradientCanvas.width = 1;
            gradientCanvas.height = 256; // 256 niveles de color
    
            // Crear el gradiente vertical (invertido)
            const gradient = gradientCtx.createLinearGradient(0, 0, 0, 256);
            gradient.addColorStop(0, '#800026'); // Rojo oscuro (máximo)
            gradient.addColorStop(0.25, '#FF0000'); // Rojo
            gradient.addColorStop(0.5, '#FFFF00'); // Amarillo
            gradient.addColorStop(0.75, '#00FFFF'); // Cyan
            gradient.addColorStop(1, '#0000FF'); // Azul (mínimo)
    
            // Dibujar el gradiente en el canvas temporal
            gradientCtx.fillStyle = gradient;
            gradientCtx.fillRect(0, 0, 1, 256);
    
            // Mapear el valor de oxígeno al rango [0, 255]
            const normalizedValue = Math.min(
                Math.max((oxigenoValue - minOxigeno) / (maxOxigeno - minOxigeno), 0),
                1
            );
            const colorIndex = Math.floor(normalizedValue * 255);
    
            // Obtener el color del gradiente en la posición correspondiente
            const imageData = gradientCtx.getImageData(0, 255 - colorIndex, 1, 1).data;
            return `rgba(${imageData[0]}, ${imageData[1]}, ${imageData[2]}, 1)`;
        }
    
        // Crear los puntos del gráfico con colores basados en el oxígeno
        const dataPoints = temperaturas.map((temp, index) => ({
            x: salinidades[index],
            y: temp,
            backgroundColor: mapOxigenoToColor(oxigenos[index])
        }));
    
        // Crear el plugin personalizado para la leyenda de gradiente
        const gradientLegendPlugin = {
            id: 'gradientLegend',
            afterDraw: (chart) => {
                const { ctx, chartArea } = chart;
                const { left, top, width, height } = chartArea;
    
                // Definir la posición y tamaño de la leyenda
                const legendWidth = 20; // Ancho de la barra de gradiente
                const legendHeight = height * 1; // 60% de la altura del gráfico
                const legendX = left + width + 10; // Posición a la derecha del gráfico
                const legendY = top + (height - legendHeight) / 2;
    
                // Crear gradiente (invertido)
                const gradient = ctx.createLinearGradient(0, legendY, 0, legendY + legendHeight);
                gradient.addColorStop(0, '#800026'); // Rojo oscuro (máximo)
                gradient.addColorStop(0.25, '#FF0000'); // Rojo
                gradient.addColorStop(0.5, '#FFFF00'); // Amarillo
                gradient.addColorStop(0.75, '#00FFFF'); // Cyan
                gradient.addColorStop(1, '#0000FF'); // Azul (mínimo)
    
                // Dibujar el rectángulo del gradiente
                ctx.fillStyle = gradient;
                ctx.fillRect(legendX, legendY, legendWidth, legendHeight);
    
                // Agregar etiquetas de intervalo
                const minOxigeno = 0.0;
                const maxOxigeno = 14.0;
                const intervalos = 2; // Intervalos de 2 unidades
    
                ctx.fillStyle = '#000';
                ctx.font = '12px Arial';
                ctx.textAlign = 'center';
    
                // Dibujar las etiquetas para cada intervalo
                for (let i = minOxigeno; i <= maxOxigeno; i += intervalos) {
                    const posY = legendY + legendHeight - ((i - minOxigeno) / (maxOxigeno - minOxigeno)) * legendHeight;
                    ctx.fillText(`${i.toFixed(1)} ml/l`, legendX + legendWidth + 25, posY + 3);
                }
    
                // Etiqueta central para "Oxígeno (ml/l)"
                ctx.save();
                ctx.translate(legendX + legendWidth + 65, legendY + legendHeight / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = 'center';
                ctx.fillText('Oxígeno (ml/l)', 0, 0);
                ctx.restore();
            }
        };
    
        // Registrar el plugin personalizado
        Chart.register(gradientLegendPlugin);
    
        // Crear el gráfico
        currentChart = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Datos TS',
                    data: temperaturas.map((temp, index) => ({
                        x: salinidades[index],
                        y: temp
                    })),
                    pointRadius: 5,
                    backgroundColor: temperaturas.map((_, index) => mapOxigenoToColor(oxigenos[index]))
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // Ocultar la leyenda predeterminada
                    }
                },
                layout: {
                    padding: {
                        right: 100 // Añadir espacio adicional a la derecha para la leyenda
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Salinidad (PSU)' // Etiqueta del eje X
                        },
                        reverse: true
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Temperatura (°C)' // Etiqueta del eje Y
                        },
                        position: 'left' // Mover el eje Y a la izquierda
                    }
                }
            }
        });
    
        console.log("Gráfico TS renderizado con éxito.");
    }
    
    
    
    
    
    
    

    

    // Guardar el orden original de las filas cuando se carga la tabla
    window.originalRows = Array.from(document.querySelectorAll("#perfiles-table tbody tr"));
    window.sortOrder = 1; // Variable global para el orden de clasificación

    window.sortTable = function(columnIndex) {
        const table = document.getElementById("perfiles-table");
        if (!table) return;
    
        // Obtener todas las filas, incluyendo las ocultas
        const rows = Array.from(table.querySelectorAll("tbody tr"));
    
        // Ordenar las filas
        rows.sort((a, b) => {
            const aText = a.cells[columnIndex].innerText;
            const bText = b.cells[columnIndex].innerText;
            const aValue = parseFloat(aText) || 0;
            const bValue = parseFloat(bText) || 0;
    
            return (aValue - bValue) * window.sortOrder;
        });
    
        // Cambia el orden de clasificación
        window.sortOrder *= -1;
    
        // Vaciar y volver a llenar el tbody en el nuevo orden
        const tbody = table.querySelector("tbody");
        tbody.innerHTML = "";
        rows.forEach(row => tbody.appendChild(row));
    
        // Reaplicar el filtro de estación
        applyStationFilter();
    };    
    
    // Función para filtrar por estación
    window.filterStations = function() {
        const table = document.getElementById("perfiles-table");
        if (!table) return;
    
        // Recolectar los nombres de las estaciones únicas
        const stations = new Set();
        Array.from(table.querySelectorAll("tbody tr")).forEach(row => {
            const stationName = row.cells[0].innerText;
            stations.add(stationName);
        });
    
        // Crear el menú desplegable directamente debajo del encabezado "Estación"
        const stationList = Array.from(stations).sort(); // Ordenar alfabéticamente
        let stationOptions = `<option value="">Todas</option>`; // Cambiado a "Todas"
        stationList.forEach(station => {
            stationOptions += `<option value="${station}">${station}</option>`;
        });
    
        // Crear un contenedor para el menú desplegable y el botón
        const filterContainer = document.createElement("div");
        filterContainer.style.marginTop = "5px"; // Espacio para separar del encabezado
        filterContainer.innerHTML = `
            <select id="station-select">${stationOptions}</select>
            <button onclick="applyStationFilter()">Filtrar</button>
        `;
    
        // Insertar el contenedor debajo del encabezado "Estación"
        const stationHeader = table.querySelector("thead th:first-child");
        if (stationHeader && !document.getElementById("station-select")) {
            stationHeader.appendChild(filterContainer);
        }
    
        window.applyStationFilter = function() {
            
            const selectedStation = document.getElementById("station-select").value;
        
            // Filtrar las filas de la tabla
            Array.from(table.querySelectorAll("tbody tr")).forEach(row => {
                const stationName = row.cells[0].innerText;
                if (selectedStation === "" || stationName === selectedStation) {
                    row.classList.remove("hidden-row");
                } else {
                    row.classList.add("hidden-row");
                }
            });
        
            // Mantén el menú desplegable visible si lo necesitas
            filterContainer.style.display = "block";
        };
        
    };

    var infoDiv = document.getElementById('station-info');
    var buttonsContainer = document.createElement('div');
    buttonsContainer.id = 'sidebar-buttons';
    infoDiv.insertBefore(buttonsContainer, infoDiv.firstChild);

    var searchInput = document.getElementById('station-search');
    var searchResultContainer = document.getElementById('search-result');
    var highlightedMarker = null; // Variable para almacenar el marcador resaltado actual

    // Manejo del evento de entrada en la barra de búsqueda
    searchInput.addEventListener('input', function () {
        var searchText = searchInput.value.trim().toLowerCase();
        updateSearchResults(searchText);
    });

    // Función para actualizar los resultados de la búsqueda en tiempo real
    function updateSearchResults(searchText) {
        // Limpiar resultados previos
        searchResultContainer.innerHTML = '';

        if (searchText.length === 0) {
            return;
        }

        // Filtrar estaciones que empiecen con el texto ingresado (por código o nombre)
        var filteredStations = estaciones.filter(estacion =>
            estacion.codigo_estacion.startsWith(searchText) ||
            estacion.nombre.toLowerCase().includes(searchText)
        );

        // Manejo de no encontrar coincidencias
        if (filteredStations.length === 0) {
            var noMatchElement = document.createElement('div');
            noMatchElement.classList.add('no-match');
            noMatchElement.innerText = 'Concesión no encontrada';
            searchResultContainer.appendChild(noMatchElement);
            return;
        }

        // Limitar a 7 resultados
        filteredStations.slice(0, 7).forEach(estacion => {
            var resultItem = document.createElement('div');
            resultItem.classList.add('result-item');
            resultItem.innerText = estacion.codigo_estacion + ' - ' + estacion.nombre;
            resultItem.addEventListener('click', function () {
                focusOnStation(estacion);
                searchResultContainer.innerHTML = ''; // Cerrar los resultados al seleccionar
                searchInput.value = ''; // Limpiar la barra de búsqueda
            });
            searchResultContainer.appendChild(resultItem);
        });
    }

    // Función para centrar el mapa y resaltar la estación seleccionada sin abrir el sidebar
    function focusOnStation(estacion) {
        var lat = parseFloat(estacion.lat);
        var lng = parseFloat(estacion.lng);

        // Validar coordenadas
        if (!isNaN(lat) && !isNaN(lng)) {
            map.setView([lat, lng], 15); // Acercar la vista en la estación

            // Eliminar el resaltado anterior si existe
            if (highlightedMarker) {
                map.removeLayer(highlightedMarker);
            }

            // Crear un nuevo marcador resaltado para la estación seleccionada
            highlightedMarker = L.circleMarker([lat, lng], {
                radius: 12,            // Tamaño ligeramente mayor para destacar
                fillColor: "#FF0000",  // Color rojo para resaltar
                color: "#FF0000",
                weight: 2,
                opacity: 1,
                fillOpacity: 0.7
            }).addTo(map);
        }
    }

    // Remover el marcador resaltado cuando se hace clic en el mapa
    map.on('click', function () {
        if (highlightedMarker) {
            map.removeLayer(highlightedMarker);
            highlightedMarker = null; // Limpiar la referencia al marcador resaltado
        }
    });
    
});
