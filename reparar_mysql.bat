@echo off
REM ========================================
REM  REPARACION DE MYSQL - Don Atilio v2
REM  Ejecutar como ADMINISTRADOR
REM ========================================

REM Verificar que se ejecuta como admin
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ========================================
    echo  ERROR: SE REQUIEREN PRIVILEGIOS DE ADMIN
    echo ========================================
    echo.
    echo Este script DEBE ejecutarse como Administrador
    echo.
    echo Pasos:
    echo 1. Click derecho en este archivo
    echo 2. Seleccionar "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

echo ========================================
echo  REPARACION DE MYSQL - Don Atilio
echo ========================================
echo.

REM Detectar directorio de instalacion
set "INSTALL_DIR=C:\Program Files\Sistema Cobros Don Atilio\"
if not exist "%INSTALL_DIR%" (
    set "INSTALL_DIR=C:\Program Files (x86)\Sistema Cobros Don Atilio\"
)

if not exist "%INSTALL_DIR%" (
    echo ERROR: No se encuentra la instalacion de Don Atilio
    echo Esperado en: C:\Program Files\Sistema Cobros Don Atilio\
    pause
    exit /b 1
)

echo Directorio detectado: %INSTALL_DIR%
echo.

set "MYSQL_DIR=%INSTALL_DIR%mysql"
set "MYSQL_BIN=%MYSQL_DIR%\bin"
set "MYSQL_DATA=%MYSQL_DIR%\data"
set "MY_INI=%MYSQL_DIR%\my.ini"

REM Verificar que mysqld.exe existe
if not exist "%MYSQL_BIN%\mysqld.exe" (
    echo ERROR: No se encuentra mysqld.exe en %MYSQL_BIN%
    echo La carpeta MySQL no se instalo correctamente
    pause
    exit /b 1
)

echo [1/7] Deteniendo servicio existente (si existe)...
sc query "MySQL_DonAtilio" >nul 2>&1
if %errorlevel% equ 0 (
    net stop "MySQL_DonAtilio" 2>nul
    timeout /t 2 /nobreak >nul
    sc delete "MySQL_DonAtilio" >nul 2>&1
    timeout /t 2 /nobreak >nul
    echo    Servicio anterior eliminado
) else (
    echo    No habia servicio anterior
)

echo.
echo [2/7] Generando my.ini con rutas correctas...
(
echo [mysqld]
echo port=3307
echo basedir="%MYSQL_DIR%"
echo datadir="%MYSQL_DATA%"
echo.
echo max_connections=100
echo key_buffer_size=16M
echo max_allowed_packet=16M
echo table_open_cache=64
echo sort_buffer_size=512K
echo net_buffer_length=8K
echo read_buffer_size=256K
echo read_rnd_buffer_size=512K
echo myisam_sort_buffer_size=8M
echo.
echo character-set-server=utf8mb4
echo collation-server=utf8mb4_unicode_ci
echo.
echo log_error="%MYSQL_DATA%\mysql_error.log"
echo sql_mode=NO_ENGINE_SUBSTITUTION
echo skip-external-locking
echo console=off
echo.
echo [client]
echo port=3307
echo default-character-set=utf8mb4
echo.
echo [mysql]
echo default-character-set=utf8mb4
) > "%MY_INI%"

if exist "%MY_INI%" (
    echo    my.ini creado exitosamente
) else (
    echo    ERROR: No se pudo crear my.ini
    pause
    exit /b 1
)

echo.
echo [3/7] Inicializando base de datos (si no existe)...

REM Verificar si ya esta inicializada
if exist "%MYSQL_DATA%\mysql\db.frm" (
    echo    Base de datos ya inicializada (encontrado mysql\db.frm)
    goto :SKIP_INIT
)

if exist "%MYSQL_DATA%\mysql" (
    echo    Base de datos ya inicializada (carpeta mysql existe)
    goto :SKIP_INIT
)

echo    Creando estructura de datos...

