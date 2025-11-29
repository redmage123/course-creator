-- Migration: 031_mobile_experience.sql
-- What: Creates tables for mobile experience and responsive design features.
-- Where: Analytics/User Management database schema.
-- Why: Enables:
--      1. Device preference management for responsive UI
--      2. Mobile session tracking and analytics
--      3. Offline content synchronization
--      4. Push notification management
--      5. Mobile-optimized content caching
--      6. Touch gesture preferences
--      7. Bandwidth-aware content delivery

-- ============================================================================
-- USER DEVICE PREFERENCES
-- What: Stores user device settings and UI preferences per device.
-- Why: Enables personalized responsive experience across devices.
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_device_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL CHECK (device_type IN ('mobile', 'tablet', 'desktop', 'watch', 'tv')),
    device_name VARCHAR(255),
    os_name VARCHAR(100),
    os_version VARCHAR(50),
    browser_name VARCHAR(100),
    browser_version VARCHAR(50),
    screen_width INTEGER,
    screen_height INTEGER,
    pixel_ratio DECIMAL(4, 2),

    -- UI Preferences
    preferred_theme VARCHAR(20) DEFAULT 'system' CHECK (preferred_theme IN ('light', 'dark', 'system', 'high_contrast')),
    font_size_preference VARCHAR(20) DEFAULT 'medium' CHECK (font_size_preference IN ('small', 'medium', 'large', 'extra_large')),
    reduced_motion BOOLEAN DEFAULT false,
    high_contrast BOOLEAN DEFAULT false,
    compact_mode BOOLEAN DEFAULT false,

    -- Navigation preferences
    sidebar_collapsed BOOLEAN DEFAULT false,
    preferred_navigation VARCHAR(20) DEFAULT 'auto' CHECK (preferred_navigation IN ('bottom_tabs', 'sidebar', 'hamburger', 'auto')),
    gesture_navigation BOOLEAN DEFAULT true,
    haptic_feedback BOOLEAN DEFAULT true,

    -- Content preferences
    data_saver_mode BOOLEAN DEFAULT false,
    auto_play_video BOOLEAN DEFAULT true,
    video_quality_preference VARCHAR(20) DEFAULT 'auto' CHECK (video_quality_preference IN ('auto', 'low', 'medium', 'high', '4k')),
    image_quality_preference VARCHAR(20) DEFAULT 'auto' CHECK (image_quality_preference IN ('auto', 'low', 'medium', 'high')),

    -- Offline preferences
    offline_enabled BOOLEAN DEFAULT true,
    max_offline_storage_mb INTEGER DEFAULT 1000,
    auto_download_wifi_only BOOLEAN DEFAULT true,

    is_primary_device BOOLEAN DEFAULT false,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, device_id)
);

CREATE INDEX idx_device_prefs_user ON user_device_preferences(user_id);
CREATE INDEX idx_device_prefs_type ON user_device_preferences(device_type);
CREATE INDEX idx_device_prefs_last_active ON user_device_preferences(last_active_at);

-- ============================================================================
-- MOBILE SESSIONS
-- What: Tracks mobile application sessions for analytics.
-- Why: Enables mobile-specific usage analytics and performance monitoring.
-- ============================================================================

CREATE TABLE IF NOT EXISTS mobile_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    device_preference_id UUID REFERENCES user_device_preferences(id) ON DELETE SET NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,

    -- Session info
    app_version VARCHAR(50),
    build_number VARCHAR(50),
    platform VARCHAR(50) NOT NULL CHECK (platform IN ('ios', 'android', 'pwa', 'mobile_web')),

    -- Connection info
    connection_type VARCHAR(50) CHECK (connection_type IN ('wifi', '4g', '5g', '3g', '2g', 'offline', 'unknown')),
    ip_address INET,
    country_code CHAR(2),
    timezone VARCHAR(100),

    -- Session metrics
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    screen_views INTEGER DEFAULT 0,
    interactions INTEGER DEFAULT 0,

    -- Performance metrics
    app_launch_time_ms INTEGER,
    avg_screen_load_time_ms INTEGER,
    memory_warnings INTEGER DEFAULT 0,
    crashes INTEGER DEFAULT 0,

    -- Engagement
    content_items_viewed INTEGER DEFAULT 0,
    videos_watched INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    labs_started INTEGER DEFAULT 0,

    is_background BOOLEAN DEFAULT false,
    is_offline BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_mobile_sessions_user ON mobile_sessions(user_id);
CREATE INDEX idx_mobile_sessions_platform ON mobile_sessions(platform);
CREATE INDEX idx_mobile_sessions_start ON mobile_sessions(session_start);
CREATE INDEX idx_mobile_sessions_token ON mobile_sessions(session_token);

