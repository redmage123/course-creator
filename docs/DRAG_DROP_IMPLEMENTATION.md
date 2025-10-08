# Drag-and-Drop File Upload Implementation

**Version**: 3.3.1
**Date**: 2025-10-07
**Status**: Completed

## Overview

Implemented drag-and-drop file upload functionality for both Instructor and Organization Admin dashboards with metadata tracking and video-recorded E2E tests.

## Business Requirements

1. **Enhanced User Experience**: Provide intuitive drag-and-drop file uploads
2. **Metadata Tracking**: Track all file uploads/downloads for analytics
3. **Role-Based Implementation**: Support both instructor and org admin workflows
4. **Test Coverage**: E2E tests with video recording for documentation

## Technical Implementation

### 1. Reusable ES6 Module

**File**: `/frontend/js/modules/drag-drop-upload.js`

- ES6 class `DragDropUpload` for drag-and-drop functionality
- Event handlers: `dragenter`, `dragover`, `dragleave`, `drop`
- Progress tracking with `XMLHttpRequest.upload.onprogress`
- File validation (type, size)
- Callbacks: `onUploadStart`, `onUploadProgress`, `onUploadComplete`, `onUploadError`

### 2. Styling

**File**: `/frontend/css/drag-drop.css`

- `.drag-drop-zone` - Main container styling
- `.drag-over` - Visual feedback during drag
- `.progress-bar` - Upload progress indicator
- Responsive design with mobile support

### 3. Configuration

**File**: `/frontend/js/config.js`

- Centralized API endpoint configuration
- `CONFIG.ENDPOINTS.METADATA_SERVICE` for metadata tracking
- `CONFIG.ENDPOINTS.CONTENT_SERVICE` for file storage
- File size and format constraints

## Integration Points

### Instructor Dashboard

**File**: `/frontend/html/instructor-dashboard.html`

**Functions Updated**:
1. `uploadSyllabusFile(courseId)` - Drag-drop syllabus upload with metadata tracking
2. `uploadSlides(courseId)` - Drag-drop presentation upload with metadata tracking

**Metadata Tracking**:
- Entity type: `course_material_upload`
- Tags: `['syllabus', 'instructor_upload']` or `['slides', 'instructor_upload']`
- Tracked fields: `file_type`, `filename`, `file_size_bytes`, `instructor_id`, `upload_timestamp`

### Organization Admin Dashboard

**File**: `/frontend/js/modules/org-admin-settings.js`

**Functions Added**:
1. `setupDragDropLogoUpload()` - Initialize drag-drop for logo upload
2. `trackLogoUpload(filename, fileSize, logoUrl)` - Track logo uploads with metadata
3. `displayLogoPreview(logoUrl)` - Show uploaded logo preview
4. `setupFallbackLogoUpload()` - Fallback to standard file input

**Metadata Tracking**:
- Entity type: `organization_logo_upload`
- Tags: `['logo', 'branding', 'org_admin_upload']`
- Tracked fields: `file_type`, `filename`, `file_size_bytes`, `logo_url`, `uploaded_by`, `organization_id`

**File**: `/frontend/html/org-admin-dashboard.html`

- Added `<link rel="stylesheet" href="../css/drag-drop.css">`
- Logo upload area ID: `logoUploadAreaSettings`
- Preview elements: `logoPreview`, `logoPreviewImg`

## Database Schema Updates

### Migration 003: Organization Entity Types

**File**: `/services/metadata-service/migrations/003_add_organization_entity_types.sql`

**Changes**:
1. Updated `entity_metadata_check_type` constraint to include:
   - `organization_logo_upload`
   - `organization_document_upload`

2. Created index for performance:
   ```sql
   CREATE INDEX idx_metadata_org_uploads
   ON entity_metadata (entity_id)
   WHERE entity_type IN ('organization_logo_upload', 'organization_document_upload');
   ```

## E2E Testing

### Video Recording Capability

**Files**:
- `/tests/e2e/video_recorder.py` - VideoRecorder class using OpenCV
- `/tests/e2e/selenium_base.py` - Enhanced BaseTest with video recording methods