REM --- CAMBIO CRITICO: Verificar que mysql_install_db.exe existe ---
if not exist "%MYSQL_BIN%\mysql_install_db.exe" (
    echo    ERROR: mysql_install_db.exe NO existe
    echo    Esto significa que instalaste MySQL en lugar de MariaDB
    echo.
    echo    SOLUCION:
    echo    1. Descarga MariaDB ZIP desde: https://mariadb.org/download/
    echo    2. Extrae y renombra la carpeta a "mysql"
    echo    3. Reemplaza la carpeta: %MYSQL_DIR%
    echo    4. Ejecuta este script de nuevo
    pause
    exit /b 1
)

REM --- CAMBIO CRITICO: No verificar errorlevel, sino la existencia de archivos ---
"%MYSQL_BIN%\mysql_install_db.exe" --datadir="%MYSQL_DATA%" --password=""

REM Verificar que se creo la estructura (independiente del errorlevel)
timeout /t 2 /nobreak >nul

if exist "%MYSQL_DATA%\mysql" (
    echo    Estructura creada exitosamente
) else (
    echo    ERROR: No se creo la carpeta mysql\data\mysql
    echo    La inicializacion fallo
    if exist "%MYSQL_DATA%\mysql_error.log" (
        echo    Revisa el log:
        type "%MYSQL_DATA%\mysql_error.log"
    )
    pause
    exit /b 1
)

:SKIP_INIT

echo.
echo [4/7] Instalando servicio MySQL_DonAtilio...
"%MYSQL_BIN%\mysqld.exe" --install "MySQL_DonAtilio" --defaults-file="%MY_INI%"
if %errorlevel% neq 0 (
    echo    ERROR: No se pudo instalar el servicio
    echo    Posibles causas:
    echo    - Ya existe otro servicio MySQL
    echo    - Faltan permisos de administrador
    pause
    exit /b 1
)
echo    Servicio instalado

echo.
echo [5/7] Iniciando servicio...
net start "MySQL_DonAtilio"
if %errorlevel% neq 0 (
    echo    ERROR: No se pudo iniciar el servicio
    echo    Revisa el log: %MYSQL_DATA%\mysql_error.log
    echo.
    if exist "%MYSQL_DATA%\mysql_error.log" (
        echo    Ultimas lineas del log:
        powershell -command "Get-Content '%MYSQL_DATA%\mysql_error.log' -Tail 10"
    )
    pause
    exit /b 1
)
echo    Servicio iniciado

echo.
echo [6/7] Esperando a que MySQL este listo...
set INTENTOS=0
:WAIT_MYSQL
timeout /t 1 /nobreak >nul
"%MYSQL_BIN%\mysql.exe" -u root --port=3307 -e "SELECT 1" >nul 2>&1
if %errorlevel% neq 0 (
    set /a INTENTOS+=1
    if %INTENTOS% geq 30 (
        echo    ERROR: MySQL no respondio despues de 30 segundos
        pause
        exit /b 1
    )
    goto WAIT_MYSQL
)
echo    MySQL listo!

echo.
echo [7/7] Creando base de datos...
if exist "%INSTALL_DIR%schema.sql" (
    echo    Ejecutando schema.sql...
    "%MYSQL_BIN%\mysql.exe" -u root --port=3307 < "%INSTALL_DIR%schema.sql"
    if %errorlevel% neq 0 (
        echo    ERROR: Fallo al crear el schema
        pause
        exit /b 1
    )
    echo    Base de datos creada
) else (
    echo    ERROR: No se encuentra schema.sql en %INSTALL_DIR%
    pause
    exit /b 1
)

echo.
echo ========================================
echo  REPARACION COMPLETADA EXITOSAMENTE
echo ========================================
echo.
echo MySQL esta corriendo en:
echo - Puerto: 3307
echo - Servicio: MySQL_DonAtilio
echo - Base de datos: supermercado_don_atilio
echo.
echo SIGUIENTE PASO: Cargar datos iniciales
echo.
echo Ejecuta esto en CMD como Administrador:
echo cd "%INSTALL_DIR%"
echo SistemaCobrosDonAtilio.exe --seed-data
echo.
pause