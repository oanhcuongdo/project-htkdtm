<#
  Đăng ký (hoặc gỡ) tác vụ Windows chạy pipeline EduVision BI mỗi ngày.

  Ví dụ (PowerShell, chạy từ thư mục gốc kho hoặc bất kỳ đâu):
    .\nhom03-65httt\src\etl\schedule\register_daily_task.ps1                 # đăng ký, chạy 02:00 mỗi ngày
    .\nhom03-65httt\src\etl\schedule\register_daily_task.ps1 -Time "20:30"   # đổi giờ chạy
    .\nhom03-65httt\src\etl\schedule\register_daily_task.ps1 -WhatIf         # chỉ xem sẽ làm gì
    .\nhom03-65httt\src\etl\schedule\register_daily_task.ps1 -Remove         # gỡ tác vụ

  Tác vụ chạy: python src\etl\run_pipeline.py --count 100
  - StartWhenAvailable: máy tắt hoặc ngủ đúng giờ thì chạy bù khi bật lại.
  - Cần Docker Desktop đang chạy (PostgreSQL ở 127.0.0.1:5432) khi tác vụ chạy.
  Nhật ký mỗi vòng: nhom03-65httt\data\logs\pipeline_runs.jsonl (ngoài Git).
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Time = "02:00",
    [string]$TaskName = "EduVisionBI-Pipeline",
    [int]$Count = 100,
    [switch]$Remove
)

$ErrorActionPreference = "Stop"

if ($Remove) {
    if ($PSCmdlet.ShouldProcess($TaskName, "Gỡ tác vụ")) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Đã gỡ tác vụ $TaskName"
    }
    return
}

$python = (Get-Command python -ErrorAction Stop).Source
$script = (Resolve-Path (Join-Path $PSScriptRoot "..\run_pipeline.py")).Path
$workDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path   # thư mục nhom03-65httt

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`" --count $Count" -WorkingDirectory $workDir
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2) -MultipleInstances IgnoreNew

if ($PSCmdlet.ShouldProcess($TaskName, "Đăng ký tác vụ chạy hằng ngày lúc $Time")) {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
        -Description "EduVision BI: thu thập đánh giá mới và nạp ETL mỗi ngày (nhom03-65httt)" -Force | Out-Null
    Write-Host "Đã đăng ký $TaskName lúc $Time mỗi ngày."
    Write-Host "Chạy thử ngay: Start-ScheduledTask -TaskName $TaskName"
    Write-Host "Xem bằng chứng:  python `"$script`" --report"
}
