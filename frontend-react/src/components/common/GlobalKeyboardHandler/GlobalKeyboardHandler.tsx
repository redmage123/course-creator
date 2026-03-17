/**
 * Global Keyboard Handler Component
 *
 * BUSINESS CONTEXT:
 * Provides platform-wide keyboard shortcuts for power users and accessibility.
 * Enables efficient keyboard-only navigation throughout the application.
 *
 * KEYBOARD SHORTCUTS:
 * - ? or F1: Show keyboard shortcuts help
 * - / or Ctrl+K: Focus search (when available)
 * - Escape: Close any open modal/popup/dropdown
 * - Alt+H: Navigate to home
 * - Alt+D: Navigate to dashboard
 * - Alt+A: Toggle AI Assistant
 * - Alt+S: Skip to main content
 *
 * WCAG 2.1 AA Compliance:
 * - 2.1.1 Keyboard (Level A) - All functionality keyboard accessible
 * - 2.1.4 Character Key Shortcuts - Shortcuts use modifier keys
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { Modal } from '../../atoms/Modal';
import styles from './GlobalKeyboardHandler.module.css';

interface KeyboardShortcutInfo {
  keys: string;
  description: string;
  category: string;
}

const KEYBOARD_SHORTCUTS: KeyboardShortcutInfo[] = [
  // Navigation
  { keys: 'Alt + H', description: 'Go to Home', category: 'Navigation' },
  { keys: 'Alt + D', description: 'Go to Dashboard', category: 'Navigation' },
  { keys: 'Alt + S', description: 'Skip to main content', category: 'Navigation' },
  { keys: 'Alt + N', description: 'Skip to navigation', category: 'Navigation' },

  // Search & Actions
  { keys: '/ or Ctrl + K', description: 'Focus search', category: 'Actions' },
  { keys: 'Alt + A', description: 'Toggle AI Assistant', category: 'Actions' },

  // General
  { keys: '? or F1', description: 'Show this help', category: 'General' },
  { keys: 'Escape', description: 'Close modal/popup/dropdown', category: 'General' },

  // Forms
  { keys: 'Enter', description: 'Submit form', category: 'Forms' },
  { keys: 'Tab', description: 'Next field', category: 'Forms' },
  { keys: 'Shift + Tab', description: 'Previous field', category: 'Forms' },

  // Dropdowns & Menus
  { keys: '↑ / ↓', description: 'Navigate options', category: 'Dropdowns' },
  { keys: 'Enter / Space', description: 'Select option', category: 'Dropdowns' },
  { keys: 'Home / End', description: 'First/last option', category: 'Dropdowns' },
  { keys: 'PgUp / PgDn', description: 'Jump 5 options', category: 'Dropdowns' },
];

/**
 * Global Keyboard Handler Component
 *
 * WHY THIS APPROACH:
 * - Centralized keyboard handling prevents conflicts
 * - Modal shows all available shortcuts for discoverability
 * - Uses modifier keys to avoid conflicts with browser/AT
 * - Respects focus context (doesn't trigger in inputs unless using modifiers)
 */
