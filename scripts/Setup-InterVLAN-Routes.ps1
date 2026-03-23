<#
.SYNOPSIS
    Inter-VLAN RDP Connectivity - Route Setup & Test Script
.DESCRIPTION
    Adds persistent static routes for cross-network RDP.
    Run as Administrator for route -p commands.
#>

param(
    [switch]$AddRoutes,
    [switch]$RemoveRoutes,
    [switch]$TestOnly
)

# ==============================================================================
# NETWORK CONFIGURATION
# ==============================================================================

$SwitchSVI_V1  = "192.168.1.254"
$SwitchSVI_V15 = "192.168.15.254"

$TestTargets = @(
    @{ Name = "TIM Router";     IP = "192.168.1.1" }
    @{ Name = "Switch SVI V1";  IP = "192.168.1.254" }
    @{ Name = "Vivo Router";    IP = "192.168.15.1" }
    @{ Name = "Switch SVI V15"; IP = "192.168.15.254" }
    @{ Name = "Huawei WAN";     IP = "192.168.15.3" }
    @{ Name = "Huawei LAN GW";  IP = "192.168.16.1" }
)

# ==============================================================================
# DETECT CURRENT NETWORK
# ==============================================================================

Write-Host ""
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Inter-VLAN RDP Connectivity Tool" -ForegroundColor White
Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "  Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray

$myIP = $null
$myNetName = $null
$myGateway = $null
$mySwitchSVI = $null

$adapters = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {
    $_.IPAddress -match "^192\.168\." -and $_.PrefixOrigin -ne "WellKnown"
}

foreach ($a in $adapters) {
    $ip = $a.IPAddress
    $parts = $ip.Split(".")
    $thirdOctet = [int]$parts[2]

    if ($thirdOctet -eq 1) {
        $myIP = $ip; $myNetName = "ISP1_TIM"; $myGateway = "192.168.1.1"; $mySwitchSVI = $SwitchSVI_V1
    }
    elseif ($thirdOctet -eq 15) {
        $myIP = $ip; $myNetName = "ISP2_VIVO"; $myGateway = "192.168.15.1"; $mySwitchSVI = $SwitchSVI_V15
    }
    elseif ($thirdOctet -eq 16) {
        $myIP = $ip; $myNetName = "HUAWEI_WIFI"; $myGateway = "192.168.16.1"; $mySwitchSVI = $null
    }
}

if (-not $myIP) {
    Write-Host "`n[!] ERROR: Not on a known network (192.168.1/15/16.x)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[*] Detected Network:" -ForegroundColor Green
Write-Host "    Network:    $myNetName" -ForegroundColor White
Write-Host "    IP:         $myIP" -ForegroundColor White
Write-Host "    Gateway:    $myGateway" -ForegroundColor White
Write-Host "    Switch SVI: $mySwitchSVI" -ForegroundColor White

# ==============================================================================
# DETERMINE ROUTES TO ADD
# ==============================================================================

$routesToManage = @()

if ($myNetName -eq "ISP1_TIM") {
    # On TIM: need routes to Vivo and Huawei via Switch SVI V1
    $routesToManage += @{ Dest = "192.168.15.0"; Mask = "255.255.255.0"; NH = $SwitchSVI_V1; Desc = "Vivo via Switch" }
    $routesToManage += @{ Dest = "192.168.16.0"; Mask = "255.255.255.0"; NH = $SwitchSVI_V1; Desc = "Huawei via Switch" }
}
elseif ($myNetName -eq "ISP2_VIVO") {
    # On Vivo: need routes to TIM and Huawei
    $routesToManage += @{ Dest = "192.168.1.0"; Mask = "255.255.255.0"; NH = $SwitchSVI_V15; Desc = "TIM via Switch" }
    # Huawei is on same VLAN 15 (via 192.168.15.3), only need if behind NAT going to .16.x
    $routesToManage += @{ Dest = "192.168.16.0"; Mask = "255.255.255.0"; NH = "192.168.15.3"; Desc = "Huawei LAN via Huawei WAN" }
}
elseif ($myNetName -eq "HUAWEI_WIFI") {
    # On Huawei WiFi: need to go through Huawei gateway -> Vivo/Switch
    # NOTE: Huawei NAT may block this unless in AP mode
    $routesToManage += @{ Dest = "192.168.1.0"; Mask = "255.255.255.0"; NH = "192.168.16.1"; Desc = "TIM via Huawei -> Switch" }
    $routesToManage += @{ Dest = "192.168.15.0"; Mask = "255.255.255.0"; NH = "192.168.16.1"; Desc = "Vivo via Huawei -> Switch" }
}

# ==============================================================================
# SHOW CURRENT ROUTES
# ==============================================================================

Write-Host ""
Write-Host "--- Current Relevant Routes ---" -ForegroundColor Yellow
$routeOutput = route print -4 2>&1 | Out-String
$routeLines = $routeOutput -split "`n" | Where-Object { $_ -match "192\.168\.(1|15|16)\." }
if ($routeLines) {
    foreach ($line in $routeLines) { Write-Host "    $($line.Trim())" -ForegroundColor Gray }
} else {
    Write-Host "    (no routes to 192.168.1/15/16.x found)" -ForegroundColor DarkGray
}

# ==============================================================================
# ADD ROUTES
# ==============================================================================

if ($AddRoutes) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  Adding Persistent Static Routes" -ForegroundColor White
    Write-Host ("=" * 70) -ForegroundColor Cyan

    foreach ($r in $routesToManage) {
        Write-Host ""
        Write-Host "  [+] $($r.Desc)" -ForegroundColor Yellow
        Write-Host "      Destination: $($r.Dest)/24" -ForegroundColor Gray
        Write-Host "      Next Hop:    $($r.NH)" -ForegroundColor Gray

        # Check existing
        $existCheck = route print -4 2>&1 | Out-String
        if ($existCheck -match [regex]::Escape($r.Dest)) {
            Write-Host "      Already exists -- skipping" -ForegroundColor DarkYellow
            continue
        }

        $cmdStr = "route -p add $($r.Dest) mask $($r.Mask) $($r.NH)"
        Write-Host "      CMD: $cmdStr" -ForegroundColor DarkGray
        $result = cmd /c $cmdStr 2>&1
        Write-Host "      Result: $result" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "--- Updated Routes ---" -ForegroundColor Yellow
    $routeOutput2 = route print -4 2>&1 | Out-String
    $routeLines2 = $routeOutput2 -split "`n" | Where-Object { $_ -match "192\.168\.(1|15|16)\." }
    foreach ($line in $routeLines2) { Write-Host "    $($line.Trim())" -ForegroundColor Gray }
}

# ==============================================================================
# REMOVE ROUTES
# ==============================================================================

if ($RemoveRoutes) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  Removing Static Routes" -ForegroundColor White
    Write-Host ("=" * 70) -ForegroundColor Cyan

    foreach ($r in $routesToManage) {
        Write-Host "  [-] Removing $($r.Dest)" -ForegroundColor Yellow
        $result = cmd /c "route delete $($r.Dest)" 2>&1
        Write-Host "      $result" -ForegroundColor Gray
    }
}

