# 内作工程チェック「簡易マスタ未登録 > rBOMにのみ存在」のうち SEINO が空欄の行を抽出して CSV に出し、rBOM の画面操作（RPA）を行う。
# 元: ../app.py の fetch_rbom_only()。RPA の入力にする。
#
# 実行条件: rBOM の夜間処理が終わっている（http://rbom-yakan/yakan.csv の1列目が 5）ときだけ。それ以外は何もせずに終わる
#
# 抽出条件（すべて AND）
#   - M0810.HMBUNCD = '7'（マシニング品目）
#   - M0810.INSTDT >= 基準日、または D3110 に INSTDT >= 基準日 の行がある
#     （D3110 は D3030 製番実績に載っている＝完納済みの製番の行を数えない。app.py には無い条件）
#   - M0840 に SRCD = '40' の行が無い
#   - Django 品目工程マスタ（KRD DATA_RES_CAPA の写し）の品目CDと前方一致しない
#   - HMCD が L / Z- / KF20 で始まらない
#
# ⚠ app.py と違う点: 照合は「どれか1つの品目CDに一致すれば登録済み」として全件を見る。
#   app.py の find_match() は品目CDごとに最初の1件しか登録済みにせず、空欄の品目CDが何にでも一致していた。
#
# 実行: powershell -ExecutionPolicy Bypass -File .\01_未登録品目抽出.ps1
# ⚠ このファイルは UTF-8（BOM付き）で保存すること。BOM が無いと PowerShell 5.1 で日本語が化ける。
# ⚠ psql.exe の場所と Postgres のパスワードはスクリプトに書かない。同じフォルダの config.ini に書く:
#     [postgres]
#     psql=C:\Program Files\PostgreSQL\16\bin\psql.exe
#     password=xxxxx
#   RPA で起動するプログラムとログイン情報も同じ config.ini に書く:
#     [rpa]
#     program=起動するファイルのフルパス
#     window_title=ログイン画面のタイトルに含まれる文字
#     login_id=xxxxx
#     login_password=xxxxx

$ErrorActionPreference = 'Stop'

# ── 設定 ────────────────────────────────────────────
$INSTDT_THRESHOLD = '2026-03-24'   # app.py の INSTDT_THRESHOLD と同じ値にする

$API_URL = 'http://pfw-api/query'
$API_KEY = 'oG5^Ls%#20yq'

$PG_HOST = '172.17.85.101'          # pfw-gyomu（esrv11）の Django 用 PostgreSQL
$PG_PORT = '5432'
$PG_DB   = 'pfw_django'
$PG_USER = 'pfw'

$CHUNK = 1000                       # Oracle の IN 句は最大1000個（ORA-01795）

# config.ini の [セクション] キー=値 を読む（値に = を含んでもよいよう、最初の = で分ける）
function Get-IniValue($sectionName, $key) {
    $path = Join-Path $PSScriptRoot 'config.ini'
    if (-not (Test-Path $path)) { throw "config.ini がありません: $path" }
    $section = ''
    foreach ($line in Get-Content $path -Encoding UTF8) {
        $t = $line.Trim()
        if ($t -match '^\[(.+)\]$') { $section = $Matches[1].Trim(); continue }
        if ($section -eq $sectionName -and $t -match "^$([regex]::Escape($key))\s*=(.*)$") { return $Matches[1].Trim() }
    }
    throw "config.ini に [$sectionName] の $key がありません: $path"
}