export const GlobalKeyboardHandler: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [showShortcutsModal, setShowShortcutsModal] = useState(false);

  /**
   * Check if user is typing in an input field
   */
  const isTypingInInput = useCallback((): boolean => {
    const activeElement = document.activeElement;
    const tagName = activeElement?.tagName.toLowerCase();
    return (
      tagName === 'input' ||
      tagName === 'textarea' ||
      tagName === 'select' ||
      (activeElement as HTMLElement)?.isContentEditable === true
    );
  }, []);

  /**
   * Get user's dashboard path based on role
   */
  const getDashboardPath = useCallback((): string => {
    if (!user?.role) return '/';

    switch (user.role) {
      case 'site_admin':
        return '/admin/dashboard';
      case 'org_admin':
        return '/org-admin/dashboard';
      case 'instructor':
        return '/instructor/dashboard';
      case 'student':
        return '/student/dashboard';
      default:
        return '/dashboard';
    }
  }, [user?.role]);

  /**
   * Focus search input if available
   */
  const focusSearch = useCallback((): void => {
    const searchInput = document.querySelector<HTMLInputElement>(
      'input[type="search"], input[placeholder*="search" i], input[aria-label*="search" i], #search-input'
    );
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }, []);

  /**
   * Toggle AI Assistant
   */
  const toggleAIAssistant = useCallback((): void => {
    const aiButton = document.querySelector<HTMLButtonElement>(
      '[data-testid="ai-assistant-button"], .ai-assistant-toggle'
    );
    if (aiButton) {
      aiButton.click();
    } else {
      // Dispatch custom event that AI Assistant can listen for
      window.dispatchEvent(new CustomEvent('toggle-ai-assistant'));
    }
  }, []);

  /**
   * Skip to main content
   */
  const skipToMain = useCallback((): void => {
    const mainContent = document.querySelector<HTMLElement>(
      '#main-content, main, [role="main"]'
    );
    if (mainContent) {
      mainContent.focus();
      mainContent.scrollIntoView({ behavior: 'smooth' });
    }
  }, []);

  /**
   * Skip to navigation
   */
  const skipToNav = useCallback((): void => {
    const nav = document.querySelector<HTMLElement>(
      '#navigation, nav, [role="navigation"]'
    );
    if (nav) {
      const firstLink = nav.querySelector<HTMLElement>('a, button');
      if (firstLink) {
        firstLink.focus();
      }
    }
  }, []);

  /**
   * Handle global keyboard events
   */
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      const { key, altKey, ctrlKey, metaKey, shiftKey } = event;
      const typing = isTypingInInput();

      // ? or F1 - Show shortcuts help (works anywhere)
      if ((key === '?' && !typing) || key === 'F1') {
        event.preventDefault();
        setShowShortcutsModal(true);
        return;
      }

      // / or Ctrl+K - Focus search (not when typing, unless using Ctrl)
      if ((key === '/' && !typing) || ((ctrlKey || metaKey) && key === 'k')) {
        event.preventDefault();
        focusSearch();
        return;
      }

      // Alt key combinations (work even when typing)
      if (altKey && !ctrlKey && !metaKey) {
        switch (key.toLowerCase()) {
          case 'h':
            event.preventDefault();
            navigate('/');
            return;
          case 'd':
            event.preventDefault();
            if (isAuthenticated) {
              navigate(getDashboardPath());
            }
            return;
          case 'a':
            event.preventDefault();
            toggleAIAssistant();
            return;
          case 's':
            event.preventDefault();
            skipToMain();
            return;
          case 'n':
            event.preventDefault();
            skipToNav();
            return;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [
    isTypingInInput,
    navigate,
    isAuthenticated,
    getDashboardPath,
    focusSearch,
    toggleAIAssistant,
    skipToMain,
    skipToNav,
  ]);

  // Group shortcuts by category for display
  const shortcutsByCategory = KEYBOARD_SHORTCUTS.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, KeyboardShortcutInfo[]>);

  return (
    <>
      {/* Keyboard Hint Indicator - subtle reminder for users */}
      <button
        className={styles.keyboardHint}
        onClick={() => setShowShortcutsModal(true)}
        aria-label="Show keyboard shortcuts (press ? key)"
        title="Keyboard shortcuts"
      >
        <kbd>?</kbd>
        <span>Shortcuts</span>
      </button>

      {/* Keyboard Shortcuts Help Modal */}
      <Modal
        isOpen={showShortcutsModal}
        onClose={() => setShowShortcutsModal(false)}
        title="Keyboard Shortcuts"
        size="medium"
        ariaLabel="Keyboard shortcuts reference"
      >
        <div className={styles.shortcutsContainer}>
          {Object.entries(shortcutsByCategory).map(([category, shortcuts]) => (
            <div key={category} className={styles.shortcutCategory}>
              <h3 className={styles.categoryTitle}>{category}</h3>
              <div className={styles.shortcutList}>
                {shortcuts.map((shortcut) => (
                  <div key={shortcut.keys} className={styles.shortcutItem}>
                    <kbd className={styles.shortcutKeys}>{shortcut.keys}</kbd>
                    <span className={styles.shortcutDescription}>
                      {shortcut.description}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <p className={styles.tip}>
          Tip: Press <kbd>?</kbd> anytime to show this help
        </p>
      </Modal>
    </>
  );
};

export default GlobalKeyboardHandler;
