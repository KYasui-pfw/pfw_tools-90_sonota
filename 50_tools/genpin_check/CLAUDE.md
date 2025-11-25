# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

現品票発行システム (Genpin Check System) - A Streamlit-based application for generating product tags and managing i-Reporter integration for Japanese manufacturing processes. The system handles QR code generation, checklist management, and progress tracking for knitting machine parts production.

## Running the Application

### Start Application
```bash
# Windows batch file startup
Genpin_Start.bat

# Direct Streamlit command
streamlit run 1_現品票発行.py --server.headless true --server.enableStaticServing=true --server.port 8502
```

**Application Structure:**
- **Main Page**: `1_現品票発行.py` - Product tag generation and batch processing
- **Page 2**: `pages/2_現品票手入力発行.py` - Manual tag creation (primarily for CMR parts)
- **Page 3**: `pages/3_チェックシート再作成.py` - Checklist regeneration for defect cases
- **Page 4**: `pages/4_iReporterチェック項目入力.py` - i-Reporter checklist item management (password: pfwpass)
- **Page 5**: `pages/5_iReporter進捗確認.py` - i-Reporter progress monitoring with heatmap visualization

### Database Locations
- **SQLite DBs**: `Database/genpinhyo.db`, `Database/checksheet.db`
- **Daily Backups**: `Database/backup/YYYYMMDD_*.db` (automatic cleanup)

## Architecture

### Multi-Database Integration Pattern

The system integrates 4 distinct data sources using SQLAlchemy:

1. **EJ System (CSV)**: `\\172.17.107.102\PrintOutCsv\4.加工\4-03 ASPKakouDenpyo.csv`
   - Source of truth for production order data
   - Triggers data refresh via "データ更新" button

2. **KRD MySQL Database** (`krd/machin`):
   - Connection: `mysql+pymysql://pfw:mejiriHoo@krd/machin?charset=utf8`
   - Tables: DATA_ASP2_PUT, MSTR_PROCODESTR, DATA_KOUTEIZUKAN, MSTR_METAL, DATA_RES_CAPA, MSTR_RES
   - Purpose: Process versions, drawing numbers, plating info, machine resources

3. **i-Reporter PostgreSQL** (`ESRV10/irepodb`):
   - Connection: `postgresql://postgres:cimtops@ESRV10/irepodb`
   - Views: view_mst_custom_record, view_report_405 (vertical), view_report_406 (horizontal), view_def_top
   - Purpose: Customer master, form generation status, checklist data

4. **Local SQLite**: `Database/genpinhyo.db`, `Database/checksheet.db`
   - Tables: genpinhyo (tag master), buhin_irepo_mst (part config), delete_mst (deletion tracking)
   - Tables: kouteizuban (process drawings), zubancheck (checklist items with 15 item/criteria pairs)

### Data Flow Architecture

```
EJ CSV (ASPKakouDenpyo.csv)
    ↓ LEFT JOIN (客先コード)
i-Reporter Customer Master
    ↓ LEFT JOIN (伝票Ｎｏ=SLIP_NO)
KRD Process Version (DATA_ASP2_PUT)
    ↓ LEFT JOIN (加工部番+VERSION)
KRD Process Code (MSTR_PROCODESTR)
    ↓ LEFT JOIN (加工部番=SETU_F)
KRD Drawing Numbers (DATA_KOUTEIZUKAN)
    ↓ LEFT JOIN (加工部番=FIN_CODE)
KRD Plating Info (MSTR_METAL)
    ↓ REPLACE INTO
SQLite genpinhyo table
    ↓ INSERT ON CONFLICT DO NOTHING
SQLite buhin_irepo_mst table
    ↓ Deletion Detection (4-month window)
SQLite delete_mst update (flg 0→1)
```

### QR Code Generation Logic

**Three Layout Types (QRコードレイアウト区分):**
- **0**: i-Reporter integrated - `jp.co.cimtops.ireporter.openreport:repid={帳票発行ID}`
- **1**: Legacy layout - Comma-separated data string
- **2**: Error template (`template/err.png`) - New part detection flag (ADD_20250122)

**Special Processing Rules:**
- Part numbers containing `-111`, `-404`, or `-102` with quantity > 1 generate multiple QR codes with "1/3", "2/3" notation
- Template selection based on total count: template5.xlsx (< 10), template1.xlsx (< 100), template.xlsx (≥ 2000)
- Layout B templates (`templateb.xlsx` series) for alignment issues (ADD_20250325)

### Automated i-Reporter Form Creation

**Module**: `module/conmas_upload.py`

