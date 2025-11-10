@echo off
setlocal ENABLEDELAYEDEXPANSION
title Compilando Sistema Cobros Don Atilio (Python 3.12 + venv)

REM *** SIEMPRE trabajar en la carpeta del script ***
cd /d "%~dp0"

echo Compilando Sistema Cobros Don Atilio [Python 3.12 + venv]
echo =========================================================
echo Carpeta de trabajo: %cd%
echo.

REM [0/7] Verificar Python 3.12
py -3.12 -V >NUL 2>&1
if errorlevel 1 (
  echo ERROR: No se encontro Python 3.12 con el lanzador "py".
  goto :fail
)

REM [1/7] Crear/usar entorno virtual .venv312
if exist ".venv312" (
  echo .venv312 ya existe, se reutilizara.
) else (
  echo Creando .venv312...
  py -3.12 -m venv .venv312 || (echo ERROR creando venv & goto :fail)
)

REM [2/7] Activar venv y actualizar pip
call ".venv312\Scripts\activate.bat"
python -m ensurepip --upgrade >NUL 2>&1
python -m pip install -U pip || (echo ERROR actualizando pip & goto :fail)

REM [3/7] Instalar dependencias
if exist "requirements.txt" (
  echo Instalando dependencias de requirements.txt...
  python -m pip install -r requirements.txt || (echo ERROR instalando deps & goto :fail)
) else (
  echo AVISO: No se encontro requirements.txt, se omite instalacion de deps.
)

REM [4/7] Instalar/actualizar PyInstaller
python -m pip install -U pyinstaller || (echo ERROR instalando PyInstaller & goto :fail)

REM [5/7] Limpiar compilaciones previas en ESTE proyecto
echo Limpiando build/dist del proyecto...
rmdir /s /q "%cd%\build"  2>NUL
rmdir /s /q "%cd%\dist"   2>NUL

REM [6/7] Compilar forzando rutas de salida a ESTE proyecto
set "SPEC=SistemaCobrosDonAtilio.spec"
if exist "%SPEC%" (
  echo Usando archivo de especificacion: %SPEC%
  python -m PyInstaller ^
    --distpath "%cd%\dist" ^
    --workpath "%cd%\build" ^
    "%SPEC%" || (echo ERROR en PyInstaller & goto :fail)
) else (

  echo No se encontro %SPEC%. Compilando con --onefile...
  python -m PyInstaller ^
    --onefile --name SistemaCobrosDonAtilio ^
    --distpath "%cd%\dist" ^
    --workpath "%cd%\build" ^
    app\main.py || (echo ERROR en PyInstaller & goto :fail)
)

REM [7/7] Verificar resultado
set "EXE=%cd%\dist\SistemaCobrosDonAtilio.exe"
echo.
if exist "%EXE%" (
  echo ========================================
  echo COMPILACION EXITOSA (Python 3.12 + venv)
  echo Ejecutable: "%EXE%"
  echo ========================================
  explorer "%cd%\dist"
  goto :end
) else (
  echo ========================================
  echo ERROR EN LA COMPILACION
  echo No se encontro "%EXE%".
  echo Revisar warn/logs en: "%cd%\build"
  echo ========================================
  goto :fail
)

:fail
echo.
echo Revisa los errores arriba
echo (la ventana queda abierta para que puedas leerlos)
echo.
if defined VIRTUAL_ENV ( call ".venv312\Scripts\deactivate.bat" )
pause
exit /b 1

:end
echo.
call ".venv312\Scripts\deactivate.bat"
pause
exit /b 0
