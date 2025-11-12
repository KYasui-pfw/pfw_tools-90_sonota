# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains a 6-stage data processing pipeline that generates four manufacturing master data files for an external vendor (outsourced parts) management system. The pipeline extracts data from KRD and EJ (Oracle) databases, processes CSV files with filtering and transformation logic, and outputs master data files for rBOM system integration.

## Key Commands

### Execute Full Pipeline (Sequential Order Required)
```bash
cd "C:\Dev\90_tools\90_temp\01_品目工程・品目構成"

# Stage 1: Database extraction and preprocessing
python 00_extract_krd_data.py

# Stage 2: CSV integration, filtering, and expansion
python 01_integrated_process.py

# Stage 3: M0910 item purchase price master creation
python 02_create_m0910_master.py

# Stage 4: MK020 item purchase process price master creation
python 03_create_mk020_master.py

# Stage 5: M0850 item composition master creation
python 04_create_item_composition_master.py

# Stage 6: M0840 item process master creation
python 05_create_item_process_master.py
```

**Critical**: Scripts must be executed in numerical order (00 → 05). Each stage depends on output from previous stages.

### Verify Pipeline Output
```bash
# Check intermediate work files
ls -lh work/

# Check final output files (4 master files expected)
ls -lh output/

# Verify specific master data
head -5 output/M0840_品目工程マスタ.csv
head -5 output/M0850_品目構成マスタ.csv
head -5 output/M0910_品目仕入単価マスタ.csv
head -5 output/MK020_品目仕入工程単価マスタ.csv
```

### Database Connection Verification
```bash
# Test EJ Oracle database connectivity
python -c "import cx_Oracle; conn = cx_Oracle.connect('EXPJ2/EXPJ2@172.17.107.102:1521/EXPJ'); print('EJ connection OK'); conn.close()"

# Test KRD MySQL database connectivity
python -c "import pymysql; conn = pymysql.connect(host='krd', user='pfw', password='mejiriHoo', database='machin'); print('KRD connection OK'); conn.close()"
```

## Pipeline Architecture

### Data Flow Overview
```
[Input Files]                 [Stage 00]              [Work Files]
├─ 前工程横展開.csv       →  extract_krd_data   →  01~05_*.csv
├─ 前工程横展開(I).csv
├─ 前工程横展開(C).csv
├─ 購買課CSVs (3 files)
├─ PEFINソート.csv
├─ M0410_工程マスタ.csv
└─ 加工実績部番.csv

[Work Files]                  [Stage 01]              [Work Files]
01~05_*.csv              →  integrated_process  →  06~14_*.csv
                                                      ├─ 13_品目構成work.csv
                                                      └─ 14_品目工程work.csv

[Work + EJ DB]                [Stages 02-05]          [Output Files]
13_品目構成work.csv      →  create_*_master     →  M0910/MK020/M0850/M0840
14_品目工程work.csv
+ EJ Oracle queries
```

### Key Data Transformations

**00_extract_krd_data.py**: Database Extraction
- KRD database → 03_マシニング課管理工程.csv (in-house machining exclusion list)
- EJ M_ITEM (PRODUCT_TYP 6/7/8) → 04_EJ678.csv (in-house processing exclusion list)
- 加工実績部番.csv + EJ M_ITEM → 05_EJ_M_ITEM_生技実績突合.csv (PEFIN process candidates)

**01_integrated_process.py**: CSV Integration and Filtering
- Concatenates 3 前工程横展開 files (vertical join)
- **Complex Exclusion Logic**:
  - Machining department processes (03_マシニング課管理工程.csv match)
  - In-house processing items (04_EJ678.csv match)
  - Purchasing department exclusions (01_購買課_対象外.csv)
  - SKD/SUJ suffix processes (rightmost column filtering)
  - TS-prefix part numbers
  - Hardcoded exceptions (13 specific part numbers)
- **MA-prefix separation**: Determines material vs. process classification
- **Horizontal → Vertical expansion**: 6 columns (前工程1~6) → 6 rows per part number
- **Outputs**: 13_品目構成work.csv (materials) and 14_品目工程work.csv (processes)

**02_create_m0910_master.py**: M0910 Item Purchase Price Master
- **Key field**: HMCD ← 前工程 (material code with MA- prefix)
- **EJ Integration**: M_PUCH_UNIT_COST_H + M_PUCH_UNIT_COST (900-item batch processing)
- **Vendor Selection**: PUCH_PRIORITY_REF_NO min → EFF_PHASE_IN_DATE latest → unique
- **Fallback**: T_RLSD_PUCH_ODR when primary data unavailable
- **Critical**: SRCD/PRICE/VALDTF/VALQTY must come from same record

**03_create_mk020_master.py**: MK020 Item Purchase Process Price Master
- **Key fields**: OYAHMCD ← 完成部番, KTCD ← 前工程 (extracted before hyphen)
- **PEFIN Positioning**: PEFINソート.csv controls PEFIN process sequence (0=delete, 1=first, 2=second, 3=third)
- **KTCD Conversion**: A0→AO, PA1/PA2→PA
- **Same EJ integration** as M0910 but keyed by process code

