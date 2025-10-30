# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System Overview

This is an automated error notification system for the rBOM manufacturing management system. It monitors Oracle database tables (DK020 for receiving/受入, DK040 for picking/棚出) for error records and sends email notifications to the employees who created those records.

## Running the Application

### Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with actual credentials

# Initialize database
python scripts/init_db.py

# Run monitor once (testing)
python -m app.monitor

# Run Streamlit admin UI
streamlit run streamlit_app/main.py --server.port=8507
```

### Docker Deployment
```bash
# Start services (monitor + admin UI)
docker-compose up -d --build

# View logs
docker logs rbom_error_monitor
docker logs rbom_admin_ui

# Check cron execution logs
docker exec rbom_error_monitor cat /app/logs/cron.log

# Check monitor logs
docker exec rbom_error_monitor cat /app/logs/monitor.log

# Restart services
docker-compose restart

# Stop services
docker-compose down
```

### Access Points
- **Admin UI**: http://localhost:8507
- **Monitor**: Runs automatically via cron every 5 minutes inside Docker container

## Architecture

### Multi-Container System
**Two Docker services coordinated via docker-compose:**

1. **monitor** (rbom_error_monitor container):
   - Python cron-based monitoring service
   - Runs `app.monitor` module every 5 minutes via cron
   - Connects to FastAPI Generic Query API for Oracle DB access
   - Sends SMTP emails when errors are detected
   - Requires `.env` file copied into Docker image (not just env_file directive)

2. **rbom_mailsend** (rbom_admin_ui container):
   - Streamlit-based web UI on port 8507
   - Manages user_email_master table (employee code → email mapping)
   - Views mail_send_history table

**Critical Docker Implementation Detail:**
- The `.env` file must be `COPY`ed into the monitor container image (see docker/Dockerfile.monitor)
- This is necessary because cron jobs don't inherit environment variables from docker-compose's `env_file` directive
- python-dotenv's `load_dotenv()` reads the copied `.env` file at runtime

### Core Components

**app/monitor.py** (ErrorMonitor class):
- Main monitoring logic executed by cron
- Monitors two tables: DK020 (受入/receiving) and DK040 (棚出/picking)
- Detection criteria: `SYORIZUMIKBN = '3'` indicates error status
- Fetches employee details from M0540 via FastAPI
- Fetches product details from D3340/D3520 via FastAPI
- Orchestrates DatabaseManager and MailSender
- Implements duplicate prevention via mail_send_history table with UNIQUE constraint on (table_name, record_id)

**app/db_manager.py** (DatabaseManager class):
- SQLite operations for mail_management.db
- Tables: user_email_master (employee→email mapping), mail_send_history (deduplication)
- Methods: get_employee_email(), add_mail_history(), check_mail_sent()

**app/mail_sender.py** (MailSender class):
- SMTP email sending with TLS
- Dynamic subject lines based on function type (受入 vs 棚出)
- Formats email body with product details (LISTNO, HMCD, HMNM)
- Supports TO and CC recipient lists

**app/config.py**:
- Loads environment variables via python-dotenv
- Configures FastAPI connection, SMTP settings, monitoring targets
- DB_PATH points to ./db/mail_management.db

### Data Flow

1. **Cron triggers** → `python -m app.monitor` (every 5 minutes)
2. **Monitor queries** → FastAPI Generic Query API → Oracle DB (DK020, DK040, M0540, D3340, D3520)
3. **Error detection** → SYORIZUMIKBN='3' records
4. **Duplicate check** → SQLite mail_send_history table via UNIQUE(table_name, record_id)
5. **Email lookup** → SQLite user_email_master table by IPTANCD (employee code)
6. **Email send** → SMTP server with dynamic subject and formatted body
7. **History record** → Insert into mail_send_history to prevent re-sending

### External Dependencies

**FastAPI Generic Query API** (expected at FASTAPI_BASE_URL):
- Endpoint: POST /generic-query/query
- Authentication: Header `X-API-Key: {READ_API_KEY}`
- Query format: JSON with `table`, `columns`, `where` fields
- Used to access Oracle tables: DK020, DK040, M0540, D3340, D3520

**Docker Network**:
- Requires external network `app-shared-net` to communicate with FastAPI container
- Network must be created before docker-compose: `docker network create app-shared-net`
- FastAPI service name in network: `fastapi` (not container name)

**Email Content Format:**
- Subject: "【rBOM】受入実績登録エラー通知" or "【rBOM】棚出実績登録エラー通知"
- Body includes: function name, order/allocation number, line number, list number, item code, item name, registration datetime, employee code/name

### Monitoring Configuration

**Monitored Tables and Fields:**
- **DK020** (受入実績/receiving): PONO, LINENO, INSTDT, IPTANCD, SYORIZUMIKBN
- **DK040** (棚出実績/picking): ALCNO, LINENO, INSTDT, IPTANCD, SYORIZUMIKBN

**Error Detection:**
- `SYORIZUMIKBN = '3'` indicates error status
- `IPTANCD` field contains employee code of the person who created the record

**Product Detail Enrichment:**
- DK020 errors → fetch from D3340 (order table) using PONO+LINENO
- DK040 errors → fetch from D3520 (allocation table) using ALCNO+LINENO
- Retrieved fields: LISTNO, HMCD, HMNM

### Date/Time Formatting

**Critical Implementation:**
The monitor handles two datetime formats from Oracle:
1. ISO format with 'T': `2025-10-29T15:30:45` (split on 'T', replace '-' with '/')
2. 14-digit string: `20251029153045` (format as YYYY/MM/DD HH:MM:SS)

Output format: `2025/10/29 15:30:45` (Japanese date format with slashes)

### Email Configuration

All SMTP settings are loaded from `.env`:
- SMTP_SERVER, SMTP_PORT (default 587)
- SMTP_USER, SMTP_PASSWORD
- MAIL_FROM, MAIL_FROM_NAME
- MAIL_SUBJECT (default subject, overridden by function type)

## Customization Points

### Change Monitoring Interval
Edit `docker/crontab` and rebuild:
```bash
# Example: Every 10 minutes instead of 5
*/10 * * * * cd /app && /usr/local/bin/python -m app.monitor >> /app/logs/cron.log 2>&1

