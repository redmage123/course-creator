/**
 * DemoPlayer Component - Course Creator Platform Demo Slideshow
 *
 * BUSINESS PURPOSE:
 * Interactive demo player showcasing platform features with professionally
 * narrated screencasts. Uses ElevenLabs AI-generated audio with SSML
 * markup for expressive, engaging narration.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Perfect audio/video synchronization with drift correction
 * - Auto-advance slides with smooth transitions
 * - SSML-enhanced narration with dramatic pauses and emphasis
 * - Keyboard navigation for accessibility
 * - Responsive design with subtitle overlay
 *
 * AUDIO/VIDEO SYNC APPROACH:
 * Uses a sync engine that monitors drift between audio and video,
 * correcting when they diverge beyond a threshold (100ms default).
 * This ensures narration stays perfectly aligned with visuals.
 */

import React, { useRef, useState, useEffect, useCallback } from 'react';
import styles from './DemoPlayer.module.css';

// Types
interface DemoSlide {
  id: number;
  title: string;
  video: string;
  audio: string;
  duration: number;
  narration: string;
}

interface DemoPlayerProps {
  autoPlay?: boolean;
  showSubtitles?: boolean;
  onComplete?: () => void;
}

// Demo slide data with video and audio paths
// Duration values match regenerated ElevenLabs audio (Rachel voice, multilingual_v2 model)
// Videos need to be recorded to match these exact audio durations
const DEMO_SLIDES: DemoSlide[] = [
  {
    id: 1,
    title: 'Platform Introduction',
    video: '/static/demo/videos/slide_01_platform_introduction.mp4',
    audio: '/static/demo/audio/slide_01_narration.mp3',
    duration: 16, // Actual: 15.8s
    narration: 'Welcome to the Course Creator Platform. Built specifically for corporate training teams and professional instructors who need to create courses fast. Our AI-powered system transforms what used to take weeks into just minutes. In the next slide, we\'ll show you how to get started.'
  },
  {
    id: 2,
    title: 'Organization Registration',
    video: '/static/demo/videos/slide_02_organization_registration.mp4',
    audio: '/static/demo/audio/slide_02_narration.mp3',
    duration: 26, // Actual: 25.9s
    narration: 'To get started, simply click Register Organization on the home page. Now, let\'s fill in the details. Enter your organization name, website, and a brief description. Add your contact information, including business email and address. Finally, set up your administrator account with credentials. Click submit, and there you go! Your organization is successfully registered. Next, we\'ll show you how to create projects.'
  },
  {
    id: 3,
    title: 'Organization Admin Dashboard',
    video: '/static/demo/videos/slide_03_organization_admin_dashboard.mp4',
    audio: '/static/demo/audio/slide_03_narration.mp3',
    duration: 81, // Actual: 81.2s
    narration: 'Let\'s log in as the organization admin we just created. First, navigate to the home page and click the Login button in the header. Now, enter the email address: sarah at acmelearning dot edu. Then enter the password. Click the login button to sign in. Notice the user icon in the header changes to show you\'re logged in. You\'re now redirected to your organization admin dashboard! From here, you can manage everything. Notice the purple AI assistant button in the bottom right corner. You can use it to manage your organization through natural language instead of filling out forms.'
  },
  {
    id: 4,
    title: 'Creating Training Tracks',
    video: '/static/demo/videos/slide_04_creating_training_tracks.mp4',
    audio: '/static/demo/audio/slide_04_narration.mp3',
    duration: 41, // Actual: 41.4s
    narration: 'Now let\'s create a learning track! We\'re already viewing the Tracks tab from the previous slide. Click the Create New Track button. This opens the track creation form. First, enter the track name: Python Fundamentals. Next, select the project. Choose Data Science Foundations from the dropdown. Then select the level. We\'ll make this a Beginner track. Now add a description: Learn Python basics for data science. Click Create Track, and there you go! Your track is created.'
  },
  {
    id: 5,
    title: 'AI Assistant',
    video: '/static/demo/videos/slide_05_ai_assistant.mp4',
    audio: '/static/demo/audio/slide_05_narration.mp3',
    duration: 47, // Actual: 47.2s
    narration: 'Instead of filling out forms, you can simply tell our AI assistant what you need. Watch how easy it is! Click the purple AI assistant button in the bottom right corner. The chat panel slides up. Now, just describe what you want in plain English. Type: Create an intermediate track called Machine Learning Basics for the Data Science project. The AI understands your request instantly! It confirms the details and creates the track for you. No forms to fill out. No dropdowns to navigate. Just natural conversation.'
  },
  {
    id: 6,
    title: 'Adding Instructors',
    video: '/static/demo/videos/slide_06_adding_instructors.mp4',
    audio: '/static/demo/audio/slide_06_narration.mp3',
    duration: 19, // Actual: 18.8s
    narration: 'Your instructors are your greatest asset. Bring them onboard in seconds, assign them to specific projects or tracks, and they\'re instantly connected to your Slack or Teams channels for seamless collaboration. Whether it\'s co-developing courses with colleagues or running independent programs, everything integrates with the tools your team already uses.'
  },
  {
    id: 7,
    title: 'Instructor Dashboard',
    video: '/static/demo/videos/slide_07_instructor_dashboard.mp4',
    audio: '/static/demo/audio/slide_07_narration.mp3',
    duration: 32, // Actual: 31.5s
    narration: 'Instructors have powerful AI tools at their fingertips! Tell the system your learning objectives, your target audience, and your key topics. Then watch as artificial intelligence generates a complete course structure, suggested modules, learning outcomes, even quiz questions! You review, refine, and approve. What used to take days of curriculum design now takes minutes. And when you schedule live sessions? Automatic Zoom or Teams integration means one click launches your class!'
  },
  {
    id: 8,
    title: 'Course Content Generation',
    video: '/static/demo/videos/slide_08_course_content.mp4',
    audio: '/static/demo/audio/slide_08_narration.mp3',
    duration: 36, // Actual: 35.8s
    narration: 'AI accelerates content creation! Need lesson content? Describe your topic and the AI generates a complete lesson draft. You just add your expertise and real-world examples. Creating quizzes? AI suggests questions based on your content: multiple choice, code challenges, scenario-based problems. You spend your time refining and personalizing, not starting from scratch. Upload presentations, embed videos, add code exercises with real-time feedback. The AI accelerates creation. You ensure quality.'
  },
  {
    id: 9,
    title: 'Student Enrollment',
    video: '/static/demo/videos/slide_09_enroll_students.mp4',
    audio: '/static/demo/audio/slide_09_narration.mp3',
    duration: 22, // Actual: 22.2s
    narration: 'Your course is ready! Now it\'s time to welcome your students. One student? Easy. One hundred students? Even easier! Upload a CSV file and enroll an entire class in seconds. Organize by section, group by skill level, track by semester. However you teach, we adapt. Because managing students should be effortless, not exhausting.'
  },
  {
    id: 10,
    title: 'Student Dashboard',
    video: '/static/demo/videos/slide_10_student_dashboard.mp4',
    audio: '/static/demo/audio/slide_10_narration.mp3',
    duration: 18, // Actual: 17.8s
    narration: 'Now let\'s see what your students experience. They log in and immediately, everything they need is right there. Their courses, their progress, upcoming deadlines, recent achievements. No confusion. No hunting for information. Just a clear path forward and the motivation to keep going.'
  },
  {
    id: 11,
    title: 'Course Browsing & Labs',
    video: '/static/demo/videos/slide_11_course_browsing.mp4',
    audio: '/static/demo/audio/slide_11_narration.mp3',
    duration: 35, // Actual: 34.5s
    narration: 'Students browse the catalog, discover courses, and enroll with one click. The game changer for technical training? When they hit a coding lesson, professional development environments open right in their browser! VS Code for web development. PyCharm for Python. JupyterLab for data science. Full Linux terminal for system administration. No installation. No configuration. No IT headaches! This is why corporate training teams choose us! Their developers learn with real professional tools, no setup time wasted.'
  },
  {
    id: 12,
    title: 'Quiz & Assessment',
    video: '/static/demo/videos/slide_12_quiz_assessment.mp4',
    audio: '/static/demo/audio/slide_12_narration.mp3',
    duration: 28, // Actual: 27.5s
    narration: 'Assessment shouldn\'t feel like a gotcha moment. It should be a learning opportunity! Our quiz system delivers multiple question formats: multiple choice for quick checks, coding challenges for hands-on validation, short answer for deeper understanding. But here\'s what matters most: instant feedback! Not just a score, but detailed explanations that turn mistakes into mastery. Because real learning happens when students understand why.'
  },
  {
    id: 13,
    title: 'Student Progress',
    video: '/static/demo/videos/slide_13_student_progress.mp4',
    audio: '/static/demo/audio/slide_13_narration.mp3',
    duration: 20, // Actual: 20.3s
    narration: 'Progress should be visible and celebrated! Every quiz completed. Every module mastered. Every achievement unlocked. Students see their journey unfold in real time. Completion rates, quiz scores, time invested. It all adds up to something powerful: proof of growth! And that\'s what keeps them coming back.'
  },
  {
    id: 14,
    title: 'Instructor Analytics',
    video: '/static/demo/videos/slide_14_instructor_analytics.mp4',
    audio: '/static/demo/audio/slide_14_narration.mp3',
    duration: 34, // Actual: 34.2s
    narration: 'We go beyond basic LMS reporting! Our AI-powered analytics don\'t just show you data. They surface insights! Which students are at risk of falling behind? AI flags them automatically. What content drives the most engagement? AI identifies patterns across all your courses. Which quiz questions are too easy or too hard? AI analyzes performance trends and suggests adjustments. Export reports to Slack or Teams so your entire training team stays informed. This isn\'t just analytics. It\'s intelligent course optimization!'
  },
  {
    id: 15,
    title: 'Summary & Next Steps',
    video: '/static/demo/videos/slide_15_summary.mp4',
    audio: '/static/demo/audio/slide_15_narration.mp3',
    duration: 26, // Actual: 26.3s
    narration: 'So that\'s Course Creator Platform! AI handles course development, content generation, and intelligent analytics. Your team works inside Slack, Teams, and Zoom, and everything integrates seamlessly. Whether you\'re building corporate training programs or teaching as an independent instructor, we turn weeks of work into minutes of guided setup. Ready to see it in action? Visit our site to get started!'
  }
];

