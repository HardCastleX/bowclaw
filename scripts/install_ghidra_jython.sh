#!/usr/bin/env bash
# Extrae la extension Jython que ya viene empaquetada con las releases oficiales
# de Ghidra (github.com/NationalSecurityAgency/ghidra), necesaria para que
# Ghidra 11+ pueda ejecutar ghidra_scripts/extractor.py (Jython).
#
# Uso: bash scripts/install_ghidra_jython.sh [ruta_a_analyzeHeadless]
# Si no se pasa argumento, se lee GHIDRA_PATH desde .env en la raiz del repo.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

GHIDRA_PATH="${1:-}"
if [ -z "$GHIDRA_PATH" ]; then
    ENV_FILE="$REPO_ROOT/.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo "No se encontro .env en $ENV_FILE y no se paso una ruta como argumento" >&2
        exit 1
    fi
    GHIDRA_PATH="$(grep -E '^GHIDRA_PATH=' "$ENV_FILE" | head -n1 | cut -d'=' -f2-)"
fi

if [ -z "$GHIDRA_PATH" ] || [ ! -e "$GHIDRA_PATH" ]; then
    echo "GHIDRA_PATH no valido o no existe: $GHIDRA_PATH" >&2
    exit 1
fi

# GHIDRA_PATH apunta a .../support/analyzeHeadless -> la raiz de instalacion
# esta dos niveles arriba.
GHIDRA_INSTALL_DIR="$(dirname "$(dirname "$GHIDRA_PATH")")"
echo "Instalacion de Ghidra detectada en: $GHIDRA_INSTALL_DIR"

EXTENSIONS_DEST_DIR="$GHIDRA_INSTALL_DIR/Ghidra/Extensions"
JYTHON_DEST_DIR="$EXTENSIONS_DEST_DIR/Jython"

if [ -d "$JYTHON_DEST_DIR/lib" ]; then
    echo "La extension Jython ya esta instalada en $JYTHON_DEST_DIR. Nada que hacer."
    exit 0
fi

ZIP_CANDIDATE="$(find "$GHIDRA_INSTALL_DIR/Extensions/Ghidra" -maxdepth 1 -iname "*_Jython.zip" 2>/dev/null | head -n1)"
if [ -z "$ZIP_CANDIDATE" ]; then
    echo "No se encontro el zip de la extension Jython en $GHIDRA_INSTALL_DIR/Extensions/Ghidra." >&2
    echo "Verifica que descargaste Ghidra desde una release oficial (github.com/NationalSecurityAgency/ghidra)." >&2
    exit 1
fi

echo "Extrayendo $(basename "$ZIP_CANDIDATE") a $EXTENSIONS_DEST_DIR ..."
mkdir -p "$EXTENSIONS_DEST_DIR"
unzip -oq "$ZIP_CANDIDATE" -d "$EXTENSIONS_DEST_DIR"

echo "Extension Jython instalada correctamente en $JYTHON_DEST_DIR"
