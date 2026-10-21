param(
    [switch]$InspectOnly,
    [switch]$AllowNonOriginal
)
$ErrorActionPreference = 'Stop'
if ($InspectOnly -and $AllowNonOriginal) {
    throw 'InspectOnly and AllowNonOriginal cannot be combined.'
}
$localPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$workspacePython = Join-Path (Split-Path $PSScriptRoot -Parent) 'work\diagnostics\venv\Scripts\python.exe'
if (Test-Path -LiteralPath $localPython) {
    $flashPython = $localPython
} elseif (Test-Path -LiteralPath $workspacePython) {
    $flashPython = $workspacePython
} else {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    $pythonExecutable = Get-Command python -ErrorAction SilentlyContinue
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    $venvFolder = Join-Path $PSScriptRoot '.venv'
    if ($pythonLauncher) {
        & $pythonLauncher.Source -3 -m venv $venvFolder
    } elseif ($pythonExecutable) {
        & $pythonExecutable.Source -m venv $venvFolder
    } elseif (Test-Path -LiteralPath $bundledPython) {
        & $bundledPython -m venv $venvFolder
    } else {
        throw 'Python 3.10+ is required.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Creating the Python environment failed.' }
    $flashPython = $localPython
    & $flashPython -m pip install -r (Join-Path $PSScriptRoot 'flash_requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Installing flash dependencies failed.' }
}
$flashMode = if ($InspectOnly) { 'inspect' } else { 'restore-original' }
$runFolder = Join-Path $PSScriptRoot ('flash_runs\' + [guid]::NewGuid().ToString('N'))
$flashArguments = @(
    (Join-Path $PSScriptRoot 'samr21_swd_flash.py'), $flashMode,
    '--reset-halt', '--output', $runFolder
)
if ($AllowNonOriginal) { $flashArguments += '--allow-nonoriginal-current' }
& $flashPython @flashArguments
if ($LASTEXITCODE -ne 0) { throw "Flash operation failed. Read $runFolder\result.json" }
Write-Host "Complete. Backups and verification: $runFolder"
