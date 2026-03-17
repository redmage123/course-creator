/**
 * AI Assistant Welcome Popup Component
 *
 * BUSINESS CONTEXT:
 * Provides a warm welcome experience for first-time users.
 * The AI assistant introduces itself and offers a guided tour
 * of the platform based on the user's role.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Triggered on first login (is_first_login from auth response)
 * - Role-specific welcome messages and tour highlights
 * - Integrates with the onboarding API endpoints
 * - Persists "tour completed" status in localStorage
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../../../components/atoms/Button';
import { useAuth } from '../../../../hooks/useAuth';
import { apiClient } from '../../../../services/apiClient';
import styles from './WelcomePopup.module.css';

interface WelcomeData {
  welcome_message: string;
  tour_highlights: string[];
  first_actions: string[];
  show_tour: boolean;
  role: string;
}

interface TourStep {
  title: string;
  description: string;
  target?: string;  // CSS selector for highlighting
}

interface WelcomePopupProps {
  isFirstLogin?: boolean;
  onClose?: () => void;
  onStartTour?: () => void;
}

/**
 * Welcome Popup Component
 *
 * WHY THIS APPROACH:
 * - Modal popup for immediate visibility on first login
 * - AI assistant personality for consistent UX
 * - Tour option for deeper onboarding
 * - Quick actions for immediate engagement
 */
