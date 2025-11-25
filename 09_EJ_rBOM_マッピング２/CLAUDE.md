# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an EJ-rBOM mapping tool (Simplified Version) - a Streamlit web application that maps order backlog data between EJ (legacy Oracle-based production management system) and rBOM (new API-based system) during a system migration.

**This version focuses on automatic mapping and fixed mapping capabilities only. Manual mapping functionality has been removed.**

## Common Commands

### Application Management
```bash
# Start the application (always use port 8501)
streamlit run "発注残マッピングリスト.py" --server.port 8501

# OR using virtual environment
venv/Scripts/python.exe -m streamlit run "発注残マッピングリスト.py" --server.port 8501

# Effective method to stop Streamlit processes (Windows)
# Step 1: Find processes using port 8501
netstat -ano | findstr :8501

# Step 2: Kill specific process by PID (replace XXXX with actual PID)
powershell -Command "Stop-Process -Id XXXX -Force"

# Clear Python module cache if changes aren't reflected
rmdir /s /q __pycache__ & rmdir /s /q data_sources\__pycache__ & del /s *.pyc
```

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Architecture Overview

### Simplified Two-Tier Mapping System
```
EJ Oracle DB → MappingEngine → SQLite (2 tables) → Streamlit UI → CSV Export
rBOM API     ↗                      ↘
```

