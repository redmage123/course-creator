/**
 * Course Video Manager Module
 *
 * Handles video upload, linking, and management for course creation.
 * Supports both file uploads and external video links (YouTube, Vimeo, etc.)
 *
 * BUSINESS CONTEXT:
 * - Enables instructors to enrich courses with video content
 * - Supports multiple video sources for flexibility
 * - Provides progress tracking for large file uploads
 * - Maintains video ordering for structured curriculum
 */

// Temporary storage for videos before course is created
let courseVideos = [];

/**
 * Initialize video management functionality
 *
 * WORKFLOW:
 * - Attach event listeners to buttons and modals
 * - Set up drag-and-drop for video reordering
 * - Initialize empty video list display
 */
function initializeVideoManager() {
    // Add Upload Video button handler
    document.getElementById('add-upload-video-btn')?.addEventListener('click', () => {
        openVideoModal('video-upload-modal');
    });

    // Add Link Video button handler
    document.getElementById('add-link-video-btn')?.addEventListener('click', () => {
        openVideoModal('video-link-modal');
    });

    // Confirm upload button
    document.getElementById('confirm-video-upload-btn')?.addEventListener('click', handleVideoUpload);

    // Confirm link button
    document.getElementById('confirm-video-link-btn')?.addEventListener('click', handleVideoLink);

    // Initialize empty state
    renderVideosList();
}

/**
 * Open video modal dialog
 *
 * @param {string} modalId - ID of modal to open
 */
function openVideoModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'flex';
    }
}

/**
 * Close video modal dialog
 *
 * @param {string} modalId - ID of modal to close
 *
 * CLEANUP:
 * - Reset form fields
 * - Hide progress indicators
 * - Clear any error messages
 */
function closeVideoModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';

        // Reset forms
        if (modalId === 'video-upload-modal') {
            document.getElementById('upload-video-title').value = '';
            document.getElementById('upload-video-description').value = '';
            document.getElementById('upload-video-file').value = '';
            document.getElementById('upload-progress-container').style.display = 'none';
            document.getElementById('upload-progress-bar').style.width = '0%';
            document.getElementById('upload-progress-text').textContent = '0%';
        } else if (modalId === 'video-link-modal') {
            document.getElementById('link-video-title').value = '';
            document.getElementById('link-video-description').value = '';
            document.getElementById('link-video-url').value = '';
            document.getElementById('link-video-type').value = 'youtube';
        }
    }
}

// Make closeVideoModal globally accessible for onclick handlers
window.closeVideoModal = closeVideoModal;

/**
 * Handle video file upload
 *
 * WORKFLOW:
 * 1. Validate form inputs
 * 2. Validate file size and type
 * 3. Add video to temporary list (file will be uploaded when course is created)
 * 4. Display video in list
 * 5. Close modal
 *
 * TECHNICAL NOTE:
 * For now, we store file references. Actual upload happens when course is created.
 * For production, consider initiating upload immediately and storing upload ID.
 */
async function handleVideoUpload() {
    const title = document.getElementById('upload-video-title').value.trim();
    const description = document.getElementById('upload-video-description').value.trim();
    const fileInput = document.getElementById('upload-video-file');
    const file = fileInput.files[0];

    // Validation
    if (!title) {
        alert('Please enter a video title');
        return;
    }

    if (!file) {
        alert('Please select a video file');
        return;
    }

    // Validate file size (2GB max)
    const maxSize = 2 * 1024 * 1024 * 1024; // 2GB
    if (file.size > maxSize) {
        alert('Video file is too large. Maximum size is 2GB.');
        return;
    }

    // Validate file type
    const allowedTypes = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/webm'];
    if (!allowedTypes.includes(file.type)) {
        alert('Unsupported video format. Please use MP4, MPEG, MOV, AVI, or WebM.');
        return;
    }

    // Add to videos list
    const video = {
        id: generateTempId(),
        title: title,
        description: description,
        video_type: 'upload',
        file: file, // Store file object for later upload
        file_size_bytes: file.size,
        mime_type: file.type,
        order_index: courseVideos.length
    };

    courseVideos.push(video);
    renderVideosList();
    closeVideoModal('video-upload-modal');
}

