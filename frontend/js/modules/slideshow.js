/**
 * SLIDESHOW MODULE - INTERACTIVE FEATURE SHOWCASE COMPONENT
 * 
 * PURPOSE: Manages the homepage feature slideshow with auto-play functionality
 * FEATURES:
 * - Auto-play with configurable timing
 * - Manual navigation controls (previous/next buttons)
 * - Slide indicators with direct navigation
 * - Responsive design with smooth transitions
 * - Pause/resume functionality
 * - Touch-friendly interface
 */
class Slideshow {
    /**
     * INITIALIZE CLASS INSTANCE WITH DEFAULT STATE
     * PURPOSE: Initialize class instance with default state
     * WHY: Establishes initial state required for class functionality
     *
     * @param {*} containerSelector - Containerselector parameter
     */
    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector);
        if (!this.container) {
            console.warn('Slideshow container not found:', containerSelector);
            return;
        }
        
        // Core elements
        this.slidesWrapper = this.container.querySelector('.slideshow-wrapper');
        this.slides = this.container.querySelectorAll('.slide');
        
        // State management
        this.currentSlide = 0;
        this.totalSlides = this.slides.length;
        this.isPlaying = true;
        this.autoplayInterval = null;
        this.autoplayDelay = 5000; // 5 seconds per slide
        
        // Touch/swipe support
        this.touchStartX = 0;
        this.touchEndX = 0;
        this.minSwipeDistance = 50;
        
        // Viewport visibility tracking (performance optimization)
        this.isInViewport = true; // Default to true for initial load
        
        this.init();
    }

    /**
     * INITIALIZE SLIDESHOW
     * PURPOSE: Set up event listeners and start auto-play
     */
    init() {
        if (this.totalSlides === 0) {
            console.warn('No slides found in slideshow');
            return;
        }

        console.log(`Slideshow found ${this.totalSlides} slides`);
        console.log('Slideshow wrapper:', this.slidesWrapper);
        
        this.setupEventListeners();
        this.setupIntersectionObserver();
        this.startAutoplay();
        this.updateSlideshow();
        
        console.log(`Slideshow initialized with ${this.totalSlides} slides`);
    }

    /**
     * EVENT LISTENERS SETUP
     * PURPOSE: Attach all interaction handlers
     */
    setupEventListeners() {



        // Touch/swipe support
        if (this.slidesWrapper) {
            this.slidesWrapper.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
            this.slidesWrapper.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
        }

        // Pause on hover
        this.container.addEventListener('mouseenter', () => this.pauseAutoplay());
        this.container.addEventListener('mouseleave', () => this.resumeAutoplay());

        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeydown(e));

        // Visibility change handling (pause when tab is not visible)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoplay();
            } else {
                this.resumeAutoplay();
            }
        });
    }

    /**
     * INTERSECTION OBSERVER SETUP
     * PURPOSE: Track viewport visibility without causing forced reflows
     */
    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) {
            // Fallback for older browsers - assume always visible
            this.isInViewport = true;
            return;
        }

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                this.isInViewport = entry.isIntersecting;
                // Pause/resume based on visibility for better performance
                if (entry.isIntersecting) {
                    this.resumeAutoplay();
                } else {
                    this.pauseAutoplay();
                }
            });
        }, {
            // Trigger when 10% of the slideshow is visible
            threshold: 0.1
        });

        observer.observe(this.container);
    }

    /**
     * NAVIGATION METHODS
     */
    nextSlide() {
        this.currentSlide = (this.currentSlide + 1) % this.totalSlides;
        this.updateSlideshow();
    }

    /**
     * Navigate to previous slide
     *
     * PURPOSE: Moves slideshow to the previous slide with wrapping
     * BUSINESS CONTEXT: Provides backward navigation through feature showcase,
     * allowing users to review previous content. Uses modulo arithmetic to
     * wrap from first slide to last, creating seamless circular navigation.
     */
    prevSlide() {
        this.currentSlide = (this.currentSlide - 1 + this.totalSlides) % this.totalSlides;
        this.updateSlideshow();
    }

    /**
     * Navigate to specific slide by index
     *
     * PURPOSE: Jump directly to any slide in the slideshow
     * BUSINESS CONTEXT: Enables quick access to specific features via slide
     * indicators or programmatic control. Validates index bounds to prevent
     * errors and maintains slideshow integrity.
     *
     * @param {number} index - Zero-based slide index to navigate to
     */
    goToSlide(index) {
        if (index >= 0 && index < this.totalSlides) {
            this.currentSlide = index;
            this.updateSlideshow();
        }
    }

    /**
     * UPDATE SLIDESHOW DISPLAY
     * PURPOSE: Update slide position
     */
    updateSlideshow() {
        // Update slide position with CSS transform
        if (this.slidesWrapper) {
            const translateX = -this.currentSlide * 100;
            this.slidesWrapper.style.transform = `translateX(${translateX}%)`;
        }
    }

    /**
     * AUTOPLAY FUNCTIONALITY
     */
    startAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
        }

        this.autoplayInterval = setInterval(() => {
            this.nextSlide();
        }, this.autoplayDelay);

        this.isPlaying = true;
    }

    /**
     * Pause automatic slideshow progression
     *
     * PURPOSE: Temporarily stops auto-play without losing state
     * BUSINESS CONTEXT: Called when user hovers over slideshow, when tab loses
     * visibility, or when slideshow scrolls out of viewport. Improves UX by
     * preventing unwanted slide changes during interaction and conserves
     * resources when content is not visible.
     */
    pauseAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
        this.isPlaying = false;
    }

    /**
     * Resume automatic slideshow progression
     *
     * PURPOSE: Restart auto-play after pause, maintaining slide position
     * BUSINESS CONTEXT: Called when user stops hovering, when tab becomes
     * visible, or when slideshow scrolls into viewport. Only resumes if
     * slideshow was previously playing to respect user's explicit pause actions.
     */
    resumeAutoplay() {
        if (!this.isPlaying && !this.autoplayInterval) {
            this.startAutoplay();
        }
    }

    /**
     * Toggle autoplay state between playing and paused
     *
     * PURPOSE: Provides user control over automatic slide progression
     * BUSINESS CONTEXT: Bound to spacebar key for accessibility, allowing users
     * to freeze slideshow on interesting content or resume when ready to
     * continue. Essential for users who need more time to read slide content.
     */
    toggleAutoplay() {
        if (this.isPlaying) {
            this.pauseAutoplay();
        } else {
            this.startAutoplay();
        }
    }


    /**
     * TOUCH/SWIPE SUPPORT
     */
    handleTouchStart(e) {
        this.touchStartX = e.changedTouches[0].screenX;
    }

    /**
     * Handle touch end event for swipe gesture detection
     *
     * PURPOSE: Capture end position of touch gesture
     * BUSINESS CONTEXT: Second phase of swipe gesture detection for mobile
     * users. Records final touch position and triggers gesture analysis to
     * determine if user performed a valid swipe for navigation.
     *
     * @param {TouchEvent} e - Touch event containing touch point data
     */
    handleTouchEnd(e) {
        this.touchEndX = e.changedTouches[0].screenX;
        this.handleSwipeGesture();
    }

    /**
     * Process swipe gesture and trigger appropriate navigation
     *
     * PURPOSE: Determine swipe direction and navigate accordingly
     * BUSINESS CONTEXT: Provides intuitive mobile navigation by detecting
     * horizontal swipe gestures. Left swipes advance to next slide, right
     * swipes return to previous slide. Minimum distance threshold (50px)
     * prevents accidental navigation from taps or small movements.
     */
    handleSwipeGesture() {
        const swipeDistance = this.touchStartX - this.touchEndX;

        if (Math.abs(swipeDistance) > this.minSwipeDistance) {
            if (swipeDistance > 0) {
                // Swiped left - go to next slide
                this.nextSlide();
            } else {
                // Swiped right - go to previous slide
                this.prevSlide();
            }
        }
    }

    /**
     * KEYBOARD NAVIGATION
     */
    handleKeydown(e) {
        // Only handle keyboard navigation if slideshow is visible
        // Use Intersection Observer API instead of getBoundingClientRect for better performance
        if (!this.isInViewport) return;

        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.prevSlide();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.nextSlide();
                break;
            case ' ':
                e.preventDefault();
                this.toggleAutoplay();
                break;
            case 'Home':
                e.preventDefault();
                this.goToSlide(0);
                break;
            case 'End':
                e.preventDefault();
                this.goToSlide(this.totalSlides - 1);
                break;
        }
    }

    /**
     * UTILITY METHODS
     */
    getCurrentSlide() {
        return this.currentSlide;
    }

    /**
     * Get total number of slides in slideshow
     *
     * PURPOSE: Provides read-only access to slide count
     * BUSINESS CONTEXT: Used by external components to render slide indicators,
     * validate navigation bounds, or display progress (e.g., "Slide 2 of 5").
     * Encapsulates internal state for better maintainability.
     *
     * @returns {number} Total number of slides
     */
    getTotalSlides() {
        return this.totalSlides;
    }

    /**
     * Check if autoplay is currently active
     *
     * PURPOSE: Query autoplay state without direct property access
     * BUSINESS CONTEXT: Allows UI components to reflect autoplay state (e.g.,
     * play/pause button icons) and external logic to make decisions based on
     * playback status. Provides clean API for state inspection.
     *
     * @returns {boolean} True if autoplay is running, false otherwise
     */
    isAutoplayActive() {
        return this.isPlaying;
    }

    /**
     * Update autoplay timing interval
     *
     * PURPOSE: Dynamically adjust slide duration during runtime
     * BUSINESS CONTEXT: Enables user preferences for slide timing or adaptive
     * behavior based on content type. If autoplay is active, immediately
     * restarts with new timing to ensure consistency.
     *
     * @param {number} delay - New delay in milliseconds between slides
     */
    setAutoplayDelay(delay) {
        this.autoplayDelay = delay;
        if (this.isPlaying) {
            this.startAutoplay(); // Restart with new delay
        }
    }

    /**
     * CLEANUP METHOD
     */
    destroy() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
        }
        
        // Remove event listeners
        document.removeEventListener('keydown', this.handleKeydown);
        document.removeEventListener('visibilitychange', this.visibilityChangeHandler);
        
        console.log('Slideshow destroyed');
    }
}

// Export for module use
export default Slideshow;

// Global export for legacy compatibility
if (typeof window !== 'undefined') {
    window.Slideshow = Slideshow;
}