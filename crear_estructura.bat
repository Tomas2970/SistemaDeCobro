@echo off
echo ========================================
echo  CREANDO ESTRUCTURA DE CARPETAS
echo  Sistema Cobros Don Atilio
echo ========================================
echo.

REM Crear carpeta para scripts de instalación
if not exist "installer_scripts" (
    mkdir "installer_scripts"
    echo [1/3] Carpeta installer_scripts\ creada
) else (
    echo [1/3] Carpeta installer_scripts\ ya existe
)

REM Crear carpeta para salida del instalador
if not exist "Instalador_Output" (
    mkdir "Instalador_Output"
    echo [2/3] Carpeta Instalador_Output\ creada
) else (
    echo [2/3] Carpeta Instalador_Output\ ya existe
)

REM Recordatorio sobre MySQL
echo [3/3] Recordatorio: Descargar MySQL portable
echo.
echo ========================================
echo  INSTRUCCIONES
echo ========================================
echo.
echo 1. Descarga MariaDB portable ZIP desde:
echo    https://mariadb.org/download/
echo    → Selecciona: Windows, ZIP file (not MSI)
echo.
echo 2. Descomprime el archivo descargado
echo.
echo 3. Renombra la carpeta extraída a "mysql"
echo.
echo 4. Mueve la carpeta "mysql" a la raíz de este proyecto
echo.
echo 5. La estructura debe quedar así:
echo    tu_proyecto\
echo    ├── mysql\
echo    │   ├── bin\
echo    │   ├── lib\
echo    │   └── share\
echo    ├── installer_scripts\
echo    └── ...
echo.
echo ========================================

pause