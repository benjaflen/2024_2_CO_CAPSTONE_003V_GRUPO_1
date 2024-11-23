-- Tabla: usuarios
CREATE TABLE usuarios (
    user VARCHAR(50) PRIMARY KEY,
    p_cod VARCHAR(50) NOT NULL
);

-- Tabla: permisos_estacion
CREATE TABLE permisos_estacion (
    user VARCHAR(50) NOT NULL,
    e_code VARCHAR(10) NOT NULL,
    FOREIGN KEY (user) REFERENCES usuarios(user),
    FOREIGN KEY (e_code) REFERENCES concesion(e_code)
);

-- Tabla: concesion
CREATE TABLE concesion (
    e_code VARCHAR(200) PRIMARY KEY,
    numero_pert INT NOT NULL,
    lat DECIMAL(10, 8),
    lon DECIMAL(10, 8),
    nombre VARCHAR(255),
    url VARCHAR(255),
    archivo_url VARCHAR(250),
    numero_perfiles INT,
    fecha DATE
);

-- Tabla: perfil
CREATE TABLE perfil (
    perfil_id INT PRIMARY KEY,
    e_code VARCHAR(10) NOT NULL,
    profundidad FLOAT,
    temperatura FLOAT,
    salinidad FLOAT,
    oxigeno_disuelto FLOAT,
    estacion VARCHAR(100),
    FOREIGN KEY (e_code) REFERENCES concesion(e_code)
);

-- Tabla: log
CREATE TABLE log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    fecha_hora DATETIME NOT NULL,
    archivo_nombre VARCHAR(255),
    tipo_archivo VARCHAR(50),
    datos_procesados INT,
    datos_insertados INT,
    datos_erroneos INT,
    tiempo_procesamiento FLOAT,
    usuario_responsable VARCHAR(50),
    mensaje VARCHAR(255),
    archivo_path VARCHAR(200)
);
