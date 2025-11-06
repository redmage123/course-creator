/**
 * the design system Modal System - JavaScript Controller
 *
 * Provides modal/dialog functionality with:
 * - Open/close with animations
 * - ESC key to close
 * - Click outside to close
 * - Body scroll lock
 * - Focus trap for accessibility
 * - Custom events for integration
 *
 * Usage:
 * Modal.open('modal-id');
 * Modal.close('modal-id');
 * Modal.closeAll();
 *
 * Events:
 * - 'modal:open' - Fired when modal opens
 * - 'modal:close' - Fired when modal closes
 */

const the design systemModal = (function() {
  'use strict';

  // Private state
  const state = {
    openModals: new Set(),
    focusableSelectors: [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])'
    ].join(', ')
  };

  /**
   * Initialize modal system
   * Sets up event listeners on all modals
   */
  function init() {
    // Only initialize if the design system UI is enabled
    const body = document.querySelector('body');
    if (!body || body.getAttribute('data-ui') !== 'enabled') {
      return;
    }

    // Set up event listeners for all modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
      setupModalEventListeners(modal);
    });

    // ESC key handler
    document.addEventListener('keydown', handleEscapeKey);
  }

  /**
   * Set up event listeners for a single modal
   * @param {HTMLElement} modal - The modal element
   */
  function setupModalEventListeners(modal) {
    const modalId = modal.id;

    // Close button
    const closeBtn = modal.querySelector('.modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => close(modalId));
    }

    // Backdrop click (click outside) - handle clicks on modal container, not content
    modal.addEventListener('click', function(e) {
      // Only close if clicking the modal container itself (not its children)
      if (e.target === modal || e.target.classList.contains('modal-backdrop')) {
        close(modalId);
      }
    });

    // Secondary/cancel buttons
    const secondaryBtns = modal.querySelectorAll('.btn-secondary');
    secondaryBtns.forEach(btn => {
      btn.addEventListener('click', () => close(modalId));
    });
  }

  /**
   * Open a modal by ID
   * @param {string} modalId - The ID of the modal to open
   */
  function open(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal || !modal.classList.contains('modal')) {
      console.error(`Modal with ID "${modalId}" not found`);
      return;
    }

    // Add to open modals set
    state.openModals.add(modalId);

    // Lock body scroll
    document.body.classList.add('modal-open');

    // Show modal with animation
    modal.classList.add('is-open');

    // Set focus to first focusable element
    setTimeout(() => {
      const focusableElements = modal.querySelectorAll(state.focusableSelectors);
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }

      // Set up focus trap
      setupFocusTrap(modal);
    }, 100);

    // Dispatch custom event
    const event = new CustomEvent('modal:open', {
      detail: { modalId }
    });
    document.dispatchEvent(event);
  }

  /**
   * Close a modal by ID
   * @param {string} modalId - The ID of the modal to close
   */
  function close(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) {
      return;
    }

    // Remove from open modals set
    state.openModals.delete(modalId);

    // Hide modal with animation
    modal.classList.remove('is-open');

    // Unlock body scroll if no modals are open
    if (state.openModals.size === 0) {
      document.body.classList.remove('modal-open');
    }

    // Remove focus trap
    removeFocusTrap(modal);

    // Dispatch custom event
    const event = new CustomEvent('modal:close', {
      detail: { modalId }
    });
    document.dispatchEvent(event);
  }

  /**
   * Close all open modals
   */
  function closeAll() {
    const modalIds = Array.from(state.openModals);
    modalIds.forEach(modalId => close(modalId));
  }

  /**
   * Handle ESC key press
   * @param {KeyboardEvent} e - The keyboard event
   */
  function handleEscapeKey(e) {
    if (e.key === 'Escape' || e.keyCode === 27) {
      // Close the most recently opened modal
      if (state.openModals.size > 0) {
        const modalIds = Array.from(state.openModals);
        const lastModalId = modalIds[modalIds.length - 1];
        close(lastModalId);
      }
    }
  }

  /**
   * Set up focus trap within modal
   * Keeps focus within the modal for accessibility
   * @param {HTMLElement} modal - The modal element
   */
  function setupFocusTrap(modal) {
    const focusableElements = modal.querySelectorAll(state.focusableSelectors);
    if (focusableElements.length === 0) {
      return;
    }

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Store reference to handler for cleanup
    modal._focusTrapHandler = function(e) {
      if (e.key !== 'Tab' && e.keyCode !== 9) {
        return;
      }

      // Shift + Tab (backwards)
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      }
      // Tab (forwards)
      else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    modal.addEventListener('keydown', modal._focusTrapHandler);
  }

  /**
   * Remove focus trap from modal
   * @param {HTMLElement} modal - The modal element
   */
  function removeFocusTrap(modal) {
    if (modal._focusTrapHandler) {
      modal.removeEventListener('keydown', modal._focusTrapHandler);
      delete modal._focusTrapHandler;
    }
  }

  /**
   * Check if a modal is currently open
   * @param {string} modalId - The ID of the modal to check
   * @returns {boolean} True if modal is open
   */
  function isOpen(modalId) {
    return state.openModals.has(modalId);
  }

  /**
   * Get count of currently open modals
   * @returns {number} Number of open modals
   */
  function getOpenCount() {
    return state.openModals.size;
  }

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Public API
  return {
    open,
    close,
    closeAll,
    isOpen,
    getOpenCount,
    init
  };
})();

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = the design systemModal;
}

// Make available globally
if (typeof window !== 'undefined') {
  window.the design systemModal = the design systemModal;
}
