[CmdletBinding()]
param()

# --- Main Execution Block ---
try {
    # --- PowerShell Version Check ---
    if (-not $PSVersionTable -or $PSVersionTable.PSVersion.Major -lt 7) {
        $pwshCmd = Get-Command -Name 'pwsh' -ErrorAction SilentlyContinue
        if (-not $pwshCmd) {
            throw 'This script requires PowerShell 7 (pwsh). Please install it and ensure it is available on your system PATH.'
        }

        $scriptPath = $MyInvocation.MyCommand.Path
        if (-not $scriptPath) {
            throw 'Unable to determine the script path for relaunch.'
        }

        $arguments = @('-NoProfile', '-File', $scriptPath) + $args
        Start-Process -FilePath $pwshCmd.Path -ArgumentList $arguments -WorkingDirectory (Split-Path -Parent $scriptPath)
        exit # Exit the current (older PowerShell) session
    }

    # --- Script Configuration ---
    Set-StrictMode -Version 3
    $ErrorActionPreference = 'Stop'

    $script:ScriptPath = $MyInvocation.MyCommand.Path
    $script:ScriptDirectory = if ($script:ScriptPath) { Split-Path -Parent $script:ScriptPath } else { Get-Location }

    $configDir = Join-Path $env:LOCALAPPDATA 'PlayifyManager'
    $configPath = Join-Path $configDir 'config.json'

    $script:BotRoot = $null
    $script:StatePath = $null

    # --- Function Definitions ---

    function Save-BotConfig {
        param(
            [Parameter(Mandatory = $true)]
            [string] $BotRootPath
        )
        if (-not (Test-Path -Path $configDir)) {
            New-Item -ItemType Directory -Path $configDir -Force | Out-Null
        }
        $config = [ordered]@{ BotRoot = $BotRootPath }
        $config | ConvertTo-Json -Depth 4 | Set-Content -Path $configPath -Encoding ASCII -Force
    }

    function Set-BotRoot {
        param(
            [Parameter(Mandatory = $true)]
            [string] $Path
        )
        try {
            $fullPath = [System.IO.Path]::GetFullPath($Path)
        }
        catch {
            throw "Bot directory path is invalid: $Path"
        }
        $botScriptPath = Join-Path $fullPath 'playify.py'
        if (-not (Test-Path -Path $botScriptPath)) {
            throw "playify.py was not found in '$fullPath'."
        }
        $script:BotRoot = $fullPath
        $script:StatePath = Join-Path $script:BotRoot 'playify_bot_state.json'
        return $script:BotRoot
    }

    function Load-BotConfig {
        if (-not (Test-Path -Path $configPath)) { return $false }

        $raw = Get-Content -Path $configPath -Raw -ErrorAction SilentlyContinue
        if ([string]::IsNullOrWhiteSpace($raw)) {
            Remove-Item -Path $configPath -Force -ErrorAction SilentlyContinue
            return $false
        }

        try {
            $config = $raw | ConvertFrom-Json -ErrorAction Stop
        }
        catch {
            Write-Warning 'Configuration data was corrupt. Resetting it.'
            Remove-Item -Path $configPath -Force -ErrorAction SilentlyContinue
            return $false
        }

        if (-not $config.BotRoot) {
            Remove-Item -Path $configPath -Force -ErrorAction SilentlyContinue
            return $false
        }

        try {
            Set-BotRoot -Path $config.BotRoot | Out-Null
        }
        catch {
            Write-Warning "Stored bot directory is invalid: $($_.Exception.Message)"
            Remove-Item -Path $configPath -Force -ErrorAction SilentlyContinue
            return $false
        }
        return $true
    }

    function Prompt-BotRoot {
        param([switch] $Reconfigure)

        Write-Host ''
        if ($Reconfigure) {
            Write-Host 'Update the Playify bot directory.' -ForegroundColor Cyan
        }
        else {
            Write-Host 'Playify bot directory is not configured.' -ForegroundColor Yellow
        }

        $suggested = $null
        if ($Reconfigure -and $script:BotRoot) {
            $suggested = $script:BotRoot
        }
        elseif ($script:ScriptDirectory) {
            $candidate = Join-Path $script:ScriptDirectory 'playify.py'
            if (Test-Path -Path $candidate) {
                $suggested = $script:ScriptDirectory
            }
        }

        while ($true) {
            if ($suggested) {
                Write-Host "Press Enter to use: $suggested"
            }
            $input = Read-Host 'Enter the full path to the folder that contains playify.py'
            if ([string]::IsNullOrWhiteSpace($input)) {
                if ($suggested) { $input = $suggested }
                else {
                    Write-Host 'A folder path is required.' -ForegroundColor Yellow
                    continue
                }
            }

            try {
                Set-BotRoot -Path $input | Out-Null
                Save-BotConfig -BotRootPath $script:BotRoot
                $action = if ($Reconfigure) { "updated" } else { "set" }
                Write-Host "Bot directory $action to $script:BotRoot" -ForegroundColor Green
                return
            }
            catch {
                Write-Host $_.Exception.Message -ForegroundColor Yellow
            }
        }
    }

    function Initialize-BotRoot {
        if (-not (Load-BotConfig)) {
            Prompt-BotRoot
        }
    }

    function Configure-BotDirectory {
        Prompt-BotRoot -Reconfigure
    }

    function Resolve-Python {
        if ($script:BotRoot) {
            $venvNames = @('venv', '.venv', 'env')
            foreach ($name in $venvNames) {
                $venvPythonPath = Join-Path $script:BotRoot ($name | Join-Path -ChildPath 'Scripts\python.exe')
                if (Test-Path -Path $venvPythonPath) {
                    Write-Host "Virtual environment found. Using Python interpreter at: $venvPythonPath" -ForegroundColor DarkCyan
                    return $venvPythonPath
                }
            }
        }

        # --- Fallback to Global Python ---
        # If no virtual environment was found, search the system PATH as a backup.
        Write-Host "No local virtual environment found. Searching for global Python..." -ForegroundColor Yellow
        $candidates = @('python.exe', 'py.exe')
        foreach ($candidate in $candidates) {
            $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
            if ($cmd) {
                Write-Host "Using global Python found at: $($cmd.Path)" -ForegroundColor DarkCyan
                return $cmd.Path
            }
        }

        # If nothing is found, throw an error.
        throw 'Unable to locate a Python interpreter. Ensure a virtual environment exists in the bot directory or that python/py is on the system PATH.'
    }

    function Get-BotScriptPath {
        $botScriptPath = Join-Path $script:BotRoot 'playify.py'
        if (-not (Test-Path -Path $botScriptPath)) {
            throw "playify.py was not found in '$script:BotRoot'. Use option 6 to update the bot directory."
        }
        return $botScriptPath
    }

    function Get-BotState {
        # 1. Check if the state file exists. If not, the bot is not running.
        if (-not $script:StatePath -or -not (Test-Path $script:StatePath)) {
            return $null
        }

        # 2. Try to read and parse the state file.
        $state = $null
        try {
            $raw = Get-Content -Path $script:StatePath -Raw -ErrorAction Stop
            if (-not [string]::IsNullOrWhiteSpace($raw)) {
                $state = $raw | ConvertFrom-Json -ErrorAction Stop
            }
        }
        catch {
            # Catch JSON parsing errors or file read errors.
        }

        # If the file was empty, corrupt, or didn't contain a PID, it's invalid.
        if (-not $state -or -not $state.Pid) {
            Write-Warning 'Bot state file was found but was invalid or corrupt. Resetting it.'
            Clear-BotState
            return $null
        }

        # 3. Try to find the process using the stored PID. Use SilentlyContinue to handle cases where it's not found.
        $proc = Get-Process -Id ([int]$state.Pid) -ErrorAction SilentlyContinue
        if (-not $proc) {
            # The process does NOT exist. The state file is stale and should be removed.
            Write-Warning "State file found for PID $($state.Pid), but the process is not running. Cleaning up stale file."
            Clear-BotState
            return $null
        }

        # 4. Validate the StartTime to protect against reused PIDs.
        if ($state.StartTime) {
            # --- START: MODIFIED BLOCK ---
            # Parse the stored string back into a DateTime object. The 'o' format is culture-neutral and includes timezone info, making it robust for parsing.
            try {
                $storedStartTime = [DateTime]::Parse($state.StartTime, $null, 'RoundtripKind')
            } catch {
                Write-Warning "Could not parse the stored start time string: $($state.StartTime). Cleaning up stale file."
                Clear-BotState
                return $null
            }

            # Get the actual process start time in UTC for a direct comparison.
            $actualStartTime = $proc.StartTime.ToUniversalTime()

            # Calculate the difference. A small tolerance (less than 1 second) accounts for potential minor precision fluctuations without allowing for a reused PID.
            $timeDifference = New-TimeSpan -Start $storedStartTime -End $actualStartTime

            if ([Math]::Abs($timeDifference.TotalSeconds) -ge 1) {
                Write-Warning "Process with PID $($proc.Id) found, but its start time ($actualStartTime) does not match the stored start time ($storedStartTime). This may be a reused PID. Cleaning up stale file."
                Clear-BotState
                return $null
            }
        }

        # 5. If all checks passed, we have a valid, running bot process.
        return [PSCustomObject]@{
            Process = $proc
            State   = $state
        }
    }

    function Save-BotState {
        param(
            [Parameter(Mandatory)] [System.Diagnostics.Process] $Process,
            [Parameter(Mandatory)] [string] $PythonPath,
            [Parameter(Mandatory)] [string[]] $Arguments
        )
        $state = [ordered]@{
            Pid        = $Process.Id
            StartTime  = $Process.StartTime.ToUniversalTime().ToString('o')
            PythonPath = $PythonPath
            Arguments  = $Arguments
        }
        $state | ConvertTo-Json -Depth 4 | Set-Content -Path $script:StatePath -Encoding ASCII -Force
    }

    function Clear-BotState {
        if ($script:StatePath -and (Test-Path $script:StatePath)) {
            Remove-Item -Path $script:StatePath -Force -ErrorAction SilentlyContinue
        }
    }

    function Start-Bot {
        if (Get-BotState) {
            Write-Host "Bot is already running." -ForegroundColor Yellow
            return
        }
        $pythonPath = Resolve-Python
        $scriptPath = Get-BotScriptPath
        $proc = Start-Process -FilePath $pythonPath -ArgumentList $scriptPath -WorkingDirectory $script:BotRoot -PassThru
        Start-Sleep -Seconds 1 # Give the process a moment to initialize
        if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
            Save-BotState -Process $proc -PythonPath $pythonPath -Arguments @($scriptPath)
            Write-Host "Bot started (PID $($proc.Id))." -ForegroundColor Green
        }
        else {
            throw "Failed to start the bot process."
        }
    }

    function Stop-Bot {
        $existing = Get-BotState
        if (-not $existing) {
            Write-Host 'Bot is not running.' -ForegroundColor Yellow
            return
        }
        try {
            Stop-Process -Id $existing.Process.Id -ErrorAction Stop
            Write-Host "Bot stopped (PID $pid)." -ForegroundColor Green
        }
        catch {
            Write-Warning "Failed to stop bot process $($existing.Process.Id): $($_.Exception.Message)"
        }
        finally {
            Clear-BotState
        }
    }

    function Restart-Bot {
        if (Get-BotState) {
            Write-Host "Restarting bot..."
            Stop-Bot
            Start-Sleep -Seconds 1
        }
        else {
            Write-Host 'Bot was not running; starting a new instance...' -ForegroundColor Yellow
        }
        Start-Bot
    }

    function Show-Status {
        Write-Host "Bot directory: $script:BotRoot" -ForegroundColor Cyan
        if (-not (Test-Path -Path (Join-Path $script:BotRoot 'playify.py'))) {
            Write-Host 'WARNING: playify.py was not found in the configured directory.' -ForegroundColor Yellow
        }
        $existing = Get-BotState
        if ($existing) {
            $started = [DateTime]::Parse($existing.State.StartTime).ToLocalTime()
            $stamp = $started.ToString('yyyy-MM-dd HH:mm:ss')
            Write-Host "Bot is running (PID $($existing.Process.Id), started $stamp)." -ForegroundColor Green
        }
        else {
            Write-Host 'Bot is not running.' -ForegroundColor Yellow
        }
    }

    # --- Initial Setup ---
    Initialize-BotRoot

    # --- Main Menu Loop ---
    $exitManager = $false
    while (-not $exitManager) {
        Write-Host ''
        
        # 1. Check the bot's state ONCE at the start of each loop iteration.
        $botState = Get-BotState
        
        # 2. Display the status first, so the user knows the context.
        Show-Status
        
        Write-Host ''
        Write-Host 'Select an option:'

        # 3. Build and display the menu dynamically based on whether the bot is running.
        if ($botState) {
            # --- MENU: Bot is RUNNING ---
            Write-Host '  1) Stop bot'
            Write-Host '  2) Restart bot'
            Write-Host '----------------------------'
            Write-Host '  3) Change bot directory'
            Write-Host '  Q) Exit Manager'
            Write-Host '  F) Full Quit (stop manager and bot)'
        }
        else {
            # --- MENU: Bot is STOPPED ---
            Write-Host '  1) Start bot'
            Write-Host '----------------------------'
            Write-Host '  2) Change bot directory'
            Write-Host '  Q) Exit manager'
        }
        
        Write-Host ''
        $choice = Read-Host 'Enter choice or Q to exit'

        # 4. Process the choice within a try/catch block.
        # The action for each number depends on the state checked earlier.
        try {
            if ($botState) {
                # --- ACTIONS: Bot is RUNNING ---
                switch ($choice.ToLowerInvariant()) {
                    '1' { Stop-Bot }
                    '2' { Restart-Bot }
                    '3' { Configure-BotDirectory }
                    'q' { $exitManager = $true }
                    'F' { 
                        Stop-Bot
                        $exitManager = $true
                    }
                    default { Write-Host 'Unknown choice.' -ForegroundColor Yellow }
                }
            }
            else {
                # --- ACTIONS: Bot is STOPPED ---
                switch ($choice.ToLowerInvariant()) {
                    '1' { Start-Bot }
                    '2' { Configure-BotDirectory }
                    'q' { $exitManager = $true }
                    default { Write-Host 'Unknown choice.' -ForegroundColor Yellow }
                }
            }
        }
        catch {
            # This catches errors from Start-Bot/Stop-Bot etc. and prevents the manager from crashing.
            Write-Host "`nACTION FAILED: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
catch {
    # This block will catch any script-terminating error that wasn't handled internally.
    Write-Host "`n--- SCRIPT HALTED DUE TO AN ERROR ---" -ForegroundColor Red
    Write-Error $_.Exception.Message
    Write-Host "---------------------------------------" -ForegroundColor Red
}
#finally {
#    Write-Host "`nScript has finished. Press Enter to exit." -ForegroundColor Cyan
#    [void](Read-Host)
#}