# ==============================================================================
# CONNECTIVITY TESTS
# ==============================================================================

if ($TestOnly -or $AddRoutes -or (-not $AddRoutes -and -not $RemoveRoutes)) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  Connectivity Tests" -ForegroundColor White
    Write-Host ("=" * 70) -ForegroundColor Cyan

    $results = @()

    foreach ($t in $TestTargets) {
        $tName = $t.Name
        $tIP   = $t.IP
        Write-Host "  Ping $tName ($tIP)..." -NoNewline

        try {
            $ping = Test-Connection -ComputerName $tIP -Count 2 -TimeoutSeconds 2 -ErrorAction Stop
            $avgMs = [math]::Round(($ping | Measure-Object -Property Latency -Average).Average)
            $ttl   = $ping[0].Reply.Options.Ttl
            Write-Host " PASS" -ForegroundColor Green -NoNewline
            Write-Host " (${avgMs}ms, TTL=$ttl)" -ForegroundColor Gray
            $results += @{ Name = $tName; IP = $tIP; Status = "PASS"; RTT = "${avgMs}ms"; TTL = $ttl }
        }
        catch {
            Write-Host " FAIL" -ForegroundColor Red
            $results += @{ Name = $tName; IP = $tIP; Status = "FAIL"; RTT = "---"; TTL = "---" }
        }
    }

    # RDP port test
    Write-Host ""
    Write-Host "--- RDP Port Tests (TCP 3389) ---" -ForegroundColor Yellow

    foreach ($t in $TestTargets) {
        $tName = $t.Name
        $tIP   = $t.IP
        Write-Host "  RDP $tName ($tIP)..." -NoNewline

        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $connect = $tcp.BeginConnect($tIP, 3389, $null, $null)
            $wait = $connect.AsyncWaitHandle.WaitOne(2000, $false)
            if ($wait -and $tcp.Connected) {
                Write-Host " OPEN" -ForegroundColor Green
                $tcp.Close()
            }
            else {
                Write-Host " CLOSED/FILTERED" -ForegroundColor DarkYellow
                $tcp.Close()
            }
        }
        catch {
            Write-Host " ERROR" -ForegroundColor Red
        }
    }

    # Traceroute
    Write-Host ""
    Write-Host "--- Traceroute to Remote Gateways ---" -ForegroundColor Yellow

    $remoteGWs = @()
    if ($myNetName -ne "ISP1_TIM")    { $remoteGWs += @{ Name = "TIM Router";  IP = "192.168.1.1" } }
    if ($myNetName -ne "ISP2_VIVO")   { $remoteGWs += @{ Name = "Vivo Router"; IP = "192.168.15.1" } }
    if ($myNetName -ne "HUAWEI_WIFI") { $remoteGWs += @{ Name = "Huawei GW";   IP = "192.168.16.1" } }

    foreach ($gw in $remoteGWs) {
        Write-Host ""
        Write-Host "  tracert $($gw.Name) ($($gw.IP)):" -ForegroundColor Yellow
        $traceResult = cmd /c "tracert -d -h 5 -w 1000 $($gw.IP)" 2>&1
        foreach ($line in $traceResult) { Write-Host "    $line" -ForegroundColor Gray }
    }

    # Summary Table
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  RESULTS SUMMARY" -ForegroundColor White
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host ""

    $passCount = ($results | Where-Object { $_.Status -eq "PASS" }).Count
    $totalCount = $results.Count
    $failCount = $totalCount - $passCount

    if ($failCount -eq 0) {
        Write-Host "  ALL $totalCount TESTS PASSED" -ForegroundColor Green
    } else {
        Write-Host "  $passCount/$totalCount passed, $failCount FAILED" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "  Target              IP               Status  RTT" -ForegroundColor Gray
    Write-Host "  ----                --               ------  ---" -ForegroundColor DarkGray
    foreach ($r in $results) {
        $nameStr = $r.Name.PadRight(20)
        $ipStr   = $r.IP.PadRight(17)
        $sColor  = if ($r.Status -eq "PASS") { "Green" } else { "Red" }
        Write-Host "  $nameStr $ipStr " -NoNewline -ForegroundColor Gray
        Write-Host "$($r.Status)   " -NoNewline -ForegroundColor $sColor
        Write-Host "$($r.RTT)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "[*] Script complete." -ForegroundColor Gray
