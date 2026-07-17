#!/usr/bin/env bash
# Instala Eclipse Temurin JDK 21 (requerido por Ghidra 11/12) si no esta ya presente.
# Uso: bash scripts/install_java.sh [install_dir]
set -euo pipefail

INSTALL_DIR="${1:-$HOME/.local/java}"

get_java_major_version() {
    if ! command -v java >/dev/null 2>&1; then
        echo ""
        return
    fi
    java -version 2>&1 | head -n1 | grep -oE '"[0-9]+' | tr -d '"' || true
}

existing_major="$(get_java_major_version)"
if [ -n "$existing_major" ] && [ "$existing_major" -ge 21 ] 2>/dev/null; then
    echo "Java $existing_major ya esta instalado y cumple el requisito (>= 21). Nada que hacer."
    java -version
    exit 0
fi

echo "Descargando Eclipse Temurin JDK 21 (Linux x64)..."
TMP_TAR="$(mktemp -t temurin21-XXXXXX.tar.gz)"
URL="https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse?project=jdk"
curl -fsSL "$URL" -o "$TMP_TAR"

echo "Extrayendo a $INSTALL_DIR ..."
mkdir -p "$INSTALL_DIR"
tar -xzf "$TMP_TAR" -C "$INSTALL_DIR"
rm -f "$TMP_TAR"

JDK_HOME="$(find "$INSTALL_DIR" -maxdepth 1 -type d -name 'jdk-21*' | head -n1)"
if [ -z "$JDK_HOME" ]; then
    echo "No se encontro el directorio del JDK extraido en $INSTALL_DIR" >&2
    exit 1
fi

RC_FILE="$HOME/.bashrc"
EXPORT_HOME="export JAVA_HOME=\"$JDK_HOME\""
EXPORT_PATH="export PATH=\"\$JAVA_HOME/bin:\$PATH\""

if ! grep -qF "$EXPORT_HOME" "$RC_FILE" 2>/dev/null; then
    {
        echo ""
        echo "# Agregado por scripts/install_java.sh"
        echo "$EXPORT_HOME"
        echo "$EXPORT_PATH"
    } >> "$RC_FILE"
    echo "Se agregaron JAVA_HOME/PATH a $RC_FILE"
else
    echo "$RC_FILE ya contiene la configuracion de JAVA_HOME, no se duplico."
fi

export JAVA_HOME="$JDK_HOME"
export PATH="$JAVA_HOME/bin:$PATH"

echo "Instalacion completada. Corre 'source ~/.bashrc' (o abre una nueva terminal) para que los cambios tomen efecto."
java -version
