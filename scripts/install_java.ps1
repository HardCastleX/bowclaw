<#
Instala Eclipse Temurin JDK 21 (requerido por Ghidra 11/12) si no esta ya presente.
Uso: .\scripts\install_java.ps1 [-InstallDir C:\Java]
#>
param(
    [string]$InstallDir = "C:\Java"
)

$ErrorActionPreference = "Stop"

function Get-JavaMajorVersion {
    # java -version escribe a stderr; con $ErrorActionPreference = "Stop" capturar
    # stderr de un ejecutable nativo via 2>&1 se convierte en un error terminante,
    # asi que lo bajamos temporalmente solo para esta llamada.
    $previousPref = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $verOutput = (& java -version) 2>&1 | Out-String
    } catch {
        return $null
    } finally {
        $ErrorActionPreference = $previousPref
    }
    if ($verOutput -match '"(\d+)(\.\d+)?') {
        return [int]$Matches[1]
    }
    return $null
}

$existingMajor = Get-JavaMajorVersion
if ($existingMajor -ge 21) {
    Write-Output "Java $existingMajor ya esta instalado y cumple el requisito (>= 21). Nada que hacer."
    & java -version
    exit 0
}

Write-Output "Descargando Eclipse Temurin JDK 21 (Windows x64)..."
$zipPath = Join-Path $env:TEMP "temurin21.zip"
$url = "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jdk/hotspot/normal/eclipse?project=jdk"
Invoke-WebRequest -Uri $url -OutFile $zipPath -UseBasicParsing

Write-Output "Extrayendo a $InstallDir ..."
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

$jdkHome = (Get-ChildItem $InstallDir -Directory | Where-Object { $_.Name -like "jdk-21*" } | Select-Object -First 1).FullName
if (-not $jdkHome) {
    throw "No se encontro el directorio del JDK extraido en $InstallDir"
}

Write-Output "Configurando JAVA_HOME y PATH (usuario) -> $jdkHome"
[System.Environment]::SetEnvironmentVariable("JAVA_HOME", $jdkHome, "User")

$userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$jdkHome\bin*") {
    $newPath = "$jdkHome\bin;$userPath"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
}

# Refrescar la sesion actual para poder verificar de inmediato
$env:JAVA_HOME = $jdkHome
$env:Path = "$jdkHome\bin;$env:Path"

Write-Output "Instalacion completada. Abre una nueva terminal para que los cambios de PATH tomen efecto."
& "$jdkHome\bin\java.exe" -version
