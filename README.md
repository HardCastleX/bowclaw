# Orquestador de Ingeniería Inversa

Orquestador en Python que coordina Ghidra (análisis headless) y un proveedor de LLM
configurable (Gemini, DeepSeek, o un servidor local/open-source compatible con OpenAI)
para automatizar el flujo de ingeniería inversa: extracción, troceo y análisis de binarios.

## Estructura

```
main.py                  # Orquestador + factory de clientes LLM (build_llm_client)
config.json              # Configuración no sensible (incluye llm_provider)
.env                      # Secretos (GHIDRA_PATH, *_API_KEY) - no versionado
modules/
  ghidra_runner.py        # Ejecuta Ghidra en modo headless
  data_chunker.py         # Trocea y limpia la data extraída
  gemini_client.py        # Cliente async para la API nativa de Gemini
  openai_compatible_client.py  # Cliente generico (DeepSeek real, o servidores
                                # locales/open-source: Ollama, LM Studio, vLLM, etc.)
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

### Ghidra 11+ y Jython

Desde Ghidra 11, el motor **PyGhidra** (integrado) tiene prioridad sobre **Jython**
para ejecutar scripts `.py`, y `ghidra_scripts/extractor.py` está escrito para Jython
(el motor clásico, Python 2). Si corres el pipeline y ves el error
`"Ghidra was not started with PyGhidra. Python is not available"`, necesitas:

1. Instalar la extensión Jython que ya viene empaquetada con la release oficial de
   Ghidra (`Extensions/Ghidra/*_Jython.zip`), usando `scripts/install_ghidra_jython.ps1`
   (Windows) o `scripts/install_ghidra_jython.sh` (Linux/WSL) — leen `GHIDRA_PATH` de
   `.env` automáticamente.
2. Deshabilitar el módulo PyGhidra integrado para que deje de competir por los `.py`:
   renombra `Ghidra/Features/PyGhidra` a `Ghidra/Features/PyGhidra.disabled` dentro de
   tu instalación de Ghidra (reversible, solo renombra de vuelta si lo necesitas).

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

En ambos casos, completa `.env` con la API key del proveedor que vayas a usar y la
ruta de `GHIDRA_PATH` correspondiente a tu instalación.

## Elegir proveedor de LLM

`config.json` tiene un campo `llm_provider` con tres opciones ya soportadas:

```json
"llm_provider": "gemini",   // "gemini" | "deepseek" | "local"
"providers": {
    "gemini":   { "model": "gemini-3.1-flash-lite", "pro_model": "gemini-3-flash-preview" },
    "deepseek": { "base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat", "pro_model": "deepseek-reasoner" },
    "local":    { "base_url": "http://localhost:11434/v1", "model": "llama3", "pro_model": "llama3" }
}
```

- **`gemini`**: API nativa de Google AI Studio (`GEMINI_API_KEY` en `.env`).
- **`deepseek`**: API oficial real de DeepSeek, formato compatible con OpenAI
  (`DEEPSEEK_API_KEY` en `.env`).
- **`local`**: cualquier servidor open-source/auto-hospedado que exponga un endpoint
  `/chat/completions` compatible con OpenAI — Ollama, LM Studio, vLLM,
  text-generation-webui, llama.cpp server, etc. No suele requerir API key
  (`LOCAL_API_KEY` puede quedar vacío en `.env`); solo ajusta `base_url` y `model`
  al nombre del modelo que tengas cargado en tu servidor.

Para agregar otro proveedor compatible con OpenAI, solo agrega una entrada nueva en
`providers` y una rama en `build_llm_client()` (`main.py`) reutilizando
`OpenAICompatibleClient` — no hace falta escribir un cliente nuevo salvo que el
proveedor use un formato de API distinto al de OpenAI (como el caso de Gemini).

## Uso

```bash
python main.py [ruta/al/binario]
```

Si no se pasa un binario, se auto-detecta el único archivo en `workspace/input/`.

### Verbose (activado por defecto)

Por defecto se muestra en vivo:
- El output completo de Ghidra (`[ghidra] ...`) linea por linea mientras corre el analisis headless.
- El razonamiento del modelo (`[gemini-thinking] ...` o `[reasoning] ...`) cuando el
  proveedor lo expone — Gemini con `use_pro=True` (thinking), o `deepseek-reasoner`
  (campo `reasoning_content`). En ambos casos, el reporte final solo incluye la
  respuesta, nunca el razonamiento crudo.

Para silenciar esto y volver al comportamiento minimo (solo INFO de alto nivel):

```bash
python main.py --quiet [ruta/al/binario]
```

## Tests

```bash
python -m unittest discover -s tests -v
```

> Estado actual: pipeline completo implementado y **validado end-to-end con Ghidra y
> Gemini reales** (extracción, chunking, análisis y reporte), con logging, limpieza
> automática y tests (16 pasando).
>
> Nota sobre cuotas: el tier gratuito de la API de Gemini tiene límites diarios muy
> bajos por modelo (algunos en 0 o 20 requests/día dependiendo del modelo y proyecto).
> Si ves errores 429 persistentes, revisa qué modelos tienen cuota disponible en tu
> cuenta (`GET /v1beta/models` + probar `generateContent` contra candidatos) y ajusta
> `gemini_model`/`gemini_pro_model` en `config.json`, o habilita facturación en
> Google AI Studio para límites mayores.
