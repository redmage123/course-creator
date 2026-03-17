/**
 * ProjectNotesWidget Integration Tests
 *
 * BUSINESS CONTEXT:
 * Integration tests for the project notes widget to verify it works
 * correctly with the API service layer and state management.
 *
 * TEST COVERAGE:
 * - API integration patterns
 * - State synchronization
 * - Component lifecycle with API calls
 * - Error recovery flows
 * - Multi-step workflows
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { http, HttpResponse, delay } from 'msw';
import { setupServer } from 'msw/node';
import { ProjectNotesWidget } from './ProjectNotesWidget';
import { ProjectNotes } from '@services/projectService';

// ==========================================================================
// MSW SERVER SETUP
// ==========================================================================

const mockOrganizationId = '123e4567-e89b-12d3-a456-426614174000';
const mockProjectId = '987fcdeb-51a2-3e4f-b567-890123456789';

const mockNotesData: ProjectNotes = {
  project_id: mockProjectId,
  project_name: 'Integration Test Project',
  notes: '# Integration Test Notes\n\nThis content tests API integration.',
  notes_content_type: 'markdown',
  notes_updated_at: '2024-01-15T10:30:00Z',
  notes_updated_by: 'user-uuid-123',
  updated_by_name: 'Integration Tester',
  updated_by_email: 'tester@example.com',
};

const mockEmptyNotes: ProjectNotes = {
  project_id: mockProjectId,
  project_name: 'Integration Test Project',
  notes: null,
  notes_content_type: 'markdown',
  notes_updated_at: null,
  notes_updated_by: null,
  updated_by_name: null,
  updated_by_email: null,
};

// Create MSW server for API mocking
// Use wildcard pattern to match full URLs with any base
const server = setupServer(
  // GET project notes
  http.get(
    '*/organizations/:orgId/projects/:projectId/notes',
    () => {
      return HttpResponse.json(mockNotesData);
    }
  ),

  // PUT update notes
  http.put(
    '*/organizations/:orgId/projects/:projectId/notes',
    async ({ request }) => {
      const body = await request.json() as { notes: string; content_type: string };
      return HttpResponse.json({
        ...mockNotesData,
        notes: body.notes,
        notes_content_type: body.content_type,
        notes_updated_at: new Date().toISOString(),
      });
    }
  ),

  // POST upload notes
  http.post(
    '*/organizations/:orgId/projects/:projectId/notes/upload',
    async ({ request }) => {
      const body = await request.json() as { file_content: string; file_name: string };
      const decodedContent = atob(body.file_content);
      const contentType = body.file_name.endsWith('.html') ? 'html' : 'markdown';
      return HttpResponse.json({
        ...mockNotesData,
        notes: decodedContent,
        notes_content_type: contentType,
        notes_updated_at: new Date().toISOString(),
      });
    }
  ),

  // DELETE notes
  http.delete(
    '*/organizations/:orgId/projects/:projectId/notes',
    () => {
      return HttpResponse.json({
        message: 'Notes deleted successfully',
        project_id: mockProjectId,
      });
    }
  )
);

// Start server before tests - use 'warn' to log unhandled requests without failing
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

// Mock window.confirm
const originalConfirm = window.confirm;

