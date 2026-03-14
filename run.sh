#!/bin/bash
echo "==================================="
echo "  Generador de Catálogos"
echo "==================================="

# Verificar python3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no está instalado."
    echo "Ejecuta: sudo apt install python3 python3-venv python3-full"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el entorno virtual."
        echo "Intenta: sudo apt install python3-venv python3-full"
        exit 1
    fi
fi

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "Instalando dependencias..."
pip install flask pillow reportlab -q
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar las dependencias."
    echo "Verifica tu conexion a internet."
    exit 1
fi

echo ""
echo "Todo listo!"
echo "Abriendo navegador en: http://localhost:7860"
echo "Para detener: presiona Ctrl+C"
echo ""

# Abrir navegador automaticamente en Linux despues de que Flask arranque
(sleep 2 && xdg-open http://localhost:7860 2>/dev/null) &

# Correr app
python3 app.py
