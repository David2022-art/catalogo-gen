# -*- coding: utf-8 -*-
# ============================================================
#  GENERADOR DE CATÁLOGOS  —  app.py
#  Servidor local Flask + ReportLab + Pillow
# ============================================================
#
#  COLORES FÁCILES DE CAMBIAR
#  --------------------------
#  Modifica los valores hex en el diccionario TEMAS más abajo.
#  Cada tema tiene estas claves:
#
#    fondo_pagina   → color de fondo de cada página de producto
#    fondo_tarjeta  → color de las tarjetas (layout 2 o 4)
#    texto          → color del nombre del producto
#    texto_tenue    → color del número de página y etiquetas
#    borde          → color de líneas separadoras y bordes
#    fondo_portada  → color de la portada
#    color_precio   → color del texto de precio
#
#  CONFIGURACIÓN GENERAL
#  ---------------------
#  PUERTO            → puerto donde corre el servidor (por defecto 7860)
#  TAMANO_MAX_IMAGEN → dimensión máxima en píxeles al redimensionar
#  CALIDAD_IMAGEN    → calidad JPEG de las imágenes (1-100)
#  MAX_SUBIDA_MB     → límite de tamaño total de subida en MB
#  EXTENSIONES_OK    → tipos de imagen permitidos
# ============================================================

from flask import Flask, render_template, request, send_file, jsonify, abort
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from PIL import Image as Imagen
import io, os, re, traceback, secrets, time

# ── CONFIGURACIÓN GENERAL ────────────────────────────────────
PUERTO            = 7860
TAMANO_MAX_IMAGEN = 1800   # píxeles máximos por lado al redimensionar
CALIDAD_IMAGEN    = 85     # calidad JPEG (1-100). Más alto = mejor calidad, más peso
MAX_SUBIDA_MB     = 500    # megabytes máximos por petición
EXTENSIONES_OK    = {'jpg', 'jpeg', 'png', 'webp', 'heic'}

# ── TEMAS DE COLOR ───────────────────────────────────────────
TEMAS = {
    'oscuro': {
        'fondo_pagina'  : '#111111',  # fondo de páginas de producto
        'fondo_tarjeta' : '#1e1e1e',  # fondo de tarjetas en grid
        'texto'         : '#ffffff',  # nombre del producto
        'texto_tenue'   : '#666666',  # número de página, etiquetas
        'borde'         : '#2a2a2a',  # líneas separadoras
        'fondo_portada' : '#0a0a0a',  # fondo de la portada
        'color_precio'  : '#888888',  # texto del precio
    },
    'claro': {
        'fondo_pagina'  : '#fafafa',
        'fondo_tarjeta' : '#ffffff',
        'texto'         : '#1a1a1a',
        'texto_tenue'   : '#999999',
        'borde'         : '#e5e5e5',
        'fondo_portada' : '#1a1a1a',
        'color_precio'  : '#888888',
    },
}

# ── SEGURIDAD ────────────────────────────────────────────────
# Token de sesión generado al arrancar. Solo peticiones con este
# token pueden generar PDFs. Evita que otras apps en la misma red
# usen el generador sin permiso.
TOKEN_SESION = secrets.token_hex(16)

# Límite de peticiones: máximo LIMITE_PETICIONES por VENTANA_SEGUNDOS
LIMITE_PETICIONES = 10
VENTANA_SEGUNDOS  = 60
_historial_peticiones = []  # almacena timestamps de peticiones recientes

def limite_de_velocidad():
    """Bloquea si se superan LIMITE_PETICIONES en VENTANA_SEGUNDOS."""
    ahora = time.time()
    # Limpiar peticiones antiguas fuera de la ventana
    _historial_peticiones[:] = [t for t in _historial_peticiones if ahora - t < VENTANA_SEGUNDOS]
    if len(_historial_peticiones) >= LIMITE_PETICIONES:
        abort(429)  # Too Many Requests
    _historial_peticiones.append(ahora)

