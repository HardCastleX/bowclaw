# PLAN.md — Orquestador de Ingeniería Inversa (bowclaw)

Orquestador en Python que automatiza el flujo de ingeniería inversa:
extrae información de un binario con **Ghidra** (headless), la trocea, la analiza
con la API de **DeepSeek** y genera un reporte legible.

---

## 1. Objetivo

Dado un binario de entrada, producir automáticamente un reporte de análisis
(funciones, código decompilado, hallazgos) sin intervención manual en Ghidra.

Pipeline principal:

```
binario → Ghidra (extractor Jython) → data cruda → chunking → DeepSeek → reporte
```

---

## 2. Estado actual

| Componente | Estado |
|---|---|
| Estructura de carpetas | ✅ Hecho |
| Firmas de clases/funciones (`pass`) | ✅ Hecho |
| Separación de secretos (`.env` / `config.json`) | ✅ Hecho |
| Repo GitHub + deploy key + rama `main` + Apache 2.0 | ✅ Hecho |
| Lógica de los módulos | ⏳ Pendiente |

---

## 3. Arquitectura

```
main.py                     # ReverseEngineeringOrchestrator (pegamento)
config.json                 # Config no sensible (chunk size, rutas workspace)
.env                        # Secretos: GHIDRA_PATH, DEEPSEEK_API_KEY
modules/
  ghidra_runner.py          # Invoca analyzeHeadless vía subprocess
  data_chunker.py           # Limpia y trocea la data extraída (json, re)
  deepseek_client.py        # Cliente async de la API (asyncio, requests)
ghidra_scripts/
  extractor.py              # Script Jython ejecutado DENTRO de Ghidra
workspace/
  input/                    # Binarios de entrada
  temp_projects/            # Proyectos temporales de Ghidra (efímeros)
  reports/                  # Reportes generados
```

---

## 4. Fases de implementación

### Fase 1 — Extracción (Ghidra)
- [ ] `ghidra_scripts/extractor.py`: lógica Jython real
  - Iterar funciones (`currentProgram.getFunctionManager()`)
  - Obtener código decompilado (`DecompInterface`)
  - Volcar resultado a JSON en `workspace/temp_projects/` o `reports/`
- [ ] `modules/ghidra_runner.py`:
  - Construir comando `analyzeHeadless <proj_dir> <proj_name> -import <bin> -postScript extractor.py`
  - Ejecutar con `subprocess`, capturar stdout/stderr, timeout
  - Manejar códigos de error de Ghidra

### Fase 2 — Preparación de datos
- [ ] `modules/data_chunker.py`:
  - `load_raw_data()`: leer el JSON de salida de Ghidra
  - `clean_text()`: normalizar/limpiar ruido (regex)
  - `split_into_chunks()`: trocear respetando `max_chunk_size` (límite de tokens)

### Fase 3 — Análisis (DeepSeek)
- [ ] `modules/deepseek_client.py`:
  - `_build_headers()`: auth con `DEEPSEEK_API_KEY`
  - `analyze_chunk()`: request async individual
  - `analyze_all_chunks()`: concurrencia con `asyncio` + control de rate limit y reintentos
  - Nota: `requests` es síncrono → evaluar `aiohttp` para async real

### Fase 4 — Orquestación y reporte
- [ ] `main.py` (`ReverseEngineeringOrchestrator`):
  - `run(binary_path)`: encadenar Ghidra → chunk → DeepSeek → reporte
  - `generate_report()`: consolidar resultados en `workspace/reports/`
  - Entrada del binario (CLI arg vs auto-detección en `workspace/input/`)

### Fase 5 — Robustez (DevSecOps)
- [x] Logging estructurado (`utils/logger.py`) — archivo + consola
- [x] Limpieza automática de `workspace/temp_projects/` (`GhidraRunner.cleanup_project`, en `finally`)
- [x] Manejo de errores/reintentos en todo el pipeline (Ghidra: timeout/exit code; DeepSeek: backoff exponencial)
- [x] Validación de que `.env` nunca se versione (ya en `.gitignore`)
- [x] `requirements.txt` completo (incluye `aiohttp`)
- [x] Tests unitarios básicos por módulo (`tests/`, 12 tests, `py -m unittest discover -s tests`)

---

## 5. Decisiones pendientes

| Decisión | Opciones |
|---|---|
| Formato del reporte | Markdown / JSON / HTML |
| Entrada del binario | CLI arg / auto-detección en `input/` |
| Procesamiento | Un binario a la vez / batch |
| Cliente HTTP async | Mantener `requests` / migrar a `aiohttp` |

---

## 6. Consideraciones de seguridad

- Los binarios analizados son **no confiables** → Ghidra headless los procesa,
  pero cualquier manipulación posterior debe tratarse como input hostil.
- Secretos solo en `.env` (nunca en `config.json` ni en commits).
- Los reportes pueden contener strings/código sensible del binario → no subir
  `workspace/reports/` al repo (ya ignorado).
