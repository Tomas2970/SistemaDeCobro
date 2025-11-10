@echo off
setlocal ENABLEDELAYEDEXPANSION
title Compilando Sistema Cobros Don Atilio

echo Compilando Sistema Cobros Don Atilio
echo ========================================

echo [1/4] Verificando dependencias...

REM 1) Verificar que Python esté disponible
where python >NUL 2>&1
if errorlevel 1 (
  echo ERROR: Python no se encuentra en el PATH.
  echo Instala Python 3.x y/o marcá "Add Python to PATH" al instalar.
  goto :fail
)

REM 2) Asegurar pip y actualizarlo (sin depender de pip.exe en PATH)
python -m ensurepip --upgrade >NUL 2>&1
python -m pip install -U pip
if errorlevel 1 (
  echo ERROR: Fallo al actualizar pip.
  goto :fail
)

REM 3) Instalar dependencias del proyecto
if exist "requirements.txt" (
  echo Instalando dependencias de requirements.txt...
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo ERROR: Fallo al instalar dependencias de requirements.txt.
    goto :fail
  )
) else (
  echo AVISO: No se encontro requirements.txt, se omite instalacion de deps del proyecto.
)

REM 4) Instalar/Actualizar PyInstaller de forma robusta
python -m pip install -U pyinstaller
if errorlevel 1 (
  echo ERROR: Fallo al instalar/actualizar PyInstaller.
  goto :fail
)

echo.
echo [2/4] Limpiando compilaciones anteriores...
rmdir /s /q build  2>NUL
rmdir /s /q dist   2>NUL
REM Si TU flujo usa .spec existente, NO borres el .spec.
REM del /q SistemaCobrosDonAtilio.spec 2>NUL

echo.
echo [3/4] Compilando aplicacion...

REM Si existe el .spec, compilar desde .spec; si no, fallback a onefile con entrypoint por defecto
set "SPEC=SistemaCobrosDonAtilio.spec"
if exist "%SPEC%" (
  echo Usando archivo de especificacion: %SPEC%
  python -m PyInstaller "%SPEC%"
) else (
  echo No se encontro %SPEC%. Compilando con --onefile.
  REM >>> Ajusta la ruta del entrypoint si tu main es otro archivo <<<
  python -m PyInstaller --onefile --name SistemaCobrosDonAtilio app\main.py
)

if errorlevel 1 (
  echo ERROR: PyInstaller reporto un error durante la compilacion.
  goto :fail
)

echo.
echo [4/4] Verificando resultado...

REM Nombre esperado de salida (ajusta si en el .spec se define otro nombre)
set "EXE=dist\SistemaCobrosDonAtilio.exe"
if exist "%EXE%" (
  echo ========================================
  echo COMPILACION EXITOSA
  echo Ejecutable generado: %EXE%
  echo ========================================
  goto :end
) else (
  echo ========================================
  echo ERROR EN LA COMPILACION
  echo No se encontro "%EXE%".
  echo Si tu .spec genera otro nombre, ajusta la variable EXE arriba.
  echo ========================================
  goto :fail
)

:fail
echo.
echo Revisa los errores arriba
echo.
pause
exit /b 1

:end
echo.
pause
exit /b 0
