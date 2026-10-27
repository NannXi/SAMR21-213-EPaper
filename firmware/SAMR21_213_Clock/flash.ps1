param(
    [ValidateSet('flash','status','step','full','test6','set-time')]
    [string]$Action='flash',
    [string]$Time,
    [string]$PythonExe
)
$ErrorActionPreference='Stop'
$localPython=Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if($PythonExe) { $flashPython=(Resolve-Path -LiteralPath $PythonExe).Path }
elseif(Test-Path -LiteralPath $localPython) { $flashPython=$localPython }
else { throw 'Create .venv and install Tools\requirements.txt, or specify -PythonExe.' }
$toolArguments=@((Join-Path $PSScriptRoot 'Tools\flash_app.py'),$Action)
if($Action -eq 'set-time') { $toolArguments+=@('--time',$Time) }
& $flashPython @toolArguments
if($LASTEXITCODE -ne 0) { throw "Operation failed: $Action. Read Runs\*\result.json." }
