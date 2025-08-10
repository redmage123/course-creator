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
     * NAVIGATION METHODS
     */
    nextSlide() {
        this.currentSlide = (this.currentSlide + 1) % this.totalSlides;
        this.updateSlideshow();
    }

    prevSlide() {
        this.currentSlide = (this.currentSlide - 1 + this.totalSlides) % this.totalSlides;
        this.updateSlideshow();
    }

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

    pauseAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
        this.isPlaying = false;
    }

    resumeAutoplay() {
        if (!this.isPlaying && !this.autoplayInterval) {
            this.startAutoplay();
        }
    }

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

    handleTouchEnd(e) {
        this.touchEndX = e.changedTouches[0].screenX;
        this.handleSwipeGesture();
    }

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
        const rect = this.container.getBoundingClientRect();
        const isVisible = rect.top < window.innerHeight && rect.bottom > 0;
        
        if (!isVisible) return;

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

    getTotalSlides() {
        return this.totalSlides;
    }

    isAutoplayActive() {
        return this.isPlaying;
    }

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