**04_create_item_composition_master.py**: M0850 Item Composition Master
- **Simple CSV transformation** (no EJ database access)
- Maps 完成部番→OYAHMCD, 前工程→KOHMCD
- Quantity conversion: 単位数分子→KOQTY, 単位数分母→OYAQTY (0→1)

**05_create_item_process_master.py**: M0840 Item Process Master
- **Most complex script** with multi-source data integration
- **Critical Key Usage**: All EJ lookups (SRCD/SRPRICE/LDTIME) use **前工程 as key**, NOT 完成部番
- **LDTIME Source**: EJ M_ITEM.PUCH_FIXED_LT (keyed by 前工程, NOT 完成部番) ← **This was a past bug**
- **PEFIN Special Handling**: LDTIME=0, SRPRICE=0, CSBCD='10', RCVTSTKBN='2', RCVCHKKBN='2'
- **SEQ/KTSEQ**: Auto-numbering (1-based, 10-based) with PEFIN position control
- **Exceptions**: KS91-03006BA and KD64-00202BA are excluded from processing

## Critical Implementation Patterns

### EJ Database Integration (Oracle)
All scripts using EJ data implement:
1. **Batch Processing**: 900-item chunks to avoid Oracle IN clause limit (1000)
2. **Priority Selection**: 3-tier sorting (PUCH_PRIORITY_REF_NO → EFF_PHASE_IN_DATE → PUCH_SIZE)
3. **Fallback Strategy**: M_PUCH_UNIT_COST_H/M_PUCH_UNIT_COST → T_RLSD_PUCH_ODR
4. **Future Date Exclusion**: EFF_PHASE_IN_DATE < 2025-12-01
5. **Same-Record Consistency**: SRCD/PRICE/DATE/QTY from identical record

Connection pattern:
```python
def ej_data_get(sql):
    connection_string = "EXPJ2/EXPJ2@172.17.107.102:1521/EXPJ"
    connection = cx_Oracle.connect(connection_string)
    df = pd.read_sql(sql, connection)
    connection.close()
    return df
```

### Key Field Mapping Rules

**CRITICAL**: Different scripts use different keys for EJ lookups:

| Script | EJ Lookup Key | Why |
|--------|--------------|-----|
| 02_create_m0910_master.py | 前工程 (zenkatei) | Material codes are in 前工程 field |
| 03_create_mk020_master.py | 前工程 (zenkatei) | Process codes are in 前工程 field |
| 05_create_item_process_master.py | 前工程 (zenkatei) | **All fields (SRCD/SRPRICE/LDTIME) use 前工程** |

**Past Bug**: 05_create_item_process_master.py previously used 完成部番 for LDTIME lookup, causing incorrect lead times. Now fixed to use 前工程 consistently.

### PEFIN Process Control Logic
PEFINソート.csv contains 前工程 values:
- **0**: Delete PEFIN row entirely, renumber SEQ/KTSEQ
- **1**: Place PEFIN at SEQ=1 (first position)
- **2**: Place PEFIN at SEQ=2 (second position)
- **3**: Place PEFIN at SEQ=3 (third position)

Implementation in 03 and 05 scripts handles SEQ reordering before final output.

### Data Validation Patterns
- **Empty Field Handling**: Convert 0 quantities to 1, convert NaN to empty string or 0
- **VALQTY Special Rule**: If PUCH_SIZE=1, convert to 0 in output
- **Date Formatting**: Oracle TIMESTAMP → YYYY/MM/DD string (remove time portion)
- **Exception Handling**: Specific part numbers bypass normal processing logic

## Input File Requirements

### Required Input Files (input/ directory)
```
前工程横展開.csv              # Primary process data
前工程横展開(I).csv           # Secondary process data
前工程横展開(C).csv           # Tertiary process data
01_購買課_対象外.csv          # Purchasing exclusion list
02_購買課_MA変換.csv          # MA-prefix conversion rules
03_購買課_そのまま.csv        # Force-include material list
PEFINソート.csv              # PEFIN positioning instructions
M0410_工程マスタ.csv         # Process master (KTCD validation)
加工実績部番.csv             # Production results part numbers
```

### CSV Encoding
All CSV files use **UTF-8 with BOM** (utf-8-sig). Scripts attempt multiple encodings (utf-8, shift_jis, cp932) for compatibility.

### Input File Structure
- **前工程横展開 files**: Header + data rows, structure: 完成部番 | (単位数分子N, 単位数分母N, 前工程N) × 6 sets
- **購買課 files**: 2 columns: 完成部番, additional data
- **PEFINソート.csv**: 2 columns: 完成部番, 前工程 (0/1/2/3)

## Output Master Data Files

All outputs in `output/` directory:

