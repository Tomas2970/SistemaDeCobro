@echo off
setlocal ENABLEDELAYEDEXPANSION
title Compilando Sistema Cobros Don Atilio

echo Compilando Sistema Cobros Don Atilio
echo ========================================

echo [1/4] Verificando dependencias...

REM 1) Verificar que Python este disponible
where python >NUL 2>&1
if errorlevel 1 (
  echo ERROR: Python no se encuentra en el PATH.
  echo Instala Python 3.x y/o marca "Add Python to PATH" al instalar.
  goto :fail
)

REM 2) Asegurar pip y actualizarlo
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

REM 4) Instalar/Actualizar PyInstaller
python -m pip install -U pyinstaller
if errorlevel 1 (
  echo ERROR: Fallo al instalar/actualizar PyInstaller.
  goto :fail
)

echo.
echo [2/4] Limpiando compilaciones anteriores...
rmdir /s /q build  2>NUL
rmdir /s /q dist   2>NUL
REM Ya no borraremos el spec viejo, usaremos SistemaCobrosDonAtilio.spec

echo.
echo [3/4] Compilando aplicacion...

REM === COMPILACION USANDO EL ARCHIVO .SPEC MEJORADO ===
echo Generando compilacion incluyendo recursos de CustomTkinter...

python -m PyInstaller --clean SistemaCobrosDonAtilio.spec

if errorlevel 1 (
  echo ERROR: PyInstaller reporto un error durante la compilacion.
  goto :fail
)

echo.
echo [4/4] Verificando resultado...

set "EXE=dist\SistemaCobrosDonAtilio.exe"
if exist "%EXE%" (
  echo ========================================
  echo COMPILACION EXITOSA
  echo Ejecutable generado: %EXE%
  echo ========================================
  echo.
  echo NOTAS:
  echo - El seed esta integrado en main.py
  echo - Usa: SistemaCobrosDonAtilio.exe --seed-data
  echo.
  goto :end
) else (
  echo ========================================
  echo ERROR EN LA COMPILACION
  echo No se encontro "%EXE%".
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