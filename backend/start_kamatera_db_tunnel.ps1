# Forward a local-only port to CampusHub PostgreSQL over the authorized SSH key.
# Starts/reuses the verified SSH forward and one hidden reconnect monitor.
# -Once is used by the monitor and performs no recursive monitor startup.
# Never terminates an existing process or restarts an application.
param([switch]$Once)

$ErrorActionPreference = 'Stop'
$serverHost = '74.113.234.180'
$forward = '127.0.0.1:15432:127.0.0.1:5432'
$identityFile = Join-Path $env:USERPROFILE '.ssh\id_ed25519_campushub_kamatera'
$sshPath = (Get-Command ssh.exe -ErrorAction Stop).Source
$stateDirectory = Join-Path $env:LOCALAPPDATA 'CampusHub\kamatera-tunnel'
$mutex = New-Object System.Threading.Mutex($false, 'Local\CampusHubKamateraDbTunnel')
$locked = $false

function Test-CampusHubTunnelProcess($processInfo) {
    return $null -ne $processInfo -and
        $processInfo.Name -eq 'ssh.exe' -and
        $processInfo.ExecutablePath -eq $sshPath -and
        $processInfo.CommandLine.Contains($identityFile) -and
        $processInfo.CommandLine.Contains($forward) -and
        $processInfo.CommandLine.Contains("root@$serverHost")
}

function Get-CampusHubTunnelListeners {
    # Windows can report a stale/incorrect State for the forwarding endpoint.
    # An unconnected endpoint has no remote peer; verify its owner and connect
    # separately instead of trusting a State=Listen filter alone.
    Get-NetTCPConnection -LocalPort 15432 -ErrorAction SilentlyContinue |
        Where-Object { $_.RemotePort -eq 0 -and $_.RemoteAddress -in @('0.0.0.0', '::') }
}

function Test-CampusHubTunnelConnection {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connecting = $client.ConnectAsync('127.0.0.1', 15432)
        if (-not $connecting.Wait(2000)) { return $false }
        return $client.Connected
    }
    catch { return $false }
    finally { $client.Dispose() }
}

function Start-CampusHubTunnelMonitor {
    $monitorScript = Join-Path $PSScriptRoot 'kamatera_db_tunnel_monitor.py'
    $monitorPython = Join-Path $PSScriptRoot 'core\venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $monitorScript -PathType Leaf) -or
        -not (Test-Path -LiteralPath $monitorPython -PathType Leaf)) {
        throw 'The CampusHub reconnect monitor or existing Python environment is missing.'
    }
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
    $monitorStatePath = Join-Path $stateDirectory 'monitor.json'
    if (Test-Path -LiteralPath $monitorStatePath -PathType Leaf) {
        try {
            $monitorState = Get-Content -LiteralPath $monitorStatePath -Raw | ConvertFrom-Json
            $monitorProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$monitorState.ProcessId)"
            if ($null -ne $monitorProcess -and $monitorProcess.Name -eq 'python.exe' -and
                $monitorProcess.CommandLine.Contains($monitorScript) -and
                $monitorState.State -ne 'stopped') { return }
        }
        catch { # Stale metadata is not authority to stop an existing process.
        }
    }
    $monitorStamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')
    Start-Process -FilePath $monitorPython -ArgumentList @(('"' + $monitorScript + '"')) -WindowStyle Hidden `
        -RedirectStandardError (Join-Path $stateDirectory "$monitorStamp.monitor.stderr.log") `
        -RedirectStandardOutput (Join-Path $stateDirectory "$monitorStamp.monitor.stdout.log") | Out-Null
    Write-Output 'CampusHub automatic tunnel reconnect monitor started.'
}

try {
    $locked = $mutex.WaitOne(0)
    if (-not $locked) { throw 'Another tunnel startup is in progress; no duplicate was started.' }
    if (-not (Test-Path -LiteralPath $identityFile -PathType Leaf)) {
        throw 'The dedicated CampusHub SSH private key is missing.'
    }
    if (-not $Once) { Start-CampusHubTunnelMonitor }
    $listeners = @(Get-CampusHubTunnelListeners)
    if ($listeners.Count -gt 0) {
        foreach ($listener in $listeners) {
            $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
            if ($listener.LocalAddress -ne '127.0.0.1' -or -not (Test-CampusHubTunnelProcess $existing)) {
                throw 'Port 15432 belongs to an unverified listener. No process was changed.'
            }
        }
        if (-not (Test-CampusHubTunnelConnection)) {
            throw 'The verified SSH endpoint is not accepting connections; no duplicate was started.'
        }
        Write-Output "Existing CampusHub SSH tunnel is ready at 127.0.0.1:15432 (PID $($listeners[0].OwningProcess))."
        return
    }
    $pending = @(Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" |
        Where-Object { Test-CampusHubTunnelProcess $_ })
    if ($pending.Count -gt 0) {
        throw "A matching SSH helper exists without a ready listener (PID $($pending[0].ProcessId)); no duplicate was started."
    }
    New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ')
    $errorLog = Join-Path $stateDirectory "$stamp.stderr.log"
    $outputLog = Join-Path $stateDirectory "$stamp.stdout.log"
    $sshArguments = @('-N', '-T', '-i', ('"' + $identityFile + '"'),
        '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
        '-o', 'StrictHostKeyChecking=yes', '-o', 'ExitOnForwardFailure=yes',
        '-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=30',
        '-o', 'ServerAliveCountMax=3', '-L', $forward, "root@$serverHost")
    $helper = Start-Process -FilePath $sshPath -ArgumentList $sshArguments -WindowStyle Hidden `
        -RedirectStandardError $errorLog -RedirectStandardOutput $outputLog -PassThru
    @{ ProcessId = $helper.Id; Host = $serverHost; LocalPort = 15432;
       CreatedAtUtc = $helper.StartTime.ToUniversalTime().ToString('o'); ErrorLog = $errorLog } |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $stateDirectory 'current.json') -Encoding UTF8
    for ($attempt = 0; $attempt -lt 30; $attempt++) {
        $helper.Refresh()
        if ($helper.HasExited) {
            throw "SSH exited before the tunnel was ready. Inspect $errorLog; no app was restarted."
        }
        $ready = @(Get-CampusHubTunnelListeners |
            Where-Object { $_.LocalAddress -eq '127.0.0.1' -and $_.OwningProcess -eq $helper.Id })
        if ($ready.Count -gt 0 -and (Test-CampusHubTunnelConnection)) {
            Write-Output "CampusHub SSH tunnel is ready at 127.0.0.1:15432 (PID $($helper.Id))."
            return
        }
        Start-Sleep -Milliseconds 500
    }
    throw "SSH helper PID $($helper.Id) has no ready listener; inspect $errorLog before retrying."
}
finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