// Sync configuration constants
const SYNC_CHECK_INTERVAL_MS = 250; // How often to check drift
const DRIFT_THRESHOLD_MS = 100; // Max allowed drift before correction
const AUTO_ADVANCE_DELAY_MS = 1000; // Delay before auto-advancing to next slide

/**
 * DemoPlayer Component
 *
 * WHY THIS IMPLEMENTATION:
 * - Uses refs for video/audio elements to enable precise sync control
 * - Implements drift correction to maintain perfect audio/video alignment
 * - Auto-advance with configurable delay for smooth transitions
 * - Keyboard navigation for accessibility
 * - Subtitle overlay with user toggle control
 */
export const DemoPlayer: React.FC<DemoPlayerProps> = ({
  autoPlay = false,
  showSubtitles: initialShowSubtitles = true,
  onComplete
}) => {
  // State
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentTime, setCurrentTime] = useState('0:00');
  const [totalTime, setTotalTime] = useState('0:00');
  const [showSubtitles, setShowSubtitles] = useState(initialShowSubtitles);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const syncIntervalRef = useRef<number | null>(null);
  const slideTimelineRef = useRef<HTMLDivElement>(null);

  // Current slide data
  const currentSlide = DEMO_SLIDES[currentSlideIndex];

  /**
   * Format seconds to mm:ss display
   */
  const formatTime = (seconds: number): string => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  /**
   * Sync Engine - Monitors and corrects audio/video drift
   *
   * WHY THIS APPROACH:
   * HTML5 audio and video elements can drift apart over time due to
   * buffering, decoding delays, or system performance. This sync engine
   * checks drift every 250ms and corrects when beyond threshold.
   */
  const startSyncEngine = useCallback(() => {
    if (syncIntervalRef.current) return;

    syncIntervalRef.current = window.setInterval(() => {
      const video = videoRef.current;
      const audio = audioRef.current;

      if (!video || !audio || video.paused) return;

      // Calculate drift in milliseconds
      const driftMs = Math.abs(video.currentTime - audio.currentTime) * 1000;

      if (driftMs > DRIFT_THRESHOLD_MS) {
        // Correct audio position to match video
        audio.currentTime = video.currentTime;
        console.log(`[Sync Engine] Corrected drift of ${driftMs.toFixed(0)}ms`);
      }
    }, SYNC_CHECK_INTERVAL_MS);
  }, []);

  /**
   * Stop the sync engine
   */
  const stopSyncEngine = useCallback(() => {
    if (syncIntervalRef.current) {
      clearInterval(syncIntervalRef.current);
      syncIntervalRef.current = null;
    }
  }, []);

  /**
   * Load a specific slide
   */
  const loadSlide = useCallback((index: number) => {
    if (index < 0 || index >= DEMO_SLIDES.length) return;

    const slide = DEMO_SLIDES[index];
    const video = videoRef.current;
    const audio = audioRef.current;

    if (!video || !audio) return;

    console.log(`[DemoPlayer] Loading slide ${slide.id}: ${slide.title}`);

    // Stop current playback
    video.pause();
    audio.pause();
    stopSyncEngine();

    // Update sources
    video.src = slide.video;
    audio.src = slide.audio;
    audio.volume = 0.8;

    // Load media
    video.load();
    audio.load();

    // Update state
    setCurrentSlideIndex(index);
    setProgress(0);
    setIsLoading(true);
    setError(null);

    // Scroll slide into view in timeline
    if (slideTimelineRef.current) {
      const thumbnails = slideTimelineRef.current.children;
      if (thumbnails[index]) {
        (thumbnails[index] as HTMLElement).scrollIntoView({
          behavior: 'smooth',
          block: 'nearest',
          inline: 'center'
        });
      }
    }
  }, [stopSyncEngine]);

  /**
   * Start playback with synchronized audio/video
   */
  const play = useCallback(async () => {
    const video = videoRef.current;
    const audio = audioRef.current;

    if (!video || !audio) return;

    try {
      // Sync audio to video position before playing
      audio.currentTime = video.currentTime;

      // Start both playbacks
      await Promise.all([
        video.play(),
        audio.play()
      ]);

      setIsPlaying(true);
      startSyncEngine();

      console.log('[DemoPlayer] Playback started with sync engine');
    } catch (err) {
      console.error('[DemoPlayer] Playback failed:', err);
      setError('Failed to start playback. Please try again.');
    }
  }, [startSyncEngine]);

  /**
   * Pause playback
   */
  const pause = useCallback(() => {
    const video = videoRef.current;
    const audio = audioRef.current;

    if (video) video.pause();
    if (audio) audio.pause();

    setIsPlaying(false);
    stopSyncEngine();

    console.log('[DemoPlayer] Playback paused');
  }, [stopSyncEngine]);

  /**
   * Toggle play/pause
   */
  const togglePlayPause = useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);

  /**
   * Navigate to previous slide
   */
  const previousSlide = useCallback(() => {
    if (currentSlideIndex > 0) {
      loadSlide(currentSlideIndex - 1);
    }
  }, [currentSlideIndex, loadSlide]);

  /**
   * Navigate to next slide
   */
  const nextSlide = useCallback(() => {
    if (currentSlideIndex < DEMO_SLIDES.length - 1) {
      loadSlide(currentSlideIndex + 1);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentSlideIndex, loadSlide, onComplete]);

  /**
   * Seek to position
   */
  const seek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const video = videoRef.current;
    const audio = audioRef.current;

    if (!video || !audio) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    const newTime = pos * video.duration;

    // Seek both video and audio
    video.currentTime = newTime;
    audio.currentTime = newTime;

    console.log(`[DemoPlayer] Seeked to ${formatTime(newTime)}`);
  }, []);

  /**
   * Handle video time update
   */
  const handleTimeUpdate = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;

    const progressPercent = (video.currentTime / video.duration) * 100;
    setProgress(progressPercent);
    setCurrentTime(formatTime(video.currentTime));
    setTotalTime(formatTime(video.duration));
  }, []);

  /**
   * Handle video ended - auto-advance to next slide
   */
  const handleVideoEnded = useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }

    if (currentSlideIndex < DEMO_SLIDES.length - 1) {
      // Auto-advance after delay
      setTimeout(() => {
        loadSlide(currentSlideIndex + 1);

        // Auto-play if was playing before
        if (isPlaying) {
          setTimeout(() => play(), 500);
        }
      }, AUTO_ADVANCE_DELAY_MS);
    } else {
      // Demo complete
      setIsPlaying(false);
      stopSyncEngine();
      if (onComplete) onComplete();
    }
  }, [currentSlideIndex, isPlaying, loadSlide, play, stopSyncEngine, onComplete]);

  /**
   * Handle video can play - ready to start
   */
  const handleCanPlay = useCallback(() => {
    setIsLoading(false);

    // Auto-play if enabled
    if (autoPlay && currentSlideIndex === 0) {
      play();
    }
  }, [autoPlay, currentSlideIndex, play]);

  /**
   * Handle video error
   */
  const handleVideoError = useCallback(() => {
    setIsLoading(false);
    setError('Failed to load video. Please check your connection and try again.');
  }, []);

  /**
   * Keyboard navigation
   */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case ' ':
          e.preventDefault();
          togglePlayPause();
          break;
        case 'ArrowLeft':
          previousSlide();
          break;
        case 'ArrowRight':
          nextSlide();
          break;
        case 'c':
          setShowSubtitles(prev => !prev);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [togglePlayPause, previousSlide, nextSlide]);

  /**
   * Initialize first slide on mount
   */
  useEffect(() => {
    loadSlide(0);
  }, [loadSlide]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stopSyncEngine();
    };
  }, [stopSyncEngine]);

  return (
    <div className={styles.demoContainer}>
      {/* Header */}
      <header className={styles.demoHeader}>
        <div>
          <h1 className={styles.demoTitle}>Course Creator Platform Demo</h1>
          <p className={styles.demoSubtitle}>See the platform in action</p>
        </div>
        <div className={styles.progressIndicator}>
          Slide {currentSlide.id} of {DEMO_SLIDES.length}
        </div>
      </header>

      {/* Video Section */}
      <div className={styles.videoSection}>
        {/* Loading State */}
        {isLoading && (
          <div className={styles.loadingState}>
            <div className={styles.spinner} />
            <p>Loading slide...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className={styles.errorState}>
            <span className={styles.errorIcon}>!</span>
            <p>{error}</p>
            <button onClick={() => loadSlide(currentSlideIndex)} className={styles.retryButton}>
              Try Again
            </button>
          </div>
        )}

        {/* Video Player */}
        <video
          ref={videoRef}
          className={styles.videoPlayer}
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleVideoEnded}
          onCanPlay={handleCanPlay}
          onError={handleVideoError}
          playsInline
        />

        {/* Hidden Audio Player for Narration */}
        <audio ref={audioRef} preload="auto" />

        {/* Subtitle/Narration Overlay */}
        {showSubtitles && isPlaying && (
          <div className={styles.narrationOverlay}>
            <div className={styles.narrationBox}>
              <span className={styles.narrationIcon}>CC</span>
              {currentSlide.narration}
            </div>
          </div>
        )}
      </div>

      {/* Controls Section */}
      <div className={styles.controlsSection}>
        {/* Main Controls Row */}
        <div className={styles.controlsRow}>
          <button
            className={`${styles.controlBtn}`}
            onClick={previousSlide}
            disabled={currentSlideIndex === 0}
            aria-label="Previous slide"
          >
            Previous
          </button>

          <button
            className={`${styles.controlBtn} ${styles.primary}`}
            onClick={togglePlayPause}
            aria-label={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>

          <button
            className={styles.controlBtn}
            onClick={nextSlide}
            disabled={currentSlideIndex === DEMO_SLIDES.length - 1}
            aria-label="Next slide"
          >
            Next
          </button>

          {/* Progress Bar */}
          <div
            className={styles.progressBarContainer}
            onClick={seek}
            role="slider"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Video progress"
          >
            <div className={styles.progressBar} style={{ width: `${progress}%` }} />
          </div>

          <span className={styles.timeDisplay}>{currentTime} / {totalTime}</span>

          <button
            className={`${styles.controlBtn} ${showSubtitles ? styles.active : ''}`}
            onClick={() => setShowSubtitles(!showSubtitles)}
            aria-label={showSubtitles ? 'Hide subtitles' : 'Show subtitles'}
          >
            CC {showSubtitles ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* Slide Timeline */}
        <div className={styles.slideTimeline} ref={slideTimelineRef} role="list">
          {DEMO_SLIDES.map((slide, index) => (
            <button
              key={slide.id}
              className={`${styles.slideThumbnail} ${index === currentSlideIndex ? styles.active : ''}`}
              onClick={() => loadSlide(index)}
              role="listitem"
              aria-label={`Slide ${slide.id}: ${slide.title}, ${slide.duration} seconds`}
              aria-current={index === currentSlideIndex ? 'true' : undefined}
            >
              <div className={styles.slideNumber}>SLIDE {slide.id}</div>
              <div className={styles.slideTitle}>{slide.title}</div>
              <div className={styles.slideDuration}>{slide.duration}s</div>
            </button>
          ))}
        </div>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className={styles.keyboardHelp}>
        <span>Keyboard: Space = Play/Pause</span>
        <span>Left/Right = Navigate</span>
        <span>C = Toggle Subtitles</span>
      </div>
    </div>
  );
};

export default DemoPlayer;
