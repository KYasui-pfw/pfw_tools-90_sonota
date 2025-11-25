# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a Docker-based scheduled data extraction application that runs on Linux servers. It performs four main processes every 15 minutes:

1. **Process 1 (process1.py)**: Copies and transforms CSV files from rBOM directory with column deletion and deduplication
2. **Process 2 (process2.py)**: Extracts tables from Microsoft Access databases (.accdb) using UCanAccess JDBC driver
3. **Process 3 (process3.py)**: Sends EJ completion data to FastAPI `/completion` endpoint
4. **Process 4 (process4.py)**: Sends Cylinder/Dial completion data to FastAPI `/completion` endpoint

Process 1 and 2 run in parallel, followed by sequential execution of Process 3 and 4. All processes are designed for Japanese manufacturing environments with UTF-8/CP932/Shift-JIS encoding support.

## Build and Deployment Commands

```bash
# Build Docker image
docker-compose build

# Start container (runs immediately on startup + every 15 minutes via cron)
docker-compose up -d

# View logs (real-time)
docker-compose logs -f

# Stop container
docker-compose down

# Rebuild after code changes
docker-compose down && docker-compose build && docker-compose up -d
```

## Testing Commands

```bash
# Execute inside container
docker-compose exec camcyl-app bash

# Manual test - Process 1 only
docker-compose exec camcyl-app python /app/scripts/process1.py

# Manual test - Process 2 only
docker-compose exec camcyl-app python /app/scripts/process2.py

# Manual test - All processes (full pipeline)
docker-compose exec camcyl-app /app/scripts/run_all.sh

# Manual test - Process 3 only
docker-compose exec camcyl-app python /app/scripts/process3.py

# Manual test - Process 4 only
docker-compose exec camcyl-app python /app/scripts/process4.py

# Check cron status
docker-compose exec camcyl-app pgrep cron
docker-compose exec camcyl-app cat /etc/cron.d/camcyl-cron
```

## Architecture

### Execution Flow

```
Container Start
    ↓
entrypoint.sh
    ↓
run_all.sh (startup execution)
    ├─ process1.py (parallel)
    └─ process2.py (parallel)
    ↓
Both succeed?
    ↓ YES
process3.py (sequential)
    ↓
process3 succeeds?
    ↓ YES
process4.py (sequential)
    ↓
cron -f (foreground)
    ↓
Every 15 minutes → run_all.sh
```

### Critical Design Decisions

**Environment Variable Handling**: The crontab directly reads the `.env` file using `export $(grep -v '^#' .env | xargs)` before executing scripts. This is essential because:
- Cron jobs don't inherit Docker container environment variables by default
- The `.env` file is explicitly loaded in the crontab command: `cd /app && export $(grep -v '^#' .env | xargs) && /app/scripts/run_all.sh`
- Python scripts also use `load_dotenv()` for redundant loading when manually executed
- This ensures READ_API_KEY, INSERT_API_KEY, and FASTAPI_BASE_URL are available during cron execution
- **Critical**: Without this, process3.py and process4.py will fail with "API key not set" errors during scheduled runs

**Encoding Auto-Detection**: process1.py tries multiple encodings sequentially (`utf-8-sig`, `utf-8`, `cp932`, `shift_jis`, `latin1`) because source CSV files may use different Japanese character encodings. This prevents UnicodeDecodeError failures.

**Process 1 CSV Transformation Pipeline**: process1.py performs sequential transformations on CSV files:
1. **Column Deletion**: Removes specified columns via `DELETE_COLUMNS_FILE1/FILE2`
2. **Column Renaming**: Applies mappings via `RENAME_COLUMNS_FILE1/FILE2` (e.g., "仕入先コード:払出先")
3. **Deduplication**: Removes duplicate rows across all columns (or Advanced Deduplication for ASPKakouDenpyo.csv)
4. **Zero Row Filtering**: For CONV.csv and SEISANKI.csv, removes rows where 数量/セットアップ/スペア are all zero
5. **Type Conversion**: Converts 生産月次 and 払出先 columns to int (empty values preserved)
6. **Column Reordering**: Rearranges columns via `REORDER_COLUMNS_FILE1/FILE2` (applied after all other transformations)
7. **Output**: Saves as cp932-encoded CSV

**Important**: Column names in `REORDER_COLUMNS_FILE2` must match exactly (e.g., "伝票No" with half-width "No", not full-width "Ｎｏ"). Mismatched names will result in incorrect column ordering.

**Process 1 Advanced Deduplication (ASPKakouDenpyo.csv only)**: Uses FastAPI integration for intelligent deduplication:
1. **API Call**: `fetch_oyalistno_from_api()` calls `/instructions/slip/batch` to get OYALISTNO for each (伝票No, 行番号) pair
2. **Stage 1**: Groups by (伝票No, OYALISTNO), keeps first row of each group
3. **Stage 2**: For same 伝票No with different OYALISTNOs, sums 必要数 and keeps one row
4. **Critical**: FastAPI returns response with **uppercase keys** (INDNO, LINENO, OYALISTNO) due to Pydantic alias settings. The code must use `item.get('INDNO')` not `item.get('indno')`.