# ── 実行条件: rBOM の夜間処理が終わっていること ──────────
# 73_ログ監視 が書き出す yakan.csv（例: 「5,夜間処理終了」）の1列目が 5 のときだけ実行する。
# 画面 http://rbom-yakan/yakan_monitor.html もこのファイルを表示している。72_1 の 00_wait_yakan.py と同じ判定。
# ⚠ 72_1 と違い、5 になるまで待たない。起動したときに1回だけ見て、5 でなければ何もせずに終わる。
$YAKAN_URL = 'http://rbom-yakan/yakan.csv'
$YAKAN_DONE = '5'
$EXIT_YAKAN_UNKNOWN = 3             # 夜間処理の状態が取れなかったときの終了コード（bat はこのとき止まらない）
try {
    $res = Invoke-WebRequest -Uri $YAKAN_URL -UseBasicParsing -TimeoutSec 10
    $yakanLine = ([Text.Encoding]::UTF8.GetString($res.RawContentStream.ToArray()) -split "`r?`n")[0].Trim()
} catch {
    # 状態が分からないときは、夜間処理中かもしれないので実行しない
    $msg = "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) [夜間処理の確認] 状態を取得できなかったため実行しませんでした: $($_.Exception.Message)"
    [IO.File]::AppendAllText((Join-Path $PSScriptRoot 'エラーログ.txt'), $msg + "`r`n", (New-Object Text.UTF8Encoding $true))
    Write-Host $msg
    exit $EXIT_YAKAN_UNKNOWN
}
if ($yakanLine.Split(',')[0].Trim() -ne $YAKAN_DONE) {
    Write-Host "夜間処理が終わっていないため、実行せずに終了します（状態: $yakanLine）"
    exit 0
}
Write-Host "夜間処理の状態: $yakanLine"

