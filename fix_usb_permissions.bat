@echo off
echo Configurando permisos USB para impresoras...
reg add "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\usbstor" /v "Start" /t REG_DWORD /d 3 /f
echo Permisos actualizados. Reinicia el servicio USB o el equipo.
pause