# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Applications

### Local Development
```bash
# Technical drawings search application
streamlit run 福原精機図面検索.py

# Work standards viewer application  
streamlit run 福原精機作業基準.py
```

### Docker Deployment
```bash
# Build and run both applications
docker-compose up --build

# Run specific service
docker-compose up fukuhara-zumen    # Technical drawings (port 8506)
docker-compose up fukuhara-kijun    # Work standards (port 8505)

# Stop services
docker-compose down
```

**Service URLs:**
- Work Standards: http://localhost:8505
- Technical Drawings Search: http://localhost:8506

### Dependencies Installation
```bash
pip install -r requirements.txt
```

## Application Architecture

### Core Application: 福原精機図面検索.py

This is a Streamlit-based document viewer for PDF and TIF files stored on network drives. The application provides a hierarchical file browser with high-quality image rendering and supports both regular drawings (図面) and obsolete drawings (廃図).

**Key Components:**

- **Dual Network File System Integration**: 
  - Regular drawings: `\\fsrv24\zumen` with JSON cache from `\\fsrv24\file_monitor\zumen`
  - Obsolete drawings: `\\fsrv24\zumenhai` with JSON cache from `\\fsrv24\file_monitor\zumenhai`
- **Cached Folder Structure**: Uses separate JSON files for each drawing type
  - Regular: `folder_structure.json`, `folder_metadata.json`  
  - Obsolete: `haizu_folder_structure.json`, `haizu_folder_metadata.json`
- **Dynamic Path Switching**: Application automatically switches paths and JSON sources based on drawing type selection
- **High-Quality Rendering**: PDF rendering at 3x resolution using PyMuPDF, TIF files converted to PNG
- **Independent Session State Management**: Separate caching for regular and obsolete drawings

**UI Structure:**
- Four selectboxes in horizontal layout: Drawing Type (1.5) | Level 1 (2) | Level 2 (2) | File (3)
- Drawing type selector with default "図面" selection
- High-quality image display with context-aware labeling (shows "廃図表示中" for obsolete drawings)
- Custom CSS to hide Streamlit UI elements for cleaner presentation

**File Processing Flow:**
1. User selects drawing type (図面/廃図)
2. Application determines appropriate network paths and JSON files
3. JSON cache loaded from corresponding file monitoring location
4. Files rendered on-demand with high-quality conversion
5. Automatic updates when JSON files are modified by external monitoring system

**Performance Optimizations:**
- JSON-based caching prevents repeated network folder scanning
- Independent session state for each drawing type
- Direct files (`__direct_files__`) handling for files in root level of categories
- Automatic detection of JSON file updates via timestamp comparison

## Docker Configuration

### Network Mount Requirements
The applications require network drive mounts on the host system:

**For Technical Drawings (fukuhara-zumen):**
- `\\fsrv24\zumen` → `/mnt/fsrv24/zumen`
- `\\fsrv24\zumenhai` → `/mnt/fsrv24/zumenhai` 
- `\\fsrv24\file_monitor\zumen` → `/mnt/fsrv24/file_monitor/zumen`
- `\\fsrv24\file_monitor\zumenhai` → `/mnt/fsrv24/file_monitor/zumenhai`

**For Work Standards (fukuhara-kijun):**
- `\\fsrv24\E\09_BUSSINES\kensa\webdata\福原精機作業基準 PDF保存版` → `/mnt/fsrv24/kijun`

### Application Paths Configuration

**Development (Windows paths):**
```python
ROOT_DIR_PATH_STR = r"\\fsrv24\zumen"           # Regular drawings
HAIZU_ROOT_DIR_PATH_STR = r"\\fsrv24\zumenhai"  # Obsolete drawings
```

**Docker (Linux container paths):**
```python
ROOT_DIR_PATH_STR = r"/app/network/zumen"           # Regular drawings  
HAIZU_ROOT_DIR_PATH_STR = r"/app/network/zumenhai"  # Obsolete drawings
ROOT_DIR_PATH_STR = r"/app/network/kijyun"          # Work standards
```

## Data Structure

The application handles a 2-level folder hierarchy:
- **Level 1**: Category folders (49 categories like "4", "44", "A", etc.)
- **Level 2**: Sub-folders or direct files (marked as `__direct_files__`)

JSON cache structure:
```json
{
  "category_name": {
    "subfolder_name": ["file1.pdf", "file2.tif"],
    "__direct_files__": ["direct_file.pdf"]
  }
}
```

## Dependencies

```
streamlit==1.39.0    # Web UI framework
PyMuPDF==1.25.1      # PDF processing and high-quality rendering  
Pillow==10.4.0       # TIF image processing (version pinned for Streamlit compatibility)
pytz==2024.2         # Timezone handling for JST display
```

**Important Version Notes:**
- Pillow must be <11.0.0 due to Streamlit 1.39.0 compatibility requirements
- pytz is used for Japanese timezone (JST) display in file timestamps

## File Types Supported

- PDF files (rendered page by page at 3x resolution)
- TIF/TIFF files (converted to PNG for display)

Both file types support click-to-view functionality that opens images in new browser tabs as PNG data URLs.

## Development Notes

### Environment-Specific Configuration
- **Local Development**: Uses Windows UNC paths (`\\fsrv24\*`)
- **Docker Production**: Uses Linux container paths (`/app/network/*`)
- Applications automatically detect JSON file updates via timestamp comparison
- All timestamps displayed in Japanese Standard Time (JST)

### UI/UX Features
- Custom CSS extensively hides Streamlit default UI elements for clean corporate presentation
- Favicons: 📋 (Technical Drawings), 📝 (Work Standards) with iPad Safari support
- Streamlit compatibility: Uses `use_column_width=True` instead of deprecated `use_container_width`

### File Monitoring Integration
- External monitoring scripts (`file_monitoring/`) scan network drives and update JSON caches
- Applications detect JSON updates automatically without restart
- **Note**: Monitoring scripts are for development only - not included in Docker deployment

### Work Standards Application Specific
- Handles folder structure: `基準チェック表 FS-　ーＰＤＦー` (contains half-width spaces)
- Tab-based navigation with display vs logic name mapping
- Single PDF viewer with page-by-page rendering

## Drawing Type Management

The technical drawings application uses a generalized `load_structure_from_json(json_path, data_type)` function that:
- Accepts different JSON file paths for regular vs obsolete drawings
- Provides context-aware console logging with drawing type labels  
- Maintains separate session state keys (`structure` vs `haizu_structure`)
- Handles automatic JSON file update detection for both drawing types

When implementing new features or modifications:
- Always consider impact on both drawing types (図面/廃図)
- Use the dynamic path variables (`current_root_dir`, `current_structure_json`, etc.)
- Test functionality with both drawing type selections
- Ensure proper session state isolation between drawing types