# ── rBOM（FastAPI /query） ───────────────────────────
function Invoke-Query($body) {
    $json = $body | ConvertTo-Json -Depth 10 -Compress
    Invoke-RestMethod -Uri $API_URL -Method Post -Headers @{ 'X-API-KEY' = $API_KEY } `
        -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($json))
}

# 1万件ずつページングして全件取る（ページングは order_by 必須）
function Get-AllRows($table, $columns, $where, $orderBy) {
    $rows = New-Object System.Collections.Generic.List[object]
    $offset = 0
    do {
        $r = Invoke-Query @{ table = $table; columns = $columns; where = $where; order_by = $orderBy; limit = 10000; offset = $offset }
        foreach ($row in $r.rows) { $rows.Add($row) }
        $offset += 10000
    } while ($r.row_count -eq 10000)
    return , $rows
}

# 値の一覧を1000個ずつに分けて「$column IN (...)」で検索し、全行を返す
# ⚠ 変数名は大文字小文字を区別しないので、ここで $chunk という名前を使うと設定の $CHUNK を上書きする
function Get-RowsByIn($table, $column, $values, $columns, $extraWhere) {
    $rows = New-Object System.Collections.Generic.List[object]
    for ($i = 0; $i -lt $values.Count; $i += $CHUNK) {
        $part = @($values[$i..([Math]::Min($i + $CHUNK, $values.Count) - 1)])
        $conds = @(@{ $column = @{ in = $part } })
        if ($extraWhere) { $conds += $extraWhere }
        foreach ($row in (Get-AllRows $table $columns @{ and = $conds } $columns)) { $rows.Add($row) }
    }
    return , $rows
}

# ── Django 品目工程マスタ（psql） ──────────────────────
function Get-DjangoItemCodes {
    # 工順が空欄の行は「新規登録が必要な品目」として足された行なので、登録済みに数えない
    $sql = 'SELECT DISTINCT final_item_code FROM machining_schedule_simplemasterrow ' +
           "WHERE process_order IS NOT NULL AND final_item_code <> ''"
    $prevEnc = [Console]::OutputEncoding
    [Console]::OutputEncoding = [Text.Encoding]::UTF8
    $env:PGCLIENTENCODING = 'UTF8'
    $psql = Get-IniValue 'postgres' 'psql'
    if (-not (Test-Path $psql)) { throw "psql.exe が見つかりません（config.ini の psql を確認）: $psql" }
    $env:PGPASSWORD = Get-IniValue 'postgres' 'password'
    try {
        $out = & $psql -h $PG_HOST -p $PG_PORT -U $PG_USER -d $PG_DB -w -X -q -A -t -v ON_ERROR_STOP=1 -c $sql
        if ($LASTEXITCODE -ne 0) { throw "psql が失敗しました（終了コード $LASTEXITCODE）" }
    } finally {
        [Console]::OutputEncoding = $prevEnc
        Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    }
    return @($out | Where-Object { $_ -and $_.Trim() })
}

# ピリオド除去・非数字直後の先頭ゼロ除去（app.py の normalize() と同じ）
function ConvertTo-NormalizedCode($code) {
    if ($null -eq $code) { return '' }
    $s = ([string]$code).Replace('.', '').Trim()
    return [regex]::Replace($s, '(?<!\d)0+(\d)', '$1')
}

# ── 抽出 ────────────────────────────────────────────
Write-Host 'M0810 取得中...'
$m0810 = Get-AllRows 'M0810' @('HMCD', 'HMNM', 'INSTDT') @{ HMBUNCD = '7' } @('HMCD')
# INSTDT を「yyyy-MM-dd HH:mm:ss」の文字列にそろえる（基準日と文字列で比べるため）。
# ⚠ PowerShell 7 は JSON の日付文字列を勝手に日付型に変える（5.1 は文字列のまま）。
#   日付型のまま文字列にすると「10/07/2026 …」の形になり、比較が崩れて 0 件になった（試験で確認）。
foreach ($row in $m0810) {
    if ($row.INSTDT -is [datetime]) {
        $row.INSTDT = $row.INSTDT.ToString('yyyy-MM-dd HH:mm:ss', [Globalization.CultureInfo]::InvariantCulture)
    } elseif ($row.INSTDT) {
        $row.INSTDT = ([string]$row.INSTDT).Replace('T', ' ')
    }
}
Write-Host "  HMBUNCD=7: $($m0810.Count) 件"

$candidates = @($m0810 | Where-Object { $_.HMCD -notmatch '^(L|Z-|KF20)' })
Write-Host "  L / Z- / KF20 始まりを除外: $($candidates.Count) 件"

Write-Host 'Django 品目工程マスタ取得中...'
$finalCodes = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($c in Get-DjangoItemCodes) {
    $n = ConvertTo-NormalizedCode $c
    if ($n) { [void]$finalCodes.Add($n) }
}
Write-Host "  品目CD: $($finalCodes.Count) 件"
# 前方一致 = HMCD（正規化後）の先頭 1〜全文字のどれかが品目CDの集合にある
$candidates = @($candidates | Where-Object {
    $h = ConvertTo-NormalizedCode $_.HMCD
    $hit = $false
    for ($len = 1; $len -le $h.Length -and -not $hit; $len++) { $hit = $finalCodes.Contains($h.Substring(0, $len)) }
    -not $hit
})
Write-Host "  品目工程マスタ登録済みを除外: $($candidates.Count) 件"

Write-Host 'M0840（SRCD=40）確認中...'
$srcd40 = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($row in (Get-RowsByIn 'M0840' 'HMCD' @($candidates | ForEach-Object { $_.HMCD }) @('HMCD') @{ SRCD = '40' })) {
    [void]$srcd40.Add($row.HMCD)
}
$candidates = @($candidates | Where-Object { -not $srcd40.Contains($_.HMCD) })
Write-Host "  SRCD=40 ありを除外: $($candidates.Count) 件"

# M0810 の登録日が基準日より前の品目は、D3110 に基準日以降の行があるものだけ残す。
# ただし D3030（製番実績）に載っている製番は完納済みでもう使わないので、その製番の行は数えない。
Write-Host 'D3110 確認中...'
$old = @($candidates | Where-Object { -not ($_.INSTDT -and [string]$_.INSTDT -ge $INSTDT_THRESHOLD) })
$d3110 = Get-RowsByIn 'D3110' 'HMCD' @($old | ForEach-Object { $_.HMCD }) @('HMCD', 'SEINO') @{ INSTDT = @{ gte = $INSTDT_THRESHOLD } }
$seinos = @($d3110 | Where-Object { $_.SEINO } | ForEach-Object { $_.SEINO } | Sort-Object -Unique)
$completed = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($row in (Get-RowsByIn 'D3030' 'SEINO' $seinos @('SEINO') $null)) { [void]$completed.Add($row.SEINO) }
$inD3110 = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($row in $d3110) {
    if (-not $row.SEINO -or -not $completed.Contains($row.SEINO)) { [void]$inD3110.Add($row.HMCD) }
}
$doneOnly = @($d3110 | ForEach-Object { $_.HMCD } | Sort-Object -Unique | Where-Object { -not $inD3110.Contains($_) }).Count
Write-Host "  D3110 の製番 $($seinos.Count) 件のうち完納済み(D3030あり) $($completed.Count) 件 → 完納済み製番にしか出ない品目 $doneOnly 件を除外"
$result = @($candidates | Where-Object {
    ($_.INSTDT -and [string]$_.INSTDT -ge $INSTDT_THRESHOLD) -or $inD3110.Contains($_.HMCD)
} | ForEach-Object {
    [pscustomobject]@{
        'HMCD'        = $_.HMCD
        'HMNM'        = $_.HMNM
        'M0810登録日' = ([string]$_.INSTDT).Replace('T', ' ')
        '抽出理由'    = $(if ($_.INSTDT -and [string]$_.INSTDT -ge $INSTDT_THRESHOLD) { 'M0810新規' } else { 'D3110に出現' })
    }
})
Write-Host "抽出結果: $($result.Count) 件"

# 抽出結果を CSV に出す（毎回上書き。Excel で開けるよう UTF-8 BOM付き。PowerShell 5.1 と 7 で同じになるよう自前で書く）
$csvPath = Join-Path $PSScriptRoot '抽出結果.csv'
$csvLines = @($result | ConvertTo-Csv -NoTypeInformation)
if ($csvLines.Count -eq 0) { $csvLines = @('"HMCD","HMNM","M0810登録日","抽出理由"') }   # 0件でも見出しだけは出す
[IO.File]::WriteAllLines($csvPath, [string[]]$csvLines, (New-Object Text.UTF8Encoding $true))
Write-Host "CSV 出力: $csvPath"

# 0件なら RPA は起動せずに終わる（終了コード 0）
if ($result.Count -eq 0) {
    Write-Host '抽出結果が 0 件のため、RPA は行わずに終了します'
    exit 0
}

# ── RPA ─────────────────────────────────────────────
# CSV を出したらそのまま始まる。キーは「その時いちばん手前にある画面」に送られるので、実行中はマウス・キーボードに触らない。
Add-Type -AssemblyName System.Windows.Forms
Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class RpaWin32 {
    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    [DllImport("user32.dll")] static extern uint MapVirtualKey(uint code, uint mapType);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern short VkKeyScan(char ch);
    const uint KEYUP = 0x2, EXTENDED = 0x1;
    const int HOLD_MS = 30;             // 押してから離すまで
    // 矢印・Insert・Delete・Home・End・PageUp・PageDown は「拡張キー」の印が要る
    // （付けないとテンキー側のキーと取り違えられ、NumLock の状態によっては数字が入る）
    static bool IsExtended(byte vk) { return (vk >= 0x21 && vk <= 0x28) || vk == 0x2D || vk == 0x2E; }
    static void Down(byte vk) { keybd_event(vk, (byte)MapVirtualKey(vk, 0), IsExtended(vk) ? EXTENDED : 0, UIntPtr.Zero); }
    static void Up(byte vk) { keybd_event(vk, (byte)MapVirtualKey(vk, 0), (IsExtended(vk) ? EXTENDED : 0) | KEYUP, UIntPtr.Zero); }
    // キーを1回押して離す（vk = 仮想キーコード）
    public static void Press(byte vk) {
        Down(vk); System.Threading.Thread.Sleep(HOLD_MS); Up(vk);
    }
    // 文字を1文字ずつ打つ。押すキーと Shift の要否はキーボード配列から割り出す（例: # → Shift＋3）
    public static void Type(string text) {
        foreach (char c in text) {
            short r = VkKeyScan(c);
            if (r == -1) throw new ArgumentException("キーボードで打てない文字です: " + c);
            byte vk = (byte)(r & 0xFF);
            int mods = (r >> 8) & 0xFF;        // 1 = Shift、2 = Ctrl、4 = Alt
            if ((mods & 1) != 0) Down(0x10);
            if ((mods & 2) != 0) Down(0x11);
            if ((mods & 4) != 0) Down(0x12);
            Press(vk);
            if ((mods & 4) != 0) Up(0x12);
            if ((mods & 2) != 0) Up(0x11);
            if ((mods & 1) != 0) Up(0x10);
            System.Threading.Thread.Sleep(50);
        }
    }
    // 見えているウィンドウのタイトルを全部返す
    public static List<string> VisibleTitles() {
        var list = new List<string>();
        EnumWindows((h, l) => {
            if (IsWindowVisible(h)) {
                var sb = new StringBuilder(512);
                if (GetWindowText(h, sb, sb.Capacity) > 0) list.Add(sb.ToString());
            }
            return true;
        }, IntPtr.Zero);
        return list;
    }
}
// 画面が見つからなかったとき専用の例外（ほかのエラーと分けて、終了処理をしてから終わるため）
public class WindowNotFoundException : Exception {
    public WindowNotFoundException(string message) : base(message) { }
}
'@

$STARTUP_WAIT_SEC = 10              # プログラム起動からログイン入力までの待ち
$AFTER_CLOSE_WAIT_SEC = 5           # 終了処理のあと、プロセスが残っているか見るまでの待ち
$AFTER_LOGIN_WAIT_SEC = 5           # ログインから本番環境の画面を操作するまでの待ち
$WINDOW_TIMEOUT_SEC = 30            # 画面が出てくるのを待つ上限
$KEY_INTERVAL_MS = 500             # キーを1回押すごとの間隔（指定が無いキーはすべてこれ）

$ERROR_LOG = Join-Path $PSScriptRoot 'エラーログ.txt'   # 追記していく（消さない）
$EXIT_WINDOW_NOT_FOUND = 2          # 画面が見つからず終了処理をして終わったときの終了コード（bat はこのとき止まらない）

$wshell = New-Object -ComObject WScript.Shell
$script:step = ''                   # いまの処理段階（エラーログに書く）

function Write-ErrorLog($message) {
    $line = "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) [$script:step] $message"
    [IO.File]::AppendAllText($ERROR_LOG, $line + "`r`n", (New-Object Text.UTF8Encoding $true))
    Write-Host "エラーログに記録: $line"
}

# ⚠ キーは .NET の SendKeys を使わず、Windows に直接「押す・離す」を送る（RpaWin32.Press / Type）。
#   SendKeys は管理者権限で動くと古い「ジャーナル再生」で送られ、キーが二重に入ったり抜けたりした
#   （RPA サーバーで TAB 8回が9回になった。一時的に入れたキー入力の記録に SendKeys のキーが1つも映らないことで判明 2026-10-08。記録の仕組みは解決後に外した）。

# 名前 → 仮想キーコード
$VK = @{
    'ALT' = 0x12; 'TAB' = 0x09; 'ENTER' = 0x0D; 'BACKSPACE' = 0x08; 'ESC' = 0x1B
    'LEFT' = 0x25; 'UP' = 0x26; 'RIGHT' = 0x27; 'DOWN' = 0x28
    'F1' = 0x70; 'F2' = 0x71; 'F3' = 0x72; 'F4' = 0x73; 'F5' = 0x74; 'F6' = 0x75
    'F7' = 0x76; 'F8' = 0x77; 'F9' = 0x78; 'F10' = 0x79; 'F11' = 0x7A; 'F12' = 0x7B
}

# 文字をそのまま打つ（1文字ずつ。# などは Shift を付けて押す）
function Send-Text($text) {
    [RpaWin32]::Type($text)
    Start-Sleep -Milliseconds $KEY_INTERVAL_MS
}
# 特殊キーを押す（例: Send-Key 'RIGHT' 3）。'ALT' は単独押し
function Send-Key($name, [int]$count = 1) {
    if (-not $VK.ContainsKey($name)) { throw "キー名が登録されていません: $name（`$VK に足すこと）" }
    for ($i = 0; $i -lt $count; $i++) {
        [RpaWin32]::Press([byte]$VK[$name])
        Start-Sleep -Milliseconds $KEY_INTERVAL_MS
    }
}
# タイトルに $part を含む画面を探して手前に出す。出てくるまで最大 $WINDOW_TIMEOUT_SEC 秒待つ。
# 見つからなければ WindowNotFoundException を投げる（別の画面にキーを送らないため）。
# 受け取った側（下の try/catch）がエラーログを書き、終了処理をしてから終わる
function Set-ActiveWindow($part) {
    for ($i = 0; $i -lt $WINDOW_TIMEOUT_SEC; $i++) {
        $title = [RpaWin32]::VisibleTitles() | Where-Object { $_.Contains($part) } | Select-Object -First 1
        if ($title -and $wshell.AppActivate($title)) {
            Write-Host "画面をアクティブにしました: $title"
            Start-Sleep -Milliseconds 500
            return
        }
        Start-Sleep -Seconds 1
    }
    throw (New-Object WindowNotFoundException "「$part」をタイトルに含む画面が見つかりません（$WINDOW_TIMEOUT_SEC 秒待ちました）")
}
# プログラムの終了（BackSpace×10 → ALT → → → ↑↑ → Enter → → → Enter）
# 画面はアクティブにしない（利用者の指示）。いまアクティブな画面にそのまま送る
function Close-Program {
    $script:step = 'プログラム終了'
    Write-Host 'プログラム終了'
    Send-Key 'BACKSPACE' 10
    Send-Key 'ALT'
    Send-Key 'RIGHT'
    Send-Key 'UP' 2
    Send-Key 'ENTER'
    Send-Key 'RIGHT'
    Send-Key 'ENTER'
}
# 終了処理のあと、プロセスが残っていたら強制終了する。次の2つが対象:
#   (1) rbom.exe（realtime BOM 本体）はすべて。⚠ RPA が起動したもの以外（手で開いた rBOM）も巻き込む（利用者の指示）
#   (2) RPA が起動した DLRUN.exe（program）とその子・孫。DLRUN.exe は rbom.exe を起動してすぐ終わるが、
#       rbom.exe 側には親として DLRUN のプロセス番号が残るので、親子関係をたどって探す。
#       プロセス番号の使い回しで無関係なものを拾わないよう、起動した時刻より後にできたものだけを対象にする。
$RBOM_PROCESS_NAME = 'rbom'         # (1) の対象（拡張子なし）
function Stop-LeftoverProcess {
    Start-Sleep -Seconds $AFTER_CLOSE_WAIT_SEC
    foreach ($p in @(Get-Process -Name $RBOM_PROCESS_NAME -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
        Write-ErrorLog "終了処理のあとも rBOM が残っていたため強制終了しました: $($p.ProcessName).exe（PID $($p.Id)）"
    }
    if (-not $proc) { return }
    $all = @(Get-CimInstance Win32_Process)
    $ids = New-Object 'System.Collections.Generic.HashSet[int]'
    [void]$ids.Add($proc.Id)
    do {
        $added = $false
        foreach ($p in $all) {
            if ($ids.Contains([int]$p.ParentProcessId) -and -not $ids.Contains([int]$p.ProcessId) -and $p.CreationDate -ge $launchedAt) {
                [void]$ids.Add([int]$p.ProcessId); $added = $true
            }
        }
    } while ($added)
    foreach ($p in $all | Where-Object { $ids.Contains([int]$_.ProcessId) -and $_.CreationDate -ge $launchedAt }) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-ErrorLog "終了処理のあともプロセスが残っていたため強制終了しました: $($p.Name)（PID $($p.ProcessId)）"
    }
}

