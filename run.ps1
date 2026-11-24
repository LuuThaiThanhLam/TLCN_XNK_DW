param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "status", "logs", "trigger-all", "dbt-run", "dbt-test", "dbt-docs", "benchmark", "verify-offline", "help")]
    [string]$Command = "help",

    [Parameter(Position = 1)]
    [string]$Arg = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$dockerBin = "C:\Program Files\Docker\Docker\resources\bin"
if ((Test-Path $dockerBin) -and ($env:Path -notlike "*$dockerBin*")) {
    $env:Path = "$dockerBin;$env:Path"
}

function Invoke-Compose {
    param([string[]]$ComposeArgs)
    & docker compose @ComposeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose $($ComposeArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Wait-DagRun {
    param(
        [string]$DagId,
        [int]$TimeoutSeconds = 600
    )
    Write-Host "[Airflow] Unpausing & triggering $DagId ..." -ForegroundColor Cyan
    & docker compose exec -T airflow-scheduler airflow dags unpause $DagId | Out-Null
    $triggerOut = & docker compose exec -T airflow-scheduler airflow dags trigger $DagId 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to trigger ${DagId}: $triggerOut"
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $rawJson = & docker compose exec -T airflow-scheduler airflow dags list-runs -d $DagId -o json 2>$null
        if ($rawJson) {
            try {
                $runs = $rawJson | ConvertFrom-Json
                if ($runs.Count -gt 0) {
                    $latest = $runs | Sort-Object -Property execution_date -Descending | Select-Object -First 1
                    $state = $latest.state
                    Write-Host "  -> $DagId run_id=$($latest.run_id) state=$state"
                    if ($state -eq "success") {
                        return $latest
                    }
                    if ($state -eq "failed") {
                        throw "DAG $DagId failed (run_id=$($latest.run_id)). Check Airflow UI at http://localhost:8080"
                    }
                }
            } catch {
                if ($_.Exception.Message -like "DAG * failed*") { throw }
            }
        }
    }
    throw "Timed out waiting for $DagId after ${TimeoutSeconds}s"
}

switch ($Command) {
    "up" {
        if (-not (Test-Path ".env")) {
            Copy-Item ".env.example" ".env"
            Write-Host "[INFO] Created .env from .env.example"
        }
        New-Item -ItemType Directory -Force -Path "airflow\logs", "data\runtime_staging", "results" | Out-Null
        Invoke-Compose @("up", "-d", "--build")
        Invoke-Compose @("ps")
    }
    "down" {
        Invoke-Compose @("down")
    }
    "status" {
        Invoke-Compose @("ps")
    }
    "logs" {
        if ($Arg) {
            Invoke-Compose @("logs", "-f", "--tail=100", $Arg)
        } else {
            Invoke-Compose @("logs", "-f", "--tail=100")
        }
    }
    "trigger-all" {
        Wait-DagRun -DagId "dag_01_ingest_raw_to_minio" -TimeoutSeconds 300
        Wait-DagRun -DagId "dag_02_dwh_elt_pipeline" -TimeoutSeconds 900
        Wait-DagRun -DagId "dag_03_benchmark_and_audit" -TimeoutSeconds 300
        Write-Host "[PASS] All 3 Airflow DAGs completed successfully!" -ForegroundColor Green
    }
    "dbt-run" {
        Invoke-Compose @("exec", "-T", "airflow-scheduler", "bash", "-lc", "cd /opt/airflow/dbt_project && dbt seed --profiles-dir . && dbt run --profiles-dir . --select staging && dbt snapshot --profiles-dir . && dbt run --profiles-dir . --select intermediate core_dwh marts")
    }
    "dbt-test" {
        Invoke-Compose @("exec", "-T", "airflow-scheduler", "bash", "-lc", "cd /opt/airflow/dbt_project && dbt test --profiles-dir .")
    }
    "dbt-docs" {
        Write-Host "Starting dbt Docs server at http://localhost:8081 (Ctrl+C to stop)..." -ForegroundColor Cyan
        Invoke-Compose @("run", "--rm", "-p", "8081:8081", "--no-deps", "airflow-scheduler", "bash", "-lc", "cd /opt/airflow/dbt_project && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir . --host 0.0.0.0 --port 8081")
    }
    "benchmark" {
        Invoke-Compose @("exec", "-T", "airflow-scheduler", "python", "/opt/airflow/scripts/benchmark_architecture.py")
    }
    "verify-offline" {
        & python (Join-Path $ProjectRoot "scripts\verify_offline.py")
        exit $LASTEXITCODE
    }
    default {
        Write-Host "Usage: .\run.ps1 <command> [arg]"
        Write-Host "Commands: up | down | status | logs [svc] | trigger-all | dbt-run | dbt-test | dbt-docs | benchmark | verify-offline"
    }
}
