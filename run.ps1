<#
.SYNOPSIS
    Displays all changed files (staged, unstaged, and untracked) in a Git repository.
.DESCRIPTION
    This script acts as a wrapper for git_diff_script.py, allowing you to run
    it from PowerShell with various options including filtering by file extension,
    ignoring binary files, and outputting in JSON format.
.PARAMETER RepoPath
    The path to the Git repository. This is a mandatory positional parameter.
.PARAMETER Output
    Specifies a file to save the output to. If not provided, output goes to the console.
.PARAMETER Quiet
    Suppresses all console output from this PowerShell script itself.
    Note: Python script's error messages will still go to stderr unless redirected.
.PARAMETER Verbose
    Enables verbose output for both this PowerShell script and the underlying Python script.
.PARAMETER Extensions
    Filters the diffs by file extensions (e.g., ".py", ".js", ".txt").
    Include the leading dot. Multiple extensions can be provided as a comma-separated list
    or space-separated if quoted (e.g., -Extensions ".py",".js" or -Extensions ".py" ".js").
.PARAMETER IgnoreBinaries
    If specified, the script will not display diffs for binary files.
.PARAMETER Json
    If specified, the script will output the diffs in JSON format,
    suitable for programmatic parsing.
.EXAMPLE
    .\run_git_diff.ps1 C:\MyRepo
    Displays all changes in C:\MyRepo to the console.

.EXAMPLE
    .\run_git_diff.ps1 C:\MyRepo -Output C:\Reports\diff.txt -Verbose
    Generates a verbose diff report for C:\MyRepo and saves it to diff.txt.

.EXAMPLE
    .\run_git_diff.ps1 C:\MyRepo -Extensions ".py",".ps1" -Json
    Outputs changes in Python and PowerShell files from C:\MyRepo in JSON format to console.

.EXAMPLE
    .\run_git_diff.ps1 C:\MyRepo -IgnoreBinaries -Quiet -Output C:\Reports\text_diffs.json -Json
    Generates a JSON report of text diffs for C:\MyRepo, ignoring binaries,
    saving it to text_diffs.json without any console output from the PowerShell script.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$RepoPath,

    [string]$Output,

    [switch]$Quiet,

    [switch]$Verbose,

    [string[]]$Extensions, # Array for multiple extensions

    [switch]$IgnoreBinaries,

    [switch]$Json # New switch for JSON output
)

# Resolve the path to the Python script relative to the current PowerShell script's location
$PYTHON_SCRIPT_PATH = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) "git_diff_script.py"

# Store arguments to pass to the Python script
$PythonArgs = @()

# Add Python verbose flag if PowerShell verbose is enabled
if ($Verbose) {
    $PythonArgs += "--verbose"
}

# Add Python extensions flag and values
if ($Extensions) {
    $PythonArgs += "--extensions"
    # Ensure extensions are properly quoted for Python if they contain spaces or special chars (though unlikely for extensions)
    $PythonArgs += $Extensions
}

# Add Python ignore binaries flag
if ($IgnoreBinaries) {
    $PythonArgs += "--ignore-binaries"
}

# Add Python JSON flag
if ($Json) {
    $PythonArgs += "--json"
}

# Determine if output should be saved to a file
$ShouldSaveToFile = $false
if (-not [string]::IsNullOrEmpty($Output)) {
    $ShouldSaveToFile = $true
}

# Inform user if PowerShell verbose mode is enabled
if ($Verbose) {
    Write-Host "Generating Git diff report for: $RepoPath"
    if ($ShouldSaveToFile) {
        Write-Host "Saving output to: $Output"
    }
    Write-Host "Python script will receive arguments: $PythonArgs"
    Write-Host "----------------------------------------------------"
}

# Create output directory if needed
if ($ShouldSaveToFile) {
    $OutputDir = Split-Path -Parent $Output
    if (-not [string]::IsNullOrEmpty($OutputDir) -and $OutputDir -ne ".") {
        New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
    }
}

# Construct the full command for the Python script
# Using '--' to separate Python script path from its arguments for clarity,
# though not strictly necessary with PowerShell's argument passing.
$PythonCommand = "python3", "$PYTHON_SCRIPT_PATH", "$RepoPath"

# Combine the Python command with its specific arguments
$FullPythonCommand = $PythonCommand + $PythonArgs

# Execute the Python script based on output and quiet options.
if ($ShouldSaveToFile) {
    if ($Quiet) {
        # Redirect all output (stdout and stderr) to the file.
        # Start-Process allows controlling streams and waiting for completion.
        & $FullPythonCommand *>&1 | Out-File -FilePath $Output -Encoding UTF8
    }
    else {
        # Tee output to both console and file.
        # *>&1 redirects all streams (stdout, stderr) to the success stream.
        & $FullPythonCommand *>&1 | Tee-Object -FilePath $Output -Encoding UTF8
    }
}
else {
    if ($Quiet) {
        # Suppress all output to console (send to null).
        & $FullPythonCommand > $null 2>&1
    }
    else {
        # Display output directly to console.
        & $FullPythonCommand
    }
}

$LastCommandExitCode = $LASTEXITCODE

# Provide a final status message based on the Python script's exit code.
if ($LastCommandExitCode -eq 0) {
    if ($Verbose) {
        if ($ShouldSaveToFile) {
            Write-Host "----------------------------------------------------"
            Write-Host "Report successfully saved to $Output"
        }
        else {
            Write-Host "----------------------------------------------------"
            Write-Host "Report completed."
        }
    }
    elseif ($ShouldSaveToFile) {
        Write-Host "----------------------------------------------------"
        Write-Host "Report successfully saved to $Output"
    }
}
else {
    if (-not $Quiet -or $ShouldSaveToFile) {
        Write-Host "----------------------------------------------------" -ForegroundColor Red -ErrorAction SilentlyContinue
        Write-Host "An error occurred (Exit Code: $LastCommandExitCode)." -ForegroundColor Red -ErrorAction SilentlyContinue
        if ($ShouldSaveToFile) {
            Write-Host "Check $Output for details." -ForegroundColor Red -ErrorAction SilentlyContinue
        }
        else {
            Write-Host "Output was displayed to console above." -ForegroundColor Red -ErrorAction SilentlyContinue
        }
    }
}

exit $LastCommandExitCode