def extension_permitida(nombre_archivo):
    """Verifica que el archivo tenga una extensión de imagen válida."""
    ext = nombre_archivo.rsplit('.', 1)[-1].lower() if '.' in nombre_archivo else ''
    return ext in EXTENSIONES_OK

# ── INICIALIZACIÓN DE FLASK ──────────────────────────────────
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_SUBIDA_MB * 1024 * 1024
app.secret_key = TOKEN_SESION

# ── UTILIDADES DE COLOR ──────────────────────────────────────
def hex_a_rgb(color_hex):
    """Convierte un color hex '#rrggbb' a tupla (r, g, b) con valores 0-1."""
    color_hex = color_hex.lstrip('#')
    return tuple(int(color_hex[i:i+2], 16) / 255 for i in (0, 2, 4))

def color_relleno(canvas, color_hex):
    canvas.setFillColorRGB(*hex_a_rgb(color_hex))

def color_borde(canvas, color_hex):
    canvas.setStrokeColorRGB(*hex_a_rgb(color_hex))

# ── PROCESAMIENTO DE IMÁGENES ────────────────────────────────
def preparar_imagen(bytes_imagen):
    """
    Abre una imagen desde bytes, la convierte a RGB,
    la redimensiona si es muy grande, y devuelve un
    ImageReader listo para ReportLab + su tamano en pixeles.
    """
    imagen = Imagen.open(io.BytesIO(bytes_imagen))
    if imagen.mode != 'RGB':
        imagen = imagen.convert('RGB')

    ancho, alto = imagen.size
    if max(ancho, alto) > TAMANO_MAX_IMAGEN:
        escala = TAMANO_MAX_IMAGEN / max(ancho, alto)
        imagen = imagen.resize(
            (int(ancho * escala), int(alto * escala)),
            Imagen.LANCZOS
        )

    buffer = io.BytesIO()
    imagen.save(buffer, format='JPEG', quality=CALIDAD_IMAGEN, optimize=True)
    buffer.seek(0)
    return ImageReader(buffer), imagen.size

def limpiar_nombre(nombre_archivo):
    """
    Extrae un nombre legible del nombre del archivo.
    Elimina el prefijo de WhatsApp y caracteres feos.
    Ej: 'WhatsApp Image 2026-03-11 at 9.24.jpg' → None (usa 'Producto N')
        'snoopy_abejas_talla_unica.jpg'          → 'snoopy abejas talla unica'
    """
    base = os.path.splitext(os.path.basename(nombre_archivo))[0]
    # Quitar patrón de WhatsApp, la mayoria de imagenes de un catalogo vienen de wasapp y no aporta nada
    nombre = re.sub(r'(?i)whatsapp[\s_\-]*image[\s_\-]*\d{4}.*', '', base).strip()
    # Reemplazar separadores por espacios
    nombre = re.sub(r'[\s_\-]+', ' ', nombre).strip()
    return nombre or None

