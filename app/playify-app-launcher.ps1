[CmdletBinding()]
param(
    # This switch is used internally to know if the script has already been relaunched.
    [switch]$IsRelaunched
)

# --- Block 1: The Relauncher ---
# The only purpose of this block is to handle being double-clicked. A double-clicked
# script is non-interactive, so this code restarts itself in a new, interactive window.
if (-not $IsRelaunched.IsPresent) {
    $pwshPath = (Get-Command -Name 'pwsh' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Path
    if (-not $pwshPath) {
        Write-Host "FATAL: PowerShell 7 (pwsh.exe) must be installed and available in your PATH." -ForegroundColor Red
        Read-Host "Press Enter to exit."
        exit 1
    }
    
    # --- CHANGE: '-NoExit' has been REMOVED ---
    # The new window will now close by default as soon as the script finishes.
    $arguments = @('-File', $MyInvocation.MyCommand.Path, '-IsRelaunched')
    Start-Process -FilePath $pwshPath -ArgumentList $arguments
    exit
}

# --- Block 2: Main Logic (only runs in the new interactive window) ---
try {
    # $PSScriptRoot is a reliable variable for the script's own directory.
    $scriptDirectory = $PSScriptRoot

    # --- Step 1: Configure Application Directory ---
    $dataDir = Join-Path $scriptDirectory 'Playify_Data'
    $configPath = Join-Path $dataDir 'config.txt'
    $appRoot = $null

    # Try to load the saved directory from the config file.
    if (Test-Path -Path $configPath) {
        $savedPath = Get-Content -Path $configPath
        if (Test-Path -Path (Join-Path $savedPath 'app.py')) {
            $appRoot = $savedPath
        }
    }

    # If the directory wasn't loaded or was invalid, we must ask the user for it.
    if ([string]::IsNullOrWhiteSpace($appRoot)) {
        Write-Host "`nYour Python application directory needs to be configured." -ForegroundColor Yellow
        
        $suggestedPath = $null
        if (Test-Path -Path (Join-Path $scriptDirectory 'app.py')) {
            $suggestedPath = $scriptDirectory
        }

        while ($true) {
            if ($suggestedPath) {
                Write-Host "Press Enter to use the default location: $suggestedPath"
            }
            
            $inputPath = Read-Host "Enter the full path to the folder containing app.py"
            $chosenPath = $null

            if ([string]::IsNullOrWhiteSpace($inputPath)) {
                if ($suggestedPath) {
                    $chosenPath = $suggestedPath
                } else {
                    Write-Host "A path is required. Please try again." -ForegroundColor Red
                    continue
                }
            } else {
                $chosenPath = $inputPath
            }

            if (Test-Path -Path (Join-Path $chosenPath 'app.py')) {
                $appRoot = $chosenPath
                
                if (-not (Test-Path -Path $dataDir)) {
                    New-Item -ItemType Directory -Path $dataDir | Out-Null
                }
                Set-Content -Path $configPath -Value $appRoot
                
                Write-Host "Directory saved: $appRoot" -ForegroundColor Green
                break
            } else {
                Write-Host "ERROR: 'app.py' not found in '$chosenPath'. Please try again." -ForegroundColor Red
            }
        }
    }

    # --- Step 2: Find the Python Interpreter ---
    $pythonPath = $null
    
    $venvNames = @('venv', '.venv', 'env')
    foreach ($name in $venvNames) {
        $testPath = Join-Path $appRoot "$name\Scripts\python.exe"
        if (Test-Path -Path $testPath) {
            $pythonPath = $testPath
            Write-Host "Found virtual environment Python: $pythonPath" -ForegroundColor Cyan
            break
        }
    }

    if ([string]::IsNullOrWhiteSpace($pythonPath)) {
        Write-Host "No virtual environment found, searching global PATH..." -ForegroundColor Yellow
        $globalPythonCmd = Get-Command -Name 'python.exe' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($globalPythonCmd) {
            $pythonPath = $globalPythonCmd.Path
            Write-Host "Found global Python: $pythonPath" -ForegroundColor Cyan
        }
    }

    # --- Step 3: Validate and Launch ---
    if ([string]::IsNullOrWhiteSpace($pythonPath)) {
        throw "CRITICAL: Could not find a Python interpreter. Please ensure one is in your PATH or a virtual environment exists."
    }

    $appScriptPath = Join-Path $appRoot 'app.py'
    Write-Host "`nLaunching application in the background..." -ForegroundColor Green
    
    Start-Process -FilePath $pythonPath -ArgumentList $appScriptPath -WorkingDirectory $appRoot -WindowStyle Hidden

    # The script now finishes here and the window will close automatically.
    Write-Host "Application launched successfully. This window will close shortly." -ForegroundColor Green
    Start-Sleep -Seconds 3
}
catch {
    # --- CHANGE: 'Read-Host' has been ADDED here ---
    # This block only runs if an error occurs.
    # The Read-Host command will pause the script, keeping the window open so you can see the error.
    Write-Host "`n--- SCRIPT HALTED DUE TO A FATAL ERROR ---" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "------------------------------------------" -ForegroundColor Red
    Read-Host "The script failed to run. Press Enter to close the window."
}