**Selenium WebDriver Workflow:**
1. Login to ConMasManager (`http://172.17.52.101/ConMasManager/AutoGenerate`)
2. Select def_top_id from view_def_top (405 vertical, 406 horizontal layouts)
3. Upload CSV with R-header format conversion
4. Wait time calculation: 0.7s/record (confirmation) + 3.3s/record (import)
5. Screenshot capture to `work/sumi/png/` for audit trail
6. CSV backup to `csv/sumi/` with timestamp

**Critical Timing Pattern:**
- `time.sleep(int(df_len * 0.7))` after confirmation click
- `time.sleep(int(df_len * 3.3))` after import click
- Always include 1-second delays between Selenium actions

## Critical Database Patterns

### Deletion Flag Management (ADD_20241124)

**Purpose**: Detect EJ system deletions without direct communication

**4-Month Window Logic:**
```python
# Current month + 3 future months
dt_now = datetime.now(timezone(timedelta(hours=9)))
next_month = dt_now + relativedelta(months=1)
next2_month = dt_now + relativedelta(months=2)
next3_month = dt_now + relativedelta(months=3)
```

**Update Process:**
1. Merge genpinhyo + delete_mst on ロット番号
2. Filter by 4-month date range
3. LEFT JOIN with fresh CSV data
4. NaN values → 削除flg=1 (deleted in EJ)
5. Matched values → 削除flg=0 (still active)
6. Export deletion candidates to `EJ削除flg_on_YYYYMMDDHHMMSS.csv`

### Checklist Database Design

**kouteizubanテーブル** (Process Drawing Master):
- Composite UNIQUE constraint: (完成部番, 工程Ver, 工程順)
- Supports dual machine/drawing per process (加工機１/図番１, 加工機２/図番２)
- Auto-syncs zubancheck table via INSERT LEFT JOIN pattern

**zubancheckテーブル** (Checklist Items):
- Composite UNIQUE constraint: (連携ID, 工程順SUB, 図面Ver)
- 15 item/criteria pairs: チェック項目１～１５, チェック基準１～１５
- Linked to kouteizuban via 連携ID (kouteizuban.ID)
- Version control via 図面Ver with 生産開始月 tracking

**Multi-Step DataFrame Transformation Pattern:**
```python
# Split 15 columns into 15 rows
df_zubancheck1 = merged_df5[['連携ID','工程順','工程順SUB','図面Ver','生産開始月','チェック項目１','チェック基準１']]
  .rename(columns={'チェック項目１': 'チェック項目','チェック基準１': 'チェック基準'})
# ... repeat for df_zubancheck2 through df_zubancheck15
merged_zubancheckdf = pd.concat([df_zubancheck1, ...], ignore_index=True)
```

**Update Pattern (Force Rewrite):**
```python
# Collect all 15 rows back into single row with iloc indexing
edited_df2['チェック項目１'] = edited_df2['チェック項目'].iloc[0]
edited_df2['チェック基準１'] = edited_df2['チェック基準'].iloc[0]
# ... repeat for items 2-15
```

### Session State Management (Page 4)

**Counter-Based Reset Pattern:**
```python
if 'select_counter' not in st.session_state:
    st.session_state.select_counter = 0

# After each update/delete operation:
st.session_state.select_counter += 1

# Use counter as key suffix for all widgets:
zumenv = ni.number_input('図面Ver選択', key=f'innum2_{st.session_state.select_counter}')
```

**Purpose**: Force complete UI reset without `st.rerun()` which causes infinite loops

## Data Processing Conventions

### Japanese Text Normalization

**Mandatory transformations before DB insert:**
```python
mdf['完成部番'] = mdf['完成部番'].str.replace('　', ' ')  # Full-width → half-width space
mdf['組立番号'] = mdf['組立番号'].str.replace('　', ' ')
mdf['機種'] = mdf['機種'].str.replace('　', ' ')
mdf['国名'] = mdf['国名'].str.replace('　', ' ')
mdf['客先名'] = mdf['客先名'].str.replace('　', ' ')
```

### Number Formatting

**Integer detection and decimal removal:**
```python
mask = (mdf['吋'] != '') & mdf['吋'].apply(lambda x: float(x).is_integer() if x != '' else False)
mdf.loc[mask, '吋'] = mdf.loc[mask, '吋'].apply(lambda x: str(int(float(x))))
```

### Month Code Handling

**6-character month codes require underscore suffix:**
```python
mdf['月次'] = mdf['月次'].astype(str)
mdf['月次'] = mdf['月次'].apply(lambda x: x + '_' if len(x) == 6 else x)
```

