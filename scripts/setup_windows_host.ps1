param(
    [string]$TargetUser = $env:USERNAME
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LogPath = Join-Path $ProjectRoot "results\host_setup.log"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $LogPath) | Out-Null

Start-Transcript -Path $LogPath -Force | Out-Null

try {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Error "Script must be run as Administrator (elevated)."
        exit 1
    }

    Write-Host "=== [1/4] Stopping legacy SQL/SSAS services & setting StartupType = Manual ==="
    $legacyServices = @(
        "MSSQL`$SQLEXPRESS1",
        "MSOLAP`$MSSQLSERVER1",
        "MSSQLLaunchpad`$SQLEXPRESS1",
        "SQLBrowser",
        "SQLTELEMETRY`$SQLEXPRESS1",
        "SQLWriter"
    )
    foreach ($svcName in $legacyServices) {
        $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
        if ($null -ne $svc) {
            if ($svc.Status -ne "Stopped") {
                Write-Host "Stopping $svcName ..."
                Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue
            }
            Set-Service -Name $svcName -StartupType Manual -ErrorAction SilentlyContinue
            $after = Get-Service -Name $svcName
            Write-Host ("  -> {0}: Status={1}, StartType={2}" -f $svcName, $after.Status, $after.StartType)
        } else {
            Write-Host "  -> $svcName not found (skipped)"
        }
    }

    Write-Host "=== [2/4] Ensuring D:\DockerData exists ==="
    New-Item -ItemType Directory -Force -Path "D:\DockerData" | Out-Null

    Write-Host "=== [3/4] Installing Docker Desktop (WSL2 backend, data root D:\DockerData) ==="
    winget install --id Docker.DockerDesktop --exact --accept-source-agreements --accept-package-agreements --override "install --accept-license --backend=wsl-2 --wsl-default-data-root=D:\DockerData"
    $dockerExit = $LASTEXITCODE
    Write-Host "Docker Desktop winget exit code: $dockerExit"

    if ($TargetUser) {
        $grp = Get-LocalGroup -Name "docker-users" -ErrorAction SilentlyContinue
        if ($null -ne $grp) {
            Add-LocalGroupMember -Group "docker-users" -Member $TargetUser -ErrorAction SilentlyContinue
            Write-Host "Ensured '$TargetUser' is in 'docker-users' group."
        }
    }

    Write-Host "=== [4/4] Installing DBeaver Community ==="
    winget install --id DBeaver.DBeaver.Community --exact --accept-source-agreements --accept-package-agreements
    $dbeaverExit = $LASTEXITCODE
    Write-Host "DBeaver winget exit code: $dbeaverExit"

    Write-Host "=== Host setup script finished ==="
    exit 0
}
finally {
    Stop-Transcript | Out-Null
}