export const WelcomePopup: React.FC<WelcomePopupProps> = ({
  isFirstLogin = false,
  onClose,
  onStartTour
}) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isVisible, setIsVisible] = useState(false);
  const [welcomeData, setWelcomeData] = useState<WelcomeData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showTour, setShowTour] = useState(false);
  const [currentTourStep, setCurrentTourStep] = useState(0);
  const [tourSteps, setTourSteps] = useState<TourStep[]>([]);

  // Check if we should show the popup
  useEffect(() => {
    const hasSeenWelcome = localStorage.getItem('ai_welcome_seen');

    if (isFirstLogin && !hasSeenWelcome) {
      setIsVisible(true);
      fetchWelcomeMessage();
    } else if (!hasSeenWelcome && user) {
      // Show on subsequent logins if user hasn't seen it
      const lastWelcomeTime = localStorage.getItem('ai_welcome_last_shown');
      if (!lastWelcomeTime) {
        setIsVisible(true);
        fetchWelcomeMessage();
      }
    }
  }, [isFirstLogin, user]);

  // Fetch welcome message from API
  const fetchWelcomeMessage = async () => {
    if (!user) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);

      const response = await apiClient.post<WelcomeData>('/api/ai/welcome', {
        user_id: user.id,
        username: user.username || user.full_name || 'there',
        role: user.role,
        organization_id: user.organization_id,
        organization_name: user.organization,
        is_first_login: isFirstLogin,
        current_page: window.location.pathname
      });

      setWelcomeData(response.data);

      // Generate tour steps based on role
      generateTourSteps(response.data.role, response.data.tour_highlights);

    } catch (error) {
      console.error('Failed to fetch welcome message:', error);
      // Use fallback welcome message
      setWelcomeData({
        welcome_message: `Welcome to Course Creator Platform, ${user.username || 'there'}! I'm your AI assistant, here to help you succeed. What would you like to do first?`,
        tour_highlights: ['Your dashboard', 'Course catalog', 'AI assistance'],
        first_actions: ['Explore your dashboard', 'Browse courses'],
        show_tour: isFirstLogin,
        role: user.role || 'guest'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Generate tour steps based on role
  const generateTourSteps = (role: string, highlights: string[]) => {
    const roleTourSteps: Record<string, TourStep[]> = {
      student: [
        { title: 'Your Dashboard', description: 'This is your home base - see your enrolled courses, progress, and upcoming deadlines.', target: '.dashboard-main' },
        { title: 'Course Catalog', description: 'Browse and enroll in courses that interest you. Filter by topic, difficulty, or duration.', target: '.course-catalog' },
        { title: 'Interactive Labs', description: 'Practice what you learn in real coding environments - no setup required!', target: '.labs-section' },
        { title: 'AI Assistant', description: "That's me! I'm always here in the bottom-right corner to help you learn and answer questions.", target: '.ai-assistant-button' }
      ],
      instructor: [
        { title: 'Instructor Dashboard', description: 'Manage your courses, view student activity, and access analytics.', target: '.dashboard-main' },
        { title: 'Course Creation', description: 'Create courses with our AI-powered content generator - turn your expertise into engaging content!', target: '.create-course-btn' },
        { title: 'Student Management', description: 'Track student progress, answer questions, and provide feedback.', target: '.students-tab' },
        { title: 'AI Assistant', description: "I can help you create content, manage students, and answer platform questions!", target: '.ai-assistant-button' }
      ],
      organization_admin: [
        { title: 'Organization Dashboard', description: 'Overview of your organization - members, projects, and learning progress.', target: '.dashboard-main' },
        { title: 'Projects & Tracks', description: 'Create learning tracks and organize courses for your team.', target: '.projects-tab' },
        { title: 'Member Management', description: 'Invite and manage instructors and students in your organization.', target: '.members-tab' },
        { title: 'AI Assistant', description: "I can help you manage your organization, create tracks, and generate reports!", target: '.ai-assistant-button' }
      ],
      site_admin: [
        { title: 'Admin Dashboard', description: 'Platform-wide overview - organizations, users, and system health.', target: '.dashboard-main' },
        { title: 'Organization Management', description: 'Manage all organizations on the platform.', target: '.orgs-tab' },
        { title: 'System Health', description: 'Monitor platform performance and service status.', target: '.health-tab' },
        { title: 'AI Assistant', description: "I can help you manage the platform, monitor health, and generate reports!", target: '.ai-assistant-button' }
      ]
    };

    setTourSteps(roleTourSteps[role] || roleTourSteps.student);
  };

  // Handle close
  const handleClose = useCallback(() => {
    setIsVisible(false);
    localStorage.setItem('ai_welcome_last_shown', new Date().toISOString());
    onClose?.();
  }, [onClose]);

  // Handle "Don't show again"
  const handleDontShowAgain = useCallback(() => {
    localStorage.setItem('ai_welcome_seen', 'true');
    handleClose();
  }, [handleClose]);

  // Handle start tour
  const handleStartTour = useCallback(() => {
    setShowTour(true);
    setCurrentTourStep(0);
    onStartTour?.();
  }, [onStartTour]);

  // Handle tour navigation
  const handleNextTourStep = useCallback(() => {
    if (currentTourStep < tourSteps.length - 1) {
      setCurrentTourStep(prev => prev + 1);
    } else {
      // Tour complete
      setShowTour(false);
      localStorage.setItem('ai_welcome_seen', 'true');
      handleClose();
    }
  }, [currentTourStep, tourSteps.length, handleClose]);

  const handlePrevTourStep = useCallback(() => {
    if (currentTourStep > 0) {
      setCurrentTourStep(prev => prev - 1);
    }
  }, [currentTourStep]);

  const handleSkipTour = useCallback(() => {
    setShowTour(false);
    localStorage.setItem('ai_welcome_seen', 'true');
    handleClose();
  }, [handleClose]);

  // Handle quick action
  const handleQuickAction = useCallback((action: string) => {
    handleClose();

    // Navigate based on action
    const actionRoutes: Record<string, string> = {
      'Browse the course catalog': '/courses',
      'Browse courses': '/courses',
      'Check out your dashboard': '/dashboard',
      'Explore your dashboard': '/dashboard',
      'Create your first course': '/instructor/courses/new',
      'Explore the content generator': '/instructor/content-generator',
      'Create your first project': '/admin/projects/new',
      'Invite team members': '/admin/members',
      'Review platform status': '/admin/health',
      'Manage organizations': '/admin/organizations'
    };

    const route = actionRoutes[action];
    if (route) {
      navigate(route);
    }
  }, [handleClose, navigate]);

  // Don't render if not visible
  if (!isVisible) {
    return null;
  }

  // Render tour overlay
  if (showTour && tourSteps.length > 0) {
    const currentStep = tourSteps[currentTourStep];
    return (
      <div className={styles.tourOverlay}>
        <div className={styles.tourPopup}>
          <div className={styles.tourHeader}>
            <span className={styles.tourProgress}>
              Step {currentTourStep + 1} of {tourSteps.length}
            </span>
            <button className={styles.skipButton} onClick={handleSkipTour}>
              Skip Tour
            </button>
          </div>

          <div className={styles.tourContent}>
            <h3 className={styles.tourTitle}>{currentStep.title}</h3>
            <p className={styles.tourDescription}>{currentStep.description}</p>
          </div>

          <div className={styles.tourNavigation}>
            <Button
              variant="secondary"
              onClick={handlePrevTourStep}
              disabled={currentTourStep === 0}
            >
              Previous
            </Button>
            <Button
              variant="primary"
              onClick={handleNextTourStep}
            >
              {currentTourStep === tourSteps.length - 1 ? 'Finish' : 'Next'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Render welcome popup
  return (
    <div className={styles.overlay}>
      <div className={styles.popup}>
        {/* Header with AI avatar */}
        <div className={styles.header}>
          <div className={styles.avatarContainer}>
            <div className={styles.avatar}>
              <span className={styles.avatarEmoji}>🤖</span>
            </div>
            <div className={styles.avatarPulse} />
          </div>
          <button className={styles.closeButton} onClick={handleClose}>
            ×
          </button>
        </div>

        {/* Content */}
        <div className={styles.content}>
          {isLoading ? (
            <div className={styles.loading}>
              <div className={styles.loadingDots}>
                <span></span>
                <span></span>
                <span></span>
              </div>
              <p>Preparing your welcome...</p>
            </div>
          ) : (
            <>
              {/* Welcome message */}
              <div className={styles.welcomeMessage}>
                {welcomeData?.welcome_message.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>

              {/* Tour highlights */}
              {welcomeData?.tour_highlights && welcomeData.tour_highlights.length > 0 && (
                <div className={styles.highlights}>
                  <h4>What you'll discover:</h4>
                  <ul>
                    {welcomeData.tour_highlights.map((highlight, i) => (
                      <li key={i}>
                        <span className={styles.checkmark}>✓</span>
                        {highlight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Quick actions */}
              {welcomeData?.first_actions && welcomeData.first_actions.length > 0 && (
                <div className={styles.quickActions}>
                  <h4>Quick actions:</h4>
                  <div className={styles.actionButtons}>
                    {welcomeData.first_actions.slice(0, 3).map((action, i) => (
                      <button
                        key={i}
                        className={styles.actionButton}
                        onClick={() => handleQuickAction(action)}
                      >
                        {action}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <button
            className={styles.dontShowButton}
            onClick={handleDontShowAgain}
          >
            Don't show again
          </button>

          <div className={styles.mainActions}>
            <Button variant="secondary" onClick={handleClose}>
              Maybe Later
            </Button>
            <Button variant="primary" onClick={handleStartTour}>
              Take a Quick Tour
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomePopup;
