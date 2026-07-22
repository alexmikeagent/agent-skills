[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RequestPath,

    [Parameter(Mandatory = $true)]
    [string]$HostJobPath
)

$ErrorActionPreference = "Stop"
$startedAt = [DateTime]::UtcNow.ToString("o")
$request = Get-Content -LiteralPath $RequestPath -Raw | ConvertFrom-Json
$localJobRoot = Join-Path $env:LOCALAPPDATA ("CodexUiPathBridge\jobs\" + $request.job_id)
$localProject = Join-Path $localJobRoot "project"
$localResults = Join-Path $localJobRoot "results"
$hostResults = Join-Path $HostJobPath "results"
$findings = [System.Collections.Generic.List[object]]::new()
$tests = [System.Collections.Generic.List[object]]::new()
$artifacts = [System.Collections.Generic.List[object]]::new()
$compileStatus = "not_run"
$executionStatus = "not_run"
$exitCode = 0

function Add-Finding {
    param([string]$Code, [string]$Severity, [string]$Message, [string]$Gate, [string]$Evidence = "")
    $value = [ordered]@{ code = $Code; severity = $Severity; message = $Message; gate = $Gate }
    if ($Evidence) { $value.evidence = $Evidence }
    $findings.Add([pscustomobject]$value)
}

function Invoke-UipCommand {
    param([string]$Name, [string[]]$Arguments)
    $logPath = Join-Path $localResults ($Name + ".log")
    $output = & uip @Arguments 2>&1 | ForEach-Object { $_.ToString() }
    $commandExit = $LASTEXITCODE
    $output | Set-Content -LiteralPath $logPath -Encoding UTF8
    $artifacts.Add([pscustomobject]@{ type = "log"; name = $Name; path = ($Name + ".log") })
    return [pscustomobject]@{ ExitCode = $commandExit; Output = ($output -join [Environment]::NewLine); LogPath = $logPath }
}

try {
    if (-not (Get-Command uip -ErrorAction SilentlyContinue)) {
        Add-Finding "WIN001" "error" "UiPath CLI was not found in the current Windows user PATH." "compile"
        $compileStatus = "blocked"
        $exitCode = 3
        throw "UiPath CLI not found"
    }

    New-Item -ItemType Directory -Path $localProject -Force | Out-Null
    New-Item -ItemType Directory -Path $localResults -Force | Out-Null
    New-Item -ItemType Directory -Path $hostResults -Force | Out-Null
    $hostProject = Join-Path $HostJobPath "project"
    Get-ChildItem -LiteralPath $hostProject -Force | Copy-Item -Destination $localProject -Recurse -Force

    $projectJsonPath = Join-Path $localProject "project.json"
    if (-not (Test-Path -LiteralPath $projectJsonPath)) {
        Add-Finding "WIN002" "error" "Snapshot does not contain project.json." "compile"
        $compileStatus = "failed"
        $exitCode = 2
        throw "project.json missing"
    }
    $project = Get-Content -LiteralPath $projectJsonPath -Raw | ConvertFrom-Json
    $uipVersion = (& uip --version 2>&1 | Out-String).Trim()

    $restore = Invoke-UipCommand "restore" @("rpa", "restore", $localProject, "--output", "json")
    if ($restore.ExitCode -ne 0) {
        Add-Finding "WIN003" "error" "UiPath dependency restore failed." "compile" $restore.Output
        $compileStatus = "failed"
        $exitCode = 1
    }
    else {
        $build = Invoke-UipCommand "build" @("rpa", "build", $localProject, "--output", "json")
        if ($build.ExitCode -ne 0) {
            Add-Finding "WIN004" "error" "UiPath project build failed." "compile" $build.Output
            $compileStatus = "failed"
            $exitCode = 1
        }
        else {
            $compileStatus = "passed"
        }
    }

    if ($compileStatus -eq "passed" -and $request.mode -eq "build-and-test") {
        $requestedTests = @($request.tests.paths)
        if ($request.tests.selection -eq "all") {
            $requestedTests = @($project.designOptions.fileInfoCollection | Where-Object { $_.testCaseId } | ForEach-Object { $_.fileName })
        }
        if ($requestedTests.Count -eq 0) {
            $executionStatus = "not_run"
            Add-Finding "WIN005" "warning" "No test workflows matched the requested selection." "execution"
        }
        else {
            $executionStatus = "passed"
            foreach ($testPathValue in $requestedTests) {
                $normalizedTestPath = $testPathValue -replace "\\", [IO.Path]::DirectorySeparatorChar
                $testPath = Join-Path $localProject $normalizedTestPath
                if (-not (Test-Path -LiteralPath $testPath)) {
                    $tests.Add([pscustomobject]@{ path = $testPathValue; status = "failed"; message = "Test file does not exist" })
                    Add-Finding "WIN006" "error" ("Selected test does not exist: " + $testPathValue) "execution"
                    $executionStatus = "failed"
                    $exitCode = 1
                    continue
                }
                $safeName = ([IO.Path]::GetFileNameWithoutExtension($testPath) -replace "[^A-Za-z0-9_-]", "_")
                $testResult = Invoke-UipCommand ("test-" + $safeName) @("rpa", "run-file", "--file-path", $testPath, "--command", "StartExecution", "--skip-build", "--output", "json")
                $status = if ($testResult.ExitCode -eq 0) { "passed" } else { "failed" }
                $tests.Add([pscustomobject]@{ path = $testPathValue; status = $status; exit_code = $testResult.ExitCode })
                if ($testResult.ExitCode -ne 0) {
                    Add-Finding "WIN007" "error" ("UiPath test execution failed: " + $testPathValue) "execution" $testResult.Output
                    $executionStatus = "failed"
                    $exitCode = 1
                }
            }
        }
    }
    elseif ($compileStatus -eq "passed" -and $request.mode -eq "run-workflow") {
        if (-not $request.allow_side_effects) {
            Add-Finding "WIN008" "error" "Workflow execution was refused because allow_side_effects is false." "execution"
            $executionStatus = "blocked"
            $exitCode = 4
        }
        else {
            $mainPath = Join-Path $localProject $project.main
            $run = Invoke-UipCommand "run-workflow" @("rpa", "run-file", "--file-path", $mainPath, "--command", "StartExecution", "--skip-build", "--output", "json")
            $executionStatus = if ($run.ExitCode -eq 0) { "passed" } else { "failed" }
            if ($run.ExitCode -ne 0) {
                Add-Finding "WIN009" "error" "UiPath workflow execution failed." "execution" $run.Output
                $exitCode = 1
            }
        }
    }

    $result = [ordered]@{
        schema = "uipath-validation-result/v1"
        job_id = $request.job_id
        project = [ordered]@{
            name = $project.name
            target_framework = $project.targetFramework
            expression_language = $project.expressionLanguage
        }
        environment = [ordered]@{
            host_os = "macOS"
            runner = "parallels"
            guest_os = [Environment]::OSVersion.VersionString
            uip_version = $uipVersion
        }
        gates = [ordered]@{
            static = @{ status = "not_run" }
            compile = @{ status = $compileStatus }
            execution = @{ status = $executionStatus }
            uat = @{ status = "not_run" }
        }
        findings = @($findings)
        tests = @($tests)
        artifacts = @($artifacts)
        started_at = $startedAt
        finished_at = [DateTime]::UtcNow.ToString("o")
    }
    $resultPath = Join-Path $localResults "validation-result.json"
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $resultPath -Encoding UTF8
    Get-ChildItem -LiteralPath $localResults -Force | Copy-Item -Destination $hostResults -Force
}
catch {
    if (-not (Test-Path -LiteralPath $hostResults)) {
        New-Item -ItemType Directory -Path $hostResults -Force | Out-Null
    }
    $fallback = [ordered]@{
        schema = "uipath-validation-result/v1"
        job_id = $request.job_id
        project = @{ name = "unknown" }
        environment = @{ host_os = "macOS"; runner = "parallels" }
        gates = @{
            static = @{ status = "not_run" }
            compile = @{ status = $(if ($compileStatus -eq "not_run") { "blocked" } else { $compileStatus }) }
            execution = @{ status = $executionStatus }
            uat = @{ status = "not_run" }
        }
        findings = @($findings) + @([pscustomobject]@{ code = "WIN010"; severity = "error"; message = $_.Exception.Message; gate = "compile" })
        tests = @($tests)
        artifacts = @($artifacts)
        started_at = $startedAt
        finished_at = [DateTime]::UtcNow.ToString("o")
    }
    $fallback | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $hostResults "validation-result.json") -Encoding UTF8
    if ($exitCode -eq 0) { $exitCode = 2 }
}
finally {
    if (-not $request.keep_job -and (Test-Path -LiteralPath $localJobRoot)) {
        Remove-Item -LiteralPath $localJobRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

exit $exitCode