**Methods Added to BaseTest**:
- `capture_video_frame()` - Capture single frame
- `start_continuous_recording(interval)` - Background frame capture
- `stop_continuous_recording()` - Stop and save video

**Video Format**: MP4 with H.264 codec (mp4v)
**Default FPS**: 5 frames per second
**Output Directory**: `tests/reports/videos/`

### Test Suites

#### 1. Instructor Drag-Drop Tests

**File**: `/tests/e2e/test_drag_drop_upload.py`

**Tests**:
- `test_upload_syllabus_drag_drop_ui_appears` - UI visibility
- `test_drag_drop_zone_styling` - CSS loading verification
- `test_drag_drop_module_loaded` - Module import verification
- `test_file_upload_with_manual_capture` - Upload workflow

**Run Command**:
```bash
RECORD_VIDEO=true pytest tests/e2e/test_drag_drop_upload.py -v -s
```

#### 2. Org Admin Drag-Drop Tests

**File**: `/tests/e2e/test_org_admin_drag_drop_upload.py`

**Tests**:
- `test_org_admin_dashboard_loads` - Dashboard accessibility
- `test_settings_tab_has_logo_upload` - Logo upload area presence
- `test_drag_drop_css_loaded` - Stylesheet verification
- `test_drag_drop_module_can_be_imported` - Module loading
- `test_logo_upload_area_exists` - Upload area element
- `test_config_js_imported` - Config module verification

**Run Command**:
```bash
RECORD_VIDEO=true pytest tests/e2e/test_org_admin_drag_drop_upload.py -v -s
```

## Analytics Integration

### Materialized Views

**File**: `/services/metadata-service/migrations/001_materialized_views_and_fulltext.sql`

**Views Created**:
1. `mv_file_upload_analytics` - Upload statistics by course/file type
2. `mv_file_download_analytics` - Download tracking
3. `mv_course_material_summary` - Combined upload/download summary

**Analytics Queries**:
- Upload analytics by course: `get_upload_analytics_by_course(course_id)`
- Upload analytics by file type: `get_upload_analytics_by_file_type(file_type)`
- Most downloaded files: `get_most_downloaded_files(limit)`
- Engagement metrics: `get_engagement_metrics(limit)`

### REST API Endpoints

**File**: `/services/metadata-service/api/analytics_endpoints.py`

**Endpoints**:
- `GET /analytics/uploads/course/{course_id}` - Course upload stats
- `GET /analytics/uploads/file-type/{file_type}` - File type stats
- `GET /analytics/downloads/course/{course_id}` - Course download stats
- `GET /analytics/downloads/most-downloaded` - Popular files
- `GET /analytics/summary/course/{course_id}` - Combined summary
- `GET /analytics/engagement` - Engagement metrics
- `POST /analytics/refresh` - Refresh materialized views
- `GET /analytics/search` - Full-text search
- `GET /analytics/fuzzy-search` - Typo-tolerant search

## File Structure

```
course-creator/
├── frontend/
│   ├── css/
│   │   └── drag-drop.css                          # Drag-drop styling
│   ├── html/
│   │   ├── instructor-dashboard.html              # Instructor uploads
│   │   └── org-admin-dashboard.html               # Org admin logo upload
│   └── js/
│       ├── config.js                              # API configuration
│       └── modules/
│           ├── drag-drop-upload.js                # Drag-drop module
│           ├── org-admin-settings.js              # Org admin settings
│           └── student-file-manager.js            # Student downloads
├── services/
│   └── metadata-service/
│       ├── api/
│       │   └── analytics_endpoints.py             # Analytics API
│       ├── data_access/
│       │   └── metadata_dao.py                    # Data access layer
│       └── migrations/
│           ├── 001_materialized_views_and_fulltext.sql
│           ├── 002_add_file_tracking_entity_types.sql
│           └── 003_add_organization_entity_types.sql
├── tests/
│   └── e2e/
│       ├── selenium_base.py                       # Enhanced base test
│       ├── video_recorder.py                      # Video recording helper
│       ├── test_drag_drop_upload.py               # Instructor tests
│       └── test_org_admin_drag_drop_upload.py     # Org admin tests
└── docs/
    └── DRAG_DROP_IMPLEMENTATION.md                # This file
```

