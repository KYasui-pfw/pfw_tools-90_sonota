# 内作工程チェック「簡易マスタ未登録 > rBOMにのみ存在」のうち、SEINO があって KTCD_CHECK が空欄の行を抽出して CSV に出す。
# 元: ../app.py の fetch_rbom_only()。RPA（手配指示に MCKR 工程を追加する）の入力にする。RPA の操作部分は未作成。
#
# 実行条件: rBOM の夜間処理が終わっている（http://rbom-yakan/yakan.csv の1列目が 5）ときだけ。それ以外は何もせずに終わる
#
# 抽出条件（すべて AND。単位は「品目CD＋製番」）
#   - D3110 の行で INSTDT >= 基準日、SEINO が空欄でない
#   - その製番が D3030（製番実績）に無い＝完納していない
#   - M0810.HMBUNCD = '7'（マシニング品目）
#   - Django 品目工程マスタ（KRD DATA_RES_CAPA の写し）の品目CDと前方一致しない
#   - HMCD が L / Z- / KF20 で始まらない
#   - SEINO が「26 で始まり KC/KD/KE/KF/KG を含む」「A で始まる」「数字だけ」のどれでもない
#   - KTCD_CHECK が空欄: その品目＋製番の D3110 の行（LISTNO）を親（OYALISTNO）に持つ子行に、
#       KTCD = 'MCKR' の行も、SRCD = '40'（社内加工）の行も無い
#
# ⚠ app.py と違う点
#   - KRD の照合は 01 と同じ「どれか1つの品目CDに一致すれば登録済み」（app.py の find_match() は最初の1件しか見ない）
#   - SRCD = '40' で KTCD が空欄の子行も「標準工程登録あり」に数える。
#     app.py は SQL の KTCD <> 'MCKR' が NULL で成り立たず、この子行を見落として空欄にしていた（2026-10-09 時点で2行）
#
# 実行: powershell -ExecutionPolicy Bypass -File .\02_手配指示登録.ps1
# ⚠ このファイルは UTF-8（BOM付き）で保存すること。BOM が無いと PowerShell 5.1 で日本語が化ける。
# ⚠ psql.exe の場所と Postgres のパスワードは 01 と同じ config.ini の [postgres] を読む。

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

$CSV_NAME = '02_抽出結果.csv'      # 01 の 抽出結果.csv と分ける

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

