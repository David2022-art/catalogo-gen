@echo off
chcp 65001 >nul
echo ===================================
echo   Generador de Catalogos
echo ===================================

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado.
    echo Descargalo en: https://www.python.org/downloads/
    echo Asegurate de marcar "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

:: Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

:: Verificar que el entorno virtual existe correctamente
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: El entorno virtual esta danado. Borra la carpeta venv e intenta de nuevo.
    pause
    exit /b 1
)

:: Activar entorno virtual
echo Activando entorno virtual...
call venv\Scripts\activate.bat

:: Instalar dependencias
echo Instalando dependencias...
pip install flask pillow reportlab -q
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias.
    echo Verifica tu conexion a internet.
    pause
    exit /b 1
)

echo.
echo Todo listo!
echo Abre tu navegador en: http://localhost:7860
echo Para detener: presiona Ctrl+C
echo.

:: Esperar 2 segundos para que Flask arranque, luego abrir navegador
ping -n 3 127.0.0.1 >nul
start http://localhost:7860

:: Correr app
python app.py
pause
