# Course Video Upload and Linking Feature

## Overview

This feature enables instructors to add videos to their courses through two methods:
1. **Video Upload**: Upload video files directly to the platform (up to 2GB)
2. **Video Linking**: Link to external videos (YouTube, Vimeo, or custom URLs)

## Implementation Summary

### Database Schema

**Migration File**: `data/migrations/018_add_course_videos.sql`

**Tables Created**:
1. `course_videos` - Stores video records
   - Supports both uploaded files and external links
   - Maintains video ordering within courses
   - Soft delete capability via `is_active` flag

2. `video_uploads` - Tracks upload progress
   - Enables progress monitoring for large files
   - Stores upload status and error messages

**Video Types** (enum):
- `upload` - Video file uploaded to platform
- `link` - Generic external URL
- `youtube` - YouTube video
- `vimeo` - Vimeo video

### Backend Components

#### Models (`services/course-management/models/course_video.py`)
- `CourseVideoBase` - Base video model with common fields
- `CourseVideoCreate` - Creation request model
- `CourseVideoUpdate` - Update request model
- `CourseVideo` - Complete video entity
- `VideoUploadRequest` - Upload initiation request
- `VideoUploadProgress` - Upload status tracking

#### Data Access Layer (`services/course-management/data_access/course_video_dao.py`)
- `CourseVideoDAO` - Database operations for videos
  - `create()` - Create new video record
  - `get_by_id()` - Retrieve specific video
  - `get_by_course()` - Get all videos for a course
  - `update()` - Update video metadata
  - `delete()` - Soft or hard delete video
  - `reorder_videos()` - Change video sequence
  - Upload tracking methods

#### API Endpoints (`services/course-management/api/video_endpoints.py`)

**Video CRUD**:
- `POST /courses/{course_id}/videos` - Add video link
- `GET /courses/{course_id}/videos` - List course videos
- `GET /courses/{course_id}/videos/{video_id}` - Get specific video
- `PUT /courses/{course_id}/videos/{video_id}` - Update video
- `DELETE /courses/{course_id}/videos/{video_id}` - Delete video

**Video Upload**:
- `POST /courses/{course_id}/videos/upload` - Initiate upload
- `POST /courses/{course_id}/videos/upload/{upload_id}/file` - Upload file

**Utilities**:
- `POST /courses/{course_id}/videos/reorder` - Reorder videos
- `GET /courses/{course_id}/videos/count` - Get video count

### Frontend Components

#### UI (`frontend/components/course-creation.html`)
- Video section added to course creation form
- Two modal dialogs:
  - **Upload Modal**: File selection and upload
  - **Link Modal**: External URL entry
- Video list display with:
  - Video type icons
  - Title and metadata
  - Remove button
- Styled video cards and progress bars

#### JavaScript (`frontend/js/modules/course-video-manager.js`)
- `initializeVideoManager()` - Initialize functionality
- `handleVideoUpload()` - Process file upload
- `handleVideoLink()` - Process external link
- `renderVideosList()` - Display videos
- `removeVideo()` - Remove from list
- `uploadCourseVideos()` - Upload all videos after course creation
- Temporary storage before course creation
- Client-side validation

## Setup Instructions

### 1. Run Database Migration

```bash
# Connect to your PostgreSQL database
docker exec -it course-creator-db-1 psql -U courseuser -d coursedb

# Run the migration
\i /path/to/data/migrations/018_add_course_videos.sql
```

Or copy the migration into the database container:
```bash
docker cp data/migrations/018_add_course_videos.sql course-creator-db-1:/tmp/
docker exec course-creator-db-1 psql -U courseuser -d coursedb -f /tmp/018_add_course_videos.sql
```

### 2. Configure Video Storage

Set the video storage path in your environment variables or `.cc_env` file:

```bash
VIDEO_STORAGE_PATH=/app/storage/videos
```

Create the storage directory:
```bash
mkdir -p /path/to/storage/videos
chmod 755 /path/to/storage/videos
```

For Docker deployments, add a volume mount in `docker-compose.yml`:
```yaml
services:
  course-management:
    volumes:
      - ./storage/videos:/app/storage/videos
```

### 3. Register API Endpoints

In `services/course-management/main.py`, add:

```python
from api.video_endpoints import router as video_router

# Include video endpoints
app.include_router(video_router, prefix="/api", tags=["videos"])
```

### 4. Initialize Video DAO

In `services/course-management/main.py`, add:

```python
from data_access.course_video_dao import CourseVideoDAO
from api import video_endpoints

# In your startup function:
video_dao = CourseVideoDAO(db_pool)
video_endpoints.video_dao = video_dao
```

### 5. Include JavaScript Module

In your instructor dashboard HTML file, add:

```html
<script src="/js/modules/course-video-manager.js"></script>
```

## Usage Guide

### For Instructors

#### Uploading a Video

1. Navigate to course creation form
2. Scroll to "Course Videos" section
3. Click "Upload Video" button
4. Fill in:
   - Video title (required)
   - Description (optional)
   - Select video file (MP4, AVI, MOV, WebM)