/**
 * Handle video link addition
 *
 * WORKFLOW:
 * 1. Validate form inputs
 * 2. Validate URL format
 * 3. Add video link to temporary list
 * 4. Display video in list
 * 5. Close modal
 */
function handleVideoLink() {
    const title = document.getElementById('link-video-title').value.trim();
    const description = document.getElementById('link-video-description').value.trim();
    const videoType = document.getElementById('link-video-type').value;
    const videoUrl = document.getElementById('link-video-url').value.trim();

    // Validation
    if (!title) {
        alert('Please enter a video title');
        return;
    }

    if (!videoUrl) {
        alert('Please enter a video URL');
        return;
    }

    // URL format validation
    try {
        new URL(videoUrl);
    } catch (e) {
        alert('Please enter a valid URL');
        return;
    }

    // Platform-specific validation
    if (videoType === 'youtube' && !videoUrl.includes('youtube.com') && !videoUrl.includes('youtu.be')) {
        alert('Please enter a valid YouTube URL');
        return;
    }

    if (videoType === 'vimeo' && !videoUrl.includes('vimeo.com')) {
        alert('Please enter a valid Vimeo URL');
        return;
    }

    // Add to videos list
    const video = {
        id: generateTempId(),
        title: title,
        description: description,
        video_type: videoType,
        video_url: videoUrl,
        order_index: courseVideos.length
    };

    courseVideos.push(video);
    renderVideosList();
    closeVideoModal('video-link-modal');
}

/**
 * Render videos list in UI
 *
 * DISPLAY LOGIC:
 * - Show empty state if no videos
 * - Render video items with appropriate icons
 * - Enable reordering and deletion
 */