-- ============================================================================
-- OFFLINE CONTENT SYNC
-- What: Manages offline content synchronization.
-- Why: Enables learning continuity without internet connection.
-- ============================================================================

CREATE TABLE IF NOT EXISTS offline_content_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id VARCHAR(255) NOT NULL,

    -- Content reference
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('course', 'module', 'lesson', 'quiz', 'lab', 'video', 'document', 'slide')),
    content_id UUID NOT NULL,
    content_version VARCHAR(50),

    -- Sync status
    sync_status VARCHAR(50) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'downloading', 'downloaded', 'syncing', 'synced', 'error', 'expired', 'deleted')),
    sync_priority INTEGER DEFAULT 5 CHECK (sync_priority BETWEEN 1 AND 10),

    -- Storage
    storage_size_bytes BIGINT,
    compressed_size_bytes BIGINT,
    storage_path TEXT,
    checksum VARCHAR(64),

    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    download_started_at TIMESTAMP WITH TIME ZONE,
    download_completed_at TIMESTAMP WITH TIME ZONE,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Error handling
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_error TEXT,

    -- Progress tracking (for offline quiz/lab)
    has_offline_progress BOOLEAN DEFAULT false,
    offline_progress_data JSONB,
    progress_synced_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, device_id, content_type, content_id)
);

CREATE INDEX idx_offline_sync_user_device ON offline_content_sync(user_id, device_id);
CREATE INDEX idx_offline_sync_status ON offline_content_sync(sync_status);
CREATE INDEX idx_offline_sync_content ON offline_content_sync(content_type, content_id);
CREATE INDEX idx_offline_sync_expires ON offline_content_sync(expires_at);

-- ============================================================================
-- PUSH NOTIFICATION SETTINGS
-- What: User push notification preferences per device.
-- Why: Enables targeted, preference-respecting notifications.
-- ============================================================================

CREATE TABLE IF NOT EXISTS push_notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_preference_id UUID REFERENCES user_device_preferences(id) ON DELETE CASCADE,

    -- Tokens
    fcm_token TEXT,
    apns_token TEXT,
    web_push_endpoint TEXT,
    web_push_p256dh TEXT,
    web_push_auth TEXT,

    -- Global settings
    notifications_enabled BOOLEAN DEFAULT true,
    quiet_hours_enabled BOOLEAN DEFAULT false,
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    quiet_hours_timezone VARCHAR(100),

    -- Notification categories
    course_updates BOOLEAN DEFAULT true,
    quiz_reminders BOOLEAN DEFAULT true,
    assignment_deadlines BOOLEAN DEFAULT true,
    discussion_replies BOOLEAN DEFAULT true,
    instructor_messages BOOLEAN DEFAULT true,
    certificate_earned BOOLEAN DEFAULT true,
    new_content_available BOOLEAN DEFAULT true,
    promotion_offers BOOLEAN DEFAULT false,
    system_announcements BOOLEAN DEFAULT true,

    -- Delivery preferences
    group_notifications BOOLEAN DEFAULT true,
    show_preview BOOLEAN DEFAULT true,
    sound_enabled BOOLEAN DEFAULT true,
    vibration_enabled BOOLEAN DEFAULT true,
    badge_count_enabled BOOLEAN DEFAULT true,

    -- Frequency limits
    max_notifications_per_hour INTEGER DEFAULT 10,
    digest_mode BOOLEAN DEFAULT false,
    digest_time TIME DEFAULT '09:00:00',

    token_updated_at TIMESTAMP WITH TIME ZONE,
    last_notification_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_push_settings_user ON push_notification_settings(user_id);
CREATE INDEX idx_push_settings_device ON push_notification_settings(device_preference_id);
CREATE INDEX idx_push_settings_fcm ON push_notification_settings(fcm_token);

-- ============================================================================
-- PUSH NOTIFICATION HISTORY
-- What: History of sent push notifications.
-- Why: Enables notification analytics and debugging.
-- ============================================================================

CREATE TABLE IF NOT EXISTS push_notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    setting_id UUID REFERENCES push_notification_settings(id) ON DELETE SET NULL,

    -- Notification content
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),

    -- Targeting
    deep_link TEXT,
    action_type VARCHAR(50),
    action_data JSONB,

    -- Media
    image_url TEXT,
    icon_url TEXT,

    -- Delivery status
    delivery_status VARCHAR(50) DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'delivered', 'failed', 'expired', 'cancelled')),
    platform_message_id VARCHAR(255),

    -- Interaction
    opened_at TIMESTAMP WITH TIME ZONE,
    action_taken VARCHAR(100),
    dismissed_at TIMESTAMP WITH TIME ZONE,

    -- Error tracking
    error_code VARCHAR(100),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timing
    scheduled_for TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    ttl_seconds INTEGER DEFAULT 86400,
    expires_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_push_history_user ON push_notification_history(user_id);