**UCanAccess Integration**: process2.py requires Java runtime and UCanAccess JAR files to read Access databases without Microsoft Access installed. The JDBC connection string format is `jdbc:ucanaccess://{path}`.

**LEFT JOIN Support**: process2.py supports optional LEFT JOIN operations. When `JOB_TABLE_NAME` is specified in .env, the first database (Cyl_pfw_table.accdb) performs a LEFT JOIN between `KaLstCyl_All` and the specified job table using the join condition `KaLstCyl_All.KUMITATENO_Job = ジョブ.lotCode`, adding all columns from the job table to the output.

**FastAPI Integration (Process 3 & 4)**: Both processes use async HTTP communication via httpx to send completion records to the FastAPI rBOM system. Key patterns:
- **Network**: Containers communicate via `app-shared-net` Docker network
- **Status Checking**: Batch status checks using `/instructions/slip/batch` endpoint before sending
- **Status Logic**: Replicates NiceGUI's status determination (only sends 未完了/登録エラー records)
- **Error Handling**: Missing rBOM data logged as ERROR + WARNING
- **Date Filtering**: Process 3 filters last 7 days + tomorrow (8 days total)
- **4-Month Window**: Process 4 searches current month + 3 future months for instructions

**Process 4 CAT2 Pattern Mapping**: Complex mapping system for Cylinder (405) and Dial (409) data:
- **405 Pattern**: 10 date columns (resultStart, resultEnd, JOB_1-8) → KTCD values (SL1ST, SL1, DDQT, SL1FIN, etc.)
- **409 Pattern**: 10 date columns → different KTCD values (DDCUT, DDQT, DRCUT, DIFIN, etc.)
- **DENPYONO→SEINO Lookup**: Required before instruction filtering
- **Fixed Values**: IPTANCD="SECT1707", prdqty=1, ktedqty=1

### Key Components

**entrypoint.sh**: Container startup script that:
- Executes initial data extraction via run_all.sh
- Displays crontab configuration for verification
- Starts cron in foreground mode (`exec cron -f`) to keep container alive
- Does NOT export environment variables (handled by crontab itself)

**run_all.sh**: Orchestration wrapper that:
- Launches process1.py and process2.py as background jobs (parallel)
- Waits for both to complete
- If both succeed, runs process3.py sequentially
- If process3 succeeds, runs process4.py sequentially
- Returns combined exit status

**process3.py**: EJ completion data sender:
- Reads `EJデータマスター_CAMFIN_LOG_ALL.csv`
- Filters DATE column (1週間前～翌日, 8 days)
- Checks instruction status via batch endpoint
- Sends to `/completion` with mapping: KTEDDT←DATE, INDNO←SRNO, lineno←1, IPTANCD←"SECT1836", prdqty/ktedqty←FINUM

**process4.py**: Cylinder/Dial completion data sender:
- Reads `Cyl_pfw_table_KaLstCyl_All.csv`
- Detects CAT2 pattern (last 3 chars: 405=CYLINDER, 409=DIAL)
- For each row: DENPYONO → get SEINO → filter 4-month instruction data
- Checks 10 date columns (resultStart, resultEnd, JOB_1-8)
- Maps each date to KTCD/HMNM based on pattern
- Sends to `/completion` with IPTANCD←"SECT1707", prdqty/ktedqty←1

**logger_config.py**: Shared logging module providing:
- Daily log rotation with 7-day retention
- Date-stamped log files (`process1_YYYYMMDD.log`)
- Automatic cleanup of old logs

## Environment Configuration

**Required Setup** (Linux server only):
1. Mount network drive: `sudo mount -a` (configure in /etc/fstab)
2. Create output directories: `/home/docker-user/KakouDenpyo` and `/home/docker-user/KakouJisseki`
3. Create .env from .env.example: `cp .env.example .env`

