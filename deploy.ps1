#requires -version 5
<#
.SYNOPSIS
  Pousse le code puis deploie back et/ou front sur l'Optiplex.

.DESCRIPTION
  git push (sauf -NoPush) -> ssh sur l'Optiplex -> git pull --ff-only -> bash
  deploy.sh <cible>. Le vrai travail est dans deploy.sh (versionne).

.EXAMPLE
  .\deploy.ps1            # back + front
.EXAMPLE
  .\deploy.ps1 back
.EXAMPLE
  .\deploy.ps1 front -NoPush
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('all', 'back', 'front')]
    [string]$Target = 'all',

    [string]$ServerHost = 'kamicron_admin@192.168.1.51',
    [switch]$NoPush
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not $NoPush) {
    Write-Host "== git push ==" -ForegroundColor Cyan
    & git push
    if ($LASTEXITCODE -ne 0) { Write-Host "git push a echoue" -ForegroundColor Red; exit 1 }
}

Write-Host "== Deploiement '$Target' sur $ServerHost ==" -ForegroundColor Cyan
& ssh -t $ServerHost "cd /opt/apisketch && git pull --ff-only && bash deploy.sh $Target"
$rc = $LASTEXITCODE

Write-Host ""
if ($rc -eq 0) { Write-Host "Deploiement OK." -ForegroundColor Green }
else { Write-Host "Deploiement KO (code $rc)." -ForegroundColor Red }
exit $rc