# Then rebuild
docker-compose up -d --build
```

### Modify Email Content
Edit `app/mail_sender.py` → `_create_mail_body()` method

### Add Monitoring Targets
Modify `app/monitor.py` → `check_errors()` method to query additional tables

### Change Error Detection Logic
Edit `app/config.py` environment variables or modify query logic in `app/monitor.py`

## Troubleshooting

### Monitor not detecting errors
1. Check FastAPI connectivity: `docker logs rbom_error_monitor | grep -i error`
2. Verify `.env` file is copied into Docker image (see docker/Dockerfile.monitor line with `COPY .env ./`)
3. Check Oracle DB has actual error records with SYORIZUMIKBN='3'
4. Verify READ_API_KEY is correct

### Emails not sending
1. Check SMTP credentials in `.env`
2. Check monitor logs: `docker exec rbom_error_monitor cat /app/logs/monitor.log`
3. Verify employee has email registered in user_email_master via admin UI
4. Check if email was already sent (mail_send_history duplicate prevention)

### Admin UI not accessible
1. Verify container is running: `docker ps | grep rbom_admin_ui`
2. Check port 8507 is not in use: `netstat -ano | findstr :8507` (Windows)
3. Check logs: `docker logs rbom_admin_ui`

### Cron not executing
1. Check cron is running: `docker exec rbom_error_monitor ps aux | grep cron`
2. Check cron logs: `docker exec rbom_error_monitor cat /app/logs/cron.log`
3. Verify crontab file has trailing newline (required by cron specification)

## Important Notes

- **Data Persistence**: SQLite database (db/mail_management.db) persists via Docker volume mount
- **Duplicate Prevention**: UNIQUE constraint on mail_send_history (table_name, record_id) ensures one email per error record
- **Server Restarts**: System will not re-send emails for already-notified errors after restart
- **Japanese Timezone**: Container uses JST (Asia/Tokyo) timezone
- **UTF-8 Encoding**: All log files and email content use UTF-8 for Japanese text support
