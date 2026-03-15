# 📋 Generador de Catálogos

Herramienta local para generar catálogos en PDF a partir de una carpeta de imágenes.  
Sube tus fotos, elige el estilo y descarga el PDF listo.

## ✨ Características

- Genera PDFs profesionales desde fotos de productos
- 2 estilos: Oscuro y Claro
- 3 layouts: 1 imagen por página, 2 o 4 por página
- Portada automática con nombre, contacto y estadísticas
- Seguridad con token de sesión
- 100% local — tus imágenes no salen de tu computador

## 🖥️ Requisitos

- **Python 3.8 o superior**
- Conexión a internet solo la primera vez (para instalar dependencias)

## 🚀 Cómo usar

### Linux / Ubuntu
```bash
bash run.sh
```

### Windows
Doble clic en `run.bat`  
*(o desde la terminal: `run.bat`)*
Si falla  "WinError 5 - Acceso denegado" se debe de iniciar como administrador 
o mover el archivo de descargas a documentos 

### Mac
```bash
bash run_mac.sh
```

Luego abre tu navegador en: **http://localhost:7860**

## 📦 Dependencias

Se instalan automáticamente al ejecutar el script:

| Librería | Para qué sirve |
|---|---|
| Flask | Servidor web local |
| Pillow | Procesamiento de imágenes |
| ReportLab | Generación de PDFs |

## ⚙️ Configuración

Abre `config.py` y modifica las variables según tus necesidades:

```python
PUERTO            = 7860   # puerto del servidor
TAMANO_MAX_IMAGEN = 1800   # píxeles máximos por lado
CALIDAD_IMAGEN    = 85     # calidad JPEG (1-100)
MAX_SUBIDA_MB     = 500    # límite de subida en MB
```

Para cambiar colores, edita el diccionario `TEMAS`:

```python
TEMAS = {
    'oscuro': {
        'fondo_pagina'  : '#111111',  # fondo de páginas
        'fondo_portada' : '#0a0a0a',  # fondo de portada
        'texto'         : '#ffffff',  # nombre del producto
        'color_precio'  : '#888888',  # texto del precio
        ...
    }
}
```

## 🔒 Seguridad

- Token de sesión único generado al arrancar
- Validación de extensiones de imagen
- Límite de 10 peticiones por minuto
- Solo accesible desde tu computador (localhost)

## 📁 Estructura del proyecto

```
catalogapp/
├── app.py              # Servidor Flask y rutas
├── config.py           # Configuración (puerto, temas, seguridad)
├── pdf_engine.py       # Motor de generación de PDF y procesamiento de imágenes
├── run.sh              # Script de arranque Linux
├── run.bat             # Script de arranque Windows
├── run_mac.sh          # Script de arranque Mac
├── requirements.txt    # Dependencias Python
├── README.md           # Este archivo
└── templates/
    └── index.html      # Interfaz web
```

## 🛑 Para detener el servidor

Presiona `Ctrl + C` en la terminal donde está corriendo.
