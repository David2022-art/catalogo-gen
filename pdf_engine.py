# -*- coding: utf-8 -*-
import io, os, re
from reportlab.lib.utils import ImageReader
from PIL import Image as Imagen
import config

# ── UTILIDADES DE COLOR ──────────────────────────────────────
def hex_a_rgb(color_hex):
    color_hex = color_hex.lstrip('#')
    return tuple(int(color_hex[i:i+2], 16) / 255 for i in (0, 2, 4))

def color_relleno(canvas, color_hex):
    canvas.setFillColorRGB(*hex_a_rgb(color_hex))

def color_borde(canvas, color_hex):
    canvas.setStrokeColorRGB(*hex_a_rgb(color_hex))

# ── PROCESAMIENTO DE IMÁGENES ────────────────────────────────
def preparar_imagen(bytes_imagen):
    imagen = Imagen.open(io.BytesIO(bytes_imagen))
    if imagen.mode != 'RGB':
        imagen = imagen.convert('RGB')
    ancho, alto = imagen.size
    if max(ancho, alto) > config.TAMANO_MAX_IMAGEN:
        escala = config.TAMANO_MAX_IMAGEN / max(ancho, alto)
        imagen = imagen.resize((int(ancho * escala), int(alto * escala)), Imagen.LANCZOS)
    buffer = io.BytesIO()
    imagen.save(buffer, format='JPEG', quality=config.CALIDAD_IMAGEN, optimize=True)
    buffer.seek(0)
    return ImageReader(buffer), imagen.size

def limpiar_nombre(nombre_archivo):
    base = os.path.splitext(os.path.basename(nombre_archivo))[0]
    nombre = re.sub(r'(?i)whatsapp[\s_\-]*image[\s_\-]*\d{4}.*', '', base).strip()
    nombre = re.sub(r'[\s_\-]+', ' ', nombre).strip()
    return nombre or None

# ── DIBUJO DE PORTADA ────────────────────────────────────────
def dibujar_portada(canvas, ancho, alto, titulo, subtitulo, negocio, contacto, tema, total_productos, total_paginas):
    color_relleno(canvas, tema['fondo_portada'])
    canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)
    color_borde(canvas, '#2a2a2a')
    canvas.setLineWidth(0.5)
    canvas.line(ancho * 0.1, alto * 0.55, ancho * 0.9, alto * 0.55)
    
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
    if linea_actual: lineas.append(linea_actual)

    y_titulo = alto * 0.575
    espacio_entre_lineas = tamano_titulo + 8
    for linea in lineas:
        canvas.setFont('Helvetica-Bold', tamano_titulo)
        canvas.drawCentredString(ancho / 2, y_titulo, linea)
        y_titulo -= espacio_entre_lineas

    if subtitulo:
        canvas.setFont('Helvetica', 11)
        canvas.setFillColorRGB(0.55, 0.55, 0.55)
        canvas.drawCentredString(ancho / 2, alto * 0.49, subtitulo)

    color_relleno(canvas, '#ffffff')
    canvas.setFont('Helvetica-Bold', 32)
    canvas.drawCentredString(ancho / 2 - 65, alto * 0.38, str(total_productos))
    canvas.drawCentredString(ancho / 2 + 65, alto * 0.38, str(total_paginas))
    canvas.setFillColorRGB(0.45, 0.45, 0.45)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(ancho / 2 - 65, alto * 0.38 - 16, 'PRODUCTOS')
    canvas.drawCentredString(ancho / 2 + 65, alto * 0.38 - 16, 'PÁGINAS')
    color_borde(canvas, '#2a2a2a')
    canvas.setLineWidth(0.5)
    canvas.line(ancho / 2, alto * 0.358, ancho / 2, alto * 0.408)

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