### Batch Processing Pattern

**1000-record batch processing to avoid SQLite limits:**
```python
batch_size = 1000
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    cur.executemany('REPLACE INTO genpinhyo(...) VALUES (...)', batch)
conn.commit()  # Commit outside loop
```

## Known Issues and Workarounds

### Issue 1: Display Column Name Inconsistency (ADD_20250106)
- **Problem**: Internal column name 'G' displayed as 'ｹﾞｰｼﾞ' to users
- **Pattern**: Rename before display, rename back before processing
```python
df = df.rename(columns={'G': 'ｹﾞｰｼﾞ'})  # For display
selected_rows = selected_rows.rename(columns={'ｹﾞｰｼﾞ': 'G'})  # Before processing
```

### Issue 2: Cache Clearing Timing (ADD_20241127)
- **Problem**: Form ID updates not reflecting due to stale cache
- **Solution**: Clear cache + rerun on first load
```python
if "initialized" not in st.session_state:
    st.session_state["initialized"] = True
    st.cache_resource.clear()
    db_update()
    st.rerun()
```

### Issue 3: Duplicate Row Merging (ADD_20250127)
- **Problem**: INNER JOIN on identical rows creates Cartesian product
- **Solution**: Reset index before merge to preserve row identity
```python
common_df = common_df.reset_index()
mdf = mdf.reset_index()
common_df = pd.merge(common_df, mdf, how='inner')
```

### Issue 4: 未完了 Process Order (ADD_20250116)
- **Problem**: Incomplete processes displayed in wrong order
- **Solution**: Sort by descending index before date assignment
```python
tate_dfa = tate_dfa.sort_index(ascending=False)
for i in range(1, 11):
    mask = tate_dfa['帳票ID'] == tate_dfa['帳票ID'].shift(-i + 1)
    tate_dfa.loc[mask, '測定日'] = pd.to_datetime(graph_min_date) + pd.Timedelta(days=i)
```

## File Organization

### Critical File Paths

**Templates:**
- Standard: `template/template.xlsx` through `template/template7.xlsx`
- Layout B: `template/templateb.xlsx` through `template/template7b.xlsx`
- Manual entry: `template/add_template.xlsx`
- Error indicator: `template/err.png`

**Work Directories:**
- QR codes: `work/qrcode_*.png` (auto-cleanup after 20 minutes)
- Generated tags: `work/現品票_YYYYMMDDHHMMSS.xlsx`
- Selenium screenshots: `work/sumi/png/*_SC1.png`, `*_SC2.png`

**CSV Management:**
- Input archive: `csv/` (with timestamp prefix)
- Processed archive: `csv/sumi/YYYYMMDDHHMMSS_作成*.csv`
- Deletion log: `EJ削除flg_on_YYYYMMDDHHMMSS.csv` (root directory)
- History export: `履歴_YYYYMMDDHHMMSS.csv` (root directory, via df_csv_cnv)

## Security and Authentication

**Page 4 Password Protection:**
```python
PASSWORD = "pfwpass"
if not st.session_state.authenticated:
    password = st.text_input("パスワードを入力してください", type="password")
```

**Selenium Login Credentials:**
- Username: `mainte`
- Password: `@next123`
- URL: `http://172.17.52.101/ConMasManager/AutoGenerate`

## Testing and Validation

**No formal test suite exists.** Validation relies on:
1. Import testing: `python -c "import 1_現品票発行; print('OK')"`
2. Manual verification via download button functionality
3. Screenshot audit trail in `work/sumi/png/`
4. CSV output inspection for データ更新 button

**Common Validation Points:**
- Check `ireporter管理flg=1` + `QRコードレイアウト区分=0` + `帳票発行ID=0` condition before auto-form creation
- Verify 削除flg CSV output when deletions detected
- Confirm kouteizuban + zubancheck synchronization after db_update1()

## Performance Considerations

**Large Dataset Handling:**
- Cache resource decorators on all DB queries: `@st.cache_resource`
- Batch size 1000 for executemany operations
- Conditional clearing: `st.cache_resource.clear()` only after mutations
- AgGrid with `reload_data=True` to force refresh after updates

**Selenium Timing:**
- Base wait: 1 second between actions
- Dynamic scaling: 0.7s + 3.3s per record for i-Reporter uploads
- Screenshot delays prevent incomplete captures

**File Cleanup:**
- Automatic 20-minute cleanup for `work/*.png` and `work/*.xlsx`
- 7-day daily backup retention in `Database/backup/`
- Manual CSV archive management in `csv/` and `csv/sumi/`
