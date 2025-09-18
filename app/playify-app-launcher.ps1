[CmdletBinding()]
param(
    # This switch is used internally to know if the script has already been relaunched.
    [switch]$IsRelaunched
)

# --- Block 1: The Relauncher ---
# This block handles being double-clicked by relaunching the script in a new,
# interactive window.
if (-not $IsRelaunched.IsPresent) {
    $pwshPath = (Get-Command -Name 'pwsh' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Path
    if (-not $pwshPath) {
        Write-Host "FATAL: PowerShell 7 (pwsh.exe) must be installed and available in your PATH." -ForegroundColor Red
        Read-Host "Press Enter to exit."
        exit 1
    }
    
    $scriptPath = $MyInvocation.MyCommand.Path
    $commandToRun = "& '$scriptPath' -IsRelaunched"
    
    $arguments = @(
        '-Command',
        $commandToRun
    )
    
    Start-Process -FilePath $pwshPath -ArgumentList $arguments
    exit
}

# --- Block 2: Main Logic ---
try {
    $scriptDirectory = Split-Path -Path $MyInvocation.MyCommand.Path -Parent

    # --- Step 1: Configure Application Directory ---
    $dataDir = Join-Path $scriptDirectory 'Playify_Data'
    $configPath = Join-Path $dataDir 'playify_launcher_config.txt'
    $appRoot = $null

    # Load saved directory from config.
    if (Test-Path -Path $configPath) {
        $savedPath = Get-Content -Path $configPath
        if (Test-Path -Path (Join-Path $savedPath 'app.py')) {
            $appRoot = $savedPath
        }
    }

    # If directory is not configured or invalid, prompt the user.
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
    
    $argumentsForPython = "`"$appScriptPath`""

    Start-Process -FilePath $pythonPath -ArgumentList $argumentsForPython -WorkingDirectory $appRoot -WindowStyle Hidden

    Write-Host "Application launched successfully. This window will close shortly." -ForegroundColor Green
    Start-Sleep -Seconds 3
}
catch {
    Write-Host "`n--- SCRIPT HALTED DUE TO A FATAL ERROR ---" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "------------------------------------------" -ForegroundColor Red
    Read-Host "The script failed to run. Press Enter to close the window."
}