# ── DIBUJO DE PORTADA ────────────────────────────────────────
def dibujar_portada(canvas, ancho, alto, titulo, subtitulo, negocio, contacto, tema, total_productos, total_paginas):
    """Dibuja la página de portada del catálogo."""

    # Fondo
    color_relleno(canvas, tema['fondo_portada'])
    canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)

    # Línea decorativa horizontal
    color_borde(canvas, '#2a2a2a')
    canvas.setLineWidth(0.5)
    canvas.line(ancho * 0.1, alto * 0.55, ancho * 0.9, alto * 0.55)

    # Etiqueta del negocio (rectángulo con borde)
    etiqueta = (negocio or 'CATÁLOGO').upper()
    canvas.setFont('Helvetica-Bold', 9)
    ancho_etiqueta = canvas.stringWidth(etiqueta, 'Helvetica-Bold', 9)
    margen_etiqueta = 14
    x_etiqueta = ancho / 2 - ancho_etiqueta / 2 - margen_etiqueta
    y_etiqueta = alto * 0.745
    color_borde(canvas, '#444444')
    canvas.setLineWidth(0.6)
    canvas.roundRect(x_etiqueta, y_etiqueta, ancho_etiqueta + margen_etiqueta * 2, 20, 2, fill=0, stroke=1)
    color_relleno(canvas, '#bbbbbb')
    canvas.drawCentredString(ancho / 2, y_etiqueta + 6, etiqueta)

    
    # Título principal — con salto de línea automático
    color_relleno(canvas, '#ffffff')
    tamano_titulo = 58
    palabras = titulo.upper().split()
    lineas = []
    linea_actual = ''

    for palabra in palabras:
        prueba = (linea_actual + ' ' + palabra).strip()
        canvas.setFont('Helvetica-Bold', tamano_titulo)
        while canvas.stringWidth(prueba, 'Helvetica-Bold', tamano_titulo) > ancho - 80 and tamano_titulo > 16:
            tamano_titulo -= 1
        if canvas.stringWidth(prueba, 'Helvetica-Bold', tamano_titulo) <= ancho - 80:
            linea_actual = prueba
        else:
            lineas.append(linea_actual)
            linea_actual = palabra

    if linea_actual:
        lineas.append(linea_actual)

    y_titulo = alto * 0.575
    espacio_entre_lineas = tamano_titulo + 8
    for linea in lineas:
        canvas.setFont('Helvetica-Bold', tamano_titulo)
        canvas.drawCentredString(ancho / 2, y_titulo, linea)
        y_titulo -= espacio_entre_lineas
    # Subtítulo
    if subtitulo:
        canvas.setFont('Helvetica', 11)
        canvas.setFillColorRGB(0.55, 0.55, 0.55)
        canvas.drawCentredString(ancho / 2, alto * 0.49, subtitulo)

    # Estadísticas (productos / páginas)
    color_relleno(canvas, '#ffffff')
    canvas.setFont('Helvetica-Bold', 32)
    canvas.drawCentredString(ancho / 2 - 65, alto * 0.38, str(total_productos))
    canvas.drawCentredString(ancho / 2 + 65, alto * 0.38, str(total_paginas))
    canvas.setFillColorRGB(0.45, 0.45, 0.45)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(ancho / 2 - 65, alto * 0.38 - 16, 'PRODUCTOS')
    canvas.drawCentredString(ancho / 2 + 65, alto * 0.38 - 16, 'PÁGINAS')
    # Separador vertical entre estadísticas
    color_borde(canvas, '#2a2a2a')
    canvas.setLineWidth(0.5)
    canvas.line(ancho / 2, alto * 0.358, ancho / 2, alto * 0.408)

    # Nombre del negocio y contacto al pie
    y_pie = alto * 0.26
    if negocio:
        canvas.setFont('Helvetica-Bold', 12)
        canvas.setFillColorRGB(0.5, 0.5, 0.5)
        canvas.drawCentredString(ancho / 2, y_pie, negocio)
        y_pie -= 18
    if contacto:
        canvas.setFont('Helvetica', 10)
        canvas.setFillColorRGB(0.35, 0.35, 0.35)
        canvas.drawCentredString(ancho / 2, y_pie, contacto)

# ── DIBUJO DE BARRA SUPERIOR ─────────────────────────────────
def dibujar_barra_superior(canvas, ancho, alto, alto_barra, margen, numero_pagina, total_paginas, negocio, titulo_catalogo, tema):
    """Dibuja la barra de navegación en la parte superior de cada página."""
    color_borde(canvas, tema['borde'])
    canvas.setLineWidth(0.4)
    canvas.line(0, alto - alto_barra, ancho, alto - alto_barra)

    # Número de página (izquierda)
    canvas.setFont('Helvetica', 8)
    color_relleno(canvas, tema['texto_tenue'])
    canvas.drawString(margen, alto - alto_barra + 14, f"{numero_pagina + 1:02d} / {total_paginas:02d}")

    # Nombre del negocio (centro, con borde)
    if negocio:
        texto_negocio = negocio.upper()
        ancho_texto = canvas.stringWidth(texto_negocio, 'Helvetica-Bold', 8)
        x_caja = ancho / 2 - ancho_texto / 2 - 10
        color_borde(canvas, tema['borde'])
        canvas.setLineWidth(0.4)
        canvas.roundRect(x_caja, alto - alto_barra + 9, ancho_texto + 20, 17, 2, fill=0, stroke=1)
        color_relleno(canvas, tema['texto_tenue'])
        canvas.setFont('Helvetica-Bold', 8)
        canvas.drawCentredString(ancho / 2, alto - alto_barra + 15, texto_negocio)

    # Nombre del catálogo (derecha)
    texto_catalogo = titulo_catalogo.upper()
    canvas.setFont('Helvetica', 7)
    color_relleno(canvas, tema['texto_tenue'])
    ancho_catalogo = canvas.stringWidth(texto_catalogo, 'Helvetica', 7)
    canvas.drawString(ancho - margen - ancho_catalogo, alto - alto_barra + 14, texto_catalogo)

