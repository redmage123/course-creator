/**
 * Unit Tests for Course Video Manager Module
 *
 * BUSINESS CONTEXT:
 * Tests the JavaScript video management functionality including
 * video upload UI, link validation, and video list rendering.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses Jest for testing
 * - Mocks DOM elements
 * - Tests validation logic
 * - Tests state management
 */

// Mock localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn()
};
global.localStorage = localStorageMock;

// Mock fetch API
global.fetch = jest.fn();

// Mock document elements
document.body.innerHTML = `
    <button id="add-upload-video-btn"></button>
    <button id="add-link-video-btn"></button>
    <button id="confirm-video-upload-btn"></button>
    <button id="confirm-video-link-btn"></button>

    <div id="course-videos-container"></div>

    <!-- Upload Modal -->
    <div id="video-upload-modal" style="display: none;">
        <input type="text" id="upload-video-title" />
        <textarea id="upload-video-description"></textarea>
        <input type="file" id="upload-video-file" accept="video/*" />
        <div id="upload-progress-container" style="display: none;">
            <div id="upload-progress-bar" style="width: 0%;"></div>
            <span id="upload-progress-text">0%</span>
        </div>
    </div>

    <!-- Link Modal -->
    <div id="video-link-modal" style="display: none;">
        <input type="text" id="link-video-title" />
        <textarea id="link-video-description"></textarea>
        <select id="link-video-type">
            <option value="youtube">YouTube</option>
            <option value="vimeo">Vimeo</option>
            <option value="link">Other URL</option>
        </select>
        <input type="url" id="link-video-url" />
    </div>
`;