# ── DIBUJO DE PÁGINAS ────────────────────────────────────────
def dibujar_barra_superior(canvas, ancho, alto, alto_barra, margen, numero_pagina, total_paginas, negocio, titulo_catalogo, tema):
    color_borde(canvas, tema['borde'])
    canvas.setLineWidth(0.4)
    canvas.line(0, alto - alto_barra, ancho, alto - alto_barra)
    canvas.setFont('Helvetica', 8)
    color_relleno(canvas, tema['texto_tenue'])
    canvas.drawString(margen, alto - alto_barra + 14, f"{numero_pagina + 1:02d}") # Simplificado para que quepa bien
    if negocio:
        color_relleno(canvas, tema['texto_tenue'])
        canvas.setFont('Helvetica-Bold', 8)
        canvas.drawCentredString(ancho / 2, alto - alto_barra + 15, negocio.upper())
    canvas.setFont('Helvetica', 7)
    canvas.drawRightString(ancho - margen, alto - alto_barra + 14, titulo_catalogo.upper())

def dibujar_pagina_una_imagen(canvas, ancho, alto, lector, tamano, nombre, precio_ind, numero, total, negocio, titulo, precio_gen, tema):
    ALTO_BARRA, ALTO_PIE, MARGEN = 42, 48, 24
    color_relleno(canvas, tema['fondo_pagina'])
    canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)
    dibujar_barra_superior(canvas, ancho, alto, ALTO_BARRA, MARGEN, numero, total, negocio, titulo, tema)
    
    espacio_ancho, espacio_alto = ancho - MARGEN * 2, alto - ALTO_BARRA - ALTO_PIE - MARGEN * 2
    ancho_img, alto_img = tamano
    escala = min(espacio_ancho / ancho_img, espacio_alto / alto_img)
    ancho_d, alto_d = ancho_img * escala, alto_img * escala
    canvas.drawImage(lector, MARGEN + (espacio_ancho - ancho_d) / 2, ALTO_PIE + MARGEN + (espacio_alto - alto_d) / 2, ancho_d, alto_d)
    
    # Pie
    color_borde(canvas, tema['borde']); canvas.setLineWidth(0.4); canvas.line(0, ALTO_PIE, ancho, ALTO_PIE)
    canvas.setFont('Helvetica-Bold', 14); color_relleno(canvas, tema['texto'])
    canvas.drawString(MARGEN, ALTO_PIE - 28, nombre[:40])
    # Precio (priorizar individual)
    p_final = precio_ind if precio_ind else precio_gen
    if p_final:
        txt_p = p_final
        canvas.setFont('Helvetica', 10); color_relleno(canvas, tema['color_precio'])
        canvas.drawRightString(ancho - MARGEN, ALTO_PIE - 28, txt_p)

def dibujar_pagina_grid(canvas, ancho, alto, grupo, precio_gen, tema, columnas, filas):
    MARGEN, ALTO_PIE = 14, 44
    ancho_t, alto_t = (ancho - MARGEN * (columnas + 1)) / columnas, (alto - MARGEN * (filas + 1)) / filas
    color_relleno(canvas, tema['fondo_pagina']); canvas.rect(0, 0, ancho, alto, fill=1, stroke=0)

    for i, (lector, tamano, nombre, precio_ind) in enumerate(grupo):
        col, fila = i % columnas, i // columnas
        x, y = MARGEN + col * (ancho_t + MARGEN), alto - MARGEN - (fila + 1) * alto_t - fila * MARGEN
        color_relleno(canvas, tema['fondo_tarjeta']); color_borde(canvas, tema['borde'])
        canvas.roundRect(x, y, ancho_t, alto_t, 8, fill=1, stroke=1)
        
        # Imagen
        R = 6
        aw, ah = ancho_t - R*2, alto_t - ALTO_PIE - R*2
        orig_w, orig_h = tamano
        e = min(aw / orig_w, ah / orig_h)
        canvas.drawImage(lector, x + R + (aw - orig_w*e)/2, y + ALTO_PIE + R + (ah - orig_h*e)/2, orig_w*e, orig_h*e)
        
        # Texto
        canvas.setFont('Helvetica-Bold', 9 if columnas==2 else 11); color_relleno(canvas, tema['texto'])
        canvas.drawString(x + 10, y + ALTO_PIE - 16, nombre[:25])
        p_final = precio_ind if precio_ind else precio_gen
        if p_final:
            canvas.setFont('Helvetica', 8 if columnas==2 else 10); color_relleno(canvas, tema['color_precio'])
            canvas.drawString(x + 10, y + ALTO_PIE - 30, p_final)