# ── DIBUJO DE PIE DE PÁGINA ──────────────────────────────────
def dibujar_pie(canvas, ancho, alto_pie, margen, nombre_producto, precio, tema):
    """Dibuja el pie de página con nombre del producto y precio."""
    color_borde(canvas, tema['borde'])
    canvas.setLineWidth(0.4)
    canvas.line(0, alto_pie, ancho, alto_pie)

    # Nombre del producto
    nombre_cortado = nombre_producto[:40] + ('…' if len(nombre_producto) > 40 else '')
    tamano_nombre = 14
    canvas.setFont('Helvetica-Bold', tamano_nombre)
    while canvas.stringWidth(nombre_cortado, 'Helvetica-Bold', tamano_nombre) > ancho * 0.55 and tamano_nombre > 8:
        tamano_nombre -= 1
    color_relleno(canvas, tema['texto'])
    canvas.setFont('Helvetica-Bold', tamano_nombre)
    canvas.drawString(margen, alto_pie - 28, nombre_cortado)

    # Caja de precio
    texto_precio = precio if precio else 'Precio: ___________'
    ancho_caja_precio = canvas.stringWidth(texto_precio, 'Helvetica', 10) + 22
    x_caja_precio = ancho - margen - ancho_caja_precio
    color_borde(canvas, tema['borde'])
    canvas.setLineWidth(0.4)
    canvas.roundRect(x_caja_precio, alto_pie - 32, ancho_caja_precio, 20, 3, fill=0, stroke=1)
    color_relleno(canvas, tema['color_precio'])
    canvas.setFont('Helvetica', 10)
    canvas.drawCentredString(x_caja_precio + ancho_caja_precio / 2, alto_pie - 25, texto_precio)

# ── DIBUJO DE PÁGINA CON 1 IMAGEN ────────────────────────────
def dibujar_pagina_una_imagen(canvas, ancho, alto, lector_imagen, tamano_imagen, nombre, numero_pagina, total_paginas, negocio, titulo, precio, tema):
    """Página completa con una sola imagen grande + barra superior + pie."""
    ALTO_BARRA = 42
    ALTO_PIE   = 48
    MARGEN     = 24

    color_relleno(canvas, tema['fondo_pagina'])
    canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)
    dibujar_barra_superior(canvas, ancho, alto, ALTO_BARRA, MARGEN, numero_pagina, total_paginas, negocio, titulo, tema)

    # Imagen centrada en el espacio disponible
    espacio_ancho = ancho - MARGEN * 2
    espacio_alto  = alto - ALTO_BARRA - ALTO_PIE - MARGEN * 2
    ancho_img, alto_img = tamano_imagen
    escala = min(espacio_ancho / ancho_img, espacio_alto / alto_img)
    ancho_dibujado = ancho_img * escala
    alto_dibujado  = alto_img * escala
    x_imagen = MARGEN + (espacio_ancho - ancho_dibujado) / 2
    y_imagen  = ALTO_PIE + MARGEN + (espacio_alto - alto_dibujado) / 2
    canvas.drawImage(lector_imagen, x_imagen, y_imagen, ancho_dibujado, alto_dibujado)

    dibujar_pie(canvas, ancho, ALTO_PIE, MARGEN, nombre, precio, tema)

