# -*- coding: utf-8 -*-
import secrets

# ── CONFIGURACIÓN GENERAL ────────────────────────────────────
PUERTO            = 7860
TAMANO_MAX_IMAGEN = 1800   # píxeles máximos por lado al redimensionar
CALIDAD_IMAGEN    = 85     # calidad JPEG (1-100)
MAX_SUBIDA_MB     = 500    # megabytes máximos por petición
EXTENSIONES_OK    = {'jpg', 'jpeg', 'png', 'webp', 'heic'}

# ── SEGURIDAD ────────────────────────────────────────────────
TOKEN_SESION = secrets.token_hex(16)
LIMITE_PETICIONES = 10
VENTANA_SEGUNDOS  = 60

# ── TEMAS DE COLOR ───────────────────────────────────────────
TEMAS = {
    'oscuro': {
        'fondo_pagina'  : '#111111',
        'fondo_tarjeta' : '#1e1e1e',
        'texto'         : '#ffffff',
        'texto_tenue'   : '#666666',
        'borde'         : '#2a2a2a',
        'fondo_portada' : '#0a0a0a',
        'color_precio'  : '#888888',
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
