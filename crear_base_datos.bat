@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Crear base de datos (idempotente) - Sistema Cobros Don Atilio

set "BASE=%~dp0"
set "BASE=%BASE:~0,-1%"
set "MYSQL=%BASE%\mysql\bin\mysql.exe"
set "SCHEMA=%BASE%\schema.sql"

REM --- Cargar .env ---
set "DB_HOST=localhost"
set "DB_PORT=3307"
set "DB_USER=root"
set "DB_PASSWORD="
set "DB_NAME=supermercado_don_atilio"

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

set "DB_HOST=%DB_HOST:"=%"
set "DB_PORT=%DB_PORT:"=%"
set "DB_USER=%DB_USER:"=%"
set "DB_PASSWORD=%DB_PASSWORD:"=%"
set "DB_NAME=%DB_NAME:"=%"

set "AUTH=-h%DB_HOST% -P%DB_PORT% -u%DB_USER% --protocol=TCP"
if defined DB_PASSWORD set "AUTH=%AUTH% -p%DB_PASSWORD%"

echo [DB] Verificando conexion...
"%MYSQL%" %AUTH% -e "SELECT VERSION();" >nul 2>&1 || ( echo [ERROR] No hay conexion; revisa servicio y .env & exit /b 1 )

echo [DB] Creando BD si no existe...
"%MYSQL%" %AUTH% -e "CREATE DATABASE IF NOT EXISTS %DB_NAME% CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" || ( echo [ERROR] No se pudo crear BD & exit /b 1 )

echo [DB] Chequeando cantidad de tablas...
for /f "usebackq delims=" %%C in (`"%MYSQL%" %AUTH% -N -B -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='%DB_NAME%';" 2^>nul`) do set "TBLCNT=%%C"
if not defined TBLCNT set "TBLCNT=0"

if "%TBLCNT%"=="0" (
  if exist "%SCHEMA%" (
    echo [DB] Importando schema.sql ...
    "%MYSQL%" %AUTH% %DB_NAME% < "%SCHEMA%" || ( echo [ERROR] Fallo importando schema.sql & exit /b 1 )
  ) else (
    echo [WARN] No existe schema.sql; se omite importacion.
  )
) else (
  echo [DB] La BD ya tiene %TBLCNT% tablas; se omite importacion.
)

echo [DB] OK.
exit /b 0
