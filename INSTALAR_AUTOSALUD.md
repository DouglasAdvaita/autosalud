# Instalar Autosalud desde Git

## Links

- Repositorio público: https://github.com/DouglasAdvaita/autosalud
- Descarga ZIP de la rama principal: https://github.com/DouglasAdvaita/autosalud/archive/refs/heads/main.zip
- Releases: https://github.com/DouglasAdvaita/autosalud/releases
- Python para Windows: https://www.python.org/downloads/windows/
- Paquete del chat: https://pypi.org/project/notebooklm-py/

## Descargar y descomprimir

Descargar el ZIP y descomprimirlo. Queda una carpeta `autosalud-main`, con esta estructura:

```
autosalud-main\
  app\            (la app: cuerpo 3D, diccionario, libros)
  datos\          (datos fuente y PDF)
  herramientas\   (scripts que regeneran los datos)
  cuaderno.json   (cuaderno de NotebookLM que usa el chat)
  servidor.py     (servidor local del chat)
  INICIAR.cmd
  INICIAR_OFFLINE.cmd
  INSTALAR_CONSULTA_IA.cmd
```

Si Windows marca los archivos como bloqueados, desbloquearlos: clic derecho sobre el ZIP antes de extraer, Propiedades, Desbloquear; o después, en PowerShell dentro de la carpeta:

```powershell
Get-ChildItem -Recurse | Unblock-File
```

## Usar sin chat

```powershell
INICIAR_OFFLINE.cmd
```

Abre la app con el cuerpo 3D y el diccionario, sin servidor ni NotebookLM. No necesita instalar nada.

## Instalar el chat (un solo archivo)

```powershell
INSTALAR_CONSULTA_IA.cmd
```

Hace todo solo:

1. Busca Python 3.10 o superior. Si no está, abre la página de descarga: instalarlo marcando "Add python.exe to PATH" y volver a ejecutar el instalador.
2. Instala o actualiza el cliente de NotebookLM (`notebooklm-py[browser]`).
3. Abre el navegador para iniciar sesión con la cuenta de Google y verifica que la sesión quede activa.

Para actualizar el cliente más adelante:

```powershell
INSTALAR_CONSULTA_IA.cmd actualizar
```

## Usar con chat

```powershell
INICIAR.cmd
```

Abre el servidor local en `http://127.0.0.1:8767/` y el navegador. Cerrar la ventana negra lo detiene.

Si el puerto está ocupado: `python servidor.py --puerto 8768`.

## Cuaderno de NotebookLM

El chat responde con el cuaderno **"Salud - enfermedad y creencias"**, que está compartido como público. Su identificador y los nombres de las fuentes están en `cuaderno.json`.

Si el chat devuelve un error de acceso, abrir el cuaderno una vez en el navegador con la misma cuenta de Google y reintentar. Si el error dice que la sesión venció:

```powershell
python -m notebooklm login --browser chrome
```

## Verificar

```powershell
python --version
python -m notebooklm auth check
```