The application implements a simplified mapping system with two persistence layers:
1. **EJ System**: Oracle database (172.17.107.102:1521/EXPJ) with order backlog data from T_RLSD_PUCH_ODR + M_ITEM tables
2. **rBOM System**: REST API (http://pfw-api/orders/) with X-API-KEY authentication
3. **SQLite Storage**: Two-table design (mapping_results + fixed_mappings)

### Core Components

- **`発注残マッピングリスト.py`**: Main Streamlit application with simplified UI
- **`data_sources/`**: External system connectors
  - `ej_connector.py`: Oracle DB connector for EJ legacy system
  - `rbom_connector.py`: REST API connector for rBOM system
  - `mk020_connector.py`: Generic Query API connector for MK020 master data (vendor/process notes)
- **`mapping/mapper.py`**: Simplified mapping engine with fixed mapping exclusion logic and MK020 LEFT JOIN
- **`database/db_manager.py`**: SQLite operations managing two tables with schema migration support
- **`ui/components.py`**: Interactive data grid using st.dataframe with CSV export

### Two-Table Database Design (Simplified)

**1. mapping_results** (Unified display table):
- Combines automatic and fixed mapping results for UI display
- Includes `is_fixed` boolean flag and `mapping_type` (always '自動')
- Cleared and rebuilt on each auto-mapping execution

**2. fixed_mappings** (User-locked mappings):
- Stores mappings that users want to preserve unchanged
- Managed via interactive checkboxes in the UI with bulk select/deselect operations
- Excluded from auto-mapping and re-added as fixed results

**Removed from this version:**
- manual_mappings table (not needed in simplified version)

### Enhanced Mapping Logic (Two-Round System)

The mapping engine processes data in **two rounds** with strict exclusion logic:

**First Round - Standard Mapping (Phase 1-5)**:
1. **MK020 Enrichment Phase**: LEFT JOIN rBOM data with MK020 master
   - Filter: `VALQTY = 0`
   - Sort: Latest `VALDTF` (有効日付From) per (OYAHMCD, KTCD, SRCD) group
   - Join: `rBOM.item_code = MK020.oyahmcd AND rBOM.ktcd = MK020.ktcd AND rBOM.srcd = MK020.srcd`
   - Result: MK020 NOTE appended to rBOM data as `mk020_note`
2. **Exclusion Phase**: Remove fixed mapping keys from source EJ/rBOM data
3. **Re-injection Phase**: Add fixed mappings (type='自動', fixed=true) with preserved mk020_note
4. **Phase 3 - Auto-mapping with Delivery Date Check**:
   - Match: `EJ.item_code = rBOM.item_code AND EJ.quantity = rBOM.quantity`
   - Delivery date tolerance check: `EJ納期許容日数` (days after rBOM) and `EJ≦rBOM許容日数` (days before rBOM)
   - Status: '済' (completed)
5. **Phase 4-5 - Temporary Lists**: Unmatched EJ/rBOM items stored for second round

**Second Round - Remarks Mapping (Phase 6, Added 2025-10-30)**:
6. **備考マッピング (Remarks Mapping)**: Match unmatched EJ items with rBOM MK020 notes
   - Match: `EJ.item_code = rBOM.mk020_note` (item code appears in notes field)
   - Delivery date tolerance check: **Same logic as Phase 3** (implemented 2025-10-30)
   - Status: '済2' (remarks mapping completed)
   - Note: This phase only processes items that failed standard matching

**Final Phase**:
7. **Classification**: Results categorized as:
   - '済' = Matched in standard mapping (Phase 3)
   - '済2' = Matched in remarks mapping (Phase 6)
   - '未' = Unmatched (EJ_ONLY or RBOM_ONLY)

### Key Business Rules

- **Date Restriction**: All data extraction limited to delivery dates ≥ 2025-11-01 (hard-coded constraint)
- **EJ Filtering**: Filter `PUCH_ODR_STS_TYP = 2` and `PUCH_ODR_TYP != 4`
- **Mapping Strategy**: Two-round system:
  - **Round 1**: Exact `item_code + quantity` match with delivery date tolerance (status='済')
  - **Round 2**: `item_code` match with `mk020_note` field with delivery date tolerance (status='済2')
- **Delivery Date Tolerance** (Added 2025-10-30):
  - Configurable thresholds: `EJ≧rBOM許容日数` (EJ after rBOM) and `EJ≦rBOM許容日数` (EJ before rBOM)
  - Applied to both standard mapping (Phase 3) and remarks mapping (Phase 6)
  - Datetime conversion: `delivery_date_dt` field created from `delivery_date` on DataFrame initialization
- **Fixed Mapping Scope**: Applies to all automatic mappings (no manual type exists)
- **CSV Export**: Always use Shift_JIS encoding for Japanese Excel compatibility
- **Sorting**: Final results sorted by `item_code → ej_order_no → rbom_order_no`

## Important Implementation Details

### Database Schema (Enhanced)
The system uses a two-table approach with recent enhancements:

**mapping_results table** (25 fields total):
- **EJ data** (9 fields): order_no, item_code, item_name, quantity, status, purch_odr_typ, delivery_date, **vend_cd (仕入先コード)**, **m_sequence (連番)**
- **rBOM data** (10 fields): order_no, **line_no (行番号 - CRITICAL: Must be INTEGER type)**, item_code, item_name, quantity, delivery_date, seino, **ktcd (工程コード)**, **srcd (仕入先コード)**, **m_sequence (連番)**
- **MK020 data** (1 field): **mk020_note (備考)** - LEFT JOIN from MK020 master where VALQTY=0 and latest VALDTF
- **Management** (3 fields): status ('済'/'済2'/'未'), mapping_type ('自動'), is_fixed (BOOLEAN)
- **System** (2 fields): created_at, updated_at

**CRITICAL Data Type Issue (Fixed 2025-10-30)**:
- `rbom_line_no` was being saved as binary blob due to Pandas data type issues
- **Fix**: Explicit integer conversion in INSERT operations:
  ```python
  int(result.get('rbom_line_no')) if pd.notna(result.get('rbom_line_no')) else None
  ```
- Applied in both `save_mapping_results()` and `save_fixed_mapping()` functions
- Requires database recreation to take effect on existing data

**fixed_mappings table**: Same structure as mapping_results, stores user-locked mappings

**Key Schema Features**:
- Automatic schema migration via ALTER TABLE for backward compatibility
- All new fields (ej_vend_cd, rbom_ktcd, rbom_srcd, mk020_note) nullable for existing data
- Database initialization on first run creates schema, subsequent runs use migration

### Interactive UI Architecture

**Single-Tier Layout**:
- **Controls**: Auto-mapping button + Fixed operation controls (マッピング確定情報更新 | 全選択 | 全解除)

**Data Grid Features**:
- Uses `st.dataframe` for read-only display with high performance
- Display columns include vendor codes (EJ/rBOM), process code (rBOM), and notes (rBOM)
- All mappings are type '自動' (automatic)
- rBOM displays combined "発注番号+行番号" format (9+3 digits with '+' separator)
- Fixed mapping checkbox controls via separate interface

### UI Conventions
- **CSS Styling**: Compressed header and clean layout
- **Column Display Order**:
  - EJ: 発注番号→連番→品目コード→品目名→数→納期→**仕入先コード**
  - rBOM: 発注番号+行番号→連番→品目コード→品目名→数→納期→**工程コード→仕入先コード→備考**
- **Index Hiding**: Always use `hide_index=True` for dataframe displays
- **Japanese Labels**: All UI text in Japanese with full kanji terms (e.g., "仕入先コード" not "仕入先CD")
- **Status Display**:
  - '済' = Green background (standard mapping success)
  - '済2' = Light blue background (remarks mapping success)
  - '未' = Default background (unmapped)
- **Top Control Panel** (Lines 178, 212-231):
  - Column ratios: `[2, 2, 2, 2, 1.5]`
  - Previous execution time displayed in 2 lines (日付 + 時刻)

### Session Management
- DatabaseManager stored in `st.session_state` for persistence across interactions
- Database initialization happens **BEFORE** UI display to ensure proper state loading
- **Critical Fix (2025-10-30)**: Database initialization moved before column display (lines 208-217)
  - Previous bug: Execution time showed "なし" on browser refresh
  - Fix: Load `last_execution_time` from database before rendering col4/col5
- Interactive state managed through streamlit rerun cycles for checkbox changes
- Previous execution time restored from database on session start

## Critical Implementation Patterns

### Database Operations (CRITICAL)
When modifying database schema or operations, always update **THREE** places in `db_manager.py`:

1. **CREATE TABLE schema** (lines 52-91 for mapping_results, 95-127 for fixed_mappings)
   - Add new column with proper type and comment
   - Example: `ej_vend_cd TEXT,  -- EJ仕入先コード (T_RLSD_PUCH_ODR.VEND_CD)`

2. **Migration logic** (lines 168-229)
   - Add try/except block to ALTER TABLE for each new column
   - Pattern:
   ```python
   try:
       cursor.execute("SELECT new_column FROM table_name LIMIT 1")
   except sqlite3.OperationalError:
       logger.info("table_nameテーブルにnew_columnカラムを追加")
       cursor.execute("ALTER TABLE table_name ADD COLUMN new_column TYPE")
   ```

3. **INSERT/SELECT statements**
   - `save_mapping_results()`: INSERT statement (lines 395-429)
   - `save_fixed_mapping()`: INSERT statement (lines 475-505)
   - `get_mapping_results()`: SELECT statement (lines 442-453)
   - Must include ALL columns in proper order with matching placeholders

**Common Bugs**:
1. Forgetting to update INSERT/SELECT statements causes columns to not save/display even if schema exists
2. **Data Type Conversion** (Critical Fix 2025-10-30):
   - Pandas DataFrames may not properly convert to SQLite types
   - **Always use explicit type conversion** for numeric fields:
     ```python
     int(result.get('rbom_line_no')) if pd.notna(result.get('rbom_line_no')) else None
     ```
   - Without explicit conversion, integer fields may be saved as binary blobs
3. **Status Field** (Fixed 2025-10-30):
   - Must use `result.get('status', '')` not hardcoded empty string
   - Hardcoded values prevent '済2' status from displaying correctly

### MK020 Master Integration Pattern
The MK020 LEFT JOIN enrichment follows strict filtering rules:

```python
# 1. Filter VALQTY = 0
mk020_filtered = mk020_df[mk020_df['valqty'] == 0].copy()

# 2. Convert VALDTF to datetime
mk020_filtered['valdtf_dt'] = pd.to_datetime(mk020_filtered['valdtf'], errors='coerce')

# 3. Get latest VALDTF per group
mk020_latest = mk020_filtered.sort_values('valdtf_dt', ascending=False).groupby(
    ['oyahmcd', 'ktcd', 'srcd'], dropna=False
).first().reset_index()

# 4. LEFT JOIN with rBOM
rbom_df = rbom_df.merge(
    mk020_latest[['oyahmcd', 'ktcd', 'srcd', 'note']],
    left_on=['item_code', 'ktcd', 'srcd'],
    right_on=['oyahmcd', 'ktcd', 'srcd'],
    how='left'
)
```

**Critical**: This pattern ensures only valid (VALQTY=0) and current (latest VALDTF) master data is used.

### Delivery Date Tolerance Pattern (Added 2025-10-30)

The delivery date checking logic applies to both standard and remarks mapping:

```python
# 1. Initialize delivery_date_dt field on DataFrame creation (mapper.py lines 50-54)
if not ej_df.empty and 'delivery_date' in ej_df.columns:
    ej_df['delivery_date_dt'] = pd.to_datetime(ej_df['delivery_date'], errors='coerce')
if not rbom_df.empty and 'delivery_date' in rbom_df.columns:
    rbom_df['delivery_date_dt'] = pd.to_datetime(rbom_df['delivery_date'], errors='coerce')

# 2. Check tolerance in matching logic (used in Phase 3 and Phase 6)
def _check_delivery_date_condition(
    self,
    ej_delivery_dt,
    rbom_delivery_dt,
    ej_after_rbom_days: int,
    ej_before_rbom_days: int
) -> bool:
    """EJ納期がrBOM納期の許容範囲内かチェック"""
    if pd.isna(ej_delivery_dt) or pd.isna(rbom_delivery_dt):
        return False

    days_diff = (ej_delivery_dt - rbom_delivery_dt).days

    # EJ納期 ≧ rBOM納期の許容日数チェック
    if days_diff > ej_after_rbom_days:
        return False

    # EJ納期 ≦ rBOM納期の許容日数チェック
    if days_diff < -ej_before_rbom_days:
        return False

    return True
```

**Critical Notes**:
- Datetime conversion must happen at DataFrame initialization (lines 50-54)
- Both Phase 3 (standard mapping) and Phase 6 (remarks mapping) use this check
- Phase 4-5 temporary lists inherit `delivery_date_dt` from original DataFrames

## Integration with External Systems

### i-Reporter Integration (scan/ej_ukeire_list_tenkai.py)

The mapping database integrates with an external i-Reporter system that processes order receipt lists:

**Current Implementation** (Lines 107-109):
```python
po_text = jdata[n-5].replace(' ', '').replace('　', '')
pono = po_text[:-4]  # Extract order number (9 digits)
lineno = po_text[-3:]  # Extract line number (3 digits)
```

**Planned Integration** (Documented in scan/README_変更要件.md):
- **Change Required**: Replace string parsing with database lookup
- **Input**: `jdata[n-5]` contains `ej_order_no` from i-Reporter
- **Process**: Query `mapping.db` to retrieve `rbom_order_no` and `rbom_line_no`
- **Output**: Use database values instead of parsed string values
- **Database Path**: `D:\py\EJ_rBOM_mapping\database\mapping.db`
- **Production Path**: `D:\ConMas\gateway\scripts\scan\ej_ukeire_list_tenkai.py`

**Unresolved Design Issue**:
When multiple rows in `mapping_results` match the same `ej_order_no` with status IN ('済', '済2'), which row should be selected?

**Candidate Solutions**:
1. **Minimum Sequence**: `ORDER BY ej_m_sequence ASC LIMIT 1` - First mapped item
2. **Fixed Only**: `AND is_fixed = 1` - Only confirmed mappings
3. **Standard Only**: `AND status = '済'` - Exclude remarks mappings ('済2')
4. **Combination**: Other criteria combinations

**Status**: Deferred pending business logic clarification (2025-10-30)

**Key Implementation Notes**:
- Must import `sqlite3` module
- `rbom_line_no` must be zero-padded to 3 digits: `str(rbom_line_no).zfill(3)`
- Raise `ValueError` if no matching data found
- Database path should be hardcoded for reliability

## Configuration Requirements

### API Authentication (CRITICAL)
```python
# rBOM API requires X-API-KEY header (not Bearer token)
headers = {
    'X-API-KEY': 'oG5^Ls%#20yq',
    'accept': 'application/json'
}
```

### Environment Variables (Optional - currently hardcoded)
```
EJ_DB_HOST=172.17.107.102
EJ_DB_PORT=1521
EJ_DB_SERVICE=EXPJ
EJ_DB_USER=EXPJ2
EJ_DB_PASSWORD=EXPJ2
RBOM_API_BASE_URL=http://pfw-api
RBOM_API_TOKEN=oG5^Ls%#20yq
```

### Dependencies Notes
- `cx-Oracle>=8.3.0` requires Oracle client libraries
- `streamlit>=1.40.0` for hide_index parameter support
- Application designed for Windows Server 2022 deployment

## Key Differences from Full Version

### Removed Features
- Manual mapping functionality (pages/ directory removed)
- manual_mappings table and related functions
- find_potential_matches() function (was for manual mapping support)
- Manual mapping UI components and filters

### Simplified Logic
- All mappings are type '自動' (no '手動' type exists)
- Filtering conditions simplified (no manual mapping exclusions)
- Database operations streamlined (2 tables instead of 3)

## Troubleshooting Common Issues

### Module Cache Issues
- Python caching can prevent code changes from taking effect
- Clear all cache: `rmdir /s /q __pycache__ & rmdir /s /q data_sources\__pycache__ & del /s *.pyc`
- Kill Python processes: `wmic process where "name='python.exe'" delete`

### Database Schema Updates
- Schema migration is automatic via ALTER TABLE pattern (no recreation needed)
- If migration fails, delete `./Database/mapping.db` to force full schema recreation
- Always test with existing database to verify backward compatibility
- Migration logs appear in application logs during startup

### API Authentication Failures
- rBOM API uses `X-API-KEY` header, not Bearer tokens
- Verify API key format: `oG5^Ls%#20yq` (exact characters including ^ and %)
- Test connectivity: `curl -H "X-API-KEY: oG5^Ls%#20yq" http://pfw-api/orders/?year=2025&month=8`

### UI State Management
- Interactive checkboxes require `st.rerun()` to reflect changes
- Button key conflicts resolved with unique key attributes
- Fixed mapping operations need database changes to persist across sessions

### Data Issues
- Empty results usually indicate date range or connectivity problems
- Check EJ data filtering if expected orders don't appear
- Fixed mappings excluded from auto-mapping source data by design

## Recent Changes and Bug Fixes

### 2025-11-17 Updates

**Fixed Mapping Feature Improvements**:
- Fixed is_fixed filtering logic to work with SQLite integer storage (0/1 instead of False/True)
- Added comprehensive debug logging for is_fixed column value distribution analysis
- Increased SQLite connection timeout from 5 to 30 seconds to prevent "database is locked" errors
- Added spinner visual feedback for all long-running operations:
  - マッピング済固定 (Fix Completed Mappings)
  - 全固定解除 (Bulk Unfix All)
  - 固定解除 (Individual Unfix)
  - 自動マッピング (Auto-mapping)
- Improved fixed mapping search UI: only display results when search field has input (empty search = no display)
- Removed 100-record display limit for fixed mapping search results (now shows all results)

**Critical Implementation Notes**:
- **is_fixed Filtering Pattern** (発注残マッピングリスト.py lines 486-507):
  ```python
  # SQLite stores BOOLEAN as 0/1 integers
  target_data = mapping_data_raw[
      (mapping_data_raw['status'].isin(['済', '済2'])) &
      ((mapping_data_raw['is_fixed'] == 0) | (mapping_data_raw['is_fixed'].isna()))
  ]
  ```
- **Database Timeout Configuration** (db_manager.py line 41):
  ```python
  conn = sqlite3.connect(self.db_path, timeout=30.0)
  ```

### 2025-10-30 Updates

**Feature Addition - 備考マッピング (Remarks Mapping)**:
- Added Phase 6 to mapping engine for matching EJ item codes with rBOM MK020 notes
- Status '済2' introduced to distinguish remarks mapping from standard mapping
- 170 successful mappings achieved in initial production run

**Critical Bug Fixes**:

1. **Status Display Issue** (db_manager.py line 425):
   - **Problem**: Status '済2' not displaying despite correct database storage
   - **Root Cause**: Hardcoded empty string instead of reading actual status value
   - **Fix**: Changed to `result.get('status', '')`
   - **Commit**: ac194c9

2. **Delivery Date Check Missing in Phase 6** (mapper.py lines 747-766):
   - **Problem**: Remarks mapping didn't check delivery date tolerance
   - **Root Cause**: Phase 6 logic didn't include `_check_delivery_date_condition()` call
   - **Fix**: Added same delivery date checking as Phase 3
   - **Commit**: ac194c9

3. **delivery_date_dt Field Missing** (mapper.py lines 50-54):
   - **Problem**: Datetime field was None in Phase 6 checks
   - **Root Cause**: Field only added to sorted DataFrames, not original DataFrames used in Phase 4-5 temporary lists
   - **Fix**: Added datetime conversion immediately after DataFrame creation
   - **Commit**: ac194c9

4. **Previous Execution Time Not Persisting** (発注残マッピングリスト.py lines 208-231):
   - **Problem**: Execution time showed "なし" on browser refresh despite database storage
   - **Root Cause**: Database initialization happened AFTER UI display
   - **Fix**: Moved database initialization before col4/col5 rendering
   - **Commit**: 7900c63

5. **rbom_line_no Stored as Blob** (db_manager.py lines 419, 497):
   - **Problem**: Integer field saved as binary blob: `b'\x01\x00\x00\x00\x00\x00\x00\x00'`
   - **Root Cause**: Pandas data types not properly converted to SQLite INTEGER
   - **Fix**: Explicit int() conversion: `int(result.get('rbom_line_no')) if pd.notna(result.get('rbom_line_no')) else None`
   - **Status**: Requires database recreation to take effect
   - **Commit**: Not yet pushed (pending database recreation)

**UI Improvements**:
- Changed column ratios from `[2, 2, 1, 2, 2.5]` to `[2, 2, 2, 2, 1.5]`
- Split previous execution time display into 2 lines for better readability
- Commit: 7900c63

## Claude Code Development Guidelines

### Thinking Approach (CRITICAL)
- **ALWAYS use systematic analysis**: Think deeply and systematically before taking any action
- **Sequential Analysis**: Break down complex problems into logical steps
- **Root Cause Investigation**: Identify fundamental causes rather than applying superficial fixes
- **Evidence-Based Decision Making**: Use debug logs and systematic testing to guide solutions

### Debug Logging Philosophy
When encountering any error or unexpected behavior:

1. **Implement Comprehensive Debug Logging**
   - Create debug output mechanisms
   - Log to files with timestamps for historical analysis
   - Include both console and file output

2. **Information-Rich Logging**
   - Log data structures with detailed type information
   - Include before/after states for data transformations
   - Record function entry/exit points with parameters
   - Track pandas.NA, None, and type conversion issues
   - Log SQL query parameters and affected row counts

3. **Systematic Error Analysis**
   - Implement debug logging BEFORE attempting fixes
   - Use logs to identify patterns and root causes
   - Preserve debug information for future reference