## Usage Examples

### Instructor: Upload Syllabus

```javascript
async function uploadSyllabusFile(courseId) {
    const modal = createUploadModal('Upload Syllabus');
    document.body.appendChild(modal);

    const dropZone = document.getElementById('syllabusDropZone');

    const { DragDropUpload } = await import('../js/modules/drag-drop-upload.js');

    new DragDropUpload(dropZone, {
        acceptedTypes: ['.pdf', '.doc', '.docx', '.txt', '.md'],
        maxSizeMB: 50,
        uploadEndpoint: `${CONFIG.ENDPOINTS.CONTENT_SERVICE}/upload-syllabus?course_id=${courseId}`,

        onUploadComplete: async (response, file) => {
            await trackFileUpload(courseId, 'syllabus', file.name, file.size, response.syllabus_id);
            showNotification('Syllabus uploaded successfully!', 'success');
        }
    });
}
```

### Org Admin: Upload Logo

```javascript
async function setupDragDropLogoUpload() {
    const logoUploadArea = document.getElementById('logoUploadAreaSettings');

    const { DragDropUpload } = await import('../js/modules/drag-drop-upload.js');

    new DragDropUpload(logoUploadArea, {
        acceptedTypes: ['.jpg', '.jpeg', '.png', '.gif'],
        maxSizeMB: 5,
        uploadEndpoint: `${CONFIG.ENDPOINTS.METADATA_SERVICE}/organizations/${orgId}/upload-logo`,

        onUploadComplete: async (response, file) => {
            await trackLogoUpload(file.name, file.size, response.logo_url);
            displayLogoPreview(response.logo_url);
        }
    });
}
```

### Query Upload Analytics

```python
# Get upload analytics for a course
analytics = await metadata_dao.get_upload_analytics_by_course(course_id=1)

# Result:
[
    {
        "course_id": 1,
        "file_type": "syllabus",
        "uploader_role": "instructor",
        "total_uploads": 5,
        "total_bytes": 12582912,
        "avg_file_size_bytes": 2516582,
        "uploads_last_7_days": 2,
        "uploads_last_30_days": 5
    }
]
```

## Benefits

1. **Enhanced UX**: Intuitive drag-and-drop interface with visual feedback
2. **Analytics**: Comprehensive tracking of all file operations
3. **Maintainability**: Reusable ES6 module with clean separation of concerns
4. **Test Coverage**: E2E tests with video recording for documentation
5. **Performance**: Materialized views for fast analytics queries
6. **Search**: Full-text and fuzzy search capabilities
7. **Scalability**: Indexed queries for large datasets

## Future Enhancements

1. **Bulk Upload**: Multi-file drag-and-drop
2. **Upload Resume**: Resume interrupted uploads
3. **Image Optimization**: Automatic image compression/resizing
4. **CDN Integration**: Upload directly to CDN
5. **Virus Scanning**: Integrate malware scanning
6. **Version Control**: Track file versions
7. **Permissions**: Fine-grained access control
8. **Notifications**: Real-time upload notifications

## Testing Status

✅ Video recording capability added to Selenium BaseTest
✅ Video recorder helper class created
✅ Instructor drag-drop E2E tests created
✅ Org admin drag-drop E2E tests created
✅ Database migrations completed (3/3)
✅ Materialized views analytics tests passing (9/9)
✅ Drag-drop module implemented
✅ Instructor dashboard integration complete
✅ Org admin dashboard integration complete

## Compliance

- **TDD Methodology**: Tests written before/during implementation (RED-GREEN-REFACTOR)
- **ES6 Modules**: No inline scripts, proper module architecture
- **Documentation**: Comprehensive inline documentation with business context
- **Metadata Tracking**: All file operations tracked for audit trail
- **Error Handling**: Graceful fallback to standard file input
