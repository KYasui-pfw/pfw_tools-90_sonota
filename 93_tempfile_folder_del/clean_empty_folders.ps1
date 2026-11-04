<#
.SYNOPSIS
  D:\TempFile 配下の「どこまでたどってもファイルが無い」古い空フォルダを削除する。

.DESCRIPTION
  fsrm が3か月経過ファイルを移動したあとに残る空フォルダの掃除用。
  フォルダが削除対象になる条件（すべて満たすこと）:
    - 直下にファイルが無い（隠し・システムファイルも含めて判定）
    - サブフォルダがある場合は、そのすべてが削除対象
    - 更新日時が「今日 - Months か月」より前
  判定は開始時点のスナップショットで行い、深い階層から順に削除する。
  そのため子が消えた結果として親が空になるケースも、同じ回でまとめて削除できる。
  削除は非再帰（Directory.Delete(path, false)）。判定漏れでファイルが残っていても巻き込まない。
  ジャンクション／シンボリックリンクは辿らず、「空ではない」扱いにして残す。
  Root 自体は削除しない。

.PARAMETER Root
  掃除対象のルート。既定 D:\TempFile

.PARAMETER Months
  更新日時がこの月数より古いフォルダのみ対象。既定 3

.PARAMETER DryRun
  削除せず、対象一覧をログに出すだけ。

.PARAMETER LogDir
  ログ出力先。既定はこのスクリプトと同じ場所の logs フォルダ。

.PARAMETER LogKeepDays
  ログの保持日数。既定 7

.EXAMPLE
  .\run.bat -DryRun        # 対象の確認のみ
  .\run.bat                # 本番（タスクスケジューラはこれ）

.NOTES
  終了コード: 0=正常 / 1=エラーあり（フォルダ無し・列挙失敗・削除失敗など）
  文字コード: UTF-8 BOM 付き・CRLF で保存すること（Windows PowerShell 5.1 向け）
#>
[CmdletBinding()]
param(
    [string]$Root = 'D:\TempFile',
    [int]$Months = 3,
    [switch]$DryRun,
    [string]$LogDir = '',
    [int]$LogKeepDays = 7
)

$ErrorActionPreference = 'Stop'
# $PSScriptRoot は古い PowerShell で param 既定値に使えないため、本体内で求める
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $LogDir) { $LogDir = Join-Path $ScriptDir 'logs' }
$Utf8Bom = New-Object System.Text.UTF8Encoding($true)
$script:LogFile = $null
$script:ErrorCount = 0
$script:Cutoff = $null
$script:Targets = New-Object 'System.Collections.Generic.List[System.IO.DirectoryInfo]'

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    Write-Host $line
    if ($script:LogFile) {
        try { [System.IO.File]::AppendAllText($script:LogFile, $line + "`r`n", $Utf8Bom) } catch { }
    }
}

# 配下にファイルが無く、かつ古い（= 削除対象）なら $true を返す。
# 削除対象のフォルダは子→親の順（深い順）で $script:Targets に積む。
function Test-EmptyTree {
    param([System.IO.DirectoryInfo]$Dir, [bool]$IsRoot)

    $ok = $true
    try {
        if ($Dir.GetFiles().Length -gt 0) { $ok = $false }
        foreach ($sub in $Dir.GetDirectories()) {
            if (($sub.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                # ジャンクション等は辿らず、残す
                Write-Log "リパースポイントのためスキップ: $($sub.FullName)" 'WARN'
                $ok = $false
                continue
            }
            if (-not (Test-EmptyTree -Dir $sub -IsRoot $false)) { $ok = $false }
        }
    }
    catch {
        # 列挙できないフォルダは安全側（削除しない）に倒す
        Write-Log "列挙に失敗したためスキップ: $($Dir.FullName) : $($_.Exception.Message)" 'ERROR'
        $script:ErrorCount++
        return $false
    }

    if ($IsRoot) { return $false }
    if ($Dir.LastWriteTime -ge $script:Cutoff) { $ok = $false }
    if ($ok) { [void]$script:Targets.Add($Dir) }
    return $ok
}

try {
    # --- ログ準備 ---
    if (-not (Test-Path -LiteralPath $LogDir)) {
        [void](New-Item -ItemType Directory -Path $LogDir -Force)
    }
    $script:LogFile = Join-Path $LogDir ('log_{0}.txt' -f (Get-Date -Format 'yyyyMMdd'))
    Get-ChildItem -LiteralPath $LogDir -Filter 'log_*.txt' |
        Where-Object { -not $_.PSIsContainer -and $_.LastWriteTime -lt (Get-Date).AddDays(-$LogKeepDays) } |
        Remove-Item -Force

    $mode = if ($DryRun) { 'DRYRUN' } else { 'LIVE' }
    Write-Log "開始 mode=$mode Root=$Root Months=$Months"

    # --- 事前チェック ---
    if ($Months -lt 1) { throw "Months は1以上を指定してください: $Months" }
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) {
        throw "Root が見つかりません: $Root"
    }
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\')
    if ($rootFull -match '^[A-Za-z]:$') {
        throw "ドライブ直下は指定できません: $Root"
    }

    # --- 走査（スナップショット）---
    $script:Cutoff = (Get-Date).AddMonths(-$Months)
    Write-Log ('基準日時: {0:yyyy-MM-dd HH:mm:ss} より前に更新されたフォルダが対象' -f $script:Cutoff)

    $rootDir = New-Object System.IO.DirectoryInfo($rootFull)
    [void](Test-EmptyTree -Dir $rootDir -IsRoot $true)
    Write-Log "削除対象: $($script:Targets.Count) 件"

    # --- 削除（深い順）---
    $deleted = 0
    foreach ($d in $script:Targets) {
        $info = '{0} (更新: {1:yyyy-MM-dd HH:mm})' -f $d.FullName, $d.LastWriteTime
        if ($DryRun) {
            Write-Log "[DRYRUN] 削除対象: $info"
            continue
        }
        try {
            [System.IO.Directory]::Delete($d.FullName, $false)
            Write-Log "削除: $info"
            $deleted++
        }
        catch [System.IO.IOException] {
            # 走査後に何かが置かれた等。中身は消さずに残す
            Write-Log "空ではなくなったためスキップ: $($d.FullName) : $($_.Exception.Message)" 'WARN'
        }
        catch {
            Write-Log "削除に失敗: $($d.FullName) : $($_.Exception.Message)" 'ERROR'
            $script:ErrorCount++
        }
    }

    if ($DryRun) {
        Write-Log "終了 (DryRun: 削除なし) 対象=$($script:Targets.Count) エラー=$($script:ErrorCount)"
    } else {
        Write-Log "終了 削除=$deleted / 対象=$($script:Targets.Count) エラー=$($script:ErrorCount)"
    }
    if ($script:ErrorCount -gt 0) { exit 1 }
    exit 0
}
catch {
    Write-Log "致命的エラー: $($_.Exception.Message)" 'ERROR'
    exit 1
}
