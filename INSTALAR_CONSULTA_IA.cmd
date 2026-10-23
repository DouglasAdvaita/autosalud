@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Autosalud - instalar consulta con IA

set "ID_CUADERNO=582dd138-4238-461e-9e1f-262665967ac8"
set "ACTUALIZAR="
if /i "%~1"=="actualizar" set "ACTUALIZAR=1"

echo ============================================================
echo  Autosalud - instalacion de la consulta con IA
echo ============================================================
echo.
echo Este instalador configura el chat (NotebookLM) que usa la app.
echo La app tambien funciona sin chat con INICIAR_OFFLINE.cmd.
echo.

rem ---------- 1. Buscar Python 3.10 o superior ----------
set "PY="
python --version >nul 2>&1
if not errorlevel 1 set "PY=python"
if not defined PY (
    py -3 --version >nul 2>&1
    if not errorlevel 1 set "PY=py -3"
)

if defined PY (
    %PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Se encontro Python, pero es anterior a la version 3.10.
        set "PY="
    )
)

if not defined PY (
    echo [FALTA PYTHON]
    echo.
    echo Instale Python 3.10 o superior desde:
    echo   https://www.python.org/downloads/
    echo.
    echo En el instalador marque la casilla "Add python.exe to PATH"
    echo y despues vuelva a ejecutar este archivo.
    echo.
    start "" "https://www.python.org/downloads/"
    pause
    exit /b 1
)

for /f "delims=" %%v in ('%PY% --version 2^>^&1') do set "VER=%%v"
echo [1/3] Python: !VER!

rem ---------- 2. Instalar el cliente de NotebookLM ----------
%PY% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo       Preparando pip...
    %PY% -m ensurepip --upgrade >nul 2>&1
)

set "INSTALADO="
%PY% -c "import notebooklm, playwright" >nul 2>&1
if not errorlevel 1 set "INSTALADO=1"

if defined ACTUALIZAR set "INSTALADO="

if defined INSTALADO (
    echo [2/3] Cliente de NotebookLM: ya instalado
) else (
    echo [2/3] Instalando cliente de NotebookLM (descarga desde internet)...
    %PY% -m pip install --upgrade "notebooklm-py[browser]"
    if errorlevel 1 (
        echo.
        echo [ERROR] No se pudo instalar el cliente.
        echo Revise la conexion a internet y vuelva a ejecutar este archivo.
        pause
        exit /b 1
    )
)

rem ---------- 3. Iniciar sesion en NotebookLM ----------
%PY% -m notebooklm auth check --test --passive >nul 2>&1
if not errorlevel 1 goto listo

echo [3/3] Iniciando sesion en NotebookLM...
echo       Se abrira una ventana del navegador.
echo       Elija su cuenta de Google, complete el ingreso y espere.
echo.
%PY% -m notebooklm login --browser chrome
if not errorlevel 1 goto verificar

echo.
echo       Chrome no respondio. Probando con Microsoft Edge...
%PY% -m notebooklm login --browser msedge
if not errorlevel 1 goto verificar

echo.
echo [ERROR] No se pudo iniciar sesion automaticamente.
echo Abra el navegador y ejecute a mano:
echo   %PY% -m notebooklm login --browser chrome
echo Luego vuelva a ejecutar este instalador.
pause
exit /b 1

:verificar
%PY% -m notebooklm auth check --test --passive >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] La sesion no quedo verificada.
    echo Vuelva a ejecutar este instalador o inicie sesion a mano.
    pause
    exit /b 1
)

:listo
echo.
echo ============================================================
echo  Listo. La consulta con IA quedo configurada.
echo ============================================================
echo.
echo   INICIAR.cmd           abre la app con chat en http://127.0.0.1:8767/
echo   INICIAR_OFFLINE.cmd   abre la app sin chat
echo.
echo El chat consulta el cuaderno %ID_CUADERNO% (publico).
echo Si el chat da error, abra ese cuaderno una vez en el navegador con la
echo misma cuenta de Google y vuelva a intentar.
echo.
echo Para actualizar el cliente mas adelante:
echo   INSTALAR_CONSULTA_IA.cmd actualizar
echo.
pause
exit /b 0
