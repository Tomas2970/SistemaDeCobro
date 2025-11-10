@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title Cargar Datos Iniciales - Sistema Cobros Don Atilio

set "BASE=%~dp0"
set "MYSQL=%BASE%\mysql\bin\mysql.exe"
set "SEED=%BASE%\cargar_datos_manual.sql"

set "DB_HOST=localhost"
set "DB_PORT=3307"
set "DB_USER=root"
set "DB_PASSWORD="
set "DB_NAME=supermercado_don_atilio"

REM Leer .env si existe
if exist "%BASE%\.env" (
  for /f "usebackq eol=# tokens=1,2 delims== " %%A in ("%BASE%\.env") do (
    set "k=%%~A"
    set "v=%%~B"
    if /I "!k!"=="DB_HOST" set "DB_HOST=!v!"
    if /I "!k!"=="DB_PORT" set "DB_PORT=!v!"
    if /I "!k!"=="DB_USER" set "DB_USER=!v!"
    if /I "!k!"=="DB_PASSWORD" set "DB_PASSWORD=!v!"
    if /I "!k!"=="DB_NAME" set "DB_NAME=!v!"
  )
)

set "AUTH=-h%DB_HOST% -P%DB_PORT% -u%DB_USER% --protocol=TCP"
if defined DB_PASSWORD set "AUTH=%AUTH% -p%DB_PASSWORD%"

echo [SEED] Verificando conexion...
"%MYSQL%" %AUTH% -e "SELECT 1;" >nul 2>&1 || ( echo [ERROR] No hay conexion DB & exit /b 1 )

if exist "%SEED%" (
  echo [SEED] Ejecutando %SEED% ...
  "%MYSQL%" %AUTH% %DB_NAME% < "%SEED%"
  if errorlevel 1 (
    echo [ERROR] Fallo al ejecutar seed.
    exit /b 1
  )
) else (
  echo [WARN] No existe %SEED%. Se omite seed.
)

REM ===== GARANTIZAR ADMIN/admin123 =====
REM Hash de 'admin123' (bcrypt $2b$12)
set "ADMIN_HASH=$2b$12$tEa6owvg3LQbn5ZmLewhAe0anU6hj9ygpkKajh1p9H2YbU9QBvKnS"

echo [SEED] Garantizando usuario admin...
"%MYSQL%" %AUTH% %DB_NAME% -e ^
 "INSERT INTO usuario (nombre, `contraseña`, id_rol, activo)
  VALUES ('admin', '%ADMIN_HASH%', 1, 1)
  ON DUPLICATE KEY UPDATE
    `contraseña`=VALUES(`contraseña`),
    id_rol=VALUES(id_rol),
    activo=VALUES(activo);"

if errorlevel 1 (
  echo [ERROR] No se pudo garantizar admin/admin123.
  exit /b 1
)

echo [SEED] Datos iniciales OK (admin/admin123 listo).
exit /b 0
