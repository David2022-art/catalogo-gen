# -*- coding: utf-8 -*-
# ============================================================
#  GENERADOR DE CATÁLOGOS  —  app.py
# ============================================================

from flask import Flask, render_template, request, send_file, jsonify, abort
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4, landscape
import io, re, traceback, secrets, time

# Importar configuración y motor de PDF
import config
from pdf_engine import (
    preparar_imagen, limpiar_nombre, dibujar_portada,
    dibujar_pagina_una_imagen, dibujar_pagina_grid
)

# ── SEGURIDAD (Estado Temporal) ──────────────────────────────
_historial_peticiones = []

def limite_de_velocidad():
    """Bloquea si se superan LIMITE_PETICIONES en VENTANA_SEGUNDOS."""
    ahora = time.time()
    _historial_peticiones[:] = [t for t in _historial_peticiones if ahora - t < config.VENTANA_SEGUNDOS]
    if len(_historial_peticiones) >= config.LIMITE_PETICIONES:
        abort(429)
    _historial_peticiones.append(ahora)

def extension_permitida(nombre_archivo):
    ext = nombre_archivo.rsplit('.', 1)[-1].lower() if '.' in nombre_archivo else ''
    return ext in config.EXTENSIONES_OK

# ── INICIALIZACIÓN DE FLASK ──────────────────────────────────
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_SUBIDA_MB * 1024 * 1024
app.secret_key = config.TOKEN_SESION

# ── RUTAS DE FLASK ───────────────────────────────────────────
@app.route('/')
def pagina_principal():
    return render_template('index.html', token=config.TOKEN_SESION)

@app.route('/generate', methods=['POST'])
def generar_catalogo():
    token_recibido = request.form.get('token', '')
    if not secrets.compare_digest(token_recibido, config.TOKEN_SESION):
        abort(403)

    limite_de_velocidad()

    try:
        titulo    = request.form.get('title', '').strip() or 'Mi Catálogo'
        subtitulo = request.form.get('subtitle', '').strip()
        negocio   = request.form.get('business', '').strip()
        precio    = request.form.get('price', '').strip()
        contacto  = request.form.get('contact', '').strip()
        estilo    = request.form.get('style', 'oscuro')
        layout    = int(request.form.get('layout', '1'))
        archivos  = request.files.getlist('images')

        # Validar longitud de campos
        for campo, valor in [('Título', titulo), ('Subtítulo', subtitulo), ('Negocio', negocio), ('Precio', precio), ('Contacto', contacto)]:
            if len(valor) > 200:
                return jsonify({'error': f'El campo {campo} es demasiado largo (máximo 200 caracteres)'}), 400
        
        if layout not in (1, 2, 4): return jsonify({'error': 'Layout no válido'}), 400
        tema = config.TEMAS.get(estilo, config.TEMAS['oscuro'])
        
        precios_ind = request.form.getlist('individual_prices')
        
        # Procesar imágenes
        imagenes = []
        contador = 1
        for i, archivo in enumerate(archivos):
            if not archivo or not archivo.filename or not extension_permitida(archivo.filename):
                continue
            bytes_img = archivo.read()
            if not bytes_img: continue
            try:
                lector, tamano = preparar_imagen(bytes_img)
                nombre = limpiar_nombre(archivo.filename) or f'Producto {contador}'
                # Obtener precio individual si existe
                p_ind = precios_ind[i] if i < len(precios_ind) else ''
                imagenes.append((lector, tamano, nombre, p_ind))
                contador += 1
            except: continue

        if not imagenes:
            return jsonify({'error': 'No hay imágenes válidas'}), 400

        # Generar PDF
        tamano_pagina = landscape(A4) if layout == 1 else A4
        ancho, alto = tamano_pagina
        total_imagenes = len(imagenes)
        total_paginas_pdf = -(-total_imagenes // layout)

        buffer_pdf = io.BytesIO()
        lienzo = pdf_canvas.Canvas(buffer_pdf, pagesize=tamano_pagina)

        dibujar_portada(lienzo, ancho, alto, titulo, subtitulo, negocio, contacto, tema, total_imagenes, total_paginas_pdf)
        lienzo.showPage()

        if layout == 1:
            for numero, (l, t, n, pi) in enumerate(imagenes):
                dibujar_pagina_una_imagen(lienzo, ancho, alto, l, t, n, pi, numero, total_imagenes, negocio, titulo, precio, tema)
                lienzo.showPage()
        else:
            columnas, filas = (1, 2) if layout == 2 else (2, 2)
            for inicio in range(0, total_imagenes, layout):
                grupo = imagenes[inicio:inicio + layout]
                dibujar_pagina_grid(lienzo, ancho, alto, grupo, precio, tema, columnas, filas)
                lienzo.showPage()

        lienzo.save()
        buffer_pdf.seek(0)
        nombre_safe = re.sub(r'[^\w\s\-]', '', titulo)[:40].strip().replace(' ', '_') or 'catalogo'
        return send_file(buffer_pdf, mimetype='application/pdf', as_attachment=True, download_name=nombre_safe + '.pdf')

    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"\n  Servidor en http://localhost:{config.PUERTO}\n")
    app.run(debug=False, port=config.PUERTO, use_reloader=False)