# ── DIBUJO DE PÁGINA CON GRID (2 o 4 IMÁGENES) ───────────────
def dibujar_pagina_grid(canvas, ancho, alto, productos, precio, tema, columnas, filas):
    """
    Dibuja una cuadrícula de tarjetas con imagen + nombre + precio.
    Layout 2 → columnas=1, filas=2  (dos tarjetas apiladas verticalmente)
    Layout 4 → columnas=2, filas=2  (cuatro tarjetas en 2x2)
    """
    MARGEN_GRID  = 14   # espacio entre tarjetas y bordes
    ALTO_PIE_TARJETA = 44   # altura del pie de cada tarjeta

    ancho_tarjeta = (ancho - MARGEN_GRID * (columnas + 1)) / columnas
    alto_tarjeta  = (alto  - MARGEN_GRID * (filas    + 1)) / filas

    color_relleno(canvas, tema['fondo_pagina'])
    canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)

    for indice, (lector_img, tamano_img, nombre) in enumerate(productos):
        columna_actual = indice % columnas
        fila_actual    = indice // columnas

        # Posición de la tarjeta
        x_tarjeta = MARGEN_GRID + columna_actual * (ancho_tarjeta + MARGEN_GRID)
        y_tarjeta = alto - MARGEN_GRID - (fila_actual + 1) * alto_tarjeta - fila_actual * MARGEN_GRID

        # Fondo y borde de la tarjeta
        color_relleno(canvas, tema['fondo_tarjeta'])
        color_borde(canvas, tema['borde'])
        canvas.setLineWidth(0.5)
        canvas.roundRect(x_tarjeta, y_tarjeta, ancho_tarjeta, alto_tarjeta, 8, fill=1, stroke=1)

        # Imagen dentro de la tarjeta
        RELLENO_IMG = 6
        ancho_img_disponible = ancho_tarjeta - RELLENO_IMG * 2
        alto_img_disponible  = alto_tarjeta - ALTO_PIE_TARJETA - RELLENO_IMG * 2
        ancho_orig, alto_orig = tamano_img
        escala = min(ancho_img_disponible / ancho_orig, alto_img_disponible / alto_orig)
        ancho_img_d = ancho_orig * escala
        alto_img_d  = alto_orig  * escala
        x_img = x_tarjeta + RELLENO_IMG + (ancho_img_disponible - ancho_img_d) / 2
        y_img = y_tarjeta + ALTO_PIE_TARJETA + RELLENO_IMG + (alto_img_disponible - alto_img_d) / 2
        canvas.drawImage(lector_img, x_img, y_img, ancho_img_d, alto_img_d)

        # Pie de la tarjeta
        nombre_corto = nombre[:28] + ('…' if len(nombre) > 28 else '')
        tamano_fuente = 10 if columnas == 1 else 8
        canvas.setFont('Helvetica-Bold', tamano_fuente)
        color_relleno(canvas, tema['texto'])
        canvas.drawString(x_tarjeta + 10, y_tarjeta + ALTO_PIE_TARJETA - 16, nombre_corto)
        texto_precio = precio if precio else 'Precio: ___________'
        canvas.setFont('Helvetica', tamano_fuente - 1)
        color_relleno(canvas, tema['color_precio'])
        canvas.drawString(x_tarjeta + 10, y_tarjeta + ALTO_PIE_TARJETA - 32, texto_precio)

# ── RUTAS DE FLASK ───────────────────────────────────────────
@app.route('/')
def pagina_principal():
    """Sirve la interfaz web, inyectando el token de sesión."""
    return render_template('index.html', token=TOKEN_SESION)

