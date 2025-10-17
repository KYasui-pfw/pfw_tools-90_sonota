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
- **`data_sources/`**: External system connectors (EJConnector for Oracle, RBOMConnector for API)
- **`mapping/mapper.py`**: Simplified mapping engine with fixed mapping exclusion logic only
- **`database/db_manager.py`**: SQLite operations managing two tables
- **`ui/components.py`**: Interactive data grid using st.data_editor with checkbox controls

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

### Simplified Mapping Logic

The mapping engine processes data in this sequence:
1. **Exclusion Phase**: Remove fixed mapping keys from source EJ/rBOM data
2. **Re-injection Phase**: Add fixed mappings (type='自動', fixed=true)
3. **Auto-mapping Phase**: Standard item_code + quantity matching on remaining data
4. **Classification**: Results categorized as MATCHED, EJ_ONLY, RBOM_ONLY

### Key Business Rules

- **Date Restriction**: All data extraction limited to delivery dates ≥ 2025-07-01 (hard-coded constraint)
- **EJ Filtering**: Filter `PUCH_ODR_STS_TYP = 2` and `PUCH_ODR_TYP != 4`
- **Mapping Strategy**: Primary match on exact `item_code + quantity` combination
- **Fixed Mapping Scope**: Applies to all automatic mappings (no manual type exists)
- **CSV Export**: Always use Shift_JIS encoding for Japanese Excel compatibility

## Important Implementation Details

### Database Schema (Simplified)
The system uses a two-table approach:
- **mapping_results**: 20 fields including EJ data (7), rBOM data (7), management (3), system (3)
- **fixed_mappings**: 18 fields, stores user-selected mappings for preservation

### Interactive UI Architecture

**Single-Tier Layout**:
- **Controls**: Auto-mapping button + Fixed operation controls (マッピング確定情報更新 | 全選択 | 全解除)

**Data Grid Features**:
- Uses `st.data_editor` for interactive checkbox controls
- Only 'マッピング確定' column is editable, all others disabled
- All mappings are type '自動' (automatic)
- rBOM displays combined "発注番号+行番号" format (9+3 digits with '+' separator)

### UI Conventions
- **CSS Styling**: Compressed header and clean layout
- **Column Display Order**: EJ発注番号→EJ連番→EJ品目コード... then rBOM発注番号+行番号→rBOM連番→rBOM品目コード...
- **Index Hiding**: Always use `hide_index=True` for dataframe displays
- **Japanese Labels**: All UI text in Japanese

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
- Simplified two-table schema requires database recreation
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
- Fixed mappings excluded from auto-mapping source data by design

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
