<#
Extrae la extension Jython que ya viene empaquetada con las releases oficiales
de Ghidra (github.com/NationalSecurityAgency/ghidra), necesaria para que
Ghidra 11+ pueda ejecutar ghidra_scripts/extractor.py (Jython).

Uso: .\scripts\install_ghidra_jython.ps1 [-GhidraPath <ruta a analyzeHeadless.bat>]
Si no se pasa -GhidraPath, se lee GHIDRA_PATH desde .env en la raiz del repo.
#>
param(
    [string]$GhidraPath
)

$ErrorActionPreference = "Stop"

function Get-GhidraPathFromEnvFile {
    $envFile = Join-Path (Split-Path -Parent $PSScriptRoot) ".env"
    if (-not (Test-Path $envFile)) {
        throw "No se encontro .env en $envFile y no se paso -GhidraPath"
    }
    $line = Get-Content $envFile | Where-Object { $_ -match '^GHIDRA_PATH=' } | Select-Object -First 1
    if (-not $line) {
        throw "No se encontro GHIDRA_PATH en $envFile"
    }
    return ($line -split '=', 2)[1].Trim()
}

if (-not $GhidraPath) {
    $GhidraPath = Get-GhidraPathFromEnvFile
}

if (-not (Test-Path $GhidraPath)) {
    throw "GHIDRA_PATH no existe: $GhidraPath"
}

# GhidraPath apunta a .../support/analyzeHeadless.bat -> la raiz de instalacion
# esta dos niveles arriba.
$ghidraInstallDir = Split-Path -Parent (Split-Path -Parent $GhidraPath)
Write-Output "Instalacion de Ghidra detectada en: $ghidraInstallDir"

$extensionsDestDir = Join-Path $ghidraInstallDir "Ghidra\Extensions"
$jythonDestDir = Join-Path $extensionsDestDir "Jython"

if (Test-Path (Join-Path $jythonDestDir "lib")) {
    Write-Output "La extension Jython ya esta instalada en $jythonDestDir. Nada que hacer."
    exit 0
}

$zipCandidate = Get-ChildItem -Path (Join-Path $ghidraInstallDir "Extensions\Ghidra") -Filter "*_Jython.zip" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $zipCandidate) {
    throw "No se encontro el zip de la extension Jython en $ghidraInstallDir\Extensions\Ghidra. Verifica que descargaste Ghidra desde una release oficial (github.com/NationalSecurityAgency/ghidra)."
}

Write-Output "Extrayendo $($zipCandidate.Name) a $extensionsDestDir ..."
New-Item -ItemType Directory -Force -Path $extensionsDestDir | Out-Null
Expand-Archive -Path $zipCandidate.FullName -DestinationPath $extensionsDestDir -Force

Write-Output "Extension Jython instalada correctamente en $jythonDestDir"
