# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-application Streamlit-based notification management system. It consists of an administrative interface (`app.py`) for managing announcements and a viewer interface (`viewer.py`) for displaying active announcements. Both applications share a SQLite database and are designed to be embedded in other applications via iframe.

## Key Commands

### Development Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the management application
streamlit run app.py

# Run the viewer application
streamlit run viewer.py
```

### Database
- Database file: `notices.db` (SQLite, auto-created on first run)
- No migration commands needed - schema is handled automatically by `init_database()`
- Initial admin account: `administrator/administrator` (created automatically)

## Architecture

### Dual Application Structure

**app.py (Management Interface):**
- Authentication-protected administrative interface
- Four-tab interface: "新規作成・編集", "一覧・削除", "マークダウン記法", "管理用"
- User management with role-based access (0=editor, 1=admin)
- Notice CRUD operations with validation

**viewer.py (Public Display):**
- Public-facing notice display interface
- Shows only active notices (within date range, not logically deleted)
- Modal dialog for notice details
- Auto-cleanup of expired notices on load

### Database Schema

**notices table:**
```sql
notices (
    id TEXT PRIMARY KEY,        -- UUID
    department TEXT NOT NULL,   -- Max 10 chars
    start_date DATE NOT NULL,   -- Today or later
    end_date DATE NOT NULL,     -- Max 2 months from today
    title TEXT NOT NULL,        -- Max 20 chars
    content TEXT NOT NULL,      -- Max 1200 chars, markdown supported
    emoji TEXT DEFAULT '📋',   -- Display emoji
    created_at TIMESTAMP,       -- JST timezone
    deleted_at TIMESTAMP NULL   -- Logical deletion
)
```

**users table:**
```sql
users (
    id TEXT PRIMARY KEY,        -- UUID
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,     -- Plain text (no hashing)
    role INTEGER NOT NULL DEFAULT 0,  -- 0=editor, 1=admin
    created_at TIMESTAMP       -- JST timezone
)
```

### Authentication System

- Login required for app.py access
- Session-based authentication (browser session lifetime)
- Password change triggers automatic logout after 5 seconds
- Role-based permissions:
  - **Editors (role=0)**: Create, edit, delete notices; change own password
  - **Admins (role=1)**: All editor permissions + user management

### Business Logic Constraints

**Notice Validation:**
- Start date: Today or later
- End date: Max 2 months from today, must be >= start date
- Department: 1-10 characters
- Title: 1-20 characters  
- Content: 1-1200 characters (markdown supported)

**Automatic Cleanup:**
- Logical deletion: 30 days after end_date
- Display rules: viewer.py shows notices where `end_date >= today`

### Key Features

**Management Interface (app.py):**
- Edit mode via dropdown selection
- Real-time markdown preview
- Form validation with Japanese error messages
- User deletion with confirmation dialog
- Logout functionality

**Viewer Interface (viewer.py):**
- Card-based notice display sorted by end_date
- Modal dialogs for notice details
- Date format: mm/dd display

## Development Notes

### Timezone Handling
All timestamps use Japan Standard Time (Asia/Tokyo) via pytz. Database operations explicitly set JST for created_at and deleted_at fields.

### Session Management
The application uses Streamlit's session state for authentication and form handling. Database connections are opened/closed for each operation (no connection pooling).

### UI Styling
Both applications include extensive CSS to hide Streamlit's default UI elements (headers, menus, decorations) for clean iframe embedding.