5. Click "Upload Video"
6. Video appears in list below

#### Linking an External Video

1. Navigate to course creation form
2. Scroll to "Course Videos" section
3. Click "Add Video Link" button
4. Fill in:
   - Video title (required)
   - Description (optional)
   - Platform (YouTube, Vimeo, or Other)
   - Video URL
5. Click "Add Video"
6. Video appears in list below

#### Managing Videos

- **Remove**: Click the "Remove" button on any video
- **Reorder**: Videos are displayed in the order added (future: drag-and-drop reordering)

### For Students

Students will see videos in the course content view:
- Videos display with appropriate platform icons
- Click video to play (embedded player or external link)
- Videos appear in instructor-defined order

## API Examples

### Add YouTube Link

```bash
curl -X POST https://localhost:8000/api/courses/{course_id}/videos \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "course-123",
    "title": "Introduction to Python",
    "description": "Learn Python basics",
    "video_type": "youtube",
    "video_url": "https://www.youtube.com/watch?v=abc123"
  }'
```

### Upload Video File

```bash
# Step 1: Initiate upload
curl -X POST https://localhost:8000/api/courses/{course_id}/videos/upload \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "course_id": "course-123",
    "filename": "intro.mp4",
    "file_size_bytes": 52428800,
    "mime_type": "video/mp4",
    "title": "Course Introduction"
  }'

# Response: { "upload_id": "upload-456", "upload_url": "/api/courses/.../upload/upload-456/file" }

# Step 2: Upload file
curl -X POST https://localhost:8000{upload_url} \
  -H "Authorization: Bearer {token}" \
  -F "file=@intro.mp4" \
  -F "title=Course Introduction" \
  -F "description=Welcome to the course"
```

### Get Course Videos

```bash
curl -X GET https://localhost:8000/api/courses/{course_id}/videos \
  -H "Authorization: Bearer {token}"
```

### Reorder Videos

```bash
curl -X POST https://localhost:8000/api/courses/{course_id}/videos/reorder \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "video_order": ["video-3", "video-1", "video-2"]
  }'
```

## File Size Limits

- **Maximum video size**: 2GB (2,147,483,648 bytes)
- **Recommended size**: < 500MB for optimal performance
- **Supported formats**: MP4, MPEG, MOV, AVI, WebM, OGG

## Security Considerations

1. **File Validation**: Only video MIME types accepted
2. **Size Limits**: 2GB maximum to prevent storage abuse
3. **URL Validation**: External URLs validated by platform
4. **Access Control**: Only course instructors can add/remove videos
5. **Soft Delete**: Videos soft-deleted by default to prevent data loss

## Performance Optimization

### For Large Files
- Consider implementing chunked uploads for files > 500MB
- Use background jobs for video transcoding
- Generate thumbnails asynchronously
- Implement CDN for video delivery

### For Many Videos
- Implement pagination for video lists
- Lazy load video thumbnails
- Cache video metadata
- Use indexed queries on (course_id, order_index)

## Future Enhancements

1. **Video Transcoding**: Convert uploaded videos to web-optimized formats
2. **Thumbnail Generation**: Auto-generate video thumbnails
3. **Drag-and-Drop Reordering**: UI for easy video sequencing
4. **Progress Tracking**: Real-time upload progress bars
5. **Cloud Storage Integration**: S3/CloudFront for scalability
6. **Video Analytics**: Track view counts and completion rates
7. **Subtitles/Captions**: Support for accessibility
8. **Video Editing**: Basic trimming and cropping tools
9. **Live Streaming**: Support for live video sessions
10. **Video Playlists**: Group videos into chapters/modules

## Troubleshooting

### Videos Not Appearing
- Check database migration ran successfully
- Verify `VIDEO_STORAGE_PATH` is configured
- Check file permissions on storage directory
- Ensure JavaScript module is loaded

### Upload Failures
- Check file size is under 2GB limit
- Verify MIME type is supported
- Check storage directory has write permissions
- Review server logs for errors

### External Links Not Working
- Verify URL format is correct
- Check URL is publicly accessible
- Ensure CORS headers allow embedding
- Test URL in isolation

## Testing

### Manual Testing Checklist

- [ ] Upload a small video (< 50MB)
- [ ] Upload a large video (> 500MB)
- [ ] Add YouTube link
- [ ] Add Vimeo link
- [ ] Add generic URL link
- [ ] Remove a video
- [ ] Try uploading file over 2GB (should fail)
- [ ] Try uploading non-video file (should fail)
- [ ] Try invalid YouTube URL (should fail)
- [ ] View videos in created course
- [ ] Reorder videos

### Automated Testing

Create test cases for:
1. Video model validation
2. DAO CRUD operations
3. API endpoint responses
4. File upload handling
5. URL validation
6. Permission checks

## Support

For issues or questions:
1. Check server logs: `docker logs course-creator-course-management-1`
2. Check browser console for JavaScript errors
3. Verify database schema with: `\d course_videos` in psql
4. Review API responses for error details
