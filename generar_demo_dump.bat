@echo off
setlocal EnableDelayedExpansion
title Generando dump de base de datos demo

echo =====================================================
echo  Exportando base de datos demo para el instalador
echo =====================================================
echo.

REM --- Verificar que MariaDB este corriendo ---
set "BIN=%~dp0mysql\bin"
set "MYSQLDUMP=%BIN%\mysqldump.exe"
set "MYSQL_CLIENT=%BIN%\mysql.exe"

if not exist "%MYSQLDUMP%" (
  echo [ERROR] No se encontro mysqldump.exe en %BIN%
  echo Asegurate de que la carpeta mysql\ este en la raiz del proyecto.
  pause
  exit /b 1
)

echo [1/3] Verificando conexion con MariaDB en puerto 3307...
"%MYSQL_CLIENT%" -u root --port=3307 --protocol=TCP -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
  echo [ERROR] MariaDB no responde en puerto 3307.
  echo Asegurate de que el sistema este corriendo antes de ejecutar este script.
  pause
  exit /b 1
)
echo [OK] MariaDB responde correctamente.

echo.
echo [2/3] Exportando base supermercado_don_atilio...
"%MYSQLDUMP%" -u root --port=3307 --protocol=TCP ^
  --no-tablespaces ^
  --skip-add-locks ^
  --single-transaction ^
  --disable-keys ^
  --extended-insert ^
  --add-drop-table ^
  supermercado_don_atilio > "%~dp0demo_data.sql"

if errorlevel 1 (
  echo [ERROR] Fallo al exportar la base de datos.
  pause
  exit /b 1
)

REM --- Verificar que el archivo no este vacio ---
for %%A in ("%~dp0demo_data.sql") do set TAMANIO=%%~zA
if "%TAMANIO%"=="0" (
  echo [ERROR] El archivo demo_data.sql quedo vacio. Algo salio mal.
  del "%~dp0demo_data.sql" >nul 2>&1
  pause
  exit /b 1
)

echo [OK] demo_data.sql generado ^(%TAMANIO% bytes^).
echo.
echo [3/3] Listo!
echo.
echo  Archivo generado: demo_data.sql
echo  Ahora podes:
echo    1. Ejecutar build.bat
echo    2. Compilar installer.iss con Inno Setup
echo    3. El instalador incluira automaticamente los datos demo.
echo.
pause
exit /b 0
