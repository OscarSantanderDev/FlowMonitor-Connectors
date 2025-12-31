@echo off
:: Configuración de rutas
set "ORIGEN=E:\Apps\Televisa Networks\Tvsa Connectors M-Cent\log"
set "DESTINO=\\10.8.10.41\CajasNegras\logs\Logs Connectos Centralizados"

:: Título de la ventana
title Sincronizando Archivos de Texto...

:: Ejecución de Robocopy
:: /MIR  -> ESPEJO (Copia todo y BORRA en el destino lo que ya no exista en el origen)
:: /XO   -> Exclude Older (No sobrescribe si el archivo en destino es más nuevo)
:: /R:3  -> Reintentos si falla (3 veces)
:: /W:2  -> Espera entre reintentos (2 segundos)
:: /Z    -> Modo reiniciable (útil si se corta la red a mitad de un archivo grande)

robocopy "%ORIGEN%" "%DESTINO%" *.log /MIR /R:3 /W:2 /Z

echo.
echo ---------------------------------------
echo Sincronizacion terminada.
echo ---------------------------------------
timeout /t 5