# ── 実行条件: rBOM の夜間処理が終わっていること（01 と同じ） ──────────
$YAKAN_URL = 'http://rbom-yakan/yakan.csv'
$YAKAN_DONE = '5'
$EXIT_YAKAN_UNKNOWN = 3             # 夜間処理の状態が取れなかったときの終了コード（bat はこのとき止まらない）
try {
    $res = Invoke-WebRequest -Uri $YAKAN_URL -UseBasicParsing -TimeoutSec 10
    $yakanLine = ([Text.Encoding]::UTF8.GetString($res.RawContentStream.ToArray()) -split "`r?`n")[0].Trim()
} catch {
    # 状態が分からないときは、夜間処理中かもしれないので実行しない
    $msg = "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss')) [02 夜間処理の確認] 状態を取得できなかったため実行しませんでした: $($_.Exception.Message)"
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

# ── Django 品目工程マスタ（psql。01 と同じ） ──────────────────────
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
$m0810 = Get-AllRows 'M0810' @('HMCD', 'HMNM') @{ HMBUNCD = '7' } @('HMCD')
Write-Host "  HMBUNCD=7: $($m0810.Count) 件"
$items = @($m0810 | Where-Object { $_.HMCD -notmatch '^(L|Z-|KF20)' })
Write-Host "  L / Z- / KF20 始まりを除外: $($items.Count) 件"

Write-Host 'Django 品目工程マスタ取得中...'
$finalCodes = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($c in Get-DjangoItemCodes) {
    $n = ConvertTo-NormalizedCode $c
    if ($n) { [void]$finalCodes.Add($n) }
}
Write-Host "  品目CD: $($finalCodes.Count) 件"
# 前方一致 = HMCD（正規化後）の先頭 1〜全文字のどれかが品目CDの集合にある
$items = @($items | Where-Object {
    $h = ConvertTo-NormalizedCode $_.HMCD
    $hit = $false
    for ($len = 1; $len -le $h.Length -and -not $hit; $len++) { $hit = $finalCodes.Contains($h.Substring(0, $len)) }
    -not $hit
})
Write-Host "  品目工程マスタ登録済みを除外: $($items.Count) 件"
$hmnm = @{}
foreach ($it in $items) { $hmnm[$it.HMCD] = $it.HMNM }

# 基準日以降の D3110 の行から「品目CD＋製番」を集める
Write-Host 'D3110（基準日以降）取得中...'
$recent = Get-RowsByIn 'D3110' 'HMCD' @($items | ForEach-Object { $_.HMCD }) @('HMCD', 'SEINO') @(
    @{ INSTDT = @{ gte = $INSTDT_THRESHOLD } }, @{ SEINO = @{ is_not_null = $true } })
$pairs = @{}                        # "HMCD`tSEINO" → @{ HMCD; SEINO }
foreach ($row in $recent) { $pairs["$($row.HMCD)`t$($row.SEINO)"] = @{ HMCD = $row.HMCD; SEINO = $row.SEINO } }
Write-Host "  品目CD＋製番: $($pairs.Count) 件"

# 製番の除外: 26 で始まり KC/KD/KE/KF/KG を含む・A で始まる・数字だけ
foreach ($k in @($pairs.Keys)) {
    $s = [string]$pairs[$k].SEINO
    if ($s -match '^26.*K[CDEFG]' -or $s -match '^A' -or $s -match '^\d+$') { $pairs.Remove($k) }
}
Write-Host "  製番の形で除外: $($pairs.Count) 件"

# 完納済み（D3030 に載っている）製番を除く
$seinos = @($pairs.Values | ForEach-Object { $_.SEINO } | Sort-Object -Unique)
$completed = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($row in (Get-RowsByIn 'D3030' 'SEINO' $seinos @('SEINO') $null)) { [void]$completed.Add($row.SEINO) }
foreach ($k in @($pairs.Keys)) { if ($completed.Contains([string]$pairs[$k].SEINO)) { $pairs.Remove($k) } }
Write-Host "  完納済み製番を除外: $($pairs.Count) 件"

# KTCD_CHECK: 品目CD＋製番の LISTNO を（基準日に関係なく）全部取り、それを親に持つ子行を見る
Write-Host 'D3110（LISTNO・子行）確認中...'
$listnos = @{}                      # "HMCD`tSEINO" → LISTNO の一覧
$pairHmcds = @($pairs.Values | ForEach-Object { $_.HMCD } | Sort-Object -Unique)
foreach ($row in (Get-RowsByIn 'D3110' 'HMCD' $pairHmcds @('HMCD', 'SEINO', 'LISTNO') @{ SEINO = @{ is_not_null = $true } })) {
    $k = "$($row.HMCD)`t$($row.SEINO)"
    if (-not $pairs.ContainsKey($k)) { continue }
    if (-not $listnos.ContainsKey($k)) { $listnos[$k] = New-Object System.Collections.Generic.List[string] }
    if (-not $listnos[$k].Contains([string]$row.LISTNO)) { $listnos[$k].Add([string]$row.LISTNO) }
}
$allListnos = @($listnos.Values | ForEach-Object { $_ } | Sort-Object -Unique)
$mckrOya = New-Object 'System.Collections.Generic.HashSet[string]'
$srcd40Oya = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($row in (Get-RowsByIn 'D3110' 'OYALISTNO' $allListnos @('OYALISTNO', 'KTCD', 'SRCD') $null)) {
    if ($row.KTCD -eq 'MCKR') { [void]$mckrOya.Add([string]$row.OYALISTNO) }
    elseif ($row.SRCD -eq '40') { [void]$srcd40Oya.Add([string]$row.OYALISTNO) }   # KTCD が空欄でも数える（app.py との違い）
}

$countMckr = 0; $countSrcd40 = 0
$result = @(foreach ($k in $pairs.Keys) {
    $ls = if ($listnos.ContainsKey($k)) { @($listnos[$k]) } else { @() }
    if (@($ls | Where-Object { $mckrOya.Contains($_) }).Count) { $countMckr++; continue }
    if (@($ls | Where-Object { $srcd40Oya.Contains($_) }).Count) { $countSrcd40++; continue }
    $p = $pairs[$k]
    [pscustomobject]@{
        'SEINO'  = $p.SEINO
        'HMCD'   = $p.HMCD
        'HMNM'   = $hmnm[$p.HMCD]
        'LISTNO' = ($ls | Sort-Object) -join ' '
    }
}) | Sort-Object SEINO, HMCD
Write-Host "  KTCD_CHECK: MCKR $countMckr 件 / 標準工程登録あり $countSrcd40 件 / 空欄 $($result.Count) 件"
Write-Host "抽出結果: $($result.Count) 件"

# 抽出結果を CSV に出す（毎回上書き。Excel で開けるよう UTF-8 BOM付き。PowerShell 5.1 と 7 で同じになるよう自前で書く）
$csvPath = Join-Path $PSScriptRoot $CSV_NAME
$csvLines = @($result | ConvertTo-Csv -NoTypeInformation)
if ($csvLines.Count -eq 0) { $csvLines = @('"SEINO","HMCD","HMNM","LISTNO"') }   # 0件でも見出しだけは出す
[IO.File]::WriteAllLines($csvPath, [string[]]$csvLines, (New-Object Text.UTF8Encoding $true))
Write-Host "CSV 出力: $csvPath"

# 0件なら RPA は起動せずに終わる（終了コード 0）
if ($result.Count -eq 0) {
    Write-Host '抽出結果が 0 件のため、RPA は行わずに終了します'
    exit 0
}

# ── RPA ─────────────────────────────────────────────
# 未作成（手配指示入力 w_ju0100_pfw_cst で BOM追加 → MCKR 工程を追加する予定）
