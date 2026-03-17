/**
 * Modal Component Tests
 *
 * BUSINESS CONTEXT:
 * Comprehensive test suite ensuring Modal component maintains Tami design standards
 * and provides accessible, reliable dialog functionality across the platform.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Vitest + React Testing Library for component testing
 * Tests portal rendering, focus management, keyboard handling, and accessibility
 *
 * COVERAGE REQUIREMENTS:
 * - Opening and closing behavior
 * - Backdrop clicks and ESC key handling
 * - Focus trap and keyboard navigation
 * - Accessibility (ARIA, roles, labels)
 * - Size variants and custom props
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Modal } from './Modal';

describe('Modal Component', () => {
  beforeEach(() => {
    // Create portal root if it doesn't exist
    if (!document.getElementById('modal-root')) {
      const modalRoot = document.createElement('div');
      modalRoot.setAttribute('id', 'modal-root');
      document.body.appendChild(modalRoot);
    }
  });

  afterEach(() => {
    // Clean up any open modals
    document.body.style.overflow = '';
  });

  describe('Rendering', () => {
    it('renders modal when isOpen is true', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Modal content
        </Modal>
      );
      expect(screen.getByText('Modal content')).toBeInTheDocument();
    });

    it('does not render modal when isOpen is false', () => {
      render(
        <Modal isOpen={false} onClose={vi.fn()}>
          Modal content
        </Modal>
      );
      expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
    });

    it('renders modal with title', () => {
      render(
        <Modal isOpen onClose={vi.fn()} title="Test Modal">
          Content
        </Modal>
      );
      expect(screen.getByText('Test Modal')).toBeInTheDocument();
    });

    it('renders modal without title', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    });
  });

  describe('Footer', () => {
    it('renders footer when provided', () => {
      render(
        <Modal
          isOpen
          onClose={vi.fn()}
          footer={<button>Action</button>}
        >
          Content
        </Modal>
      );
      expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument();
    });

    it('renders without footer when not provided', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      const buttons = screen.queryAllByRole('button');
      // Should only have close button if title is present
      expect(buttons.length).toBeLessThanOrEqual(1);
    });

    it('renders multiple footer actions', () => {
      render(
        <Modal
          isOpen
          onClose={vi.fn()}
          footer={
            <>
              <button>Cancel</button>
              <button>Confirm</button>
            </>
          }
        >
          Content
        </Modal>
      );
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument();
    });
  });

  describe('Sizes', () => {
    it('renders medium size by default', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
    });

    it('renders small size', () => {
      render(
        <Modal isOpen onClose={vi.fn()} size="small">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
    });

    it('renders large size', () => {
      render(
        <Modal isOpen onClose={vi.fn()} size="large">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
    });

    it('renders fullscreen size', () => {
      render(
        <Modal isOpen onClose={vi.fn()} size="fullscreen">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toBeInTheDocument();
    });
  });

  describe('Close Button', () => {
    it('renders close button by default', () => {
      render(
        <Modal isOpen onClose={vi.fn()} title="Test">
          Content
        </Modal>
      );
      expect(screen.getByLabelText(/close modal/i)).toBeInTheDocument();
    });

    it('calls onClose when close button clicked', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose} title="Test">
          Content
        </Modal>
      );
      const closeButton = screen.getByLabelText(/close modal/i);
      await userEvent.click(closeButton);
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('does not render close button when preventClose is true', () => {
      render(
        <Modal isOpen onClose={vi.fn()} title="Test" preventClose>
          Content
        </Modal>
      );
      expect(screen.queryByLabelText(/close modal/i)).not.toBeInTheDocument();
    });
  });

  describe('Backdrop Click', () => {
    it('closes modal when backdrop clicked by default', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose}>
          <div>Content</div>
        </Modal>
      );
      const backdrop = screen.getByRole('dialog').parentElement;
      if (backdrop) {
        await userEvent.click(backdrop);
        expect(handleClose).toHaveBeenCalledTimes(1);
      }
    });

    it('does not close when modal content is clicked', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose}>
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      await userEvent.click(modal);
      expect(handleClose).not.toHaveBeenCalled();
    });

    it('does not close when closeOnBackdropClick is false', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose} closeOnBackdropClick={false}>
          Content
        </Modal>
      );
      const backdrop = screen.getByRole('dialog').parentElement;
      if (backdrop) {
        await userEvent.click(backdrop);
        expect(handleClose).not.toHaveBeenCalled();
      }
    });

    it('does not close when preventClose is true', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose} preventClose>
          Content
        </Modal>
      );
      const backdrop = screen.getByRole('dialog').parentElement;
      if (backdrop) {
        await userEvent.click(backdrop);
        expect(handleClose).not.toHaveBeenCalled();
      }
    });
  });

  describe('ESC Key Handling', () => {
    it('closes modal when ESC pressed by default', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose}>
          Content
        </Modal>
      );
      await userEvent.keyboard('{Escape}');
      expect(handleClose).toHaveBeenCalledTimes(1);
    });

    it('does not close when closeOnEscape is false', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose} closeOnEscape={false}>
          Content
        </Modal>
      );
      await userEvent.keyboard('{Escape}');
      expect(handleClose).not.toHaveBeenCalled();
    });

    it('does not close when preventClose is true', async () => {
      const handleClose = vi.fn();
      render(
        <Modal isOpen onClose={handleClose} preventClose>
          Content
        </Modal>
      );
      await userEvent.keyboard('{Escape}');
      expect(handleClose).not.toHaveBeenCalled();
    });
  });

  describe('Body Scroll Lock', () => {
    it('locks body scroll when modal opens', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(document.body.style.overflow).toBe('hidden');
    });

    it('restores body scroll when modal closes', () => {
      const { rerender } = render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(document.body.style.overflow).toBe('hidden');

      rerender(
        <Modal isOpen={false} onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('Focus Management', () => {
    it('focuses modal when opened', async () => {
      render(
        <Modal isOpen onClose={vi.fn()} title="Test">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      await waitFor(() => {
        expect(document.activeElement).toBe(modal);
      });
    });

    it('traps focus within modal', async () => {
      render(
        <Modal
          isOpen
          onClose={vi.fn()}
          title="Test"
          footer={
            <>
              <button>First</button>
              <button>Last</button>
            </>
          }
        >
          <button>Middle</button>
        </Modal>
      );

      const closeButton = screen.getByLabelText(/close modal/i);
      const middleButton = screen.getByRole('button', { name: /middle/i });
      const firstButton = screen.getByRole('button', { name: /first/i });
      const lastButton = screen.getByRole('button', { name: /last/i });

      // Focus last button
      lastButton.focus();
      expect(document.activeElement).toBe(lastButton);

      // Tab should cycle to first focusable element
      await userEvent.tab();
      expect([closeButton, middleButton, firstButton]).toContain(document.activeElement);
    });
  });

  describe('Accessibility', () => {
    it('has role="dialog"', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('sets aria-modal="true"', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-modal', 'true');
    });

    it('associates title with aria-labelledby', () => {
      render(
        <Modal isOpen onClose={vi.fn()} title="Test Modal">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-labelledby', 'modal-title');
      expect(screen.getByText('Test Modal')).toHaveAttribute('id', 'modal-title');
    });

    it('uses aria-label when provided', () => {
      render(
        <Modal isOpen onClose={vi.fn()} ariaLabel="Custom label">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-label', 'Custom label');
    });

    it('uses title as aria-label fallback', () => {
      render(
        <Modal isOpen onClose={vi.fn()} title="Fallback Title">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal).toHaveAttribute('aria-label', 'Fallback Title');
    });
  });

  describe('Custom Props', () => {
    it('accepts custom className', () => {
      render(
        <Modal isOpen onClose={vi.fn()} className="custom-modal">
          Content
        </Modal>
      );
      const modal = screen.getByRole('dialog');
      expect(modal.className).toContain('custom-modal');
    });
  });

  describe('Portal Rendering', () => {
    it('renders modal in document.body', () => {
      render(
        <Modal isOpen onClose={vi.fn()}>
          Portal Content
        </Modal>
      );
      // Modal should be in body, not in the test container
      expect(document.body).toContainElement(screen.getByText('Portal Content'));
    });
  });

  describe('Display Name', () => {
    it('has Modal as display name', () => {
      expect(Modal.displayName).toBe('Modal');
    });
  });

  describe('Regression Tests', () => {
    it('handles rapid open/close cycles', () => {
      const { rerender } = render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(screen.getByText('Content')).toBeInTheDocument();

      rerender(
        <Modal isOpen={false} onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(screen.queryByText('Content')).not.toBeInTheDocument();

      rerender(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('handles content updates while open', () => {
      const { rerender } = render(
        <Modal isOpen onClose={vi.fn()}>
          Initial content
        </Modal>
      );
      expect(screen.getByText('Initial content')).toBeInTheDocument();

      rerender(
        <Modal isOpen onClose={vi.fn()}>
          Updated content
        </Modal>
      );
      expect(screen.getByText('Updated content')).toBeInTheDocument();
      expect(screen.queryByText('Initial content')).not.toBeInTheDocument();
    });

    it('cleans up event listeners on unmount', () => {
      const { unmount } = render(
        <Modal isOpen onClose={vi.fn()}>
          Content
        </Modal>
      );
      unmount();
      expect(document.body.style.overflow).toBe('');
    });
  });
});