function renderVideosList() {
    const container = document.getElementById('course-videos-container');

    if (courseVideos.length === 0) {
        container.innerHTML = `
            <div class="videos-list-empty">
                <i class="fas fa-video" style="font-size: 48px; color: #ddd; margin-bottom: 10px;"></i>
                <p>No videos added yet. Click the buttons above to add videos to your course.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = courseVideos.map((video, index) => {
        const icon = getVideoIcon(video.video_type);
        const meta = getVideoMeta(video);

        return `
            <div class="video-item" data-video-id="${video.id}">
                <div class="video-item-info">
                    <div class="video-item-icon">
                        <i class="${icon}"></i>
                    </div>
                    <div class="video-item-details">
                        <div class="video-item-title">${escapeHtml(video.title)}</div>
                        <div class="video-item-meta">${meta}</div>
                    </div>
                </div>
                <div class="video-item-actions">
                    <button class="btn-danger" onclick="removeVideo('${video.id}')">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Get appropriate icon for video type
 *
 * @param {string} videoType - Type of video (upload, youtube, vimeo, link)
 * @returns {string} Font Awesome icon class
 */
function getVideoIcon(videoType) {
    switch (videoType) {
        case 'upload':
            return 'fas fa-file-video';
        case 'youtube':
            return 'fab fa-youtube';
        case 'vimeo':
            return 'fab fa-vimeo';
        case 'link':
            return 'fas fa-external-link-alt';
        default:
            return 'fas fa-video';
    }
}

/**
 * Get video metadata text
 *
 * @param {object} video - Video object
 * @returns {string} Formatted metadata string
 */
function getVideoMeta(video) {
    if (video.video_type === 'upload') {
        const sizeMB = (video.file_size_bytes / (1024 * 1024)).toFixed(2);
        return `Uploaded file • ${sizeMB} MB • ${video.mime_type}`;
    } else {
        return `${video.video_type.charAt(0).toUpperCase() + video.video_type.slice(1)} link • ${video.video_url}`;
    }
}

/**
 * Remove video from list
 *
 * @param {string} videoId - Temporary ID of video to remove
 */
function removeVideo(videoId) {
    if (confirm('Are you sure you want to remove this video?')) {
        courseVideos = courseVideos.filter(v => v.id !== videoId);

        // Reindex remaining videos
        courseVideos.forEach((video, index) => {
            video.order_index = index;
        });

        renderVideosList();
    }
}

// Make removeVideo globally accessible for onclick handlers
window.removeVideo = removeVideo;

/**
 * Generate temporary ID for video before it's saved to database
 *
 * @returns {string} Temporary ID
 */
function generateTempId() {
    return 'temp-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}

/**
 * Escape HTML to prevent XSS attacks
 *
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Upload videos for a created course
 *
 * This function is called after a course is successfully created.
 * It uploads all video files and creates video link records.
 *
 * @param {string} courseId - ID of the created course
 * @returns {Promise<Array>} Array of created video records
 *
 * WORKFLOW:
 * 1. Iterate through courseVideos array
 * 2. For uploads: Upload file with progress tracking
 * 3. For links: Create video record immediately
 * 4. Return array of created video records
 */
async function uploadCourseVideos(courseId) {
    const uploadedVideos = [];

    for (const video of courseVideos) {
        try {
            if (video.video_type === 'upload') {
                // Upload file
                const uploadedVideo = await uploadVideoFile(courseId, video);
                uploadedVideos.push(uploadedVideo);
            } else {
                // Create link record
                const linkedVideo = await createVideoLink(courseId, video);
                uploadedVideos.push(linkedVideo);
            }
        } catch (error) {
            console.error(`Failed to add video "${video.title}":`, error);
            // Continue with other videos even if one fails
        }
    }

    return uploadedVideos;
}

/**
 * Upload video file to server
 *
 * @param {string} courseId - Course ID
 * @param {object} video - Video object with file
 * @returns {Promise<object>} Created video record
 */
async function uploadVideoFile(courseId, video) {
    // Get upload initiation first
    const token = localStorage.getItem('authToken') || localStorage.getItem('token');
    const initResponse = await fetch(`https://localhost:8004/courses/${courseId}/videos/upload`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            course_id: courseId,
            filename: video.file.name,
            file_size_bytes: video.file_size_bytes,
            mime_type: video.mime_type,
            title: video.title,
            description: video.description || ''
        })
    });

    if (!initResponse.ok) {
        throw new Error(`Upload initiation failed: ${initResponse.statusText}`);
    }

    const initResult = await initResponse.json();
    const uploadId = initResult.upload_id;

    // Create FormData for multipart upload
    const formData = new FormData();
    formData.append('file', video.file);
    formData.append('title', video.title);
    formData.append('description', video.description || '');

    const response = await fetch(`https://localhost:8004/courses/${courseId}/videos/upload/${uploadId}/file`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    });

    if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
    }

    const result = await response.json();
    return result.video;
}

/**
 * Create video link record
 *
 * @param {string} courseId - Course ID
 * @param {object} video - Video object with URL
 * @returns {Promise<object>} Created video record
 */
async function createVideoLink(courseId, video) {
    const token = localStorage.getItem('authToken') || localStorage.getItem('token');
    const response = await fetch(`https://localhost:8004/courses/${courseId}/videos`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            course_id: courseId,
            title: video.title,
            description: video.description || '',
            video_type: video.video_type,
            video_url: video.video_url,
            order_index: video.order_index
        })
    });

    if (!response.ok) {
        throw new Error(`Failed to create video link: ${response.statusText}`);
    }

    const result = await response.json();
    return result.video;
}

/**
 * Clear videos list
 *
 * Called when course form is reset or submitted
 */
function clearCourseVideos() {
    courseVideos = [];
    renderVideosList();
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeVideoManager,
        uploadCourseVideos,
        clearCourseVideos,
        getCourseVideos: () => courseVideos
    };
}

// Also export to window for use in instructor dashboard
if (typeof window !== 'undefined') {
    window.uploadCourseVideos = uploadCourseVideos;
    window.clearCourseVideos = clearCourseVideos;
    window.getCourseVideos = () => courseVideos;
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeVideoManager);
} else {
    initializeVideoManager();
}
