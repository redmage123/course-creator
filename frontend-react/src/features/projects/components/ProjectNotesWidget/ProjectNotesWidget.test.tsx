/**
 * ProjectNotesWidget Unit Tests
 *
 * BUSINESS CONTEXT:
 * Tests for the project notes widget component that allows organization
 * admins to create, edit, and manage project documentation.
 *
 * TEST COVERAGE:
 * - Rendering in various states (loading, empty, with content)
 * - Edit mode functionality
 * - File upload handling
 * - Content type switching
 * - Collapsible behavior
 * - Error handling
 * - Accessibility compliance
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ProjectNotesWidget } from './ProjectNotesWidget';
import { projectService, ProjectNotes } from '@services/projectService';

// Mock the project service
vi.mock('@services/projectService', () => ({
  projectService: {
    getProjectNotes: vi.fn(),
    updateProjectNotes: vi.fn(),
    uploadProjectNotes: vi.fn(),
    deleteProjectNotes: vi.fn(),
  },
}));

// Mock window.confirm
const originalConfirm = window.confirm;

describe('ProjectNotesWidget', () => {
  const mockOrganizationId = '123e4567-e89b-12d3-a456-426614174000';
  const mockProjectId = '987fcdeb-51a2-3e4f-b567-890123456789';

  const mockNotesData: ProjectNotes = {
    project_id: mockProjectId,
    project_name: 'Test Project',
    notes: '# Test Notes\n\nThis is test content.',
    notes_content_type: 'markdown',
    notes_updated_at: '2024-01-15T10:30:00Z',
    notes_updated_by: 'user-uuid-123',
    updated_by_name: 'John Doe',
    updated_by_email: 'john@example.com',
  };

  const mockEmptyNotes: ProjectNotes = {
    project_id: mockProjectId,
    project_name: 'Test Project',
    notes: null,
    notes_content_type: 'markdown',
    notes_updated_at: null,
    notes_updated_by: null,
    updated_by_name: null,
    updated_by_email: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    window.confirm = vi.fn(() => true);
  });

  afterEach(() => {
    window.confirm = originalConfirm;
  });

  // ==========================================================================
  // RENDERING TESTS
  // ==========================================================================

  describe('Rendering', () => {
    it('should render loading state initially', () => {
      vi.mocked(projectService.getProjectNotes).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      expect(screen.getByText(/loading notes/i)).toBeInTheDocument();
    });

    it('should render notes content after loading', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/# Test Notes/)).toBeInTheDocument();
      });
    });

    it('should render empty state when no notes exist', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockEmptyNotes);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/no notes have been added/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /add notes/i })).toBeInTheDocument();
      });
    });

    it('should render with title "Project Notes"', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Project Notes')).toBeInTheDocument();
      });
    });

    it('should display content type badge', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Markdown')).toBeInTheDocument();
      });
    });

    it('should display HTML badge when content type is html', async () => {
      const htmlNotes = { ...mockNotesData, notes_content_type: 'html' as const };
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(htmlNotes);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('HTML')).toBeInTheDocument();
      });
    });

    it('should display metadata (last updated, updated by)', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/last updated:/i)).toBeInTheDocument();
        expect(screen.getByText(/john doe/i)).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // EDIT MODE TESTS
  // ==========================================================================

  describe('Edit Mode', () => {
    it('should show edit button when canEdit is true and notes exist', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
      });
    });

    it('should not show edit button when canEdit is false', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={false}
        />
      );

      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
      });
    });

    it('should enter edit mode when edit button is clicked', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /edit/i }));

      expect(screen.getByRole('textbox', { name: /project notes content/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save notes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('should populate textarea with existing notes in edit mode', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const textarea = screen.getByRole('textbox', { name: /project notes content/i });
      expect(textarea).toHaveValue('# Test Notes\n\nThis is test content.');
    });

    it('should cancel edit mode and restore original content', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'Modified content' } });

      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      await waitFor(() => {
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
        expect(screen.getByText(/# Test Notes/)).toBeInTheDocument();
      });
    });

    it('should save notes when save button is clicked', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.updateProjectNotes).mockResolvedValue({
        ...mockNotesData,
        notes: 'Updated content',
      });

      const onNotesUpdated = vi.fn();

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
          onNotesUpdated={onNotesUpdated}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'Updated content' } });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(projectService.updateProjectNotes).toHaveBeenCalledWith(
          mockOrganizationId,
          mockProjectId,
          { notes: 'Updated content', content_type: 'markdown' }
        );
        expect(onNotesUpdated).toHaveBeenCalled();
      });
    });

    it('should show saving state while saving', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.updateProjectNotes).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      expect(screen.getByText(/saving/i)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // CONTENT TYPE TESTS
  // ==========================================================================

  describe('Content Type', () => {
    it('should allow switching content type in edit mode', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const select = screen.getByLabelText(/format/i);
      expect(select).toHaveValue('markdown');

      fireEvent.change(select, { target: { value: 'html' } });
      expect(select).toHaveValue('html');
    });

    it('should save with selected content type', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.updateProjectNotes).mockResolvedValue({
        ...mockNotesData,
        notes_content_type: 'html',
      });

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const select = screen.getByLabelText(/format/i);
      fireEvent.change(select, { target: { value: 'html' } });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(projectService.updateProjectNotes).toHaveBeenCalledWith(
          mockOrganizationId,
          mockProjectId,
          expect.objectContaining({ content_type: 'html' })
        );
      });
    });
  });

  // ==========================================================================
  // FILE UPLOAD TESTS
  // ==========================================================================

  describe('File Upload', () => {
    it('should show upload button in edit mode', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      expect(screen.getByRole('button', { name: /upload file/i })).toBeInTheDocument();
    });

    it('should accept markdown files', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.uploadProjectNotes).mockResolvedValue({
        ...mockNotesData,
        notes: '# Uploaded Content',
      });

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const fileInput = screen.getByLabelText(/upload notes file/i);
      const file = new File(['# Uploaded Content'], 'notes.md', { type: 'text/markdown' });

      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [file] } });
      });

      await waitFor(() => {
        expect(projectService.uploadProjectNotes).toHaveBeenCalledWith(
          mockOrganizationId,
          mockProjectId,
          file
        );
      });
    });

    it('should accept HTML files', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.uploadProjectNotes).mockResolvedValue({
        ...mockNotesData,
        notes: '<h1>Uploaded Content</h1>',
        notes_content_type: 'html',
      });

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const fileInput = screen.getByLabelText(/upload notes file/i);
      const file = new File(['<h1>Uploaded Content</h1>'], 'notes.html', { type: 'text/html' });

      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [file] } });
      });

      await waitFor(() => {
        expect(projectService.uploadProjectNotes).toHaveBeenCalled();
      });
    });

    it('should reject invalid file types', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const fileInput = screen.getByLabelText(/upload notes file/i);
      const file = new File(['content'], 'notes.txt', { type: 'text/plain' });

      await act(async () => {
        fireEvent.change(fileInput, { target: { files: [file] } });
      });

      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
        expect(projectService.uploadProjectNotes).not.toHaveBeenCalled();
      });
    });
  });

  // ==========================================================================
  // DELETE TESTS
  // ==========================================================================

  describe('Delete Notes', () => {
    it('should show delete button when notes exist in edit mode', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      expect(screen.getByRole('button', { name: /delete notes/i })).toBeInTheDocument();
    });

    it('should confirm before deleting', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.deleteProjectNotes).mockResolvedValue({ message: 'deleted', project_id: mockProjectId });

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      fireEvent.click(screen.getByRole('button', { name: /delete notes/i }));

      expect(window.confirm).toHaveBeenCalledWith(
        expect.stringMatching(/are you sure/i)
      );
    });

    it('should not delete if user cancels confirmation', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      window.confirm = vi.fn(() => false);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      fireEvent.click(screen.getByRole('button', { name: /delete notes/i }));

      expect(projectService.deleteProjectNotes).not.toHaveBeenCalled();
    });

    it('should delete notes when confirmed', async () => {
      vi.mocked(projectService.getProjectNotes)
        .mockResolvedValueOnce(mockNotesData)
        .mockResolvedValueOnce(mockEmptyNotes);
      vi.mocked(projectService.deleteProjectNotes).mockResolvedValue({ message: 'deleted', project_id: mockProjectId });

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      fireEvent.click(screen.getByRole('button', { name: /delete notes/i }));

      await waitFor(() => {
        expect(projectService.deleteProjectNotes).toHaveBeenCalledWith(
          mockOrganizationId,
          mockProjectId
        );
      });
    });
  });

  // ==========================================================================
  // COLLAPSIBLE TESTS
  // ==========================================================================

  describe('Collapsible Behavior', () => {
    it('should render expanded by default', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/# Test Notes/)).toBeInTheDocument();
      });
    });

    it('should render collapsed when defaultCollapsed is true', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          defaultCollapsed={true}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/# Test Notes.../)).toBeInTheDocument();
      });
    });

    it('should toggle collapsed state on button click', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/# Test Notes/)).toBeInTheDocument();
      });

      const collapseButton = screen.getByRole('button', { name: /collapse notes/i });
      fireEvent.click(collapseButton);

      await waitFor(() => {
        expect(screen.getByText(/# Test Notes.../)).toBeInTheDocument();
      });

      const expandButton = screen.getByRole('button', { name: /expand notes/i });
      fireEvent.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText(/# Test Notes/)).toBeInTheDocument();
      });
    });

    it('should have correct aria-expanded attribute', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        const collapseButton = screen.getByRole('button', { name: /collapse notes/i });
        expect(collapseButton).toHaveAttribute('aria-expanded', 'true');
      });
    });
  });

  // ==========================================================================
  // ERROR HANDLING TESTS
  // ==========================================================================

  describe('Error Handling', () => {
    it('should display error when loading fails', async () => {
      vi.mocked(projectService.getProjectNotes).mockRejectedValue(
        new Error('Network error')
      );

      const onError = vi.fn();

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          onError={onError}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
        expect(onError).toHaveBeenCalledWith('Network error');
      });
    });

    it('should display error when saving fails', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.updateProjectNotes).mockRejectedValue(
        new Error('Save failed')
      );

      const onError = vi.fn();

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
          onError={onError}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText(/save failed/i)).toBeInTheDocument();
        expect(onError).toHaveBeenCalledWith('Save failed');
      });
    });

    it('should allow dismissing error', async () => {
      vi.mocked(projectService.getProjectNotes).mockRejectedValue(
        new Error('Network error')
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      const dismissButton = screen.getByRole('button', { name: /dismiss error/i });
      fireEvent.click(dismissButton);

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // ACCESSIBILITY TESTS
  // ==========================================================================

  describe('Accessibility', () => {
    it('should have accessible name for textarea', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const textarea = screen.getByRole('textbox', { name: /project notes content/i });
      expect(textarea).toBeInTheDocument();
    });

    it('should have accessible name for file input', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const fileInput = screen.getByLabelText(/upload notes file/i);
      expect(fileInput).toBeInTheDocument();
    });

    it('should have accessible name for content type selector', async () => {
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      const select = screen.getByLabelText(/format/i);
      expect(select).toBeInTheDocument();
    });

    it('should mark error container with role="alert"', async () => {
      vi.mocked(projectService.getProjectNotes).mockRejectedValue(
        new Error('Network error')
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      await waitFor(() => {
        const alert = screen.getByRole('alert');
        expect(alert).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // CALLBACK TESTS
  // ==========================================================================

  describe('Callbacks', () => {
    it('should call onNotesUpdated after successful save', async () => {
      const updatedNotes = { ...mockNotesData, notes: 'Updated content' };
      vi.mocked(projectService.getProjectNotes).mockResolvedValue(mockNotesData);
      vi.mocked(projectService.updateProjectNotes).mockResolvedValue(updatedNotes);

      const onNotesUpdated = vi.fn();

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
          onNotesUpdated={onNotesUpdated}
        />
      );

      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(onNotesUpdated).toHaveBeenCalledWith(updatedNotes);
      });
    });

    it('should call onError when an error occurs', async () => {
      vi.mocked(projectService.getProjectNotes).mockRejectedValue(
        new Error('Load error')
      );

      const onError = vi.fn();

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          onError={onError}
        />
      );

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith('Load error');
      });
    });
  });
});
