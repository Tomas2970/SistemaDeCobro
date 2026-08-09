@echo off
echo ========================================
echo  VERIFICADOR DE REQUISITOS INSTALADOR
echo  Sistema Cobros Don Atilio - v2.0
echo ========================================
echo.

set "ERRORES=0"
set "ADVERTENCIAS=0"

REM Verificar Python
echo [1/9] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo    X Python NO encontrado
    set /a ERRORES+=1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo    √ Python %%i instalado
)

REM Verificar dependencias
echo.
echo [2/9] Verificando dependencias Python...
python -c "import mysql.connector" 2>nul
if %errorlevel% neq 0 (
    echo    X mysql-connector-python NO instalado
    set /a ERRORES+=1
) else (
    echo    √ mysql-connector-python OK
)

python -c "import bcrypt" 2>nul
if %errorlevel% neq 0 (
    echo    X bcrypt NO instalado
    set /a ERRORES+=1
) else (
    echo    √ bcrypt OK
)

python -c "import dotenv" 2>nul
if %errorlevel% neq 0 (
    echo    X python-dotenv NO instalado
    set /a ERRORES+=1
) else (
    echo    √ python-dotenv OK
)

python -c "import PIL" 2>nul
if %errorlevel% neq 0 (
    echo    X Pillow NO instalado
    set /a ERRORES+=1
) else (
    echo    √ Pillow OK
)

REM Verificar PyInstaller
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo    ! PyInstaller NO instalado (necesario para compilar)
    set /a ADVERTENCIAS+=1
) else (
    echo    √ PyInstaller OK
)

REM Verificar logo
echo.
echo [3/9] Verificando logo.ico...
if exist "logo.ico" (
    echo    √ logo.ico encontrado
) else (
    echo    X logo.ico NO encontrado
    echo    → Ejecuta: python crear_logo.py
    set /a ERRORES+=1
)

REM Verificar que existe el PNG fuente
echo.
echo [4/9] Verificando imagen fuente...
if exist "app\frontend\Don atilio.png" (
    echo    √ Don atilio.png encontrado
) else (
    echo    X app\frontend\Don atilio.png NO encontrado
    set /a ERRORES+=1
)

REM Verificar MySQL
echo.
echo [5/9] Verificando MySQL portable...
if exist "mysql\bin\mysqld.exe" (
    echo    √ MySQL portable encontrado
) else (
    echo    X MySQL portable NO encontrado
    echo    → Descarga MariaDB ZIP desde: https://mariadb.org/download/
    echo    → Descomprime y renombra la carpeta a "mysql"
    set /a ERRORES+=1
)

REM Verificar mysql_install_db.exe (específico de MariaDB)
if exist "mysql\bin\mysql_install_db.exe" (
    echo    √ mysql_install_db.exe encontrado (MariaDB)
) else (
    echo    ! mysql_install_db.exe NO encontrado
    echo    → Asegúrate de descargar MariaDB (no MySQL)
    set /a ADVERTENCIAS+=1
)

REM Verificar schema
echo.
echo [6/9] Verificando schema.sql...
if exist "app\database\schema.sql" (
    echo    √ Schema SQL encontrado
) else (
    echo    X app\database\schema.sql NO encontrado
    set /a ERRORES+=1
)

REM Verificar scripts de instalación
echo.
echo [7/9] Verificando scripts de instalación...
if exist "installer_scripts\setup_mysql.bat" (
    echo    √ setup_mysql.bat OK
) else (
    echo    X installer_scripts\setup_mysql.bat NO encontrado
    set /a ERRORES+=1
)

if exist "installer_scripts\.env.production" (
    echo    √ .env.production OK
    REM Verificar que el puerto sea 3307
    findstr /C:"DB_PORT=3307" "installer_scripts\.env.production" >nul
    if %errorlevel% neq 0 (
        echo    ! ADVERTENCIA: .env.production no usa puerto 3307
        set /a ADVERTENCIAS+=1
    )
) else (
    echo    X installer_scripts\.env.production NO encontrado
    set /a ERRORES+=1
)

REM Verificar que my.ini NO tenga rutas hardcodeadas
echo.
echo [8/9] Verificando my.ini...
if exist "installer_scripts\my.ini" (
    findstr /C:"C:/Program Files" "installer_scripts\my.ini" >nul
    if %errorlevel% equ 0 (
        echo    ! ADVERTENCIA: my.ini tiene rutas hardcodeadas
        echo    → El setup_mysql.bat lo generará dinámicamente
        set /a ADVERTENCIAS+=1
    ) else (
        echo    √ my.ini OK (será generado por setup_mysql.bat)
    )
) else (
    echo    ! my.ini NO encontrado (se generará automáticamente)
)

REM Verificar archivo .spec de PyInstaller
echo.
echo [9/9] Verificando archivo de compilación...
if exist "SistemaCobrosDonAtilio.spec" (
    echo    √ SistemaCobrosDonAtilio.spec OK
) else (
    echo    X SistemaCobrosDonAtilio.spec NO encontrado
    set /a ERRORES+=1
)

REM Verificar Inno Setup (opcional)
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    echo    √ Inno Setup 6 instalado
) else (
    echo    ! Inno Setup NO encontrado (necesario para crear instalador)
    echo    → Descarga desde: https://jrsoftware.org/isdl.php
    set /a ADVERTENCIAS+=1
)

echo.
echo ========================================
if %ERRORES% equ 0 (
    if %ADVERTENCIAS% equ 0 (
        echo   TODO PERFECTO!
    ) else (
        echo   LISTO CON %ADVERTENCIAS% ADVERTENCIAS
    )
    echo ========================================
    echo.
    echo Pasos siguientes:
    echo   1. Si falta logo.ico: python crear_logo.py
    echo   2. Compila el ejecutable: build.bat
    echo   3. Crea el instalador: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
    echo   4. El instalador estará en: Instalador_Output\
) else (
    echo   FALTAN %ERRORES% REQUISITOS CRITICOS
    if %ADVERTENCIAS% gtr 0 (
        echo   Y HAY %ADVERTENCIAS% ADVERTENCIAS
    )
    echo ========================================
    echo.
    echo Revisa los errores marcados con X arriba
    echo y corrígelos antes de continuar.
)

echo.
pause