| File | Rows | Purpose | Key Fields |
|------|------|---------|------------|
| M0910_品目仕入単価マスタ.csv | ~3,932 | Item purchase price | HMCD(=前工程), SRCD, PRICE |
| MK020_品目仕入工程単価マスタ.csv | ~10,439 | Item purchase process price | OYAHMCD, KTCD, SRCD, SRPRICE |
| M0850_品目構成マスタ.csv | ~3,932 | Item composition (BOM) | OYAHMCD, KOHMCD, KOQTY, OYAQTY |
| M0840_品目工程マスタ.csv | ~4,532 | Item process routing | HMCD, SEQ, KTSEQ, KTCD, LDTIME |

### Master Data Relationships
```
M0850: Parent-Child BOM structure (完成部番 → MA-材料)
M0840: Process routing (完成部番 → 工程1 → 工程2 → ...)
M0910: Material pricing (MA-材料 → vendor/price)
MK020: Process pricing (完成部番 + 工程 → vendor/price)
```

## Troubleshooting

### Common Issues

**"Oracle IN clause too many items"**
- Cause: Attempting to query >1000 items in single SQL
- Solution: Batch processing already implemented (900-item chunks)
- Check: Verify `batch_size = 900` in scripts 02/03/05

**"LDTIME value incorrect for specific KTCD"**
- Cause: Using wrong key (完成部番 instead of 前工程) for M_ITEM lookup
- Solution: Always use 前工程 (zenkatei_key) for all EJ lookups
- Verify: Check line 275 in 05_create_item_process_master.py uses `ldtime_dict.get(zenkatei_key, 0)`

**"PEFIN row appears in wrong position"**
- Cause: PEFINソート.csv missing or incorrect 前工程 value
- Solution: Verify PEFINソート.csv contains target part number with correct positioning value (1/2/3)
- Debug: Check console output "=== PEFINソート.csv前工程情報取得 ===" for loaded entries

**"Duplicate records in output"**
- Cause: Multiple vendor records from EJ not properly deduplicated
- Solution: Priority selection logic (PUCH_PRIORITY_REF_NO min) should handle this
- Check: Verify `ORDER BY` clauses in EJ SQL queries include all priority fields

**"Missing SRCD/PRICE for certain items"**
- Cause: Item not found in M_PUCH_UNIT_COST, fallback also fails
- Expected: Scripts output empty SRCD and 0 for PRICE
- Verify: Check "フォールバック取得" log messages for fallback usage statistics

### Verification Commands

```bash
# Count output records
wc -l output/*.csv

# Check for empty SRCD (data quality issue)
grep -c ",," output/M0840_品目工程マスタ.csv

# Verify specific part number processing
grep "K-24913AB" output/M0840_品目工程マスタ.csv

# Check PEFIN positioning
grep "PEFIN" output/M0840_品目工程マスタ.csv | head -10

# Validate LDTIME values (should match EJ M_ITEM.PUCH_FIXED_LT for 前工程)
# Manual verification required via SQL query
```

## Database Schema References

### EJ Oracle Database (EXPJ2 schema)
- **M_ITEM**: Item master (ITEM_CD, PUCH_FIXED_LT, PRODUCT_TYP)
- **M_PUCH_UNIT_COST_H**: Purchase unit cost header (ITEM_CD, VEND_CD, PUCH_PRIORITY_REF_NO)
- **M_PUCH_UNIT_COST**: Purchase unit cost (ITEM_CD, VEND_CD, UNIT_COST, EFF_PHASE_IN_DATE, PUCH_SIZE)
- **T_RLSD_PUCH_ODR**: Released purchase order (ITEM_CD, VEND_CD, UNIT_COST, PUCH_ODR_DLV_DATE)

### KRD MySQL Database
- **machin.DATA_RES_CAPA**: Machining department capacity (品番, 工程)

Connection details in 00_extract_krd_data.py and 05_create_item_process_master.py.

## Development Notes

### Modifying Exclusion Logic
If adding new exclusion rules to 01_integrated_process.py:
1. Add CSV file to `input/` directory
2. Load CSV in script after line 140
3. Add filtering condition in exclusion logic section (lines 200-350)
4. Update `07_matched_前工程横展開.csv` output (excluded data)
5. Remaining data flows to `08_unmatched_前工程横展開.csv`

### Adding New Master Data Output
If creating new master file:
1. Create new script `0X_create_*_master.py`
2. Choose input: `13_品目構成work.csv` (materials) or `14_品目工程work.csv` (processes)
3. Follow EJ integration pattern from scripts 02/03/05
4. Output to `output/` directory with `.csv` extension
5. Update documentation in `外注分：品目構成マスタ・品目工程マスタ.md`

### Encoding Handling Pattern
All scripts use try-except with multiple encoding attempts:
```python
for encoding in ['utf-8', 'shift_jis', 'cp932']:
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
```

Follow this pattern for all new CSV reading operations.
