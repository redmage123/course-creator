/**
 * Project Builder Chat Component Tests
 *
 * BUSINESS CONTEXT:
 * Tests the AI-powered project builder interface to ensure correct
 * rendering and basic interactions.
 *
 * TEST CATEGORIES:
 * 1. Rendering tests - Initial display and component structure
 * 2. Accessibility - Keyboard navigation, ARIA labels
 * 3. Basic interactions - Button clicks, input handling
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ProjectBuilderChat } from './ProjectBuilderChat';

// Mock dependencies
vi.mock('../../../../hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'user-123',
      organizationId: 'org-123',
      role: 'org_admin'
    },
    isAuthenticated: true
  })
}));

vi.mock('../../../../services/apiClient', () => ({
  apiClient: {
    post: vi.fn()
  }
}));

describe('ProjectBuilderChat', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('renders start screen when no session exists', () => {
      render(<ProjectBuilderChat />);

      expect(screen.getByText('Create Multi-Location Training Program')).toBeInTheDocument();
      expect(screen.getByText('Start Project Builder')).toBeInTheDocument();
    });

    it('displays feature list on start screen', () => {
      render(<ProjectBuilderChat />);

      expect(screen.getByText(/Parse CSV, Excel, or JSON roster files/)).toBeInTheDocument();
      expect(screen.getByText(/Generate optimized training schedules/)).toBeInTheDocument();
      expect(screen.getByText(/Create Zoom rooms automatically/)).toBeInTheDocument();
      expect(screen.getByText(/Configure multiple locations with tracks/)).toBeInTheDocument();
      expect(screen.getByText(/Assign instructors and students/)).toBeInTheDocument();
    });

    it('shows header with Project Builder title', () => {
      render(<ProjectBuilderChat />);

      expect(screen.getByText('Project Builder')).toBeInTheDocument();
    });

    it('displays "Not Started" state indicator initially', () => {
      render(<ProjectBuilderChat />);

      expect(screen.getByText('Not Started')).toBeInTheDocument();
    });

    it('shows rocket icon on start screen', () => {
      render(<ProjectBuilderChat />);

      // The rocket emoji is rendered in the start icon
      expect(document.querySelector('[class*="startIcon"]')).toBeInTheDocument();
    });
  });

  describe('Close Handler', () => {
    it('calls onClose when close button clicked', async () => {
      const onClose = vi.fn();
      render(<ProjectBuilderChat onClose={onClose} />);

      const closeButton = screen.getByLabelText('Close project builder');
      await userEvent.click(closeButton);

      expect(onClose).toHaveBeenCalled();
    });

    it('shows close button when onClose is provided', () => {
      render(<ProjectBuilderChat onClose={() => {}} />);

      const closeButton = screen.getByLabelText('Close project builder');
      expect(closeButton).toBeInTheDocument();
    });

    it('does not show close button when onClose not provided', () => {
      render(<ProjectBuilderChat />);

      const closeButton = screen.queryByLabelText('Close project builder');
      expect(closeButton).not.toBeInTheDocument();
    });
  });

  describe('Start Button', () => {
    it('has start button on initial render', () => {
      render(<ProjectBuilderChat />);

      const startButton = screen.getByRole('button', { name: /Start Project Builder/ });
      expect(startButton).toBeInTheDocument();
    });

    it('start button is enabled initially', () => {
      render(<ProjectBuilderChat />);

      const startButton = screen.getByRole('button', { name: /Start Project Builder/ });
      expect(startButton).not.toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('close button has aria-label', () => {
      render(<ProjectBuilderChat onClose={() => {}} />);

      const closeButton = screen.getByRole('button', { name: 'Close project builder' });
      expect(closeButton).toBeInTheDocument();
    });

    it('has accessible header structure', () => {
      render(<ProjectBuilderChat />);

      // Header with title and state indicator
      expect(screen.getByText('Project Builder')).toBeInTheDocument();
      expect(screen.getByText('Not Started')).toBeInTheDocument();
    });

    it('has accessible start screen heading', () => {
      render(<ProjectBuilderChat />);

      const heading = screen.getByRole('heading', { level: 2 });
      expect(heading).toHaveTextContent('Create Multi-Location Training Program');
    });
  });

  describe('Props Handling', () => {
    it('accepts onProjectCreated callback', () => {
      const onProjectCreated = vi.fn();

      // Should render without errors
      expect(() => {
        render(<ProjectBuilderChat onProjectCreated={onProjectCreated} />);
      }).not.toThrow();
    });

    it('renders correctly with all props', () => {
      const onClose = vi.fn();
      const onProjectCreated = vi.fn();

      render(
        <ProjectBuilderChat
          onClose={onClose}
          onProjectCreated={onProjectCreated}
        />
      );

      expect(screen.getByText('Project Builder')).toBeInTheDocument();
      expect(screen.getByLabelText('Close project builder')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('applies container styles', () => {
      render(<ProjectBuilderChat />);

      const container = document.querySelector('[class*="container"]');
      expect(container).toBeInTheDocument();
    });

    it('applies header styles', () => {
      render(<ProjectBuilderChat />);

      const header = document.querySelector('[class*="header"]');
      expect(header).toBeInTheDocument();
    });

    it('applies start screen styles', () => {
      render(<ProjectBuilderChat />);

      const startScreen = document.querySelector('[class*="startScreen"]');
      expect(startScreen).toBeInTheDocument();
    });
  });
});
