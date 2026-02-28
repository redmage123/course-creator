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
// Duration values = max(audio, video) rounded up. Audio: Charlotte voice (ElevenLabs eleven_turbo_v2).
// Duration is used for display only; actual playback uses media ended events.
const DEMO_SLIDES: DemoSlide[] = [
  {
    id: 1,
    title: 'Platform Introduction',
    video: '/demo/videos/slide_01_platform_introduction.mp4',
    audio: '/demo/audio/slide_01_narration.mp3',
    duration: 25, // Audio 24.6s, Video 17.8s
    narration: 'Welcome to Course Creator Platform. This is built for people who create training — corporate teams, professional instructors, anyone who\'s tired of spending weeks building courses from scratch. What if you could do all of that in minutes instead? That\'s exactly what our AI-powered system delivers. Let me show you how it works.'
  },
  {
    id: 2,
    title: 'Organization Registration',
    video: '/demo/videos/slide_02_organization_registration.mp4',
    audio: '/demo/audio/slide_02_narration.mp3',
    duration: 36, // Audio 35.8s, Video 18.6s
    narration: 'Getting started is really straightforward. Head to the home page and click Register Organization. You\'ll see a clean form — just fill in your organization name, website, and a short description of what you do. Add your contact details, business email, address, the basics. Then set up your admin account with a username and password. Hit submit and... that\'s it. Your organization is live and ready to go. Now let me show you what happens next.'
  },
  {
    id: 3,
    title: 'Organization Admin Dashboard',
    video: '/demo/videos/slide_03_organization_admin_dashboard.mp4',
    audio: '/demo/audio/slide_03_narration.mp3',
    duration: 89, // Audio 88.7s, Video 83.1s
    narration: 'Let\'s log in as the organization admin we just created. Go to the home page, click Login, and enter the credentials. For this demo, that\'s sarah at Acme Learning dot e-d-u. Type in the password and sign in. And here we are — the organization admin dashboard. Think of this as your command center. Everything you need to manage your training program lives right here. See that purple button in the bottom right? That\'s our AI assistant. You can manage your entire organization just by talking to it in plain English — but we\'ll get to that in a moment. First, let\'s create a project. Projects are how you organize courses and content. Click Create New Project, give it a name and description, and hit Create. Done. You can always come back to edit or delete it later. Now watch what happens when we switch projects using this dropdown. Select Data Science Foundations and the dashboard updates instantly. You can see your Tracks, those are learning paths. Your Instructors, showing your teaching team. And Students, total enrollment across the board. Below the metrics you\'ve got three tabs: Tracks for managing learning paths, Members for your team, and Settings for configuration. Next up — creating tracks for your project.'
  },
  {
    id: 4,
    title: 'Creating Training Tracks',
    video: '/demo/videos/slide_04_creating_training_tracks.mp4',
    audio: '/demo/audio/slide_04_narration.mp3',
    duration: 44, // Audio 40.1s, Video 43.4s
    narration: 'Now let\'s create a learning track. We\'re already on the Tracks tab from the previous step, so click Create New Track. Here\'s the form. Start with the track name — we\'ll call this one Python Fundamentals. Choose the project, Data Science Foundations. Set the level to Beginner. And add a quick description: Learn Python basics for data science. Click Create Track and there you go. Your track is ready. That\'s all it takes — name it, assign it to a project, set the level, and you\'re done.'
  },
  {
    id: 5,
    title: 'AI Assistant',
    video: '/demo/videos/slide_05_ai_assistant.mp4',
    audio: '/demo/audio/slide_05_narration.mp3',
    duration: 54, // Audio 53.2s, Video 49.4s
    narration: 'Here\'s where it gets interesting. Instead of filling out forms, you can just tell our AI assistant what you need. Click that purple button in the bottom right corner. The chat panel slides open. Now just type what you want in plain English: Create an intermediate track called Machine Learning Basics for the Data Science project. And watch — the AI understands exactly what you mean. It confirms the details and creates the track right there. No forms. No dropdowns. No hunting through menus. Just a natural conversation. This works for creating courses, enrolling students, pulling up reports — pretty much anything you\'d normally do through the interface.'
  },
  {
    id: 6,
    title: 'Adding Instructors',
    video: '/demo/videos/slide_06_adding_instructors.mp4',
    audio: '/demo/audio/slide_06_narration.mp3',
    duration: 46, // Audio 30.3s, Video 45.4s
    narration: 'Your instructors are your greatest asset, so bringing them onboard should be effortless. Add them in seconds, assign them to specific projects or tracks, and they\'re instantly connected to your Slack or Teams channels for real-time collaboration. Whether they\'re co-developing courses with colleagues or running their own independent programs, everything integrates with the tools your team already uses.'
  },
  {
    id: 7,
    title: 'Instructor Dashboard',
    video: '/demo/videos/slide_07_instructor_dashboard.mp4',
    audio: '/demo/audio/slide_07_narration.mp3',
    duration: 51, // Audio 39.5s, Video 50.5s
    narration: 'Here\'s what instructors see when they log in. They\'ve got powerful AI tools right at their fingertips. Tell the system your learning objectives, target audience, and key topics — and watch it generate a complete course structure. Modules, learning outcomes, even quiz questions, all created in seconds. You review it, refine it, make it yours. What used to take days of curriculum design now takes minutes. And when you schedule live sessions, automatic Zoom or Teams integration means one click launches your class.'
  },
  {
    id: 8,
    title: 'Course Content Generation',
    video: '/demo/videos/slide_08_course_content.mp4',
    audio: '/demo/audio/slide_08_narration.mp3',
    duration: 57, // Audio 46.6s, Video 56.6s
    narration: 'This is where AI really shines for content creation. Need a lesson? Just describe your topic and the AI drafts a complete lesson for you. Add your expertise and real-world examples to make it yours. Quizzes? The AI generates questions based on your content — multiple choice, coding challenges, scenario-based problems. You spend your time refining and personalizing, not starting from a blank page. Upload presentations, embed videos, add code exercises with real-time feedback. The AI handles the heavy lifting so you can focus on what matters — the quality of the learning experience.'
  },
  {
    id: 9,
    title: 'Student Enrollment',
    video: '/demo/videos/slide_09_enroll_students.mp4',
    audio: '/demo/audio/slide_09_narration.mp3',
    duration: 60, // Audio 43.7s, Video 59.6s
    narration: 'Your course is ready, so now it\'s time to bring in your students. And enrollment is incredibly flexible. Got one student? Just enter their email and they\'re in. A hundred students? Upload a CSV file and the whole class is enrolled in seconds. No manual data entry at all. You can organize them however makes sense for your program — by section, skill level, semester, department, whatever works. The system adapts to your workflow, not the other way around. Because honestly, managing students should be the easy part, not the time-consuming part.'
  },
  {
    id: 10,
    title: 'Student Dashboard',
    video: '/demo/videos/slide_10_student_dashboard.mp4',
    audio: '/demo/audio/slide_10_narration.mp3',
    duration: 40, // Audio 27.6s, Video 39.4s
    narration: 'Now let\'s see what the experience looks like from a student\'s perspective. They log in and immediately, everything they need is right here. Their courses, their progress, upcoming deadlines, recent achievements. There\'s no confusion and no searching around. Just a clean, clear path forward and the motivation to keep learning.'
  },
  {
    id: 11,
    title: 'Course Browsing & Labs',
    video: '/demo/videos/slide_11_course_browsing.mp4',
    audio: '/demo/audio/slide_11_narration.mp3',
    duration: 49, // Audio 40.2s, Video 48.6s
    narration: 'Students can browse the catalog, find courses they\'re interested in, and enroll with a single click. But here\'s where it gets really exciting for technical training. When they open a coding lesson, a professional development environment launches right in their browser. VS Code for web development. PyCharm for Python. JupyterLab for data science. Full Linux terminal for system administration. No installation. No configuration headaches. No waiting for IT to set things up. Developers learn with real professional tools from day one.'
  },
  {
    id: 12,
    title: 'Quiz & Assessment',
    video: '/demo/videos/slide_12_quiz_assessment.mp4',
    audio: '/demo/audio/slide_12_narration.mp3',
    duration: 48, // Audio 35.0s, Video 47.5s
    narration: 'Assessment shouldn\'t feel like a trap — it should be a genuine learning experience. Our quiz system supports multiple formats. Multiple choice for quick knowledge checks, coding challenges for hands-on skill validation, and short answers for deeper understanding. But what really makes the difference is instant, detailed feedback. Not just a score — actual explanations that help students understand what they got wrong and why. That\'s how mistakes turn into real learning.'
  },
  {
    id: 13,
    title: 'Student Progress',
    video: '/demo/videos/slide_13_student_progress.mp4',
    audio: '/demo/audio/slide_13_narration.mp3',
    duration: 46, // Audio 27.3s, Video 45.5s
    narration: 'Progress should be visible and worth celebrating. Every quiz completed, every module mastered, every milestone reached — students see it all unfold in real time. Completion rates, quiz scores, time invested — it adds up to something meaningful. Proof of growth. And that sense of progress? That\'s what keeps people coming back.'
  },
  {
    id: 14,
    title: 'Instructor Analytics',
    video: '/demo/videos/slide_14_instructor_analytics.mp4',
    audio: '/demo/audio/slide_14_narration.mp3',
    duration: 56, // Audio 45.2s, Video 55.2s
    narration: 'We go well beyond basic LMS reporting. Our AI-powered analytics don\'t just show you numbers — they surface actual insights. Which students are falling behind? The system flags them automatically. What content drives the most engagement? AI spots the patterns across all your courses. Which quiz questions are too easy or too hard? The system analyzes performance trends and recommends adjustments. You can export reports directly to Slack or Teams so your whole training team stays in the loop. This isn\'t just analytics — it\'s intelligent course optimization.'
  },
  {
    id: 15,
    title: 'Learning Analytics Dashboard',
    video: '/demo/videos/slide_15_learning_analytics.mp4',
    audio: '/demo/audio/slide_15_learning_analytics_narration.mp3',
    duration: 60, // Audio 49.5s, Video 59.2s
    narration: 'Students want more than just a progress bar, and this dashboard delivers. The Learning Analytics Dashboard gives them genuinely useful insights into their own learning. Skill mastery shows up as visual radar charts — you can immediately see your strengths and where you need more work. Learning velocity tells you how quickly you\'re absorbing new concepts. Session activity patterns help you figure out when you learn best and optimize your study habits. And for multi-course tracks, you can follow your progress through the entire learning path, not just one course at a time. It\'s not about just finishing courses. It\'s about understanding where you actually stand.'
  },
  {
    id: 16,
    title: 'Instructor Insights Dashboard',
    video: '/demo/videos/slide_16_instructor_insights.mp4',
    audio: '/demo/audio/slide_16_instructor_insights_narration.mp3',
    duration: 66, // Audio 52.8s, Video 65.2s
    narration: 'Now let\'s look at the Instructor Insights Dashboard — this is where AI really earns its keep. At a glance, you can see course performance metrics: completion rates, engagement levels, average scores. Student engagement widgets show you who\'s thriving and who might need some extra support. Content effectiveness charts highlight which lessons are driving the most actual learning. But the best part? AI-powered teaching recommendations. The system looks at patterns across all your courses and tells you specifically what to improve. Maybe a lesson needs more worked examples. Maybe a quiz is discouraging students because it\'s too difficult. The AI identifies these issues and suggests concrete changes. That\'s the kind of insight that used to take weeks of manual analysis.'
  },
  {
    id: 17,
    title: 'Third-Party Integrations',
    video: '/demo/videos/slide_17_integrations.mp4',
    audio: '/demo/audio/slide_17_integrations_narration.mp3',
    duration: 64, // Audio 50.1s, Video 63.9s
    narration: 'Your organization doesn\'t work in isolation, and your learning platform shouldn\'t either. Click the Integrations tab and you can connect everything your team already uses. Slack for instant notifications when students hit milestones. Google Calendar or Outlook for automatic scheduling. OAuth connections for single sign-on with your existing identity provider. Webhooks to trigger your own custom automation workflows. And if you\'re already running another learning management system, LTI integration lets you embed our courses directly into it. The whole point is seamless connectivity — your training platform working with your tools, not competing with them.'
  },
  {
    id: 18,
    title: 'Accessibility Settings',
    video: '/demo/videos/slide_18_accessibility.mp4',
    audio: '/demo/audio/slide_18_accessibility_narration.mp3',
    duration: 62, // Audio 54.3s, Video 61.2s
    narration: 'Accessibility isn\'t something we bolted on at the end — it\'s baked into every part of the platform. Every user can personalize their experience. Font sizes go from default up to extra large. Color schemes include light, dark, and high contrast options. You can reduce motion for anyone sensitive to animations, choose your preferred focus indicator style, and enable screen reader optimizations. Keyboard shortcuts are fully configurable to match how you like to work, and skip links are always there for keyboard navigation. We\'re committed to WCAG 2.1 double-A compliance across the entire platform. Because if your training isn\'t accessible to everyone on your team, it isn\'t really working for your organization.'
  },
  {
    id: 19,
    title: 'Mobile Experience',
    video: '/demo/videos/slide_19_mobile.mp4',
    audio: '/demo/audio/slide_19_mobile_narration.mp3',
    duration: 64, // Audio 50.6s, Video 63.1s
    narration: 'Learning doesn\'t stop when someone leaves their desk, and the platform is built with that in mind. The entire experience is fully responsive — it adapts to phones and tablets seamlessly. Swipe through course cards, pull down to refresh, all the touch gestures you\'d expect. But here\'s the real game changer: offline sync. Your team can download courses and learn on the go, even without an internet connection. Progress syncs automatically the moment they\'re back online. Train your people anywhere, anytime, on any device. That\'s not a nice-to-have — for a lot of organizations, that\'s the feature that makes everything else possible.'
  },
  {
    id: 20,
    title: 'Summary & Next Steps',
    video: '/demo/videos/slide_15_summary.mp4',
    audio: '/demo/audio/slide_20_summary_narration.mp3',
    duration: 56, // Audio 55.2s, Video 39.2s
    narration: 'So that\'s Course Creator Platform. Let me recap what we\'ve covered. AI handles the heavy lifting — course development, content generation, and intelligent analytics that actually help you improve. Deep learning insights for both students and instructors. Seamless integrations with Slack, Teams, Zoom, and your existing systems. Full accessibility support. Mobile-first design with offline learning. Whether you\'re building corporate training programs or teaching independently, this platform turns what used to take weeks of manual work into minutes of guided setup. So, ready to try it yourself? Head to our site, register your organization, and see how it works for your team.'
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
  const shouldContinuePlayingRef = useRef<boolean>(false);  // Track auto-continue across slides
  const videoEndedRef = useRef<boolean>(false);  // Track video ended for sync
  const audioEndedRef = useRef<boolean>(false);  // Track audio ended for sync
  const videoReadyRef = useRef<boolean>(false);  // Track video canplay
  const audioReadyRef = useRef<boolean>(false);  // Track audio canplay
  const pendingPlayRef = useRef<boolean>(false); // Play requested but waiting for media ready

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
   * Sync Engine - Monitors and corrects audio/video drift using playback rate
   *
   * WHY PLAYBACK RATE INSTEAD OF HARD SEEK:
   * Hard-seeking audio (audio.currentTime = x) causes audible stutters/clicks.
   * Instead, we gently speed up or slow down audio playback rate to gradually
   * close the gap. Only hard-seek for very large drift (>500ms).
   */
  const startSyncEngine = useCallback(() => {
    if (syncIntervalRef.current) return;

    syncIntervalRef.current = window.setInterval(() => {
      const video = videoRef.current;
      const audio = audioRef.current;

      if (!video || !audio || video.paused || video.ended) return;
      if (audio.ended) return; // Audio finished, no need to sync

      const driftMs = (video.currentTime - audio.currentTime) * 1000;
      const absDrift = Math.abs(driftMs);

      if (absDrift > 500) {
        // Large drift — hard correct (unavoidable stutter, but rare)
        audio.currentTime = video.currentTime;
        audio.playbackRate = 1.0;
        console.log(`[Sync Engine] Hard corrected drift of ${absDrift.toFixed(0)}ms`);
      } else if (absDrift > DRIFT_THRESHOLD_MS) {
        // Moderate drift — adjust playback rate to gradually close the gap
        // Audio behind video (positive drift) → speed up audio slightly
        // Audio ahead of video (negative drift) → slow down audio slightly
        audio.playbackRate = driftMs > 0 ? 1.03 : 0.97;
      } else {
        // Within threshold — normal speed
        audio.playbackRate = 1.0;
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

    // Stop current playback and reset all tracking
    video.pause();
    audio.pause();
    audio.playbackRate = 1.0;
    stopSyncEngine();
    videoEndedRef.current = false;
    audioEndedRef.current = false;
    videoReadyRef.current = false;
    audioReadyRef.current = false;
    pendingPlayRef.current = false;

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
   * Actually start both media together once both are ready.
   * Called internally when both canplay events have fired.
   */
  const startBothMedia = useCallback(async () => {
    const video = videoRef.current;
    const audio = audioRef.current;

    if (!video || !audio) return;

    try {
      audio.currentTime = video.currentTime;
      audio.playbackRate = 1.0;

      await Promise.all([
        video.play(),
        audio.play()
      ]);

      setIsPlaying(true);
      shouldContinuePlayingRef.current = true;
      startSyncEngine();

      console.log('[DemoPlayer] Playback started with sync engine');
    } catch (err) {
      console.error('[DemoPlayer] Playback failed:', err);
      setError('Failed to start playback. Please try again.');
    }
  }, [startSyncEngine]);

  /**
   * Start playback — waits for both video and audio to be loaded
   *
   * WHY WAIT FOR BOTH:
   * Starting audio before video is buffered causes the narration to play
   * over a black/frozen screen. We set a pending flag and only start
   * once both media fire their canplay events.
   */
  const play = useCallback(async () => {
    const video = videoRef.current;
    const audio = audioRef.current;

    if (!video || !audio) return;

    if (videoReadyRef.current && audioReadyRef.current) {
      // Both ready — start immediately
      await startBothMedia();
    } else {
      // Not ready yet — flag it and wait for canplay events
      pendingPlayRef.current = true;
      console.log('[DemoPlayer] Waiting for media to buffer before playing...');
    }
  }, [startBothMedia]);

  /**
   * Pause playback
   */
  const pause = useCallback(() => {
    const video = videoRef.current;
    const audio = audioRef.current;

    if (video) video.pause();
    if (audio) audio.pause();

    setIsPlaying(false);
    shouldContinuePlayingRef.current = false;  // User explicitly paused
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
   * Advance to next slide once both audio and video have ended.
   *
   * WHY WAIT FOR BOTH:
   * Audio narration can be longer than the video (e.g., slides 2 and 3).
   * Previously, handleVideoEnded would immediately stop the audio mid-sentence.
   * Now we wait for both media to finish so narration is never cut off.
   */
  const advanceToNextSlide = useCallback(() => {
    if (!videoEndedRef.current || !audioEndedRef.current) return;

    // Reset for next slide
    videoEndedRef.current = false;
    audioEndedRef.current = false;

    const shouldContinue = shouldContinuePlayingRef.current;

    if (currentSlideIndex < DEMO_SLIDES.length - 1) {
      setTimeout(() => {
        loadSlide(currentSlideIndex + 1);

        if (shouldContinue) {
          // Don't use a fixed timeout — play() will wait for canplay events
          play();
        }
      }, AUTO_ADVANCE_DELAY_MS);
    } else {
      // Demo complete
      setIsPlaying(false);
      shouldContinuePlayingRef.current = false;
      stopSyncEngine();
      if (onComplete) onComplete();
    }
  }, [currentSlideIndex, loadSlide, play, stopSyncEngine, onComplete]);

  /**
   * Handle video ended - mark video as done, advance if audio also done
   */
  const handleVideoEnded = useCallback(() => {
    videoEndedRef.current = true;
    stopSyncEngine();
    advanceToNextSlide();
  }, [stopSyncEngine, advanceToNextSlide]);

  /**
   * Handle audio ended - mark audio as done, advance if video also done
   */
  const handleAudioEnded = useCallback(() => {
    audioEndedRef.current = true;
    advanceToNextSlide();
  }, [advanceToNextSlide]);

  /**
   * Check if both media are ready and a play is pending
   */
  const tryStartPendingPlay = useCallback(async () => {
    if (pendingPlayRef.current && videoReadyRef.current && audioReadyRef.current) {
      pendingPlayRef.current = false;
      await startBothMedia();
    }
  }, [startBothMedia]);

  /**
   * Handle video can play - track readiness
   */
  const handleCanPlay = useCallback(() => {
    videoReadyRef.current = true;
    setIsLoading(false);

    // Auto-play on first load if enabled
    if (autoPlay && currentSlideIndex === 0 && audioReadyRef.current) {
      pendingPlayRef.current = true;
    }

    tryStartPendingPlay();
  }, [autoPlay, currentSlideIndex, tryStartPendingPlay]);

  /**
   * Handle audio can play - track readiness
   */
  const handleAudioCanPlay = useCallback(() => {
    audioReadyRef.current = true;
    tryStartPendingPlay();
  }, [tryStartPendingPlay]);

  /**
   * Handle video error
   */
  const handleVideoError = useCallback(() => {
    const video = videoRef.current;
    const mediaError = video?.error;
    const errorMsg = mediaError
      ? `Video error (code ${mediaError.code}): ${mediaError.message || 'Unknown'}`
      : 'Failed to load video';
    console.error(`[DemoPlayer] ${errorMsg}`, { src: video?.src, slide: currentSlide?.title });
    setIsLoading(false);
    setError('Failed to load video. Please check your connection and try again.');
  }, [currentSlide]);

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
          preload="auto"
        />

        {/* Hidden Audio Player for Narration */}
        <audio ref={audioRef} preload="auto" onEnded={handleAudioEnded} onCanPlay={handleAudioCanPlay} />
      </div>

      {/* Narration Section - Below video, not overlaid */}
      {showSubtitles && (
        <div className={styles.narrationSection}>
          <div className={styles.narrationBox}>
            <span className={styles.narrationIcon}>CC</span>
            {currentSlide.narration}
          </div>
        </div>
      )}

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
