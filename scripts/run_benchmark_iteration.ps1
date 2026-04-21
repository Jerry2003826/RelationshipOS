param(
    [string]$RunName = "full500",
    [string]$RunStamp = "",
    [int]$Port = 8023,
    [int]$Turns = 500,
    [int]$MinCharacters = 50000,
    [int]$TimeoutSeconds = 120,
    [int]$SuiteTimeoutSeconds = 10800,
    [string]$Suite = "companion_stress_zh",
    [string]$Languages = "zh",
    [int]$MaxCasesPerSuite = 1,
    [string]$EnvFile = ".env",
    [string]$OutputRoot = "benchmark_results"
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path ".").Path
$timestamp = if ($RunStamp) { $RunStamp } else { Get-Date -Format "yyyyMMdd_HHmmss" }
$outputDir = Join-Path $root (Join-Path $OutputRoot "${RunName}_$timestamp")
$statusFile = Join-Path $outputDir "run_status.json"
$serverStdout = Join-Path $outputDir "server.stdout.log"
$serverStderr = Join-Path $outputDir "server.stderr.log"
$benchmarkStdout = Join-Path $outputDir "benchmark.stdout.log"
$benchmarkStderr = Join-Path $outputDir "benchmark.stderr.log"
$baseUrl = "http://127.0.0.1:$Port"
$server = $null
$benchmark = $null
$uvCacheDir = Join-Path $root ".uv-cache"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
New-Item -ItemType Directory -Force -Path $uvCacheDir | Out-Null

function Write-Status {
    param(
        [string]$Phase,
        [string]$Message,
        [hashtable]$Extra = @{}
    )

    $payload = [ordered]@{
        timestamp = (Get-Date).ToString("o")
        phase = $Phase
        message = $Message
        output_dir = $outputDir
        port = $Port
        turns = $Turns
        min_characters = $MinCharacters
        suite = $Suite
        languages = $Languages
    }

    foreach ($entry in $Extra.GetEnumerator()) {
        $payload[$entry.Key] = $entry.Value
    }

    $payload | ConvertTo-Json -Depth 8 | Set-Content -Path $statusFile -Encoding UTF8
}