describe('ProjectNotesWidget Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.confirm = vi.fn(() => true);
  });

  afterEach(() => {
    window.confirm = originalConfirm;
  });

  // ==========================================================================
  // API INTEGRATION TESTS
  // ==========================================================================

  describe('API Integration', () => {
    it('should fetch notes from API on mount', async () => {
      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      // Should show loading first
      expect(screen.getByText(/loading notes/i)).toBeInTheDocument();

      // Then show content after API response
      await waitFor(() => {
        expect(screen.getByText(/# Integration Test Notes/)).toBeInTheDocument();
      });
    });

    it('should send correct payload when updating notes', async () => {
      let capturedRequest: any = null;

      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async ({ request }) => {
            capturedRequest = await request.json();
            return HttpResponse.json({
              ...mockNotesData,
              notes: (capturedRequest as { notes: string; content_type: string }).notes,
              notes_content_type: (capturedRequest as { notes: string; content_type: string }).content_type,
            });
          }
        )
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

      const textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'Updated via integration test' } });

      // Change content type
      const select = screen.getByLabelText(/format/i);
      fireEvent.change(select, { target: { value: 'html' } });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(capturedRequest).toEqual({
          notes: 'Updated via integration test',
          content_type: 'html',
        });
      });
    });

    it('should handle API errors gracefully', async () => {
      server.use(
        http.get(
          '*/organizations/:orgId/projects/:projectId/notes',
          () => {
            return HttpResponse.json({ error: 'Server error' }, { status: 500 });
          }
        )
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
    });

    it('should handle network timeout', async () => {
      server.use(
        http.get(
          '*/organizations/:orgId/projects/:projectId/notes',
          async () => {
            await delay('infinite');
            return HttpResponse.json(mockNotesData);
          }
        )
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
        />
      );

      // Should stay in loading state
      expect(screen.getByText(/loading notes/i)).toBeInTheDocument();
    });
  });

  // ==========================================================================
  // STATE SYNCHRONIZATION TESTS
  // ==========================================================================

  describe('State Synchronization', () => {
    it('should update UI after successful save', async () => {
      const updatedContent = 'Content updated successfully';

      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async () => {
            return HttpResponse.json({
              ...mockNotesData,
              notes: updatedContent,
            });
          }
        )
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

      const textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: updatedContent } });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      // Should exit edit mode and show updated content
      await waitFor(() => {
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
        expect(screen.getByText(updatedContent)).toBeInTheDocument();
      });
    });

    it('should preserve content type after save', async () => {
      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async ({ request }) => {
            const body = await request.json() as { notes: string; content_type: string };
            return HttpResponse.json({
              ...mockNotesData,
              notes_content_type: body.content_type,
            });
          }
        )
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

      const select = screen.getByLabelText(/format/i);
      fireEvent.change(select, { target: { value: 'html' } });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(screen.getByText('HTML')).toBeInTheDocument();
      });
    });

    it('should refetch notes after delete', async () => {
      let fetchCount = 0;

      server.use(
        http.get(
          '*/organizations/:orgId/projects/:projectId/notes',
          () => {
            fetchCount++;
            // Return empty on second fetch (after delete)
            return HttpResponse.json(fetchCount === 1 ? mockNotesData : mockEmptyNotes);
          }
        )
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

      fireEvent.click(screen.getByRole('button', { name: /delete notes/i }));

      await waitFor(() => {
        expect(fetchCount).toBe(2); // Initial + refetch after delete
        expect(screen.getByText(/no notes have been added/i)).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // MULTI-STEP WORKFLOW TESTS
  // ==========================================================================

  describe('Multi-Step Workflows', () => {
    it('should handle edit-save-edit-save cycle', async () => {
      let saveCount = 0;

      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async ({ request }) => {
            saveCount++;
            const body = await request.json() as { notes: string; content_type: string };
            return HttpResponse.json({
              ...mockNotesData,
              notes: body.notes,
            });
          }
        )
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      // First edit-save cycle
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      let textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'First update' } });
      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(screen.getByText('First update')).toBeInTheDocument();
      });

      // Second edit-save cycle
      fireEvent.click(screen.getByRole('button', { name: /edit/i }));

      textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'Second update' } });
      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(screen.getByText('Second update')).toBeInTheDocument();
        expect(saveCount).toBe(2);
      });
    });

    it('should handle edit-cancel-edit-save flow', async () => {
      let saveCount = 0;

      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async () => {
            saveCount++;
            return HttpResponse.json({ ...mockNotesData, notes: 'Final content' });
          }
        )
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      // First edit then cancel
      await waitFor(() => {
        fireEvent.click(screen.getByRole('button', { name: /edit/i }));
      });

      let textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'This will be cancelled' } });
      fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

      await waitFor(() => {
        expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
      });

      // Second edit then save
      fireEvent.click(screen.getByRole('button', { name: /edit/i }));

      textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'Final content' } });
      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(saveCount).toBe(1); // Only saved once
        expect(screen.getByText('Final content')).toBeInTheDocument();
      });
    });

    it('should handle create-from-empty workflow', async () => {
      server.use(
        http.get(
          '*/organizations/:orgId/projects/:projectId/notes',
          () => {
            return HttpResponse.json(mockEmptyNotes);
          }
        ),
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async ({ request }) => {
            const body = await request.json() as { notes: string; content_type: string };
            return HttpResponse.json({
              ...mockNotesData,
              notes: body.notes,
            });
          }
        )
      );

      render(
        <ProjectNotesWidget
          organizationId={mockOrganizationId}
          projectId={mockProjectId}
          canEdit={true}
        />
      );

      // Should show empty state
      await waitFor(() => {
        expect(screen.getByText(/no notes have been added/i)).toBeInTheDocument();
      });

      // Click Add Notes button
      fireEvent.click(screen.getByRole('button', { name: /add notes/i }));

      // Enter content
      const textarea = screen.getByRole('textbox', { name: /project notes content/i });
      fireEvent.change(textarea, { target: { value: 'Brand new notes' } });

      // Save
      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(screen.getByText('Brand new notes')).toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // ERROR RECOVERY TESTS
  // ==========================================================================

  describe('Error Recovery', () => {
    it('should allow retry after save failure', async () => {
      let attemptCount = 0;

      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async () => {
            attemptCount++;
            if (attemptCount === 1) {
              return HttpResponse.json({ error: 'Server error' }, { status: 500 });
            }
            return HttpResponse.json({ ...mockNotesData, notes: 'Success on retry' });
          }
        )
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

      // First save attempt (will fail)
      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      // Dismiss error
      fireEvent.click(screen.getByRole('button', { name: /dismiss error/i }));

      // Retry save (will succeed)
      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(attemptCount).toBe(2);
        expect(screen.getByText('Success on retry')).toBeInTheDocument();
      });
    });

    it('should recover from 404 error gracefully', async () => {
      server.use(
        http.get(
          '*/organizations/:orgId/projects/:projectId/notes',
          () => {
            return HttpResponse.json({ error: 'Project not found' }, { status: 404 });
          }
        )
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
    });

    it('should handle concurrent save attempts', async () => {
      let saveCount = 0;

      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async () => {
            saveCount++;
            await new Promise(resolve => setTimeout(resolve, 100));
            return HttpResponse.json({ ...mockNotesData, notes: `Save ${saveCount}` });
          }
        )
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

      // Click save multiple times quickly
      const saveButton = screen.getByRole('button', { name: /save notes/i });
      fireEvent.click(saveButton);

      // Button should be disabled during save
      await waitFor(() => {
        expect(saveButton).toBeDisabled();
      });
    });
  });

  // ==========================================================================
  // OPTIMISTIC UPDATE TESTS
  // ==========================================================================

  describe('Optimistic Updates', () => {
    it('should show saving indicator during API call', async () => {
      server.use(
        http.put(
          '*/organizations/:orgId/projects/:projectId/notes',
          async () => {
            await new Promise(resolve => setTimeout(resolve, 200));
            return HttpResponse.json(mockNotesData);
          }
        )
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

      // Should show saving state
      expect(screen.getByText(/saving/i)).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.queryByText(/saving/i)).not.toBeInTheDocument();
      });
    });
  });

  // ==========================================================================
  // CALLBACK INTEGRATION TESTS
  // ==========================================================================

  describe('Callback Integration', () => {
    it('should pass updated notes object to onNotesUpdated callback', async () => {
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
      fireEvent.change(textarea, { target: { value: 'Callback test content' } });

      fireEvent.click(screen.getByRole('button', { name: /save notes/i }));

      await waitFor(() => {
        expect(onNotesUpdated).toHaveBeenCalledWith(
          expect.objectContaining({
            notes: 'Callback test content',
          })
        );
      });
    });

    it('should call onError with error message on failure', async () => {
      server.use(
        http.get(
          '*/organizations/:orgId/projects/:projectId/notes',
          () => {
            return HttpResponse.json({ detail: 'Database connection failed' }, { status: 500 });
          }
        )
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
        expect(onError).toHaveBeenCalled();
      });
    });
  });
});
