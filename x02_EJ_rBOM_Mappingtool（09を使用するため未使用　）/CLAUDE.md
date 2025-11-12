# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an EJ-rBOM mapping tool - a Streamlit web application that maps order backlog data between EJ (legacy Oracle-based production management system) and rBOM (new API-based system) during a system migration. The tool provides automatic, manual, and fixed mapping capabilities with interactive UI for managing mapping states.

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

# Test module connectivity
python test_modules.py
```

## Architecture Overview

### Multi-Tier Mapping System
```
EJ Oracle DB → MappingEngine → SQLite (3 tables) → Streamlit UI → CSV Export
rBOM API     ↗                      ↘
```

The application implements a sophisticated mapping system with three persistence layers:
1. **EJ System**: Oracle database (172.17.107.102:1521/EXPJ) with order backlog data from T_RLSD_PUCH_ODR + M_ITEM tables
2. **rBOM System**: REST API (http://pfw-api/orders/) with X-API-KEY authentication
3. **SQLite Storage**: Three-table design for flexible mapping management

### Core Components

- **`発注残マッピングリスト.py`**: Main Streamlit application with two-tier UI layout (extraction controls + mapping operations)
- **`data_sources/`**: External system connectors (EJConnector for Oracle, RBOMConnector for API)
- **`mapping/mapper.py`**: Advanced mapping engine with manual/fixed mapping exclusion logic
- **`database/db_manager.py`**: SQLite operations managing three interconnected tables
- **`ui/components.py`**: Interactive data grid using st.data_editor with checkbox controls
- **`pages/`**: Multi-page Streamlit structure (manual mapping page is prototype-level)

### Three-Table Database Design

**1. mapping_results** (Unified display table):
- Combines automatic, manual, and fixed mapping results for UI display
- Includes `is_fixed` boolean flag and `mapping_type` ('自動'/'手動')
- Cleared and rebuilt on each auto-mapping execution

**2. manual_mappings** (Persistent manual mappings):
- Stores user-created manual mappings that persist across auto-mapping runs
- Data excluded from source datasets during auto-mapping to prevent conflicts

**3. fixed_mappings** (User-locked mappings):
- Stores mappings that users want to preserve unchanged
- Managed via interactive checkboxes in the UI with bulk select/deselect operations
- Excluded from auto-mapping and re-added as fixed results

### Advanced Mapping Logic

The mapping engine processes data in this sequence:
1. **Exclusion Phase**: Remove manual/fixed mapping keys from source EJ/rBOM data
2. **Re-injection Phase**: Add manual mappings (type='手動') and fixed mappings (type='自動', fixed=true)
3. **Auto-mapping Phase**: Standard item_code + quantity matching on remaining data
4. **Classification**: Results categorized as MATCHED, EJ_ONLY, RBOM_ONLY

### Key Business Rules

- **Date Restriction**: All data extraction limited to delivery dates ≥ 2025-07-01 (hard-coded constraint)
- **EJ Filtering**: Additional filter `ACPT_CMPLT_DATE IS NULL` to exclude completed orders
- **Mapping Strategy**: Primary match on exact `item_code + quantity` combination
- **Fixed Mapping Scope**: Only applies to '自動' mapping type (manual mappings are always fixed)
- **CSV Export**: Always use Shift_JIS encoding for Japanese Excel compatibility

## Important Implementation Details

### Database Schema Evolution
The system uses a three-table approach for maximum flexibility:
- **mapping_results**: 20 fields including EJ data (5), rBOM data (7), management (5), system (3)
- **manual_mappings**: 18 fields, same structure minus `is_fixed` (always true for manual)
- **fixed_mappings**: 18 fields, stores user-selected mappings for preservation

### Interactive UI Architecture

**Two-Tier Layout**:
- **Upper Tier**: Extraction conditions (collapsible) + Auto-mapping button
- **Lower Tier**: Fixed operation controls (固定登録 | 全選択 | 全解除) + target count display

**Data Grid Features**:
- Uses `st.data_editor` for interactive checkbox controls
- Only '固定' column is editable, all others disabled
- Manual mappings show "必ず固定" instead of checkboxes
- rBOM displays combined "発注番号+行番号" format (9+3 digits with '+' separator)

### UI Conventions
- **CSS Styling**: Uses config.py pattern for header compression and clean layout
- **Column Display Order**: EJ発注番号→EJ連番→EJ品目コード... then rBOM発注番号+行番号→rBOM連番→rBOM品目コード...
- **Index Hiding**: Always use `hide_index=True` for dataframe displays
- **Japanese Labels**: All UI text in Japanese, column headers translated from English field names

### Session Management
- DatabaseManager stored in `st.session_state` for persistence across interactions
- Database initialization happens once per session on first access
- Interactive state managed through streamlit rerun cycles for checkbox changes

## Configuration Requirements

### API Authentication (Critical)
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

## Troubleshooting Common Issues

### Module Cache Issues
- Python caching can prevent code changes from taking effect
- Clear all cache: `rmdir /s /q __pycache__ & rmdir /s /q data_sources\__pycache__ & del /s *.pyc`
- Kill Python processes: `wmic process where "name='python.exe'" delete`

### Database Schema Updates
- New three-table schema requires database recreation
- Delete `./Database/mapping.db` to force recreation with new schema
- Schema auto-initializes on first application startup

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
- Manual/fixed mappings excluded from auto-mapping source data by design

## Claude Code Development Guidelines

### Thinking Approach (CRITICAL)
- **ALWAYS use ULTRATHINK mode**: Think deeply, calmly, and systematically before taking any action
- **Sequential Analysis**: Break down complex problems into logical steps and analyze each component
- **Root Cause Investigation**: When encountering errors, identify the fundamental cause rather than applying superficial fixes
- **Evidence-Based Decision Making**: Use debug logs, data analysis, and systematic testing to guide solutions

### Debug Logging Philosophy
When encountering any error or unexpected behavior:

1. **Implement Comprehensive Debug Logging**
   - Create debug output mechanisms (like `debug_logger.py`)
   - Log to files with timestamps for historical analysis
   - Include both console and file output for immediate and persistent debugging

2. **Information-Rich Logging**
   - Log data structures with detailed type information
   - Include before/after states for data transformations
   - Record function entry/exit points with parameters
   - Track pandas.NA, None, and type conversion issues specifically
   - Log SQL query parameters and affected row counts

3. **Systematic Error Analysis**
   - Implement debug logging BEFORE attempting fixes
   - Use logs to identify patterns and root causes
   - Preserve debug information for future reference

### Windows Streamlit Process Management (Proven Method)

**Reliable Process Termination Sequence:**

1. **Identify Processes Using Port 8501**
   ```bash
   netstat -ano | findstr :8501
   ```
   This will show output like:
   ```
   TCP    0.0.0.0:8501    0.0.0.0:0    LISTENING    12345
   TCP    [::]:8501       [::]:0       LISTENING    12345
   ```

2. **Kill Main Process**
   ```bash
   powershell -Command "Stop-Process -Id 12345 -Force"
   ```

3. **Kill Related Browser Connections (if present)**
   Look for additional PIDs in the netstat output and kill them:
   ```bash
   powershell -Command "Stop-Process -Id 67890 -Force"
   ```

4. **Verify Port is Free**
   ```bash
   netstat -ano | findstr :8501
   ```
   Should return no results or "Error" indicating port is free

5. **Wait Before Restart**
   Allow 2-3 seconds before starting new Streamlit instance

**Why This Method Works:**
- `netstat -ano` reliably identifies exact processes using the port
- PowerShell `Stop-Process -Force` provides reliable termination
- Killing by specific PID avoids affecting other Python processes
- Verification step ensures clean startup environment

### Debugging Process Template

1. **Problem Identification**: Clearly describe the unexpected behavior
2. **Debug Implementation**: Add comprehensive logging to relevant functions
3. **Data Collection**: Execute the problematic operation and collect logs
4. **Analysis Phase**: Review logs systematically to identify root cause
5. **Solution Design**: Implement targeted fix based on evidence
6. **Verification**: Test fix and confirm resolution through logs