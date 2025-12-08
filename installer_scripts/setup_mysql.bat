@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Setup MariaDB - Sistema Cobros Don Atilio

REM === RUTAS BASE ===
set "BASE=%~dp0"
set "BASE=%BASE:~0,-1%"
set "BIN=%BASE%\mysql\bin"
set "MYSQLD=%BIN%\mariadbd.exe"
set "MYSQL_INSTALL_DB_A=%BIN%\mariadb-install-db.exe"
set "MYSQL_INSTALL_DB_B=%BIN%\mysql_install_db.exe"
set "MYSQL_CLIENT=%BIN%\mysql.exe"
set "SERVICE=MySQL_DonAtilio"
set "DATADIR=%BASE%\mysql\data"
set "MYINI=%BASE%\my.ini"
set "SCHEMA=%BASE%\schema.sql"

echo [SETUP] Iniciando configuracion MariaDB...

REM --- Validaciones basicas ---
if not exist "%MYSQLD%" (
  echo [ERROR] No se encontro %MYSQLD%
  echo Copia el ZIP/portable de MariaDB dentro de {app}\mysql\
  exit /b 1
)

if not exist "%DATADIR%" mkdir "%DATADIR%" >nul 2>&1

REM --- Crear my.ini si no existe ---
if not exist "%MYINI%" (
  >"%MYINI%" echo [mysqld]
  >>"%MYINI%" echo port=3307
  >>"%MYINI%" echo basedir=%BASE%\mysql
  >>"%MYINI%" echo datadir=%BASE%\mysql\data
  >>"%MYINI%" echo character-set-server=utf8mb4
  >>"%MYINI%" echo collation-server=utf8mb4_unicode_ci
  >>"%MYINI%" echo sql_mode=NO_ENGINE_SUBSTITUTION
  >>"%MYINI%" echo [client]
  >>"%MYINI%" echo port=3307
  >>"%MYINI%" echo default-character-set=utf8mb4
  >>"%MYINI%" echo [mysql]
  >>"%MYINI%" echo default-character-set=utf8mb4
  echo [SETUP] Archivo my.ini generado.
)

REM --- Inicializar data dir si esta vacio ---
dir /b "%DATADIR%\mysql" >nul 2>&1
if errorlevel 1 (
  echo [SETUP] Inicializando data dir...
  if exist "%MYSQL_INSTALL_DB_A%" (
    "%MYSQL_INSTALL_DB_A%" --basedir="%BASE%\mysql" --datadir="%DATADIR%" --verbose-bootstrap
  ) else if exist "%MYSQL_INSTALL_DB_B%" (
    "%MYSQL_INSTALL_DB_B%" --basedir="%BASE%\mysql" --datadir="%DATADIR%" --verbose-bootstrap
  ) else (
    echo [ERROR] No se encontro mariadb-install-db.exe ni mysql_install_db.exe
    exit /b 1
  )
)

REM --- Rellenar placeholders de my.ini si los tiene ---
set "MYSQL_DIR=%BASE%mysql"
set "DATA_DIR=%BASE%mysql\data"
if exist "%BASE%my.ini" (
  powershell -NoProfile -Command ^
    "(Get-Content '%BASE%my.ini') ^
      -replace '__MYSQL_DIR__',  '%MYSQL_DIR%' ^
      -replace '__DATA_DIR__',   '%DATA_DIR%' | ^
     Set-Content -Encoding ASCII '%BASE%my.ini'"
  echo [SETUP] my.ini actualizado con rutas reales.
)

REM --- (Re)instalar servicio ---
sc query "%SERVICE%" >nul 2>&1
if errorlevel 1 (
  echo [SETUP] Instalando servicio %SERVICE%...
  "%MYSQLD%" --install "%SERVICE%" --defaults-file="%MYINI%"
) else (
  echo [SETUP] Servicio ya existe, reiniciando...
  net stop "%SERVICE%" >nul 2>&1
  timeout /t 2 /nobreak >nul
)

REM --- Iniciar servicio ---
echo [SETUP] Iniciando servicio...
net start "%SERVICE%" >nul 2>&1
if errorlevel 1 (
  echo [WARN] No se pudo iniciar mediante 'net start'. Mostrando error en consola:
  "%MYSQLD%" --defaults-file="%MYINI%" --console
  exit /b 1
)

REM --- 🔥 ESPERAR A QUE MYSQL RESPONDA ---
echo [SETUP] Esperando a que MySQL este listo...
set INTENTOS=0
:WAIT_MYSQL
timeout /t 1 /nobreak >nul
"%MYSQL_CLIENT%" -u root --port=3307 --protocol=TCP -e "SELECT 1;" >nul 2>&1
if errorlevel 1 (
  set /a INTENTOS+=1
  if %INTENTOS% geq 30 (
    echo [ERROR] MySQL no respondio en 30 segundos
    exit /b 1
  )
  goto WAIT_MYSQL
)
echo [SETUP] MySQL responde correctamente!

REM --- 🔥 EJECUTAR SCHEMA.SQL ---
if exist "%SCHEMA%" (
  echo [SETUP] Creando estructura de base de datos...
  "%MYSQL_CLIENT%" -u root --port=3307 --protocol=TCP < "%SCHEMA%"
  if errorlevel 1 (
    echo [ERROR] Fallo al ejecutar schema.sql
    exit /b 1
  )
  echo [SETUP] Schema creado exitosamente!
) else (
  echo [WARN] No se encuentra schema.sql, omitiendo creacion de estructura
)

echo [SETUP] MariaDB OK (servicio RUNNING en puerto 3307).
exit /b 0