param([string]$KeilRoot = 'D:\12-keil5')
$ErrorActionPreference='Stop'
$toolDirectory=Join-Path $KeilRoot 'ARM\ARMCC\bin'
function Invoke-ArmTool([string]$Name,[string[]]$Arguments) {
    & (Join-Path $toolDirectory $Name) @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Name failed: $LASTEXITCODE" }
}
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path Objects,Listings | Out-Null
    $common=@('--cpu','Cortex-M0plus','--thumb','--c99','-O1','-g','--library_type=microlib','-D__SAMR21G18A__','-IApp','-I..\SAMR21_EPD_Keil\Device','-I..\SAMR21_EPD_Keil\CMSIS','-c')
    foreach($source in @('App\main.c','App\graphics.c','App\clock.c','Drivers\epd.c','Startup\system_samr21.c')) {
        $objectPath='Objects\'+[IO.Path]::GetFileNameWithoutExtension($source)+'.o'
        Invoke-ArmTool 'armcc.exe' ($common+@($source,'-o',$objectPath))
    }
    Invoke-ArmTool 'armasm.exe' @('--cpu','Cortex-M0plus','--thumb','-g','--pd','__MICROLIB SETA 1','Startup\startup_samr21.s','-o','Objects\startup_samr21.o')
    Invoke-ArmTool 'armlink.exe' @('--cpu','Cortex-M0plus','--library_type=microlib','--scatter','samr21.sct','--map','--symbols','--info','sizes','--list','Listings\epd_clock.map','Objects\main.o','Objects\graphics.o','Objects\clock.o','Objects\epd.o','Objects\system_samr21.o','Objects\startup_samr21.o','-o','Objects\epd_clock.axf')
    Invoke-ArmTool 'fromelf.exe' @('--bin','--output','Objects\epd_clock.bin','Objects\epd_clock.axf')
    Invoke-ArmTool 'fromelf.exe' @('--i32','--output','Objects\epd_clock.hex','Objects\epd_clock.axf')
    Write-Host 'Built: Objects\epd_clock.axf / .bin / .hex'
} finally { Pop-Location }