@app.route('/generate', methods=['POST'])
def generar_catalogo():
    """Recibe las imágenes y parámetros, devuelve el PDF generado."""

    # ── Seguridad: verificar token ──
    token_recibido = request.form.get('token', '')
    if not secrets.compare_digest(token_recibido, TOKEN_SESION):
        abort(403)  # Forbidden

    # ── Seguridad: límite de peticiones ──
    limite_de_velocidad()

    try:
        # Leer parámetros del formulario
        titulo    = request.form.get('title',    '').strip() or 'Mi Catálogo'
        subtitulo = request.form.get('subtitle', '').strip()
        negocio   = request.form.get('business', '').strip()
        precio    = request.form.get('price',    '').strip()
        contacto  = request.form.get('contact',  '').strip()
        estilo    = request.form.get('style',    'oscuro')
        layout    = int(request.form.get('layout', '1'))
        archivos  = request.files.getlist('images')

        # ── Seguridad: validar parámetros ──
        if layout not in (1, 2, 4):
            return jsonify({'error': 'Layout no válido'}), 400
        if estilo not in TEMAS:
            estilo = 'oscuro'
        # Sanitizar textos: quitar caracteres peligrosos
        for campo in (titulo, subtitulo, negocio, precio, contacto):
            if len(campo) > 200:
                return jsonify({'error': 'Un campo de texto es demasiado largo'}), 400

        # Procesar imágenes
        imagenes = []
        contador = 1
        for archivo in archivos:
            if not archivo or not archivo.filename:
                continue
            # ── Seguridad: validar extensión ──
            if not extension_permitida(archivo.filename):
                continue
            bytes_imagen = archivo.read()
            if not bytes_imagen:
                continue
            # ── Seguridad: verificar que realmente es imagen ──
            try:
                lector, tamano = preparar_imagen(bytes_imagen)
                nombre = limpiar_nombre(archivo.filename) or f'Producto {contador}'
                imagenes.append((lector, tamano, nombre))
                contador += 1
            except Exception as error:
                print(f"Imagen ignorada ({archivo.filename}): {error}")
                continue

        if not imagenes:
            return jsonify({'error': 'No se pudieron leer las imágenes. Verifica que sean JPG o PNG.'}), 400

        # Configuración del PDF
        tema = TEMAS.get(estilo, TEMAS['oscuro'])
        tamano_pagina = landscape(A4) if layout == 1 else A4
        ancho_pagina, alto_pagina = tamano_pagina
        total_imagenes = len(imagenes)

        # Configuración de columnas/filas según layout
        if layout == 2:
            columnas, filas = 1, 2   # dos tarjetas apiladas verticalmente
        elif layout == 4:
            columnas, filas = 2, 2   # cuadrícula 2×2
        else:
            columnas, filas = 1, 1

        total_paginas_pdf = -(-total_imagenes // layout)  # división con techo

        # Generar PDF
        buffer_pdf = io.BytesIO()
        lienzo = pdf_canvas.Canvas(buffer_pdf, pagesize=tamano_pagina)

        # Portada
        dibujar_portada(lienzo, ancho_pagina, alto_pagina, titulo, subtitulo,
                        negocio, contacto, tema, total_imagenes, total_paginas_pdf)
        lienzo.showPage()

        # Páginas de productos
        if layout == 1:
            for numero, (lector, tamano, nombre) in enumerate(imagenes):
                dibujar_pagina_una_imagen(
                    lienzo, ancho_pagina, alto_pagina,
                    lector, tamano, nombre,
                    numero, total_imagenes,
                    negocio, titulo, precio, tema
                )
                lienzo.showPage()
        else:
            for inicio in range(0, total_imagenes, layout):
                grupo = imagenes[inicio:inicio + layout]
                dibujar_pagina_grid(lienzo, ancho_pagina, alto_pagina,
                                    grupo, precio, tema, columnas, filas)
                lienzo.showPage()

        lienzo.save()
        buffer_pdf.seek(0)

        # Nombre seguro para el archivo descargado
        nombre_archivo = re.sub(r'[^\w\s\-]', '', titulo)[:40].strip().replace(' ', '_') or 'catalogo'
        return send_file(buffer_pdf, mimetype='application/pdf',
                         as_attachment=True,
                         download_name=nombre_archivo + '.pdf')

    except Exception as error:
        traceback.print_exc()
        return jsonify({'error': str(error)}), 500

# ── ARRANQUE ─────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"\n  Generador de Catálogos corriendo en http://localhost:{PUERTO}\n")
    app.run(debug=False, port=PUERTO, use_reloader=False)
