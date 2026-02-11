[CmdletBinding()]
param(
    # Specify the output CSV file name; default is "containerStats.csv"
    [Parameter(Mandatory=$false)]
    [string]$CsvName = "containerStats.csv"
)

# Function: Convert memory value (e.g. "10MiB", "1.23GiB") to MB (as a double)
function ConvertTo-MB($valueWithUnit) {
    if ($valueWithUnit -match "([\d\.]+)([KMG]i?)?B") {
        $value = [double]$matches[1]
        $unit = $matches[2]
        switch ($unit) {
            "KB" { return $value / 1024 }
            "KiB" { return $value / 1024 }
            "MB" { return $value }
            "MiB" { return $value }
            "GB" { return $value * 1024 }
            "GiB" { return $value * 1024 }
            default { return $value }
        }
    }
    return 0
}

# Function: Convert a generic value with unit (e.g. for NetIO or BlockIO like "2.3kB") to bytes.
function ConvertTo-Bytes($valueWithUnit) {
    if ($valueWithUnit -match "([\d\.]+)([KMG]i?)?B") {
        $value = [double]$matches[1]
        $unit = $matches[2]
        switch ($unit) {
            { $_ -eq $null } { return $value }  # No unit provided
            "KB" { return $value * 1024 }
            "KiB" { return $value * 1024 }
            "MB" { return $value * 1024 * 1024 }
            "MiB" { return $value * 1024 * 1024 }
            "GB" { return $value * 1024 * 1024 * 1024 }
            "GiB" { return $value * 1024 * 1024 * 1024 }
            default { return $value }
        }
    }
    return 0
}

# Flag to check if we're on the first iteration (to create the CSV with headers)
$firstIteration = $true

while ($true) {
    # Get IDs of all running containers
    $containerIDs = docker ps -q

    # Get the current timestamp for this snapshot
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # Array to hold per-container stats objects for this cycle
    $statsList = @()

    if (-not $containerIDs) {
        Write-Output "No running containers found at $timestamp."
    } else {
        # Variables for aggregated calculations
        $totalCPU = 0.0
        $totalMemUsageMB = 0.0
        $totalMemPerc = 0.0
        $totalNetRxBytes = 0
        $totalNetTxBytes = 0
        $totalBlockRxBytes = 0
        $totalBlockTxBytes = 0
        $totalPIDs = 0
        $count = 0

        foreach ($containerID in $containerIDs) {
            # Retrieve docker stats for the container using --no-stream to get a single snapshot
            # Format: ContainerID,Name,CPUPerc,MemUsage,MemPerc,NetIO,BlockIO,PIDs
            $statsOutput = docker stats $containerID --no-stream --format "{{.Container}},{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}"
            $values = $statsOutput.Split(',')

            # Create a custom object for the container stats
            $obj = [PSCustomObject]@{
                TimeStamp = $timestamp
                Container = $values[0].Trim()
                Name      = $values[1].Trim()
                CPUPerc   = $values[2].Trim()
                MemUsage  = $values[3].Trim()   # This is typically "used / total"
                MemPerc   = $values[4].Trim()
                NetIO     = $values[5].Trim()   # Format: "Rx / Tx"
                BlockIO   = $values[6].Trim()   # Format: "Read / Write"
                PIDs      = $values[7].Trim()
            }
            $statsList += $obj

            # Aggregate calculations
            try {
                # CPU: remove the "%" and convert
                $cpu = [double]($obj.CPUPerc.TrimEnd('%'))
                $totalCPU += $cpu

                # Memory usage: take the "used" part from "used / total" and convert to MB
                $memParts = $obj.MemUsage.Split('/')
                if ($memParts.Length -ge 1) {
                    $usedMemStr = $memParts[0].Trim()
                    $usedMemMB = ConvertTo-MB $usedMemStr
                    $totalMemUsageMB += $usedMemMB
                }

                # Memory percentage: remove "%" and add
                $memPerc = [double]($obj.MemPerc.TrimEnd('%'))
                $totalMemPerc += $memPerc

                # NetIO: split by "/" and convert each part to bytes
                $netParts = $obj.NetIO.Split('/')
                if ($netParts.Length -eq 2) {
                    $netRx = ConvertTo-Bytes ($netParts[0].Trim())
                    $netTx = ConvertTo-Bytes ($netParts[1].Trim())
                    $totalNetRxBytes += $netRx
                    $totalNetTxBytes += $netTx
                }

                # BlockIO: split by "/" and convert each part to bytes
                $blockParts = $obj.BlockIO.Split('/')
                if ($blockParts.Length -eq 2) {
                    $blockRx = ConvertTo-Bytes ($blockParts[0].Trim())
                    $blockTx = ConvertTo-Bytes ($blockParts[1].Trim())
                    $totalBlockRxBytes += $blockRx
                    $totalBlockTxBytes += $blockTx
                }

                # PIDs: convert to int and add
                $totalPIDs += [int]$obj.PIDs
                $count++
            } catch {
                Write-Warning "Error processing stats for container $($obj.Container): $_"
            }
        }  # end foreach container

        # Prepare aggregated row
        if ($count -gt 0) {
            # For average memory percentage, divide total by count
            $avgMemPerc = $totalMemPerc / $count

            # Convert aggregated NetIO and BlockIO back to a human-readable format in MB (rounded to 2 decimals)
            $netRxMB = [math]::Round($totalNetRxBytes / (1024*1024),2)
            $netTxMB = [math]::Round($totalNetTxBytes / (1024*1024),2)
            $blockRxMB = [math]::Round($totalBlockRxBytes / (1024*1024),2)
            $blockTxMB = [math]::Round($totalBlockTxBytes / (1024*1024),2)

            # Build an aggregated object; note that CPU and memory usage are sums,
            # while memory percentage is averaged.
            $aggObj = [PSCustomObject]@{
                TimeStamp = $timestamp
                Container = "ALL"
                Name      = "All Containers"
                CPUPerc   = ("{0:N2}%" -f $totalCPU)
                # Show total memory usage in MB with "MB" suffix
                MemUsage  = ("{0:N2} MB" -f $totalMemUsageMB)
                MemPerc   = ("{0:N2}%" -f $avgMemPerc)
                # NetIO as "Rx/Tx" in MB
                NetIO     = ("{0} MB / {1} MB" -f $netRxMB, $netTxMB)
                # BlockIO as "Read/Write" in MB
                BlockIO   = ("{0} MB / {1} MB" -f $blockRxMB, $blockTxMB)
                PIDs      = $totalPIDs
            }
            # Add aggregated row to our list (it will appear after the individual rows)
            $statsList += $aggObj
        }
    }
    
    # Write or append the stats to the CSV file
    if ($firstIteration) {
        $statsList | Export-Csv -Path $CsvName -NoTypeInformation
        $firstIteration = $false
    } else {
        $statsList | Export-Csv -Path $CsvName -NoTypeInformation -Append
    }
    
    Write-Output "Stats recorded at $timestamp"
    # Wait for 5 seconds before the next recording cycle
    Start-Sleep -Seconds 5
}
