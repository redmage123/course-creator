import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, u as useNavigate } from "./react-vendor-cEae-lCc.js";
const demoContainer = "_demoContainer_1q2x9_13";
const demoHeader = "_demoHeader_1q2x9_25";
const demoTitle = "_demoTitle_1q2x9_34";
const demoSubtitle = "_demoSubtitle_1q2x9_40";
const progressIndicator = "_progressIndicator_1q2x9_46";
const videoSection = "_videoSection_1q2x9_55";
const videoPlayer = "_videoPlayer_1q2x9_62";
const loadingState = "_loadingState_1q2x9_79";
const spinner = "_spinner_1q2x9_94";
const errorState = "_errorState_1q2x9_110";
const errorIcon = "_errorIcon_1q2x9_127";
const retryButton = "_retryButton_1q2x9_139";
const narrationSection = "_narrationSection_1q2x9_156";
const narrationBox = "_narrationBox_1q2x9_165";
const narrationIcon = "_narrationIcon_1q2x9_184";
const controlsSection = "_controlsSection_1q2x9_201";
const controlsRow = "_controlsRow_1q2x9_207";
const controlBtn = "_controlBtn_1q2x9_216";
const primary$1 = "_primary_1q2x9_243";
const active = "_active_1q2x9_256";
const progressBarContainer = "_progressBarContainer_1q2x9_263";
const progressBar = "_progressBar_1q2x9_263";
const timeDisplay = "_timeDisplay_1q2x9_280";
const slideTimeline = "_slideTimeline_1q2x9_289";
const slideThumbnail = "_slideThumbnail_1q2x9_311";
const slideNumber = "_slideNumber_1q2x9_334";
const slideTitle = "_slideTitle_1q2x9_343";
const slideDuration = "_slideDuration_1q2x9_354";
const keyboardHelp = "_keyboardHelp_1q2x9_361";
const styles$1 = {
  demoContainer,
  demoHeader,
  demoTitle,
  demoSubtitle,
  progressIndicator,
  videoSection,
  videoPlayer,
  loadingState,
  spinner,
  errorState,
  errorIcon,
  retryButton,
  narrationSection,
  narrationBox,
  narrationIcon,
  controlsSection,
  controlsRow,
  controlBtn,
  primary: primary$1,
  active,
  progressBarContainer,
  progressBar,
  timeDisplay,
  slideTimeline,
  slideThumbnail,
  slideNumber,
  slideTitle,
  slideDuration,
  keyboardHelp
};
const DEMO_SLIDES = [
  {
    id: 1,
    title: "Platform Introduction",
    video: "/demo/videos/slide_01_platform_introduction.mp4",
    audio: "/demo/audio/slide_01_narration.mp3",
    duration: 16,
    // Actual: 15.8s
    narration: "Welcome to the Course Creator Platform. Built specifically for corporate training teams and professional instructors who need to create courses fast. Our AI-powered system transforms what used to take weeks into just minutes. In the next slide, we'll show you how to get started."
  },
  {
    id: 2,
    title: "Organization Registration",
    video: "/demo/videos/slide_02_organization_registration.mp4",
    audio: "/demo/audio/slide_02_narration.mp3",
    duration: 26,
    // Actual: 25.9s
    narration: "To get started, simply click Register Organization on the home page. Now, let's fill in the details. Enter your organization name, website, and a brief description. Add your contact information, including business email and address. Finally, set up your administrator account with credentials. Click submit, and there you go! Your organization is successfully registered. Next, we'll show you how to create projects."
  },
  {
    id: 3,
    title: "Organization Admin Dashboard",
    video: "/demo/videos/slide_03_organization_admin_dashboard.mp4",
    audio: "/demo/audio/slide_03_narration.mp3",
    duration: 81,
    // Actual: 81.2s
    narration: "Let's log in as the organization admin we just created. First, navigate to the home page and click the Login button in the header. Now, enter the email address: sarah at acmelearning dot e-d-u. Then enter the password. Click the login button to sign in. Notice the user icon in the header changes to show you're logged in. You're now redirected to your organization admin dashboard! From here, you can manage everything. Notice the purple AI assistant button in the bottom right corner. You can use it to manage your organization through natural language instead of filling out forms."
  },
  {
    id: 4,
    title: "Creating Training Tracks",
    video: "/demo/videos/slide_04_creating_training_tracks.mp4",
    audio: "/demo/audio/slide_04_narration.mp3",
    duration: 41,
    // Actual: 41.4s
    narration: "Now let's create a learning track! We're already viewing the Tracks tab from the previous slide. Click the Create New Track button. This opens the track creation form. First, enter the track name: Python Fundamentals. Next, select the project. Choose Data Science Foundations from the dropdown. Then select the level. We'll make this a Beginner track. Now add a description: Learn Python basics for data science. Click Create Track, and there you go! Your track is created."
  },
  {
    id: 5,
    title: "AI Assistant",
    video: "/demo/videos/slide_05_ai_assistant.mp4",
    audio: "/demo/audio/slide_05_narration.mp3",
    duration: 47,
    // Actual: 47.2s
    narration: "Instead of filling out forms, you can simply tell our AI assistant what you need. Watch how easy it is! Click the purple AI assistant button in the bottom right corner. The chat panel slides up. Now, just describe what you want in plain English. Type: Create an intermediate track called Machine Learning Basics for the Data Science project. The AI understands your request instantly! It confirms the details and creates the track for you. No forms to fill out. No dropdowns to navigate. Just natural conversation."
  },
  {
    id: 6,
    title: "Adding Instructors",
    video: "/demo/videos/slide_06_adding_instructors.mp4",
    audio: "/demo/audio/slide_06_narration.mp3",
    duration: 19,
    // Actual: 18.8s
    narration: "Your instructors are your greatest asset. Bring them onboard in seconds, assign them to specific projects or tracks, and they're instantly connected to your Slack or Teams channels for seamless collaboration. Whether it's co-developing courses with colleagues or running independent programs, everything integrates with the tools your team already uses."
  },
  {
    id: 7,
    title: "Instructor Dashboard",
    video: "/demo/videos/slide_07_instructor_dashboard.mp4",
    audio: "/demo/audio/slide_07_narration.mp3",
    duration: 32,
    // Actual: 31.5s
    narration: "Instructors have powerful AI tools at their fingertips! Tell the system your learning objectives, your target audience, and your key topics. Then watch as artificial intelligence generates a complete course structure, suggested modules, learning outcomes, even quiz questions! You review, refine, and approve. What used to take days of curriculum design now takes minutes. And when you schedule live sessions? Automatic Zoom or Teams integration means one click launches your class!"
  },
  {
    id: 8,
    title: "Course Content Generation",
    video: "/demo/videos/slide_08_course_content.mp4",
    audio: "/demo/audio/slide_08_narration.mp3",
    duration: 36,
    // Actual: 35.8s
    narration: "AI accelerates content creation! Need lesson content? Describe your topic and the AI generates a complete lesson draft. You just add your expertise and real-world examples. Creating quizzes? AI suggests questions based on your content: multiple choice, code challenges, scenario-based problems. You spend your time refining and personalizing, not starting from scratch. Upload presentations, embed videos, add code exercises with real-time feedback. The AI accelerates creation. You ensure quality."
  },
  {
    id: 9,
    title: "Student Enrollment",
    video: "/demo/videos/slide_09_enroll_students.mp4",
    audio: "/demo/audio/slide_09_narration.mp3",
    duration: 22,
    // Actual: 22.2s
    narration: "Your course is ready! Now it's time to welcome your students. One student? Easy. One hundred students? Even easier! Upload a CSV file and enroll an entire class in seconds. Organize by section, group by skill level, track by semester. However you teach, we adapt. Because managing students should be effortless, not exhausting."
  },
  {
    id: 10,
    title: "Student Dashboard",
    video: "/demo/videos/slide_10_student_dashboard.mp4",
    audio: "/demo/audio/slide_10_narration.mp3",
    duration: 18,
    // Actual: 17.8s
    narration: "Now let's see what your students experience. They log in and immediately, everything they need is right there. Their courses, their progress, upcoming deadlines, recent achievements. No confusion. No hunting for information. Just a clear path forward and the motivation to keep going."
  },
  {
    id: 11,
    title: "Course Browsing & Labs",
    video: "/demo/videos/slide_11_course_browsing.mp4",
    audio: "/demo/audio/slide_11_narration.mp3",
    duration: 35,
    // Actual: 34.5s
    narration: "Students browse the catalog, discover courses, and enroll with one click. The game changer for technical training? When they hit a coding lesson, professional development environments open right in their browser! VS Code for web development. PyCharm for Python. JupyterLab for data science. Full Linux terminal for system administration. No installation. No configuration. No IT headaches! This is why corporate training teams choose us! Their developers learn with real professional tools, no setup time wasted."
  },
  {
    id: 12,
    title: "Quiz & Assessment",
    video: "/demo/videos/slide_12_quiz_assessment.mp4",
    audio: "/demo/audio/slide_12_narration.mp3",
    duration: 28,
    // Actual: 27.5s
    narration: "Assessment shouldn't feel like a gotcha moment. It should be a learning opportunity! Our quiz system delivers multiple question formats: multiple choice for quick checks, coding challenges for hands-on validation, short answer for deeper understanding. But here's what matters most: instant feedback! Not just a score, but detailed explanations that turn mistakes into mastery. Because real learning happens when students understand why."
  },
  {
    id: 13,
    title: "Student Progress",
    video: "/demo/videos/slide_13_student_progress.mp4",
    audio: "/demo/audio/slide_13_narration.mp3",
    duration: 20,
    // Actual: 20.3s
    narration: "Progress should be visible and celebrated! Every quiz completed. Every module mastered. Every achievement unlocked. Students see their journey unfold in real time. Completion rates, quiz scores, time invested. It all adds up to something powerful: proof of growth! And that's what keeps them coming back."
  },
  {
    id: 14,
    title: "Instructor Analytics",
    video: "/demo/videos/slide_14_instructor_analytics.mp4",
    audio: "/demo/audio/slide_14_narration.mp3",
    duration: 34,
    // Actual: 34.2s
    narration: "We go beyond basic LMS reporting! Our AI-powered analytics don't just show you data. They surface insights! Which students are at risk of falling behind? AI flags them automatically. What content drives the most engagement? AI identifies patterns across all your courses. Which quiz questions are too easy or too hard? AI analyzes performance trends and suggests adjustments. Export reports to Slack or Teams so your entire training team stays informed. This isn't just analytics. It's intelligent course optimization!"
  },
  {
    id: 15,
    title: "Learning Analytics Dashboard",
    video: "/demo/videos/slide_15_learning_analytics.mp4",
    audio: "/demo/audio/slide_15_learning_analytics_narration.mp3",
    duration: 32,
    // Estimated
    narration: "But students want more than just progress bars! Our Learning Analytics Dashboard gives them deep insights. See skill mastery across different topics with visual radar charts. Track learning velocity to understand how quickly concepts are being absorbed. View session activity patterns to optimize study habits. Monitor learning path progress through multi-course tracks. Students can identify their strengths and areas for improvement. It's not just about completing courses. It's about truly understanding your learning journey!"
  },
  {
    id: 16,
    title: "Instructor Insights Dashboard",
    video: "/demo/videos/slide_16_instructor_insights.mp4",
    audio: "/demo/audio/slide_16_instructor_insights_narration.mp3",
    duration: 35,
    // Estimated
    narration: "Now let's see the Instructor Insights Dashboard! This is where AI truly shines. Course performance metrics show completion rates, engagement levels, and average scores at a glance. Student engagement widgets reveal who's thriving and who needs support. Content effectiveness charts identify which lessons drive the most learning. And the best part? AI-powered teaching recommendations! The system analyzes patterns across all your courses and suggests specific improvements. Maybe a lesson needs more examples. Maybe a quiz is too difficult. The AI tells you exactly what to optimize!"
  },
  {
    id: 17,
    title: "Third-Party Integrations",
    video: "/demo/videos/slide_17_integrations.mp4",
    audio: "/demo/audio/slide_17_integrations_narration.mp3",
    duration: 38,
    // Estimated
    narration: "Your organization doesn't exist in isolation! Let's set up integrations. Click the Integrations tab. Here you can connect Slack for instant notifications when students complete courses. Link your Google Calendar or Outlook for automatic scheduling. Set up OAuth connections for single sign-on with your existing identity provider. Configure webhooks to trigger your own automation workflows. LTI integration lets you embed our courses directly in your existing LMS. Everything works together seamlessly!"
  },
  {
    id: 18,
    title: "Accessibility Settings",
    video: "/demo/videos/slide_18_accessibility.mp4",
    audio: "/demo/audio/slide_18_accessibility_narration.mp3",
    duration: 30,
    // Estimated
    narration: "Accessibility isn't an afterthought. It's built into everything we do! Every user can customize their experience. Adjust font sizes from default to extra large. Switch between light, dark, or high contrast color schemes. Reduce motion for users sensitive to animations. Choose your preferred focus indicator style. Enable screen reader optimizations. Configure keyboard shortcuts to match your workflow. Skip links are always available for keyboard navigation. We're committed to WCAG 2.1 double-A compliance because learning should be accessible to everyone!"
  },
  {
    id: 19,
    title: "Mobile Experience",
    video: "/demo/videos/slide_19_mobile.mp4",
    audio: "/demo/audio/slide_19_mobile_narration.mp3",
    duration: 28,
    // Estimated
    narration: "Learning doesn't stop when you leave your desk! Our mobile experience brings the full platform to any device. Responsive design adapts beautifully to phones and tablets. Swipe through course cards with touch gestures. Pull down to refresh for the latest content. And the game changer? Offline sync! Download courses to learn on the go, even without internet. Your progress syncs automatically when you're back online. Train your team anywhere, anytime. That's the power of mobile-first design!"
  },
  {
    id: 20,
    title: "Summary & Next Steps",
    video: "/demo/videos/slide_15_summary.mp4",
    audio: "/demo/audio/slide_15_narration.mp3",
    duration: 26,
    // Actual: 26.3s
    narration: "So that's Course Creator Platform! AI handles course development, content generation, and intelligent analytics. Deep learning insights for both students and instructors. Third-party integrations with Slack, Teams, Zoom, and your existing systems. Full accessibility support and mobile-first design. Your team works inside the tools they already use, and everything integrates seamlessly. Whether you're building corporate training programs or teaching as an independent instructor, we turn weeks of work into minutes of guided setup. Ready to see it in action? Visit our site to get started!"
  }
];
const SYNC_CHECK_INTERVAL_MS = 250;
const DRIFT_THRESHOLD_MS = 100;
const AUTO_ADVANCE_DELAY_MS = 1e3;
const DemoPlayer = ({
  autoPlay = false,
  showSubtitles: initialShowSubtitles = true,
  onComplete
}) => {
  const [currentSlideIndex, setCurrentSlideIndex] = reactExports.useState(0);
  const [isPlaying, setIsPlaying] = reactExports.useState(false);
  const [progress, setProgress] = reactExports.useState(0);
  const [currentTime, setCurrentTime] = reactExports.useState("0:00");
  const [totalTime, setTotalTime] = reactExports.useState("0:00");
  const [showSubtitles, setShowSubtitles] = reactExports.useState(initialShowSubtitles);
  const [isLoading, setIsLoading] = reactExports.useState(true);
  const [error, setError] = reactExports.useState(null);
  const videoRef = reactExports.useRef(null);
  const audioRef = reactExports.useRef(null);
  const syncIntervalRef = reactExports.useRef(null);
  const slideTimelineRef = reactExports.useRef(null);
  const shouldContinuePlayingRef = reactExports.useRef(false);
  const currentSlide = DEMO_SLIDES[currentSlideIndex];
  const formatTime = (seconds) => {
    if (isNaN(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };
  const startSyncEngine = reactExports.useCallback(() => {
    if (syncIntervalRef.current) return;
    syncIntervalRef.current = window.setInterval(() => {
      const video = videoRef.current;
      const audio = audioRef.current;
      if (!video || !audio || video.paused) return;
      const driftMs = Math.abs(video.currentTime - audio.currentTime) * 1e3;
      if (driftMs > DRIFT_THRESHOLD_MS) {
        audio.currentTime = video.currentTime;
        console.log(`[Sync Engine] Corrected drift of ${driftMs.toFixed(0)}ms`);
      }
    }, SYNC_CHECK_INTERVAL_MS);
  }, []);
  const stopSyncEngine = reactExports.useCallback(() => {
    if (syncIntervalRef.current) {
      clearInterval(syncIntervalRef.current);
      syncIntervalRef.current = null;
    }
  }, []);
  const loadSlide = reactExports.useCallback((index) => {
    if (index < 0 || index >= DEMO_SLIDES.length) return;
    const slide = DEMO_SLIDES[index];
    const video = videoRef.current;
    const audio = audioRef.current;
    if (!video || !audio) return;
    console.log(`[DemoPlayer] Loading slide ${slide.id}: ${slide.title}`);
    video.pause();
    audio.pause();
    stopSyncEngine();
    video.src = slide.video;
    audio.src = slide.audio;
    audio.volume = 0.8;
    video.load();
    audio.load();
    setCurrentSlideIndex(index);
    setProgress(0);
    setIsLoading(true);
    setError(null);
    if (slideTimelineRef.current) {
      const thumbnails = slideTimelineRef.current.children;
      if (thumbnails[index]) {
        thumbnails[index].scrollIntoView({
          behavior: "smooth",
          block: "nearest",
          inline: "center"
        });
      }
    }
  }, [stopSyncEngine]);
  const play = reactExports.useCallback(async () => {
    const video = videoRef.current;
    const audio = audioRef.current;
    if (!video || !audio) return;
    try {
      audio.currentTime = video.currentTime;
      await Promise.all([
        video.play(),
        audio.play()
      ]);
      setIsPlaying(true);
      shouldContinuePlayingRef.current = true;
      startSyncEngine();
      console.log("[DemoPlayer] Playback started with sync engine");
    } catch (err) {
      console.error("[DemoPlayer] Playback failed:", err);
      setError("Failed to start playback. Please try again.");
    }
  }, [startSyncEngine]);
  const pause = reactExports.useCallback(() => {
    const video = videoRef.current;
    const audio = audioRef.current;
    if (video) video.pause();
    if (audio) audio.pause();
    setIsPlaying(false);
    shouldContinuePlayingRef.current = false;
    stopSyncEngine();
    console.log("[DemoPlayer] Playback paused");
  }, [stopSyncEngine]);
  const togglePlayPause = reactExports.useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);
  const previousSlide = reactExports.useCallback(() => {
    if (currentSlideIndex > 0) {
      loadSlide(currentSlideIndex - 1);
    }
  }, [currentSlideIndex, loadSlide]);
  const nextSlide = reactExports.useCallback(() => {
    if (currentSlideIndex < DEMO_SLIDES.length - 1) {
      loadSlide(currentSlideIndex + 1);
    } else if (onComplete) {
      onComplete();
    }
  }, [currentSlideIndex, loadSlide, onComplete]);
  const seek = reactExports.useCallback((e) => {
    const video = videoRef.current;
    const audio = audioRef.current;
    if (!video || !audio) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    const newTime = pos * video.duration;
    video.currentTime = newTime;
    audio.currentTime = newTime;
    console.log(`[DemoPlayer] Seeked to ${formatTime(newTime)}`);
  }, []);
  const handleTimeUpdate = reactExports.useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    const progressPercent = video.currentTime / video.duration * 100;
    setProgress(progressPercent);
    setCurrentTime(formatTime(video.currentTime));
    setTotalTime(formatTime(video.duration));
  }, []);
  const handleVideoEnded = reactExports.useCallback(() => {
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    const shouldContinue = shouldContinuePlayingRef.current;
    if (currentSlideIndex < DEMO_SLIDES.length - 1) {
      setTimeout(() => {
        loadSlide(currentSlideIndex + 1);
        if (shouldContinue) {
          setTimeout(() => {
            play();
          }, 600);
        }
      }, AUTO_ADVANCE_DELAY_MS);
    } else {
      setIsPlaying(false);
      shouldContinuePlayingRef.current = false;
      stopSyncEngine();
      if (onComplete) onComplete();
    }
  }, [currentSlideIndex, loadSlide, play, stopSyncEngine, onComplete]);
  const handleCanPlay = reactExports.useCallback(() => {
    setIsLoading(false);
    if (autoPlay && currentSlideIndex === 0) {
      play();
    }
  }, [autoPlay, currentSlideIndex, play]);
  const handleVideoError = reactExports.useCallback(() => {
    const video = videoRef.current;
    const mediaError = video?.error;
    const errorMsg = mediaError ? `Video error (code ${mediaError.code}): ${mediaError.message || "Unknown"}` : "Failed to load video";
    console.error(`[DemoPlayer] ${errorMsg}`, { src: video?.src, slide: currentSlide?.title });
    setIsLoading(false);
    setError("Failed to load video. Please check your connection and try again.");
  }, [currentSlide]);
  reactExports.useEffect(() => {
    const handleKeyDown = (e) => {
      switch (e.key) {
        case " ":
          e.preventDefault();
          togglePlayPause();
          break;
        case "ArrowLeft":
          previousSlide();
          break;
        case "ArrowRight":
          nextSlide();
          break;
        case "c":
          setShowSubtitles((prev) => !prev);
          break;
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [togglePlayPause, previousSlide, nextSlide]);
  reactExports.useEffect(() => {
    loadSlide(0);
  }, [loadSlide]);
  reactExports.useEffect(() => {
    return () => {
      stopSyncEngine();
    };
  }, [stopSyncEngine]);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.demoContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { className: styles$1.demoHeader, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles$1.demoTitle, children: "Course Creator Platform Demo" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.demoSubtitle, children: "See the platform in action" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.progressIndicator, children: [
        "Slide ",
        currentSlide.id,
        " of ",
        DEMO_SLIDES.length
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.videoSection, children: [
      isLoading && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.loadingState, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.spinner }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading slide..." })
      ] }),
      error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.errorState, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.errorIcon, children: "!" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: () => loadSlide(currentSlideIndex), className: styles$1.retryButton, children: "Try Again" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "video",
        {
          ref: videoRef,
          className: styles$1.videoPlayer,
          onTimeUpdate: handleTimeUpdate,
          onEnded: handleVideoEnded,
          onCanPlay: handleCanPlay,
          onError: handleVideoError,
          playsInline: true,
          preload: "auto"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx("audio", { ref: audioRef, preload: "auto" })
    ] }),
    showSubtitles && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.narrationSection, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.narrationBox, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.narrationIcon, children: "CC" }),
      currentSlide.narration
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.controlsSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.controlsRow, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles$1.controlBtn}`,
            onClick: previousSlide,
            disabled: currentSlideIndex === 0,
            "aria-label": "Previous slide",
            children: "Previous"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles$1.controlBtn} ${styles$1.primary}`,
            onClick: togglePlayPause,
            "aria-label": isPlaying ? "Pause" : "Play",
            children: isPlaying ? "Pause" : "Play"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$1.controlBtn,
            onClick: nextSlide,
            disabled: currentSlideIndex === DEMO_SLIDES.length - 1,
            "aria-label": "Next slide",
            children: "Next"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "div",
          {
            className: styles$1.progressBarContainer,
            onClick: seek,
            role: "slider",
            "aria-valuenow": progress,
            "aria-valuemin": 0,
            "aria-valuemax": 100,
            "aria-label": "Video progress",
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.progressBar, style: { width: `${progress}%` } })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.timeDisplay, children: [
          currentTime,
          " / ",
          totalTime
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            className: `${styles$1.controlBtn} ${showSubtitles ? styles$1.active : ""}`,
            onClick: () => setShowSubtitles(!showSubtitles),
            "aria-label": showSubtitles ? "Hide subtitles" : "Show subtitles",
            children: [
              "CC ",
              showSubtitles ? "ON" : "OFF"
            ]
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.slideTimeline, ref: slideTimelineRef, role: "list", children: DEMO_SLIDES.map((slide, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          className: `${styles$1.slideThumbnail} ${index === currentSlideIndex ? styles$1.active : ""}`,
          onClick: () => loadSlide(index),
          role: "listitem",
          "aria-label": `Slide ${slide.id}: ${slide.title}, ${slide.duration} seconds`,
          "aria-current": index === currentSlideIndex ? "true" : void 0,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.slideNumber, children: [
              "SLIDE ",
              slide.id
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.slideTitle, children: slide.title }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.slideDuration, children: [
              slide.duration,
              "s"
            ] })
          ]
        },
        slide.id
      )) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.keyboardHelp, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Keyboard: Space = Play/Pause" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Left/Right = Navigate" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "C = Toggle Subtitles" })
    ] })
  ] });
};
const demoPageContainer = "_demoPageContainer_xfbod_8";
const demoWrapper = "_demoWrapper_xfbod_18";
const ctaSection = "_ctaSection_xfbod_24";
const ctaTitle = "_ctaTitle_xfbod_43";
const ctaDescription = "_ctaDescription_xfbod_50";
const ctaButtons = "_ctaButtons_xfbod_58";
const ctaButton = "_ctaButton_xfbod_58";
const primary = "_primary_xfbod_81";
const backLink = "_backLink_xfbod_92";
const link = "_link_xfbod_96";
const styles = {
  demoPageContainer,
  demoWrapper,
  ctaSection,
  ctaTitle,
  ctaDescription,
  ctaButtons,
  ctaButton,
  primary,
  backLink,
  link
};
const DemoPage = () => {
  const navigate = useNavigate();
  const [demoCompleted, setDemoCompleted] = reactExports.useState(false);
  const handleDemoComplete = reactExports.useCallback(() => {
    setDemoCompleted(true);
  }, []);
  const handleGetStarted = reactExports.useCallback(() => {
    navigate("/register");
  }, [navigate]);
  const handleContactSales = reactExports.useCallback(() => {
    window.location.href = "mailto:sales@coursecreator.com?subject=Demo%20Follow-up";
  }, []);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.demoPageContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.demoWrapper, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        DemoPlayer,
        {
          autoPlay: false,
          showSubtitles: true,
          onComplete: handleDemoComplete
        }
      ),
      demoCompleted && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.ctaSection, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles.ctaTitle, children: "Ready to Transform Your Training?" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.ctaDescription, children: "Join thousands of organizations using Course Creator Platform to build engaging, AI-powered learning experiences." }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.ctaButtons, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              className: `${styles.ctaButton} ${styles.primary}`,
              onClick: handleGetStarted,
              children: "Get Started Free"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              className: styles.ctaButton,
              onClick: handleContactSales,
              children: "Contact Sales"
            }
          )
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.backLink, children: /* @__PURE__ */ jsxRuntimeExports.jsx("a", { href: "/", className: styles.link, children: "Back to Home" }) })
  ] });
};
export {
  DemoPage,
  DemoPage as default
};
//# sourceMappingURL=DemoPage-CsZusMWb.js.map
