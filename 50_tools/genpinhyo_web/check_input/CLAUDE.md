# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

NiceGUI app (port 8506) for managing i-Reporter checklist items. A rewrite of `pages/4_iReporterチェック項目入力.py` (Streamlit), running as an independent process with its own venv. No pandas — stdlib + nicegui only.

## Starting the App

```bat
:: From genpin_check\ directory
Check_input_start.bat

:: Or directly
cd check_input
venv\Scripts\python.exe main.py
```

On first run, the bat creates `check_input\venv\` and installs nicegui. Kills any existing process on port 8506 first.

## Architecture

Single file: `main.py` (~1000 lines). Two routes:
- `/login` — password form (`pfwpass`), sets `app.storage.user['authenticated']`
- `/` — 4-tab main app; redirects to `/login` if not authenticated

All tab state lives as **local variables inside `main_page()`** — no global state except `_krd_synced`. DB calls use `await run.io_bound(fn, *args)` because NiceGUI is async.

### DB connections

| DB | Path | Purpose |
|---|---|---|
| `checksheet.db` | `../Database/checksheet.db` | kouteizuban + zubancheck tables |
| `genpinhyo.db` | `../Database/genpinhyo.db` | buhin_irepo_mst table |
| KRD SQLite | `\\esrv11\KakouDenpyo\krd_machine.db` | DATA_RES_CAPA + MSTR_RES (read-only) |

`_connect(path)` sets `row_factory = sqlite3.Row` so rows behave as dicts.

### Startup sync (db_update1)

Runs once per process (`_krd_synced` global flag) in a background thread at page load. Syncs KRD `DATA_RES_CAPA` → `kouteizuban`, then inserts missing `zubancheck` stubs. If KRD is unreachable, `ensure_tables()` still runs so the app stays usable.

### Tab overview

| Tab | Label | Key behavior |
|---|---|---|
| Tab1 | 加工機・図番 登録 | Search kouteizuban; inline-edit 加工機/図番/未使用flg; update or delete |
| Tab2 | チェックシート項目 登録 | Select 図番 → edit 15 check items → upsert zubancheck |
| Tab3 | チェックシートイメージ | Read-only preview of Tab2's selected 完成部番+工程Ver |
| Tab4 | i-Reporter発行対象管理 | Inline-edit buhin_irepo_mst flags |

## Critical Patterns

### Inline editing with Vue slots

All editable tables use `add_slot()` — not `ui.input()` children:

```python
for field in ('加工機１', '図番１', '加工機２', '図番２'):
    tab1_table.add_slot(f'body-cell-{field}', f'''
        <q-td :props="props">
            <q-input v-model="props.row['{field}']" dense borderless
                @update:model-value="$parent.$parent.$emit('cell_changed',
                    {{id: props.row.ID, field: '{field}', value: $event}})" />
        </q-td>''')
tab1_table.on('cell_changed', lambda e: ...)
```

**Never call `table.update()` after a cell edit** — it replaces the DOM and loses the in-progress input value. Only call `table.update()` after full row reloads (search/update).

### Pagination must be a constructor arg, not a prop

Tab1's table paginates 50 rows/page. NiceGUI's `ui.table` **ignores** `:pagination="{rowsPerPage:50}"` passed via `.props()` — it renders every row and shows no pagination footer. Pass `pagination=` to the constructor instead:

```python
tab1_table = ui.table(columns=TAB1_COLS, rows=[], row_key='ID', pagination=50) \
    .classes('w-full').props('dense flat bordered :rows-per-page-options="[50,100,200,0]"')
```

`_initial_load()` / `search_tab1()` load **all** matching rows (no SQL `LIMIT`); the 50/page split is client-side. kouteizuban is ~20k rows — client-side pagination handles it, but this is the reason there is no server-side paging.

### 未使用flg=1 → DELETE (not flag)

`db_update2()` **deletes** rows where `未使用flg=1` from `kouteizuban`. This is intentional. Rows deleted from kouteizuban will reappear on next KRD sync (db_update1) if they still exist in KRD.

### Tab2 zuban_select population

The Tab2 dropdown is built from **Tab1's current search results** (`tab1_rows`), not a separate DB query. `zuban_list_from_rows(tab1_rows)` generates the option labels. Must be called after **both** `search_tab1()` and `update_tab1()` to stay in sync.

```python
filtered = zuban_list_from_rows(tab1_rows)
tab2_state['zuban_list'] = filtered
new_labels = [''] + [z['label'] for z in filtered]
zuban_select.options = new_labels
zuban_select.set_value('')
zuban_select.update()
```

### Wide ↔ Tall conversion (Tab2)

`zubancheck` stores 15 check items as **columns** (チェック項目１〜１５, チェック基準１〜１５). The UI shows them as **15 rows**. Use `wide_to_tall(row)` / `tall_to_wide(items, meta)` to convert.

`工程順SUB`: `1` = 加工機１/図番１ slot, `2` = 加工機２/図番２ slot.

### @ui.refreshable

`render_check_table()` (Tab2) and `render_preview()` (Tab3) are decorated with `@ui.refreshable`. Call `.refresh()` after mutating `tab2_state['check_rows']` or changing the Tab2 selection.

### Daily backup

`backup_db(path)` copies the DB to `../Database/backup/YYYYMMDD_<filename>` — skipped if today's backup already exists. Called at the start of `db_update2`, `db_update3`, `db_update4`, `db_update5`.

### Tab3 build_preview_display rules (Streamlit compatibility)

`build_preview_display(raw)` converts DB rows into the display row list. Non-obvious rules:

- **Ver: row**: shown below every 図番 row — including 図番=「なし」(0 check items). Added as the 2nd row of the group when check items exist, or as an appended row when they don't.
- **Blank row before `=====`**: only inserted when the preceding 工程順 group has **2 or more** check item rows in total (across 工程順SUB=1 and 2). 0 or 1 check items → no blank, separator appears directly.
- **行 column**: leftmost column, 1-based sequential number across all rows (including blank and ===== rows).
- Blank row + ===== logic tracks `ord_check_counts` dict (keyed by 工程順) accumulated during the first pass.

## Deployment Note

**NiceGUI version mismatch → icons disappear.** Material Icons are served from NiceGUI's own static files. If the production venv has a different NiceGUI version than dev, icon fonts may not load (`fonts.css 404`). Fix: pin the same version in both environments.

```bat
venv\Scripts\pip show nicegui          :: check version
venv\Scripts\pip install nicegui==X.Y.Z  :: pin to match dev
```

## DB Write Functions

| Function | Table | Trigger |
|---|---|---|
| `db_update1()` | kouteizuban ← KRD | Once per process (background thread) |
| `db_update2(rows)` | kouteizuban | Tab1「加工機・図番更新」; 未使用flg=1 → DELETE |
| `db_update3(wide_row)` | zubancheck | Tab2「チェック項目更新」(INSERT OR REPLACE) |
| `db_update4(rows)` | buhin_irepo_mst | Tab4「項目更新」 |
| `db_update5(id, ver)` | zubancheck | Tab2「チェック項目削除」|
