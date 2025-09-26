# PowerShell script to build Troubleshooting-Wizard executable

# Define the path to the Python executable in the virtual environment
$projectRoot = Split-Path $PSScriptRoot -Parent
$pythonPath = Join-Path $projectRoot ".venv/Scripts/python.exe"

# Kill any running TroubleshootingWizard.exe before cleaning
Stop-Process -Name TroubleshootingWizard -Force -ErrorAction SilentlyContinue

# Remove previous build artifacts
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
Remove-Item -Force run.spec -ErrorAction SilentlyContinue

# Change to project root for build
Set-Location $projectRoot

# Build the executable, adding necessary data and paths
Write-Host "Building executable with PyInstaller..."
& $pythonPath -m PyInstaller --onefile --windowed --add-data "./data;data" --add-data "./media;media" --add-data "./manuals;manuals" --paths "./src" run.py

Write-Host "Build complete."