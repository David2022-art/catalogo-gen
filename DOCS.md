# 📚 Documentación Técnica — catalogo-gen

## Tabla de contenidos

1. [Arquitectura general](#1-arquitectura-general)
2. [Estructura del proyecto](#2-estructura-del-proyecto)
3. [Flujo de la aplicación](#3-flujo-de-la-aplicación)
4. [Configuración](#4-configuración)
5. [Temas de color](#5-temas-de-color)
6. [Layouts disponibles](#6-layouts-disponibles)
7. [Seguridad](#7-seguridad)
8. [API interna](#8-api-interna)
9. [Funciones del backend](#9-funciones-del-backend)
10. [Interfaz web (frontend)](#10-interfaz-web-frontend)
11. [Cómo agregar un nuevo tema](#11-cómo-agregar-un-nuevo-tema)
12. [Cómo agregar un nuevo layout](#12-cómo-agregar-un-nuevo-layout)
13. [Dependencias](#13-dependencias)
14. [Compatibilidad](#14-compatibilidad)
15. [Errores comunes](#15-errores-comunes)

---

## 1. Arquitectura general

```
┌─────────────────────────────────────────────────┐
│                  NAVEGADOR                       │
│   index.html  ←→  JavaScript  →  fetch POST     │
└─────────────────────┬───────────────────────────┘
                      │ HTTP POST /generate
                      │ (imágenes + parámetros)
┌─────────────────────▼───────────────────────────┐
│              FLASK (app.py)                      │
│                                                  │
│  1. Valida token de sesión                       │
│  2. Valida extensiones de imagen                 │
│  3. Procesa imágenes con Pillow                  │
│  4. Genera PDF con ReportLab                     │
│  5. Devuelve el PDF como descarga                │
└─────────────────────────────────────────────────┘
```

El servidor corre **100% local** en `http://localhost:7860`.
Las imágenes nunca salen del computador del usuario.

---

## 2. Estructura del proyecto

```
catalogo-gen/
│
├── app.py                  # Servidor Flask y rutas
├── config.py               # Configuración y temas de color
├── pdf_engine.py           # Lógica de generación de PDF y Pillow
├── requirements.txt        # Dependencias Python
│
├── templates/
│   └── index.html          # Interfaz web (HTML + CSS + JS)
│
├── static/
│   └── .gitkeep            # Carpeta reservada para archivos estáticos
│
├── run.sh                  # Script de arranque Linux/Ubuntu
├── run.bat                 # Script de arranque Windows
├── run_mac.sh              # Script de arranque Mac
│
├── README.md               # Guía de uso rápido
├── DOCS.md                 # Este archivo (documentación técnica)
└── .gitignore              # Archivos ignorados por Git
```

---

## 3. Flujo de la aplicación

```
Usuario abre run.sh / run.bat / run_mac.sh
        │
        ▼
Se crea entorno virtual (solo la primera vez)
        │
        ▼
Se instalan dependencias (solo si no están)
        │
        ▼
Flask arranca en localhost:7860
        │
        ▼
Se abre el navegador automáticamente
        │
        ▼
Usuario sube imágenes + completa el formulario
        │
        ▼
JavaScript envía POST a /generate con:
  - Las imágenes (multipart/form-data)
  - Título, subtítulo, negocio, precio, contacto
  - Estilo (oscuro / claro)
  - Layout (1 / 2 / 4 imágenes por página)
  - Token de sesión (seguridad)
        │
        ▼
Flask valida el token y los parámetros
        │
        ▼
Pillow procesa cada imagen:
  - Convierte a RGB
  - Redimensiona si es mayor a TAMANO_MAX_IMAGEN px
  - Convierte a JPEG con CALIDAD_IMAGEN
        │
        ▼
ReportLab construye el PDF:
  - Página 1: Portada
  - Páginas siguientes: productos según layout
        │
        ▼
El PDF se envía al navegador como descarga
```

---

## 4. Configuración

Todas las variables de configuración están en `config.py`
y tienen comentarios explicativos:

```python
# Puerto donde corre el servidor web
PUERTO = 7860

# Dimensión máxima de imagen en píxeles (ancho o alto)
# Imágenes más grandes se redimensionan automáticamente
# Valor más alto = mejor calidad pero más lento
TAMANO_MAX_IMAGEN = 1800

# Calidad de compresión JPEG (1-100)
# 85 es un buen balance entre calidad y tamaño de archivo
# 95+ para máxima calidad, 70- para archivos más pequeños
CALIDAD_IMAGEN = 85

# Tamaño máximo total de la petición en megabytes
# Aumenta este valor si tienes muchas imágenes grandes
MAX_SUBIDA_MB = 500

# Extensiones de imagen permitidas
# Agrega o quita extensiones según tus necesidades
EXTENSIONES_OK = {'jpg', 'jpeg', 'png', 'webp', 'heic'}
```

### Límites de seguridad

```python
# Máximo de catálogos generados por minuto
LIMITE_PETICIONES = 10

# Ventana de tiempo para el límite (en segundos)
VENTANA_SEGUNDOS = 60
```

---

## 5. Temas de color

Los temas se definen en el diccionario `TEMAS` en `config.py`.
Cada clave es un color en formato hexadecimal `#rrggbb`.

```python
TEMAS = {
    'oscuro': {
        'fondo_pagina'  : '#111111',  # fondo de páginas de producto
        'fondo_tarjeta' : '#1e1e1e',  # fondo de tarjetas en grid
        'texto'         : '#ffffff',  # nombre del producto
        'texto_tenue'   : '#666666',  # número de página, etiquetas
        'borde'         : '#2a2a2a',  # líneas separadoras y bordes
        'fondo_portada' : '#0a0a0a',  # fondo de la portada
        'color_precio'  : '#888888',  # texto del precio
    },
    'claro': { ... }
}
```

### Referencia visual de cada clave

```
┌─────────────────────────────────────────┐  ← fondo_portada
│            NOMBRE DEL NEGOCIO           │  ← texto (portada)
│                                         │
│           TÍTULO DEL CATÁLOGO           │
│              subtítulo                  │
│       15 PRODUCTOS   |   8 PÁGINAS      │
└─────────────────────────────────────────┘

┌──────────────┬─────────────────────────┐  ← borde (línea top)
│ 01 / 15      │  NEGOCIO  │   CATÁLOGO  │
├──────────────┴─────────────────────────┤
│                                        │  ← fondo_pagina
│            [IMAGEN DEL                 │
│             PRODUCTO]                  │
│                                        │
├────────────────────────────────────────┤  ← borde (línea bottom)
│ NOMBRE PRODUCTO         Precio: ____   │  ← texto / color_precio
└────────────────────────────────────────┘
```

---

## 6. Layouts disponibles

### Layout 1 — Una imagen por página
- Orientación: **Landscape (horizontal)**
- Tamaño de página: A4 apaisado (297 × 210 mm)
- La imagen ocupa el máximo espacio disponible

```
┌─────────────────────────────────────────┐
│ 01/15      [ NEGOCIO ]       CATÁLOGO   │  ← barra superior (42pt)
├─────────────────────────────────────────┤
│                                         │
│                                         │
│         [  IMAGEN GRANDE  ]             │
│                                         │
│                                         │
├─────────────────────────────────────────┤
│ NOMBRE PRODUCTO          Precio: ____   │  ← pie (48pt)
└─────────────────────────────────────────┘
```

### Layout 2 — Dos imágenes por página
- Orientación: **Portrait (vertical)**
- Tamaño de página: A4 (210 × 297 mm)
- Columnas: 1 / Filas: 2 (tarjetas apiladas)

```
┌─────────────────────────────────────────┐
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │         [ IMAGEN 1 ]              │  │
│  │                                   │  │
│  │ Nombre producto 1    Precio: ___  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │                                   │  │
│  │         [ IMAGEN 2 ]              │  │
│  │                                   │  │
│  │ Nombre producto 2    Precio: ___  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Layout 4 — Cuatro imágenes por página
- Orientación: **Portrait (vertical)**
- Tamaño de página: A4 (210 × 297 mm)
- Columnas: 2 / Filas: 2 (cuadrícula 2×2)

```
┌─────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐    │
│  │  [ IMG 1 ]   │  │  [ IMG 2 ]   │    │
│  │ Nombre 1     │  │ Nombre 2     │    │
│  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐    │
│  │  [ IMG 3 ]   │  │  [ IMG 4 ]   │    │
│  │ Nombre 3     │  │ Nombre 4     │    │
│  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────┘
```

---

## 7. Seguridad

La app implementa 5 capas de seguridad para uso local:

### 7.1 Token de sesión CSRF
```python
TOKEN_SESION = secrets.token_hex(16)
```
- Se genera un token aleatorio de 32 caracteres cada vez que arranca el servidor
- Flask inyecta el token en el HTML como `<meta name="csrf-token">`
- Cada petición POST debe incluir el token
- El servidor verifica con `secrets.compare_digest()` (resistente a timing attacks)
- Sin el token correcto → respuesta `403 Forbidden`

### 7.2 Rate limiting (límite de velocidad)
```python
LIMITE_PETICIONES = 10
VENTANA_SEGUNDOS  = 60
```
- Máximo 10 catálogos por minuto
- Superado el límite → respuesta `429 Too Many Requests`

### 7.3 Validación de extensiones
```python
EXTENSIONES_OK = {'jpg', 'jpeg', 'png', 'webp', 'heic'}
```
- Solo se aceptan extensiones de imagen conocidas
- Archivos con extensión no permitida son ignorados silenciosamente

### 7.4 Validación real de imagen
```python
imagen = Imagen.open(io.BytesIO(bytes_imagen))
```
- Pillow intenta abrir el archivo como imagen
- Si falla (archivo corrupto o no es imagen) → se ignora sin error al usuario

### 7.5 Sanitización de textos
- Límite de 200 caracteres por campo
- El nombre del PDF descargado se sanitiza con regex:
  ```python
  re.sub(r'[^\w\s\-]', '', titulo)
  ```

---

## 8. API interna

### `GET /`
Sirve la interfaz web con el token inyectado.

**Respuesta:** HTML completo de `index.html`

---

### `POST /generate`

Genera y devuelve el catálogo PDF.

**Headers requeridos:**
```
Content-Type: multipart/form-data
```

**Campos del formulario:**

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `token` | string | ✅ | Token de sesión CSRF |
| `images` | file[] | ✅ | Una o más imágenes |
| `title` | string | ❌ | Título del catálogo (default: "Mi Catálogo") |
| `subtitle` | string | ❌ | Subtítulo de la portada |
| `business` | string | ❌ | Nombre del negocio |
| `price` | string | ❌ | Precio por defecto para todos los productos |
| `contact` | string | ❌ | Teléfono o contacto |
| `style` | string | ❌ | `oscuro` o `claro` (default: `oscuro`) |
| `layout` | int | ❌ | `1`, `2` o `4` (default: `1`) |
| `individual_prices` | string[] | ❌ | Lista de precios específicos para cada imagen |

**Respuestas:**

| Código | Descripción |
|--------|-------------|
| `200` | PDF generado — se descarga directamente |
| `400` | Error en los datos enviados |
| `403` | Token inválido |
| `429` | Demasiadas peticiones |
| `500` | Error interno del servidor |

---

## 9. Funciones del backend

### `preparar_imagen(bytes_imagen)`
Convierte bytes crudos de imagen en un `ImageReader` listo para ReportLab.

- Abre la imagen con Pillow
- Convierte a modo RGB (necesario para JPEG)
- Redimensiona si supera `TAMANO_MAX_IMAGEN` píxeles
- Comprime a JPEG con `CALIDAD_IMAGEN`
- Retorna: `(ImageReader, (ancho, alto))`

---

### `limpiar_nombre(nombre_archivo)`
Extrae un nombre legible del nombre del archivo.

- Elimina el patrón `WhatsApp Image YYYY-MM-DD...`
- Reemplaza guiones bajos y guiones por espacios
- Si queda vacío, retorna `None` (se usa "Producto N")

**Ejemplos:**
```
"WhatsApp Image 2026-03-11 at 9.24.jpg" → None → "Producto 1"
"snoopy_abejas_talla_unica.jpg"         → "snoopy abejas talla unica"
"Mafalda-Roja.jpg"                      → "Mafalda Roja"
```

---

### `dibujar_portada(...)`
Dibuja la primera página del catálogo con:
- Fondo sólido
- Línea decorativa horizontal
- Etiqueta del negocio con borde
- Título principal (tamaño automático)
- Subtítulo
- Estadísticas (productos / páginas)
- Nombre del negocio y contacto al pie

---

### `dibujar_barra_superior(...)`
Dibuja la barra de navegación en la parte superior de cada página:
- Número de página (izquierda)
- Nombre del negocio con borde (centro)
- Nombre del catálogo (derecha)

---

### `dibujar_pie(...)`
Dibuja el pie de página con:
- Nombre del producto (tamaño de fuente automático)
- Caja con el precio (derecha)

---

### `dibujar_pagina_una_imagen(...)`
Dibuja una página completa con una sola imagen.
Usa `dibujar_barra_superior` y `dibujar_pie` internamente.

---

### `dibujar_pagina_grid(...)`
Dibuja una página con múltiples tarjetas (layout 2 o 4).
Cada tarjeta contiene imagen + nombre + precio.

---

### `hex_a_rgb(color_hex)`
Convierte un color hexadecimal `#rrggbb` a tupla `(r, g, b)`
con valores entre 0 y 1, requerido por ReportLab.

---

## 10. Interfaz web (frontend)

El archivo `templates/index.html` es un archivo único que contiene
HTML, CSS y JavaScript sin dependencias externas (excepto Google Fonts).

### Estado de la aplicación (JavaScript)
```javascript
var state = {
    files: [],          // archivos de imagen seleccionados
    folderName: '',     // nombre de la carpeta subida
    style: 'oscuro',    // tema seleccionado
    layout: '1',        // layout seleccionado
    lastBlob: null      // último PDF generado (para re-descargar)
};
```

### Pantallas
La interfaz tiene 4 pantallas que se muestran/ocultan con CSS:

| ID | Descripción |
|----|-------------|
| `pg-form` | Formulario principal |
| `pg-prog` | Pantalla de carga con barra de progreso |
| `pg-ok` | Pantalla de éxito con botón de descarga |
| `pg-err` | Pantalla de error con mensaje |

### Flujo del JavaScript
```
Usuario hace clic en "Generar"
    → Valida que hay imágenes
    → Muestra pg-prog
    → Construye FormData con imágenes + parámetros + token
    → fetch POST a /generate
    → Si ok: descarga el PDF automáticamente → muestra pg-ok
    → Si error: muestra pg-err con el mensaje
```

---

## 11. Personalización de Temas (Ejemplo)

> [!NOTE]
> Los siguientes pasos son un ejemplo de cómo podrías extender el sistema.

1. Abre `app.py`
2. Agrega una nueva entrada al diccionario `TEMAS`:

```python
TEMAS = {
    'oscuro': { ... },
    'claro':  { ... },
    'rosa': {                        # ← nuevo tema
        'fondo_pagina'  : '#fff0f5',
        'fondo_tarjeta' : '#ffffff',
        'texto'         : '#4a0020',
        'texto_tenue'   : '#cc6699',
        'borde'         : '#ffb3cc',
        'fondo_portada' : '#cc0055',
        'color_precio'  : '#cc6699',
    },
}
```

3. Abre `templates/index.html`
4. Agrega el botón en la sección de estilos:

```html
<div class="opt" data-v="rosa">
    <div class="opt-check">✓</div>
    <div class="style-bar" style="background:#cc0055;color:#fff;">ROSA</div>
    <div class="opt-title">🌸 Rosa</div>
    <div class="opt-desc">Ideal para productos femeninos</div>
</div>
```

5. Cambia el grid de `c2` a `c3` para que quepan 3 opciones:
```html
<div class="opts c3" id="style-opts">
```

---

## 12. Personalización de Layouts (Ejemplo)

> [!NOTE]
> Los siguientes pasos muestran la lógica interna necesaria para soportar nuevos formatos.

1. En `app.py`, en la función `generar_catalogo()`, agrega el nuevo caso:

```python
if layout == 2:
    columnas, filas = 1, 2
elif layout == 4:
    columnas, filas = 2, 2
elif layout == 6:          # ← nuevo layout
    columnas, filas = 2, 3
```

2. Agrega el valor al validador:
```python
if layout not in (1, 2, 4, 6):   # ← agregar 6
```

3. En `templates/index.html`, agrega el botón:
```html
<div class="opt" data-v="6">
    <div class="opt-check">✓</div>
    <span class="opt-icon">⊟</span>
    <div class="opt-title">6 por página</div>
    <div class="opt-desc">Muy compacto</div>
</div>
```

4. Cambia el grid de layouts de `c3` a `c4` en el HTML.

---

## 13. Dependencias

| Librería | Versión mínima | Para qué se usa |
|----------|---------------|-----------------|
| Flask | 2.3.0 | Servidor web local, rutas HTTP, templates |
| Pillow | 10.0.0 | Abrir imágenes, convertir formatos, redimensionar |
| ReportLab | 4.0.0 | Generar el archivo PDF con canvas |

Todas se instalan automáticamente con:
```bash
pip install flask pillow reportlab
```

---

## 14. Compatibilidad

| Sistema | Script | Python requerido | Notas |
|---------|--------|-----------------|-------|
| Ubuntu / Debian | `bash run.sh` | 3.8+ | Abre browser con `xdg-open` |
| Windows 10/11 | `run.bat` | 3.8+ | Abre browser automáticamente |
| macOS 12+ | `bash run_mac.sh` | 3.8+ | Abre browser con `open` |

### Notas por sistema

**Windows:**
- Python debe tener marcado "Add Python to PATH" durante la instalación
- El script activa encoding UTF-8 con `chcp 65001`
- Si hay problemas con el venv, borrar la carpeta `venv/` y re-ejecutar

**Mac:**
- Python no viene preinstalado en versiones recientes de macOS
- Recomendado instalar con Homebrew: `brew install python3`
- En Mac con Apple Silicon (M1/M2/M3) funciona igual de bien

**Linux:**
- En Ubuntu puede ser necesario instalar: `sudo apt install python3-venv python3-full`
- En otras distribuciones el comando de instalación varía

---

## 15. Errores comunes

### "Address already in use"
El puerto 7860 está ocupado por otro programa.
**Solución:** Cambiar `PUERTO = 7861` en `app.py`

---

### "No se pudieron leer las imágenes"
Las imágenes no son válidas o tienen una extensión no permitida.
**Solución:** Verificar que sean JPG, PNG, WEBP o HEIC. Agregar la extensión a `EXTENSIONES_OK` si es necesario.

---

### "Un campo de texto es demasiado largo"
Uno de los campos del formulario supera 200 caracteres.
**Solución:** Acortar el texto o aumentar el límite en `app.py`:
```python
if len(campo) > 200:  # ← cambiar a 500 si se necesita
```

---

### El PDF sale en blanco / sin imágenes
La imagen no pudo ser procesada por Pillow.
**Causa común:** Archivo HEIC en Windows (requiere librería adicional).
**Solución:** Convertir las imágenes a JPG o PNG antes de subir.

---

### El venv no se activa en Windows
**Solución:** Ejecutar en PowerShell como administrador:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### El browser no abre automáticamente en Linux
`xdg-open` puede no estar disponible en todas las distribuciones.
**Solución:** Abrir manualmente `http://localhost:7860` en el navegador.

---

*Documentación para catalogo-gen v1.0*
