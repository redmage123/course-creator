/**
 * Homepage Component
 *
 * BUSINESS CONTEXT:
 * Landing page for Course Creator Platform.
 * Showcases platform features and provides clear CTAs for different user types.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Public page (no authentication required)
 * - SEO optimized
 * - Responsive design
 * - Clear navigation to registration and login flows
 * - Interactive feature cards with detailed modal popups
 */

import { useState, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { SEO } from '@components/common/SEO';
import styles from './Homepage.module.css';

/**
 * Feature data structure with brief and detailed descriptions.
 *
 * BUSINESS CONTEXT:
 * Each feature card shows a brief description on hover, but clicking
 * opens a modal with comprehensive details to help potential users
 * understand the full capabilities of each feature.
 */
interface Feature {
  id: string;
  icon: string;
  title: string;
  brief: string;
  detailed: string;
  highlights: string[];
}

const FEATURES: Feature[] = [
  {
    id: 'ai-content',
    icon: 'fas fa-brain',
    title: 'AI Content Generation',
    brief: 'Generate course content, quizzes, and slides instantly with advanced AI. Save hours of content creation time while maintaining quality.',
    detailed: 'Our AI-powered content generation system leverages state-of-the-art language models to help instructors create comprehensive course materials in minutes instead of hours. The system understands educational best practices and generates pedagogically sound content tailored to your subject matter.',
    highlights: [
      'Generate complete course outlines from a simple topic description',
      'Create engaging slide presentations with speaker notes',
      'Auto-generate quiz questions at varying difficulty levels',
      'Produce lab exercises with step-by-step instructions',
      'Support for multiple languages and localization',
      'Content suggestions based on learning objectives'
    ]
  },
  {
    id: 'labs',
    icon: 'fas fa-code',
    title: 'Interactive Lab Environments',
    brief: 'Provide hands-on coding practice with isolated Docker containers. Support for Python, JavaScript, Java, and more with built-in AI assistance.',
    detailed: 'Each student gets their own isolated Docker container environment where they can safely experiment with code without affecting others. The built-in AI assistant helps students debug issues and provides contextual hints based on the current exercise.',
    highlights: [
      'Isolated Docker containers for each student session',
      'Pre-configured environments for Python, JavaScript, Java, Go, and more',
      'Built-in VS Code-style editor with syntax highlighting',
      'Real-time code execution with instant feedback',
      'AI-powered debugging assistant and code suggestions',
      'Automatic environment cleanup and resource management'
    ]
  },
  {
    id: 'analytics',
    icon: 'fas fa-chart-line',
    title: 'Real-time Analytics',
    brief: 'Track student progress, engagement, and performance with comprehensive dashboards. Make data-driven decisions to improve learning outcomes.',
    detailed: 'Our analytics engine provides instructors and administrators with deep insights into student performance and engagement. Real-time dashboards show completion rates, time spent on materials, quiz scores, and identify students who may need additional support.',
    highlights: [
      'Real-time progress tracking across all enrolled students',
      'Engagement metrics including time on task and interaction patterns',
      'Quiz and assessment performance analytics with question-level insights',
      'Early warning system for at-risk students',
      'Exportable reports in CSV, PDF, and Excel formats',
      'Customizable dashboards for different stakeholder views'
    ]
  },
  {
    id: 'multi-tenant',
    icon: 'fas fa-users-cog',
    title: 'Multi-tenant Architecture',
    brief: 'Perfect for organizations with multiple teams. Manage instructors, students, and courses with granular role-based permissions.',
    detailed: 'Our multi-tenant architecture allows organizations to maintain complete separation between departments, teams, or client groups while sharing the same platform infrastructure. Each organization has full control over their users, courses, and settings.',
    highlights: [
      'Complete data isolation between organizations',
      'Hierarchical role system: Site Admin, Org Admin, Instructor, Student',
      'Granular permissions for course access and management',
      'Custom branding options per organization',
      'Centralized billing with per-organization usage tracking',
      'SSO integration support (SAML, OAuth, LDAP)'
    ]
  },
  {
    id: 'assessments',
    icon: 'fas fa-clipboard-check',
    title: 'Comprehensive Assessments',
    brief: 'Create multiple choice, coding challenges, and essay questions. Automated grading and instant feedback for students.',
    detailed: 'Build assessments that truly measure understanding with our versatile question types. From auto-graded multiple choice to AI-assisted essay evaluation and live code execution for programming challenges, our assessment tools cover every learning scenario.',
    highlights: [
      'Multiple choice, true/false, and matching questions',
      'Coding challenges with automated test case validation',
      'Essay questions with AI-assisted grading rubrics',
      'Timed assessments with anti-cheating measures',
      'Question banks for randomized quiz generation',
      'Immediate feedback with detailed explanations'
    ]
  },
  {
    id: 'certificates',
    icon: 'fas fa-certificate',
    title: 'Digital Certificates',
    brief: 'Award verifiable certificates upon course completion. Students can download PDFs and share achievements on social media.',
    detailed: 'Motivate students and validate their achievements with beautiful, verifiable digital certificates. Each certificate includes a unique verification code and QR link that employers can use to confirm authenticity.',
    highlights: [
      'Customizable certificate templates with organization branding',
      'Unique verification codes for each certificate',
      'QR code linking to online verification page',
      'One-click sharing to LinkedIn and other platforms',
      'Downloadable PDF and image formats',
      'Certificate revocation and expiration management'
    ]
  }
];

/**
 * Homepage Component
 *
 * WHY THIS APPROACH:
 * - Hero section grabs attention with value proposition
 * - Feature cards highlight key platform capabilities
 * - Clickable cards open detailed modals for deeper exploration
 * - Multiple CTAs for different user types (individual login vs. org registration)
 * - Professional gradient design matching platform theme
 */
export const Homepage = () => {
  const [selectedFeature, setSelectedFeature] = useState<Feature | null>(null);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);

  const openFeatureModal = useCallback((feature: Feature) => {
    setSelectedFeature(feature);
    setIsMinimized(false);
    setIsMaximized(false);
    document.body.style.overflow = 'hidden'; // Prevent background scroll
  }, []);

  const closeFeatureModal = useCallback(() => {
    setSelectedFeature(null);
    setIsMinimized(false);
    setIsMaximized(false);
    document.body.style.overflow = 'auto'; // Restore scroll
  }, []);

  const toggleMinimize = useCallback(() => {
    setIsMinimized((prev) => !prev);
    if (isMaximized) setIsMaximized(false);
  }, [isMaximized]);

  const toggleMaximize = useCallback(() => {
    setIsMaximized((prev) => !prev);
    if (isMinimized) setIsMinimized(false);
  }, [isMinimized]);

  // Global Escape key handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedFeature) {
        closeFeatureModal();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [selectedFeature, closeFeatureModal]);

  return (
    <>
      <SEO
        title="Course Creator Platform - AI-Powered Learning Management System"
        description="Transform your training programs with AI-powered content generation, multi-IDE lab environments, and real-time analytics. Perfect for corporate training and educational institutions."
        keywords="education, learning management, course creation, online courses, AI-powered, LMS, e-learning, corporate training, course authoring"
      />

      <div className={styles.homepage}>
        {/* Hero Section */}
        <section className={styles.hero}>
          <h1 className={styles.heroTitle}>
            Transform Learning with AI-Powered Course Creation
          </h1>
          <p className={styles.heroSubtitle}>
            Create, deliver, and track comprehensive training programs with advanced AI assistance,
            interactive labs, and real-time analytics.
          </p>

          <div className={styles.ctaButtons}>
            <Link to="/login" className={`${styles.ctaButton} ${styles.ctaButtonPrimary}`}>
              <i className="fas fa-sign-in-alt"></i>
              Sign In
            </Link>
            <Link to="/register" className={`${styles.ctaButton} ${styles.ctaButtonSecondary}`}>
              <i className="fas fa-user-plus"></i>
              Create Account
            </Link>
            <Link to="/demo" className={`${styles.ctaButton} ${styles.ctaButtonDemo}`}>
              <i className="fas fa-play-circle"></i>
              Watch Demo
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section className={styles.featuresSection}>
          <div className={styles.featuresContainer}>
            <h2 className={styles.sectionTitle}>
              Everything You Need for Modern Learning
            </h2>

            <div className={styles.featuresGrid}>
              {FEATURES.map((feature) => (
                <div
                  key={feature.id}
                  className={styles.featureCard}
                  onClick={() => openFeatureModal(feature)}
                  onKeyDown={(e) => e.key === 'Enter' && openFeatureModal(feature)}
                  role="button"
                  tabIndex={0}
                  aria-label={`Learn more about ${feature.title}`}
                >
                  <div className={styles.featureIcon}>
                    <i className={feature.icon}></i>
                  </div>
                  <h3 className={styles.featureTitle}>{feature.title}</h3>
                  <p className={styles.featureDescription}>{feature.brief}</p>
                  <span className={styles.featureLearnMore}>
                    Click to learn more <i className="fas fa-arrow-right"></i>
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Organization Registration CTA */}
        <section className={styles.organizationSection}>
          <h2 className={styles.organizationTitle}>
            Ready to Transform Your Organization's Training?
          </h2>
          <p className={styles.organizationDescription}>
            Register your organization and start creating courses in minutes.
          </p>

          <Link
            to="/organization/register"
            className={`${styles.ctaButton} ${styles.ctaButtonPrimary}`}
          >
            <i className="fas fa-building"></i>
            Register Your Organization
          </Link>
        </section>

        {/* Footer */}
        <footer className={styles.footer}>
          <div className={styles.footerContent}>
            <p className={styles.footerText}>
              Course Creator Platform - Built with React, TypeScript, and FastAPI
            </p>

            <div className={styles.footerLinks}>
              <Link to="/login" className={styles.footerLink}>
                Sign In
              </Link>
              <Link to="/register" className={styles.footerLink}>
                Register
              </Link>
              <Link to="/organization/register" className={styles.footerLink}>
                Organization Registration
              </Link>
            </div>
          </div>
        </footer>
      </div>

      {/* Feature Detail Modal */}
      {selectedFeature && (
        <div
          className={styles.modalOverlay}
          onClick={closeFeatureModal}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div
            className={`${styles.modalContent} ${isMinimized ? styles.modalMinimized : ''} ${isMaximized ? styles.modalMaximized : ''}`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Window Title Bar with Controls */}
            <div className={styles.modalTitleBar}>
              <span className={styles.modalTitleBarText}>{selectedFeature.title}</span>
              <div className={styles.modalWindowControls}>
                <button
                  className={`${styles.modalWindowBtn} ${styles.modalMinimizeBtn}`}
                  onClick={toggleMinimize}
                  aria-label={isMinimized ? "Restore window" : "Minimize window"}
                  title={isMinimized ? "Restore" : "Minimize"}
                >
                  <i className={isMinimized ? "fas fa-window-restore" : "fas fa-window-minimize"}></i>
                </button>
                <button
                  className={`${styles.modalWindowBtn} ${styles.modalMaximizeBtn}`}
                  onClick={toggleMaximize}
                  aria-label={isMaximized ? "Restore window" : "Maximize window"}
                  title={isMaximized ? "Restore" : "Maximize"}
                >
                  <i className={isMaximized ? "fas fa-window-restore" : "fas fa-window-maximize"}></i>
                </button>
                <button
                  className={`${styles.modalWindowBtn} ${styles.modalCloseBtn}`}
                  onClick={closeFeatureModal}
                  aria-label="Close window"
                  title="Close (Esc)"
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
            </div>

            {/* Collapsible content when not minimized */}
            {!isMinimized && (
              <>
                <div className={styles.modalHeader}>
                  <div className={styles.modalIcon}>
                    <i className={selectedFeature.icon}></i>
                  </div>
                  <h2 id="modal-title" className={styles.modalTitle}>
                    {selectedFeature.title}
                  </h2>
                </div>

                <div className={styles.modalBody}>
                  <p className={styles.modalDescription}>
                    {selectedFeature.detailed}
                  </p>

                  <h3 className={styles.modalHighlightsTitle}>Key Features</h3>
                  <ul className={styles.modalHighlights}>
                    {selectedFeature.highlights.map((highlight, index) => (
                      <li key={index} className={styles.modalHighlightItem}>
                        <i className="fas fa-check-circle"></i>
                        <span>{highlight}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className={styles.modalFooter}>
                  <Link
                    to="/demo"
                    className={`${styles.ctaButton} ${styles.ctaButtonDemo}`}
                    onClick={closeFeatureModal}
                  >
                    <i className="fas fa-play-circle"></i>
                    Watch Demo
                  </Link>
                  <Link
                    to="/register"
                    className={`${styles.ctaButton} ${styles.ctaButtonPrimary}`}
                    onClick={closeFeatureModal}
                  >
                    <i className="fas fa-user-plus"></i>
                    Get Started
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
};