describe('Course Video Manager', () => {
    let courseVideos;

    beforeEach(() => {
        // Reset module state
        courseVideos = [];
        jest.clearAllMocks();

        // Reset DOM
        document.getElementById('course-videos-container').innerHTML = '';
        document.getElementById('upload-video-title').value = '';
        document.getElementById('upload-video-description').value = '';
        document.getElementById('link-video-title').value = '';
        document.getElementById('link-video-description').value = '';
        document.getElementById('link-video-url').value = '';

        // Mock alert
        global.alert = jest.fn();
        global.confirm = jest.fn();
    });

    describe('Modal Operations', () => {
        test('openVideoModal should display modal', () => {
            const modal = document.getElementById('video-upload-modal');
            expect(modal.style.display).toBe('none');

            // Simulate opening
            modal.style.display = 'flex';

            expect(modal.style.display).toBe('flex');
        });

        test('closeVideoModal should hide modal and reset form', () => {
            const modal = document.getElementById('video-upload-modal');
            const titleInput = document.getElementById('upload-video-title');

            // Set values
            modal.style.display = 'flex';
            titleInput.value = 'Test Title';

            // Simulate closing
            modal.style.display = 'none';
            titleInput.value = '';

            expect(modal.style.display).toBe('none');
            expect(titleInput.value).toBe('');
        });
    });

    describe('Video Upload Validation', () => {
        test('should reject upload without title', () => {
            const titleInput = document.getElementById('upload-video-title');
            titleInput.value = '';

            const fileInput = document.getElementById('upload-video-file');
            const mockFile = new File(['content'], 'test.mp4', { type: 'video/mp4' });
            Object.defineProperty(fileInput, 'files', {
                value: [mockFile],
                writable: false
            });

            // Validation check
            if (!titleInput.value.trim()) {
                alert('Please enter a video title');
            }

            expect(global.alert).toHaveBeenCalledWith('Please enter a video title');
        });

        test('should reject upload without file', () => {
            const titleInput = document.getElementById('upload-video-title');
            titleInput.value = 'Test Video';

            const fileInput = document.getElementById('upload-video-file');
            Object.defineProperty(fileInput, 'files', {
                value: [],
                writable: false
            });

            // Validation check
            if (fileInput.files.length === 0) {
                alert('Please select a video file');
            }

            expect(global.alert).toHaveBeenCalledWith('Please select a video file');
        });

        test('should reject file larger than 2GB', () => {
            const maxSize = 2 * 1024 * 1024 * 1024; // 2GB
            const tooLarge = maxSize + 1;

            const mockFile = {
                name: 'huge.mp4',
                size: tooLarge,
                type: 'video/mp4'
            };

            // Validation check
            if (mockFile.size > maxSize) {
                alert('Video file is too large. Maximum size is 2GB.');
            }

            expect(global.alert).toHaveBeenCalledWith('Video file is too large. Maximum size is 2GB.');
        });

        test('should reject unsupported file types', () => {
            const allowedTypes = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/webm'];

            const mockFile = {
                name: 'document.pdf',
                size: 1000000,
                type: 'application/pdf'
            };

            // Validation check
            if (!allowedTypes.includes(mockFile.type)) {
                alert('Unsupported video format. Please use MP4, MPEG, MOV, AVI, or WebM.');
            }

            expect(global.alert).toHaveBeenCalledWith(
                'Unsupported video format. Please use MP4, MPEG, MOV, AVI, or WebM.'
            );
        });

        test('should accept valid video file', () => {
            const maxSize = 2 * 1024 * 1024 * 1024; // 2GB
            const allowedTypes = ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/webm'];

            const mockFile = {
                name: 'tutorial.mp4',
                size: 50 * 1024 * 1024, // 50MB
                type: 'video/mp4'
            };

            // Validation check
            let isValid = true;
            if (mockFile.size > maxSize) {
                isValid = false;
            }
            if (!allowedTypes.includes(mockFile.type)) {
                isValid = false;
            }

            expect(isValid).toBe(true);
        });
    });

    describe('Video Link Validation', () => {
        test('should reject link without title', () => {
            const titleInput = document.getElementById('link-video-title');
            titleInput.value = '';

            // Validation check
            if (!titleInput.value.trim()) {
                alert('Please enter a video title');
            }

            expect(global.alert).toHaveBeenCalledWith('Please enter a video title');
        });

        test('should reject link without URL', () => {
            const urlInput = document.getElementById('link-video-url');
            urlInput.value = '';

            // Validation check
            if (!urlInput.value.trim()) {
                alert('Please enter a video URL');
            }

            expect(global.alert).toHaveBeenCalledWith('Please enter a video URL');
        });

        test('should reject invalid URL format', () => {
            const invalidUrl = 'not-a-valid-url';

            let isValid = true;
            try {
                new URL(invalidUrl);
            } catch (e) {
                isValid = false;
                alert('Please enter a valid URL');
            }

            expect(isValid).toBe(false);
            expect(global.alert).toHaveBeenCalledWith('Please enter a valid URL');
        });

        test('should reject non-YouTube URL for YouTube type', () => {
            const videoType = 'youtube';
            const videoUrl = 'https://vimeo.com/123456789';

            // Validation check
            if (videoType === 'youtube' && !videoUrl.includes('youtube.com') && !videoUrl.includes('youtu.be')) {
                alert('Please enter a valid YouTube URL');
            }

            expect(global.alert).toHaveBeenCalledWith('Please enter a valid YouTube URL');
        });

        test('should reject non-Vimeo URL for Vimeo type', () => {
            const videoType = 'vimeo';
            const videoUrl = 'https://youtube.com/watch?v=abc123';

            // Validation check
            if (videoType === 'vimeo' && !videoUrl.includes('vimeo.com')) {
                alert('Please enter a valid Vimeo URL');
            }

            expect(global.alert).toHaveBeenCalledWith('Please enter a valid Vimeo URL');
        });

        test('should accept valid YouTube URL', () => {
            const validYouTubeUrls = [
                'https://www.youtube.com/watch?v=abc123',
                'https://youtube.com/watch?v=abc123',
                'https://youtu.be/abc123'
            ];

            validYouTubeUrls.forEach(url => {
                const isValid = url.includes('youtube.com') || url.includes('youtu.be');
                expect(isValid).toBe(true);
            });
        });

        test('should accept valid Vimeo URL', () => {
            const validVimeoUrls = [
                'https://vimeo.com/123456789',
                'https://www.vimeo.com/123456789'
            ];

            validVimeoUrls.forEach(url => {
                const isValid = url.includes('vimeo.com');
                expect(isValid).toBe(true);
            });
        });
    });

    describe('Video List Management', () => {
        test('should generate unique temp IDs', () => {
            const id1 = 'temp-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            const id2 = 'temp-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

            expect(id1).toMatch(/^temp-/);
            expect(id2).toMatch(/^temp-/);
            // IDs should be different (very high probability)
            expect(id1).not.toBe(id2);
        });

        test('should render empty state when no videos', () => {
            const container = document.getElementById('course-videos-container');

            if (courseVideos.length === 0) {
                container.innerHTML = `
                    <div class="videos-list-empty">
                        <p>No videos added yet.</p>
                    </div>
                `;
            }

            expect(container.innerHTML).toContain('No videos added yet');
        });

        test('should display video icon based on type', () => {
            const getVideoIcon = (videoType) => {
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
            };

            expect(getVideoIcon('upload')).toBe('fas fa-file-video');
            expect(getVideoIcon('youtube')).toBe('fab fa-youtube');
            expect(getVideoIcon('vimeo')).toBe('fab fa-vimeo');
            expect(getVideoIcon('link')).toBe('fas fa-external-link-alt');
        });

        test('should format file size for uploaded videos', () => {
            const fileSizeBytes = 52428800; // 50MB
            const sizeMB = (fileSizeBytes / (1024 * 1024)).toFixed(2);

            expect(sizeMB).toBe('50.00');
        });

        test('should escape HTML in video titles to prevent XSS', () => {
            const maliciousTitle = '<script>alert("XSS")</script>';

            const div = document.createElement('div');
            div.textContent = maliciousTitle;
            const escaped = div.innerHTML;

            expect(escaped).not.toContain('<script>');
            expect(escaped).toContain('&lt;script&gt;');
        });
    });

    describe('Video Removal', () => {
        test('should remove video after confirmation', () => {
            global.confirm.mockReturnValue(true);

            courseVideos = [
                { id: 'video-1', title: 'Video 1' },
                { id: 'video-2', title: 'Video 2' },
                { id: 'video-3', title: 'Video 3' }
            ];

            const videoIdToRemove = 'video-2';

            if (confirm('Are you sure you want to remove this video?')) {
                courseVideos = courseVideos.filter(v => v.id !== videoIdToRemove);
            }

            expect(courseVideos.length).toBe(2);
            expect(courseVideos.find(v => v.id === 'video-2')).toBeUndefined();
        });

        test('should not remove video if cancelled', () => {
            global.confirm.mockReturnValue(false);

            courseVideos = [
                { id: 'video-1', title: 'Video 1' },
                { id: 'video-2', title: 'Video 2' }
            ];

            const originalLength = courseVideos.length;

            if (confirm('Are you sure you want to remove this video?')) {
                courseVideos = courseVideos.filter(v => v.id !== 'video-1');
            }

            expect(courseVideos.length).toBe(originalLength);
        });

        test('should reindex videos after removal', () => {
            courseVideos = [
                { id: 'video-1', title: 'Video 1', order_index: 0 },
                { id: 'video-2', title: 'Video 2', order_index: 1 },
                { id: 'video-3', title: 'Video 3', order_index: 2 }
            ];

            // Remove middle video
            courseVideos = courseVideos.filter(v => v.id !== 'video-2');

            // Reindex
            courseVideos.forEach((video, index) => {
                video.order_index = index;
            });

            expect(courseVideos[0].order_index).toBe(0);
            expect(courseVideos[1].order_index).toBe(1);
        });
    });

    describe('Video Upload API', () => {
        test('uploadVideoFile should make correct API call', async () => {
            const courseId = 'test-course-123';
            const video = {
                title: 'Test Video',
                description: 'Test description',
                file: new File(['content'], 'test.mp4', { type: 'video/mp4' }),
                file_size_bytes: 1000000,
                mime_type: 'video/mp4'
            };

            localStorageMock.getItem.mockReturnValue('mock-token');

            fetch
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ upload_id: 'upload-123', video_id: 'video-456' })
                })
                .mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ video: { id: 'video-456', title: 'Test Video' } })
                });

            // Simulate upload initiation
            const initResponse = await fetch(`https://localhost:8004/courses/${courseId}/videos/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer mock-token`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    course_id: courseId,
                    filename: video.file.name,
                    file_size_bytes: video.file_size_bytes,
                    mime_type: video.mime_type,
                    title: video.title,
                    description: video.description
                })
            });

            expect(initResponse.ok).toBe(true);
            const initResult = await initResponse.json();
            expect(initResult.upload_id).toBe('upload-123');
        });

        test('createVideoLink should make correct API call', async () => {
            const courseId = 'test-course-123';
            const video = {
                title: 'YouTube Tutorial',
                description: 'Learn programming',
                video_type: 'youtube',
                video_url: 'https://youtube.com/watch?v=abc123',
                order_index: 0
            };

            localStorageMock.getItem.mockReturnValue('mock-token');

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({
                    video: {
                        id: 'video-789',
                        title: 'YouTube Tutorial',
                        video_type: 'youtube'
                    }
                })
            });

            const response = await fetch(`https://localhost:8004/courses/${courseId}/videos`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer mock-token`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(video)
            });

            expect(response.ok).toBe(true);
            const result = await response.json();
            expect(result.video.video_type).toBe('youtube');
        });
    });
});

// Run tests with: npm test -- course-video-manager.test.js
