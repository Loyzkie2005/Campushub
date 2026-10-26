# Forward a local-only port to CampusHub PostgreSQL over the authorized SSH key.
# Starts one hidden SSH helper, reuses only the verified matching listener,
# and never terminates an existing process or restarts an application.
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

try {
    $locked = $mutex.WaitOne(0)
    if (-not $locked) { throw 'Another tunnel startup is in progress; no duplicate was started.' }
    if (-not (Test-Path -LiteralPath $identityFile -PathType Leaf)) {
        throw 'The dedicated CampusHub SSH private key is missing.'
    }
    $listeners = @(Get-NetTCPConnection -State Listen -LocalPort 15432 -ErrorAction SilentlyContinue)
    if ($listeners.Count -gt 0) {
        foreach ($listener in $listeners) {
            $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
            if ($listener.LocalAddress -ne '127.0.0.1' -or -not (Test-CampusHubTunnelProcess $existing)) {
                throw 'Port 15432 belongs to an unverified listener. No process was changed.'
            }
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
        $ready = @(Get-NetTCPConnection -State Listen -LocalPort 15432 -ErrorAction SilentlyContinue |
            Where-Object { $_.LocalAddress -eq '127.0.0.1' -and $_.OwningProcess -eq $helper.Id })
        if ($ready.Count -gt 0) {
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