CREATE INDEX idx_push_history_status ON push_notification_history(delivery_status);
CREATE INDEX idx_push_history_category ON push_notification_history(category);
CREATE INDEX idx_push_history_sent ON push_notification_history(sent_at);
CREATE INDEX idx_push_history_opened ON push_notification_history(opened_at) WHERE opened_at IS NOT NULL;

-- ============================================================================
-- MOBILE CONTENT CACHE
-- What: Tracks mobile content caching for bandwidth optimization.
-- Why: Enables efficient content delivery based on device capabilities.
-- ============================================================================

CREATE TABLE IF NOT EXISTS mobile_content_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('image', 'video', 'document', 'audio', 'data', 'style', 'script')),
    content_id UUID NOT NULL,

    -- Variants for different quality/size
    variant_key VARCHAR(100) NOT NULL,
    variant_quality VARCHAR(20) CHECK (variant_quality IN ('thumbnail', 'low', 'medium', 'high', 'original')),

    -- Storage
    cache_url TEXT NOT NULL,
    cdn_url TEXT,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100),

    -- Optimization
    is_compressed BOOLEAN DEFAULT false,
    compression_ratio DECIMAL(4, 2),
    is_lazy_loadable BOOLEAN DEFAULT true,
    preload_priority INTEGER DEFAULT 5,

    -- Responsive info
    width INTEGER,
    height INTEGER,
    aspect_ratio DECIMAL(6, 4),

    -- Validation
    etag VARCHAR(255),
    last_modified TIMESTAMP WITH TIME ZONE,
    cache_control VARCHAR(255),
    max_age_seconds INTEGER,

    -- Stats
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    UNIQUE(content_type, content_id, variant_key)
);

CREATE INDEX idx_content_cache_content ON mobile_content_cache(content_type, content_id);
CREATE INDEX idx_content_cache_variant ON mobile_content_cache(variant_key);
CREATE INDEX idx_content_cache_expires ON mobile_content_cache(expires_at);
CREATE INDEX idx_content_cache_access ON mobile_content_cache(last_accessed_at);

-- ============================================================================
-- TOUCH GESTURE CUSTOMIZATION
-- What: Custom touch gesture mappings per user.
-- Why: Enables accessibility and personalized touch interactions.
-- ============================================================================

CREATE TABLE IF NOT EXISTS touch_gesture_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_preference_id UUID REFERENCES user_device_preferences(id) ON DELETE CASCADE,

    -- Gesture mappings
    swipe_left_action VARCHAR(50) DEFAULT 'next_item',
    swipe_right_action VARCHAR(50) DEFAULT 'previous_item',
    swipe_down_action VARCHAR(50) DEFAULT 'refresh',
    swipe_up_action VARCHAR(50) DEFAULT 'scroll_up',
    double_tap_action VARCHAR(50) DEFAULT 'toggle_fullscreen',
    long_press_action VARCHAR(50) DEFAULT 'context_menu',
    pinch_action VARCHAR(50) DEFAULT 'zoom',
    two_finger_swipe_action VARCHAR(50) DEFAULT 'navigate_back',

    -- Sensitivity settings
    swipe_threshold_px INTEGER DEFAULT 50,
    long_press_duration_ms INTEGER DEFAULT 500,
    double_tap_interval_ms INTEGER DEFAULT 300,
    scroll_sensitivity DECIMAL(3, 2) DEFAULT 1.0,

    -- Accessibility
    gesture_feedback_enabled BOOLEAN DEFAULT true,
    gesture_hints_enabled BOOLEAN DEFAULT true,
    simplified_gestures BOOLEAN DEFAULT false,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_gesture_settings_user ON touch_gesture_settings(user_id);
CREATE INDEX idx_gesture_settings_device ON touch_gesture_settings(device_preference_id);

-- ============================================================================
-- RESPONSIVE BREAKPOINT ANALYTICS
-- What: Analytics for responsive design usage patterns.
-- Why: Enables data-driven responsive design decisions.
-- ============================================================================