function Load-EnvFile {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Env file not found: $Path"
    }

    foreach ($rawLine in Get-Content $Path) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            continue
        }

        $idx = $line.IndexOf("=")
        if ($idx -lt 1) {
            continue
        }

        $name = $line.Substring(0, $idx)
        $value = $line.Substring($idx + 1)
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Start-LoggedProcess {
    param(
        [string]$Command,
        [string]$StdoutPath,
        [string]$StderrPath
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "cmd.exe"
    $psi.Arguments = "/d /c ""$Command 1>> ""$StdoutPath"" 2>> ""$StderrPath"""""
    $psi.WorkingDirectory = $root
    $psi.UseShellExecute = $false
    return [System.Diagnostics.Process]::Start($psi)
}

function Get-ChildProcessIds {
    param([int]$ParentId)

    $children = @(
        Get-CimInstance Win32_Process -Filter "ParentProcessId = $ParentId" -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty ProcessId
    )
    $all = @()
    foreach ($childId in $children) {
        $all += $childId
        $all += Get-ChildProcessIds -ParentId $childId
    }
    return $all
}

function Stop-ProcessTree {
    param([int]$RootProcessId)

    if (-not $RootProcessId) {
        return
    }

    $processIds = @($RootProcessId) + @(Get-ChildProcessIds -ParentId $RootProcessId)
    $orderedIds = $processIds | Sort-Object -Descending -Unique
    foreach ($processId in $orderedIds) {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

function Stop-ListeningPortProcesses {
    param([int]$LocalPort)

    if (-not $LocalPort) {
        return
    }

    $owners = @(
        Get-NetTCPConnection -LocalPort $LocalPort -State Listen -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    )
    foreach ($ownerId in $owners) {
        Stop-ProcessTree -RootProcessId $ownerId
    }
}

Write-Status -Phase "initializing" -Message "Preparing benchmark run."

try {
    Load-EnvFile -Path (Join-Path $root $EnvFile)

    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        $owners = ($listener | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique) -join ", "
        throw "Port $Port is already in use by process id(s): $owners"
    }

    $env:MEM0_DIR = Join-Path $outputDir ".mem0"
    $env:RELATIONSHIP_OS_PORT = "$Port"
    $env:BENCHMARK_STRESS_TURNS = "$Turns"
    $env:BENCHMARK_STRESS_MIN_CHARACTERS = "$MinCharacters"
    $env:BENCHMARK_INTER_TURN_IDLE_SECONDS = "0"
    $env:UV_CACHE_DIR = $uvCacheDir

    Write-Status -Phase "starting_server" -Message "Starting uvicorn." -Extra @{
        mem0_dir = $env:MEM0_DIR
        uv_cache_dir = $env:UV_CACHE_DIR
        server_stdout = $serverStdout
        server_stderr = $serverStderr
        benchmark_stdout = $benchmarkStdout
        benchmark_stderr = $benchmarkStderr
    }

    $serverCommand = "uv run uvicorn relationship_os.main:app --host 127.0.0.1 --port $Port"
    $server = Start-LoggedProcess -Command $serverCommand -StdoutPath $serverStdout -StderrPath $serverStderr

    $healthy = $false
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Seconds 2

        if ($server.HasExited) {
            throw "Server exited early with code $($server.ExitCode). See $serverStderr"
        }

        try {
            $resp = Invoke-WebRequest -Uri "$baseUrl/healthz" -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        } catch {
        }
    }

    if (-not $healthy) {
        throw "Server did not become healthy in time. See $serverStderr"
    }

    Write-Status -Phase "benchmark_running" -Message "Server healthy. Running benchmark." -Extra @{
        server_pid = $server.Id
        base_url = $baseUrl
    }

    $benchmarkCommand = @(
        "uv run python -m benchmarks",
        "--base-url", """$baseUrl""",
        "--output-dir", """$outputDir""",
        "--timeout", "$TimeoutSeconds",
        "--suite-timeout", "$SuiteTimeoutSeconds",
        "--suite", $Suite,
        "--languages", $Languages,
        "--max-cases-per-suite", "$MaxCasesPerSuite"
    ) -join " "

    $benchmark = Start-LoggedProcess -Command $benchmarkCommand -StdoutPath $benchmarkStdout -StderrPath $benchmarkStderr

    Write-Status -Phase "benchmark_running" -Message "Benchmark process started." -Extra @{
        server_pid = $server.Id
        benchmark_pid = $benchmark.Id
        base_url = $baseUrl
    }

    $null = $benchmark.WaitForExit()

    $artifacts = [ordered]@{}
    foreach ($pattern in @("benchmark_*.json", "benchmark_*.md", "benchmark_*.html")) {
        $file = Get-ChildItem -Path $outputDir -Filter $pattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($file) {
            $artifacts[$pattern] = $file.FullName
        }
    }

    $benchmarkExitCode = [int]$benchmark.ExitCode
    $phase = if ($benchmarkExitCode -eq 0) { "completed" } else { "failed" }
    $message = if ($benchmarkExitCode -eq 0) { "Benchmark run completed." } else { "Benchmark run failed." }
    Write-Status -Phase $phase -Message $message -Extra @{
        server_pid = $server.Id
        benchmark_pid = $benchmark.Id
        benchmark_exit_code = $benchmarkExitCode
        artifacts = $artifacts
    }

    exit $benchmarkExitCode
} catch {
    Write-Status -Phase "failed" -Message $_.Exception.Message -Extra @{
        server_pid = if ($server) { $server.Id } else { $null }
        benchmark_pid = if ($benchmark) { $benchmark.Id } else { $null }
        benchmark_exit_code = if ($benchmark) { [int]$benchmark.ExitCode } else { $null }
    }
    throw
} finally {
    if ($benchmark) {
        Stop-ProcessTree -RootProcessId $benchmark.Id
    }
    if ($server) {
        Stop-ProcessTree -RootProcessId $server.Id
    }
    Stop-ListeningPortProcesses -LocalPort $Port
}
