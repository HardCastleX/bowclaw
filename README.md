# Orquestador de Ingeniería Inversa

Orquestador en Python que coordina Ghidra (análisis headless) y la API de Gemini
(Google AI Studio) para automatizar el flujo de ingeniería inversa: extracción, troceo y análisis de binarios.

## Estructura

```
main.py                  # Orquestador principal
config.json              # Configuración no sensible
.env                      # Secretos (GHIDRA_PATH, GEMINI_API_KEY) - no versionado
modules/
  ghidra_runner.py        # Ejecuta Ghidra en modo headless
  data_chunker.py         # Trocea y limpia la data extraída
  gemini_client.py        # Cliente async para la API de Gemini
ghidra_scripts/
  extractor.py            # Script Jython ejecutado dentro de Ghidra
workspace/
  input/                  # Binarios de entrada
  temp_projects/          # Proyectos temporales de Ghidra
  reports/                # Reportes generados
```

## Prerrequisitos

- **Ghidra 11 o superior** instalado (no viene incluido en este repo).
- **Java (JDK) 21 o superior** — requisito de Ghidra 11/12. Si no lo tienes, usa el
  script de instalación automática incluido en `scripts/` (ver más abajo).
- Python 3.10+.

`GHIDRA_PATH` en `.env` debe apuntar al **script `analyzeHeadless` dentro de
`support/`**, no a la carpeta raíz de la instalación de Ghidra:

- Windows: `C:\ruta\a\ghidra_12.x\support\analyzeHeadless.bat`
- Linux/WSL: `/ruta/a/ghidra_12.x/support/analyzeHeadless`

## Setup

Compatible con Windows y Linux (incluyendo WSL). El código no depende de rutas ni
comandos específicos de un SO; solo cambia cómo activas el entorno virtual y qué
binario de Ghidra apuntas en `GHIDRA_PATH`.

### Windows

```powershell
# Opcional: instala Java 21 automaticamente si no lo tienes (no hace nada si ya cumples el requisito)
.\scripts\install_java.ps1

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`GHIDRA_PATH` debe apuntar a `analyzeHeadless.bat` (ej. `C:\ghidra\support\analyzeHeadless.bat`).

### Linux / WSL

```bash
# Opcional: instala Java 21 automaticamente si no lo tienes (no hace nada si ya cumples el requisito)
bash scripts/install_java.sh
source ~/.bashrc   # o abre una nueva terminal, para que JAVA_HOME/PATH tomen efecto

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`GHIDRA_PATH` debe apuntar al script sin extensión (ej. `/opt/ghidra_11.0/support/analyzeHeadless`).

En ambos casos, completa `.env` con tu `GEMINI_API_KEY` real y la ruta de `GHIDRA_PATH`
correspondiente a tu instalación.

## Uso

```bash
python main.py [ruta/al/binario]
```

Si no se pasa un binario, se auto-detecta el único archivo en `workspace/input/`.

## Tests

```bash
python -m unittest discover -s tests -v
```

> Estado actual: pipeline completo implementado (Ghidra → chunking → Gemini → reporte),
> con logging, limpieza automática y tests (16 pasando). Pendiente: probar con Ghidra real.