CREATE TABLE IF NOT EXISTS responsive_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Dimensions
    recorded_date DATE NOT NULL,
    organization_id UUID,

    -- Breakpoint distribution
    breakpoint VARCHAR(20) NOT NULL CHECK (breakpoint IN ('xs', 'sm', 'md', 'lg', 'xl', '2xl')),
    device_type VARCHAR(20) NOT NULL,
    orientation VARCHAR(20) CHECK (orientation IN ('portrait', 'landscape')),

    -- Metrics
    unique_users INTEGER DEFAULT 0,
    total_sessions INTEGER DEFAULT 0,
    total_page_views INTEGER DEFAULT 0,
    avg_session_duration_seconds INTEGER,

    -- Engagement by breakpoint
    course_completions INTEGER DEFAULT 0,
    quiz_completions INTEGER DEFAULT 0,
    video_completions INTEGER DEFAULT 0,

    -- Performance by breakpoint
    avg_page_load_ms INTEGER,
    avg_interaction_delay_ms INTEGER,
    layout_shift_score DECIMAL(5, 4),

    -- Problems
    ui_error_count INTEGER DEFAULT 0,
    accessibility_issues INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(recorded_date, organization_id, breakpoint, device_type, orientation)
);

CREATE INDEX idx_responsive_analytics_date ON responsive_analytics(recorded_date);
CREATE INDEX idx_responsive_analytics_org ON responsive_analytics(organization_id);
CREATE INDEX idx_responsive_analytics_breakpoint ON responsive_analytics(breakpoint);

-- ============================================================================
-- BANDWIDTH USAGE TRACKING
-- What: Tracks data usage for bandwidth optimization.
-- Why: Enables data saver features and usage monitoring.
-- ============================================================================

CREATE TABLE IF NOT EXISTS bandwidth_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_preference_id UUID REFERENCES user_device_preferences(id) ON DELETE SET NULL,
    session_id UUID REFERENCES mobile_sessions(id) ON DELETE SET NULL,

    -- Period
    usage_date DATE NOT NULL,
    usage_hour INTEGER CHECK (usage_hour BETWEEN 0 AND 23),

    -- Data usage by type
    video_bytes_downloaded BIGINT DEFAULT 0,
    image_bytes_downloaded BIGINT DEFAULT 0,
    document_bytes_downloaded BIGINT DEFAULT 0,
    api_bytes_downloaded BIGINT DEFAULT 0,
    other_bytes_downloaded BIGINT DEFAULT 0,
    total_bytes_downloaded BIGINT DEFAULT 0,

    -- Upload usage
    bytes_uploaded BIGINT DEFAULT 0,

    -- Connection info
    connection_type VARCHAR(50),
    is_metered BOOLEAN,

    -- Savings from optimization
    bytes_saved_compression BIGINT DEFAULT 0,
    bytes_saved_caching BIGINT DEFAULT 0,
    bytes_saved_data_saver BIGINT DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(user_id, device_preference_id, usage_date, usage_hour)
);

CREATE INDEX idx_bandwidth_user ON bandwidth_usage(user_id);
CREATE INDEX idx_bandwidth_date ON bandwidth_usage(usage_date);
CREATE INDEX idx_bandwidth_connection ON bandwidth_usage(connection_type);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamps
CREATE OR REPLACE FUNCTION update_mobile_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_device_preferences_timestamp
    BEFORE UPDATE ON user_device_preferences
    FOR EACH ROW EXECUTE FUNCTION update_mobile_timestamp();

CREATE TRIGGER update_mobile_sessions_timestamp
    BEFORE UPDATE ON mobile_sessions
    FOR EACH ROW EXECUTE FUNCTION update_mobile_timestamp();

CREATE TRIGGER update_offline_sync_timestamp
    BEFORE UPDATE ON offline_content_sync
    FOR EACH ROW EXECUTE FUNCTION update_mobile_timestamp();

CREATE TRIGGER update_push_settings_timestamp
    BEFORE UPDATE ON push_notification_settings
    FOR EACH ROW EXECUTE FUNCTION update_mobile_timestamp();

CREATE TRIGGER update_content_cache_timestamp
    BEFORE UPDATE ON mobile_content_cache
    FOR EACH ROW EXECUTE FUNCTION update_mobile_timestamp();

CREATE TRIGGER update_gesture_settings_timestamp
    BEFORE UPDATE ON touch_gesture_settings
    FOR EACH ROW EXECUTE FUNCTION update_mobile_timestamp();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE user_device_preferences IS 'Stores per-device UI and content preferences for responsive experience';
COMMENT ON TABLE mobile_sessions IS 'Tracks mobile app sessions for analytics and performance monitoring';
COMMENT ON TABLE offline_content_sync IS 'Manages offline content download and synchronization';
COMMENT ON TABLE push_notification_settings IS 'User push notification preferences per device';
COMMENT ON TABLE push_notification_history IS 'History of sent notifications for analytics';
COMMENT ON TABLE mobile_content_cache IS 'Optimized content variants for mobile delivery';
COMMENT ON TABLE touch_gesture_settings IS 'Custom touch gesture mappings for accessibility';
COMMENT ON TABLE responsive_analytics IS 'Analytics for responsive design usage patterns';
COMMENT ON TABLE bandwidth_usage IS 'Data usage tracking for bandwidth optimization';
