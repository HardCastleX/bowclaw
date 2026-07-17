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

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # completar con tus valores reales
```

## Uso

```bash
python main.py
```

> Estado actual: arquitectura base, lógica pendiente de implementación.