**Critical .env Variables**:
- `CSV1_PATH` through `CSV4_PATH`: Source CSV file paths (Process 1)
- `ACCDB_SOURCE1`, `ACCDB_SOURCE2`: Access database UNC paths (Process 2, must be mounted to /mnt/schejule)
- `DELETE_COLUMNS_FILE1`, `DELETE_COLUMNS_FILE2`: Comma-separated column names to delete (Process 1)
- `RENAME_COLUMNS_FILE1`, `RENAME_COLUMNS_FILE2`: Column rename mappings in format "old:new,old2:new2" (Process 1)
- `REORDER_COLUMNS_FILE1`, `REORDER_COLUMNS_FILE2`: Column order specification in format "col1,col2,col3,..." (Process 1)
- `TABLE1_NAME`, `TABLE2_NAME`: Access table names to extract (Process 2)
- `JOB_TABLE_NAME`: Job table name for LEFT JOIN with TABLE1 (Process 2, default: "ジョブ")
- `PROCESS3_CSV_PATH`: EJ data CSV input path (Process 3)
- `PROCESS4_CSV_PATH`: Cyl/Dial data CSV input path (Process 4)
- `FASTAPI_BASE_URL`: FastAPI server URL (Process 3 & 4, default: http://fastapi-rbom-app:8000)
- `READ_API_KEY`: API key for status checks (Process 3 & 4)
- `INSERT_API_KEY`: API key for completion writes (Process 3 & 4)

## Volume Mounts

docker-compose.yml expects these host paths:
- `/mnt/schejule` (read-only): Network drive with Access databases
- `/home/docker-user/rBOM` (read-only): Source CSV files
- `/home/docker-user/KakouDenpyo`: Process 1 output
- `/home/docker-user/KakouJisseki`: Process 2 output
- `./data`: Temporary Access DB copies
- `./logs`: Application logs

## Troubleshooting

**Environment variables not loading during cron execution**:
- Verify crontab includes `.env` loading: `cat /etc/cron.d/camcyl-cron` should show `export $(grep -v '^#' .env | xargs)`
- Check `.env` file exists in `/app/` directory: `docker-compose exec camcyl-app ls -la /app/.env`
- Test manual execution: `docker-compose exec camcyl-app bash -c "cd /app && export $(grep -v '^#' .env | xargs) && env | grep API_KEY"`
- Common cause: `.env` file not copied to container or `.env` syntax errors (spaces around `=` are not allowed)

**CSV encoding errors**: Confirm process1.py includes the encoding auto-detection loop. The application tries 5 encodings before failing.

**Column reordering not working**: Verify:
1. Column names in `REORDER_COLUMNS_FILE2` match exactly (check half-width vs full-width characters)
2. `.env` file was rebuilt into container: `docker-compose down && docker-compose build && docker-compose up -d`
3. Check logs for "カラム並び替え: N列を指定順に並び替え" message
4. Common issue: "伝票Ｎｏ" (full-width No) vs "伝票No" (half-width No) mismatch

**Access DB connection failures**: Verify:
1. UCanAccess JAR files exist in `ucanaccess_lib/` (5 files required)
2. Network drive is mounted: `docker-compose exec camcyl-app ls /mnt/schejule`
3. Java is available: `docker-compose exec camcyl-app java -version`

**Cron not executing**: Check:
1. `docker-compose exec camcyl-app pgrep cron` returns a PID
2. `/etc/cron.d/camcyl-cron` has 0644 permissions
3. Container logs show "cron is running"

**Process 3/4 FastAPI connection failures**: Verify:
1. `app-shared-net` Docker network exists: `docker network ls | grep app-shared-net`
2. FastAPI container is running: `docker ps | grep fastapi-rbom-app`
3. API keys are correctly set in .env file
4. Container can resolve hostname: `docker-compose exec camcyl-app ping fastapi-rbom-app`

**Process 3/4 rBOM data not found errors**:
- Check logs for "✗ エラー: rBOMシステムにデータが存在しません" messages
- Verify INDNO values exist in rBOM system via `/instructions/slip/batch` endpoint
- This is a critical error indicating missing master data in the rBOM system

**Process 4 CAT2 pattern issues**:
- Verify CAT2 column contains values ending in "405" (CYLINDER) or "409" (DIAL)
- Check DENPYONO→SEINO lookup is successful (requires valid DENPYONO in rBOM)
- Confirm 4-month instruction data window covers expected date ranges

**Process 1 OYALISTNO all None (Advanced Deduplication failure)**:
- **Symptom**: Log shows "マッピング辞書作成: 0件" and "OYALISTNO 追加結果: 取得=0件"
- **Cause**: FastAPI returns uppercase keys (INDNO, LINENO, OYALISTNO) but code was using lowercase
- **Solution**: Ensure `fetch_oyalistno_from_api()` uses `item.get('INDNO')`, `item.get('LINENO')`, `item.get('OYALISTNO')` (uppercase)
- **Verification**: Check logs for "不正なデータをスキップ: INDNO=None, LINENO=None" - if all records show None, key case mismatch is likely

## File Modifications

When editing Python scripts or shell scripts, rebuild the Docker image to deploy changes. The `./scripts` volume mount in docker-compose.yml is for development convenience but does not replace the image build process for production deployment.

**Important**: The `.env` file is copied into the container during build (`COPY .env /app/.env` in Dockerfile). It must exist in the build context before running `docker-compose build`.

When modifying .env variables:
- **Always requires rebuild**: `docker-compose down && docker-compose build && docker-compose up -d`
- The `.env` file is baked into the image, not volume-mounted
- Changes to `.env` on the host will NOT be reflected until rebuild