$program = Get-IniValue 'rpa' 'program'
if (-not $program -or -not (Test-Path $program)) { throw "起動するプログラムが見つかりません（config.ini の [rpa] program を確認）: $program" }
$loginId = Get-IniValue 'rpa' 'login_id'
$loginPassword = Get-IniValue 'rpa' 'login_password'

Write-Host "プログラム起動: $program"
$launchedAt = (Get-Date).AddSeconds(-1)
$proc = Start-Process -FilePath $program -WorkingDirectory (Split-Path $program -Parent) -PassThru
Write-Host "$STARTUP_WAIT_SEC 秒待機..."
Start-Sleep -Seconds $STARTUP_WAIT_SEC

try {
    # ログイン画面を手前に出す。
    # ⚠ プロセス番号では、bat・ショートカット経由の起動だと別プロセスの画面になってつかめない（試験で確認）。
    #   そのため config.ini の window_title（タイトルに含まれる文字）で探す。
    #   見つからないときは、別の画面にパスワードを打ち込まないよう止める。
    $script:step = 'ログイン'
    $windowTitle = Get-IniValue 'rpa' 'window_title'
    if ($windowTitle) {
        Set-ActiveWindow $windowTitle
    } else {
        Write-Host '⚠ window_title が空欄のため、起動したプロセスの画面を手前に出せたかは確認しません'
        try { [void]$wshell.AppActivate($proc.Id) } catch { }
        Start-Sleep -Milliseconds 500
    }

    Write-Host 'ログイン入力'
    Send-Text $loginId
    Send-Key 'TAB'
    Send-Text $loginPassword
    Send-Key 'TAB'
    Send-Key 'ENTER'

    Write-Host "$AFTER_LOGIN_WAIT_SEC 秒待機..."
    Start-Sleep -Seconds $AFTER_LOGIN_WAIT_SEC

    # 本番環境の画面のメニューから品目工程マスタを開く（ALT → →×3 → ↓×6 → →×1 → ↓×8 → Enter）
    $script:step = '品目工程マスタを開く'
    Write-Host '品目工程マスタを開く'
    Set-ActiveWindow '本番環境'
    Send-Key 'ALT'
    Send-Key 'RIGHT' 3
    Send-Key 'DOWN' 6
    Send-Key 'RIGHT' 1
    Send-Key 'DOWN' 8
    Send-Key 'ENTER'
    Set-ActiveWindow '品目工程マスタ'

    # 抽出した品目ごとに MCKR 工程を登録する
    # （F3 → 2秒 → HMCD → TAB → F6 → 8000 → TAB → MCKR → TAB×8 → # → F9 → 3秒）
    for ($n = 0; $n -lt $result.Count; $n++) {
        $hmcd = $result[$n].HMCD
        $script:step = "品目工程マスタ登録 $($n + 1)/$($result.Count) $hmcd"
        Write-Host $script:step
        # 1件ごとに品目工程マスタの画面が手前にあることを確かめる（無ければ終了処理をして終わる）
        Set-ActiveWindow '品目工程マスタ'
        Send-Key 'F3'
        Start-Sleep -Seconds 2
        Send-Text $hmcd
        Send-Key 'TAB'
        Send-Key 'F6'
        Send-Text '8000'
        Send-Key 'TAB'
        Send-Text 'MCKR'
        Send-Key 'TAB' 8
        Send-Text '#'
        Send-Key 'F9'
        Start-Sleep -Seconds 3
    }

    Close-Program
    Stop-LeftoverProcess
} catch {
    # 画面が見つからないとき以外のエラーは、これまでどおりそのまま止める
    if (-not ($_.Exception -is [WindowNotFoundException])) { throw }
    Write-ErrorLog $_.Exception.Message
    # 画面が見つからなかったら終了処理をして終わる
    Close-Program
    Stop-LeftoverProcess
    exit $EXIT_WINDOW_NOT_FOUND
}
