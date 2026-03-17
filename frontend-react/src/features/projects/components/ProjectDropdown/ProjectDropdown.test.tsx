/**
 * Project Dropdown Component Tests
 *
 * BUSINESS CONTEXT:
 * Tests the searchable project dropdown component to ensure correct
 * rendering, interaction, and accessibility.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { ProjectDropdown } from './ProjectDropdown';

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
    get: vi.fn().mockResolvedValue({
      data: {
        projects: [
          {
            id: 'project-1',
            name: 'Main Training Project',
            organizationId: 'org-123',
            status: 'active',
            trackCount: 3
          },
          {
            id: 'project-2',
            name: 'New York Location',
            organizationId: 'org-123',
            parentProjectId: 'project-1',
            status: 'active',
            locationName: 'New York',
            trackCount: 2
          },
          {
            id: 'project-3',
            name: 'Los Angeles Location',
            organizationId: 'org-123',
            parentProjectId: 'project-1',
            status: 'draft',
            locationName: 'Los Angeles',
            trackCount: 1
          }
        ]
      }
    })
  }
}));

describe('ProjectDropdown', () => {
  const mockOnChange = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial Rendering', () => {
    it('renders with placeholder text', () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      expect(screen.getByText('Select a project...')).toBeInTheDocument();
    });

    it('renders with custom placeholder', () => {
      render(
        <ProjectDropdown
          onChange={mockOnChange}
          placeholder="Choose your project"
        />
      );

      expect(screen.getByText('Choose your project')).toBeInTheDocument();
    });

    it('renders with label when provided', () => {
      render(
        <ProjectDropdown
          onChange={mockOnChange}
          label="Select Project"
        />
      );

      expect(screen.getByText('Select Project')).toBeInTheDocument();
    });

    it('shows required indicator when required', () => {
      render(
        <ProjectDropdown
          onChange={mockOnChange}
          label="Project"
          required
        />
      );

      expect(screen.getByText('*')).toBeInTheDocument();
    });
  });

  describe('Dropdown Interaction', () => {
    it('opens dropdown on click', async () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.getByPlaceholderText('Search projects...')).toBeInTheDocument();
    });

    it('opens dropdown on Enter key', async () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = screen.getByRole('combobox');
      trigger.focus();
      fireEvent.keyDown(trigger, { key: 'Enter' });

      expect(screen.getByPlaceholderText('Search projects...')).toBeInTheDocument();
    });

    it('opens dropdown on ArrowDown key', async () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = screen.getByRole('combobox');
      trigger.focus();
      fireEvent.keyDown(trigger, { key: 'ArrowDown' });

      expect(screen.getByPlaceholderText('Search projects...')).toBeInTheDocument();
    });

    it('closes dropdown on Escape key', async () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      // Open dropdown
      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      // Press Escape
      fireEvent.keyDown(trigger, { key: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByPlaceholderText('Search projects...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Selected Value', () => {
    it('displays selected project name', async () => {
      render(
        <ProjectDropdown
          value="project-1"
          onChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Main Training Project')).toBeInTheDocument();
      });
    });

    it('shows clear button when value is selected', async () => {
      render(
        <ProjectDropdown
          value="project-1"
          onChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Clear selection')).toBeInTheDocument();
      });
    });

    it('calls onChange with null when clearing', async () => {
      render(
        <ProjectDropdown
          value="project-1"
          onChange={mockOnChange}
        />
      );

      await waitFor(() => {
        expect(screen.getByLabelText('Clear selection')).toBeInTheDocument();
      });

      const clearBtn = screen.getByLabelText('Clear selection');
      await userEvent.click(clearBtn);

      expect(mockOnChange).toHaveBeenCalledWith(null, null);
    });
  });

  describe('Disabled State', () => {
    it('applies disabled styles', () => {
      render(
        <ProjectDropdown
          onChange={mockOnChange}
          disabled
        />
      );

      const container = document.querySelector('[class*="disabled"]');
      expect(container).toBeInTheDocument();
    });

    it('does not show clear button when disabled', async () => {
      render(
        <ProjectDropdown
          value="project-1"
          onChange={mockOnChange}
          disabled
        />
      );

      expect(screen.queryByLabelText('Clear selection')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error message', () => {
      render(
        <ProjectDropdown
          onChange={mockOnChange}
          error="Project is required"
        />
      );

      expect(screen.getByText('Project is required')).toBeInTheDocument();
    });

    it('applies error styles to trigger', () => {
      render(
        <ProjectDropdown
          onChange={mockOnChange}
          error="Project is required"
        />
      );

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveClass('error');
    });
  });

  describe('Accessibility', () => {
    it('has proper combobox role', () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('has aria-expanded attribute', async () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-expanded', 'false');

      await userEvent.click(trigger);

      expect(trigger).toHaveAttribute('aria-expanded', 'true');
    });

    it('has aria-haspopup attribute', () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-haspopup', 'listbox');
    });

    it('has aria-label when no label provided', () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveAttribute('aria-label', 'Select project');
    });

    it('renders listbox when open', async () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = screen.getByRole('combobox');
      await userEvent.click(trigger);

      expect(screen.getByRole('listbox')).toBeInTheDocument();
    });
  });

  describe('Props', () => {
    it('accepts custom className', () => {
      render(
        <ProjectDropdown
          onChange={mockOnChange}
          className="custom-class"
        />
      );

      const container = document.querySelector('.custom-class');
      expect(container).toBeInTheDocument();
    });

    it('accepts showSubProjects prop', () => {
      // Should not throw
      expect(() => {
        render(
          <ProjectDropdown
            onChange={mockOnChange}
            showSubProjects={false}
          />
        );
      }).not.toThrow();
    });

    it('accepts includeArchived prop', () => {
      // Should not throw
      expect(() => {
        render(
          <ProjectDropdown
            onChange={mockOnChange}
            includeArchived={true}
          />
        );
      }).not.toThrow();
    });

    it('accepts organizationId prop', () => {
      // Should not throw
      expect(() => {
        render(
          <ProjectDropdown
            onChange={mockOnChange}
            organizationId="custom-org-id"
          />
        );
      }).not.toThrow();
    });
  });

  describe('Styling', () => {
    it('applies container styles', () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const container = document.querySelector('[class*="container"]');
      expect(container).toBeInTheDocument();
    });

    it('applies trigger styles', () => {
      render(<ProjectDropdown onChange={mockOnChange} />);

      const trigger = document.querySelector('[class*="trigger"]');
      expect(trigger).toBeInTheDocument();
    });
  });
});
