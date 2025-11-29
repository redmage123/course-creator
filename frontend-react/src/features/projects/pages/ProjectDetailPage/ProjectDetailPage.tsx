/**
 * Project Detail Page
 *
 * BUSINESS CONTEXT:
 * Displays detailed information about a specific project within an organization.
 * Organization admins can view project details, manage tracks, and edit project notes.
 * This page integrates the ProjectNotesWidget for documentation management.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses React Router for URL params (orgId, projectId)
 * - Fetches project data from organization-management service
 * - Integrates ProjectNotesWidget for notes management
 * - Role-based access control (org_admin can edit)
 */

import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { SEO } from '@components/common/SEO';
import { DashboardLayout } from '@components/templates/DashboardLayout';
import { Card } from '@components/atoms/Card';
import { Button } from '@components/atoms/Button';
import { Heading } from '@components/atoms/Heading';
import { Spinner } from '@components/atoms/Spinner';
import { useAuth } from '@hooks/useAuth';
import { projectService, Project } from '@services/projectService';
import { organizationService } from '@services/organizationService';
import { ProjectNotesWidget } from '../../components/ProjectNotesWidget';
import styles from './ProjectDetailPage.module.css';

/**
 * Project Detail Page Component
 *
 * WHY THIS APPROACH:
 * - Centralized view for project management
 * - Integrates notes widget for documentation
 * - Shows project metadata and tracks
 * - Provides navigation to related resources
 */
export const ProjectDetailPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Determine if user can edit (org_admin role)
  const canEdit = user?.role === 'org_admin' || user?.role === 'site_admin';

  /**
   * Fetch organization data first
   */
  const { data: organization, isLoading: orgLoading } = useQuery({
    queryKey: ['organization', 'me'],
    queryFn: () => organizationService.getMyOrganization(),
    staleTime: 10 * 60 * 1000,
  });

  /**
   * Fetch project data
   */
  const {
    data: project,
    isLoading: projectLoading,
    error: projectError,
    refetch,
  } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectService.getProject(projectId!),
    enabled: !!projectId,
    staleTime: 5 * 60 * 1000,
  });

  const isLoading = orgLoading || projectLoading;

  /**
   * Handle notes update callback
   */
  const handleNotesUpdated = () => {
    // Optionally refetch project data or show toast
    console.log('Project notes updated successfully');
  };

  /**
   * Handle notes error callback
   */
  const handleNotesError = (error: string) => {
    console.error('Project notes error:', error);
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) return 'Not set';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  /**
   * Get status badge class
   */
  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'active':
        return styles.statusActive;
      case 'draft':
        return styles.statusDraft;
      case 'completed':
        return styles.statusCompleted;
      case 'archived':
        return styles.statusArchived;
      default:
        return '';
    }
  };

  // SEO
  const seoElement = (
    <SEO
      title={project?.name ? `${project.name} - Project Details` : 'Project Details'}
      description={project?.description || 'View and manage project details, tracks, and documentation.'}
      keywords="project details, training project, project notes, organization project"
    />
  );

  // Loading state
  if (isLoading) {
    return (
      <>
        {seoElement}
        <DashboardLayout>
          <div className={styles.projectDetailPage}>
            <div className={styles.loadingContainer}>
              <Spinner size="large" />
              <p>Loading project details...</p>
            </div>
          </div>
        </DashboardLayout>
      </>
    );
  }

  // Error state
  if (projectError || !project) {
    return (
      <>
        {seoElement}
        <DashboardLayout>
          <div className={styles.projectDetailPage}>
            <Card variant="outlined" padding="large">
              <div className={styles.errorContainer}>
                <i className="fas fa-exclamation-triangle" aria-hidden="true"></i>
                <Heading level="h2">Project Not Found</Heading>
                <p>The requested project could not be found or you don't have permission to view it.</p>
                <Button variant="primary" onClick={() => navigate('/organization/projects')}>
                  Back to Projects
                </Button>
              </div>
            </Card>
          </div>
        </DashboardLayout>
      </>
    );
  }

  return (
    <>
      {seoElement}
      <DashboardLayout>
        <div className={styles.projectDetailPage} data-testid="project-detail">
          {/* Breadcrumb Navigation */}
          <nav className={styles.breadcrumb} aria-label="Breadcrumb">
            <Link to="/dashboard/org-admin">Dashboard</Link>
            <span className={styles.breadcrumbSeparator}>/</span>
            <Link to="/organization/projects">Projects</Link>
            <span className={styles.breadcrumbSeparator}>/</span>
            <span className={styles.breadcrumbCurrent}>{project.name}</span>
          </nav>

          {/* Page Header */}
          <div className={styles.pageHeader}>
            <div className={styles.headerLeft}>
              <Heading level="h1">{project.name}</Heading>
              <span className={`${styles.statusBadge} ${getStatusClass(project.status)}`}>
                {project.status}
              </span>
            </div>
            <div className={styles.headerRight}>
              {canEdit && (
                <>
                  <Button
                    variant="secondary"
                    onClick={() => navigate(`/organization/projects/${projectId}/edit`)}
                  >
                    <i className="fas fa-edit" aria-hidden="true"></i>
                    Edit Project
                  </Button>
                  {project.status === 'draft' && (
                    <Button
                      variant="primary"
                      onClick={() => projectService.publishProject(projectId!).then(() => refetch())}
                    >
                      <i className="fas fa-rocket" aria-hidden="true"></i>
                      Publish
                    </Button>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Project Description */}
          {project.description && (
            <Card variant="outlined" padding="medium" className={styles.descriptionCard}>
              <p className={styles.description}>{project.description}</p>
            </Card>
          )}

          {/* Main Content Grid */}
          <div className={styles.contentGrid}>
            {/* Left Column - Project Info & Notes */}
            <div className={styles.mainColumn}>
              {/* Project Notes Widget */}
              {organization?.id && projectId && (
                <ProjectNotesWidget
                  organizationId={organization.id}
                  projectId={projectId}
                  canEdit={canEdit}
                  onNotesUpdated={handleNotesUpdated}
                  onError={handleNotesError}
                  defaultCollapsed={false}
                />
              )}

              {/* Tracks Section */}
              <Card variant="elevated" padding="large">
                <div className={styles.sectionHeader}>
                  <Heading level="h2">Training Tracks</Heading>
                  {canEdit && (
                    <Button
                      variant="secondary"
                      size="small"
                      onClick={() => navigate(`/organization/projects/${projectId}/tracks/new`)}
                    >
                      <i className="fas fa-plus" aria-hidden="true"></i>
                      Add Track
                    </Button>
                  )}
                </div>
                <div className={styles.tracksPlaceholder}>
                  <i className="fas fa-road" aria-hidden="true"></i>
                  <p>Tracks will be displayed here</p>
                  <Link to={`/organization/projects/${projectId}/tracks`}>
                    <Button variant="primary" size="small">
                      Manage Tracks
                    </Button>
                  </Link>
                </div>
              </Card>
            </div>

            {/* Right Column - Sidebar */}
            <div className={styles.sidebarColumn}>
              {/* Project Details Card */}
              <Card variant="outlined" padding="medium">
                <Heading level="h3">Project Details</Heading>
                <dl className={styles.detailsList}>
                  <dt>Duration</dt>
                  <dd>{project.duration_weeks ? `${project.duration_weeks} weeks` : 'Not set'}</dd>

                  <dt>Start Date</dt>
                  <dd>{formatDate(project.start_date)}</dd>

                  <dt>End Date</dt>
                  <dd>{formatDate(project.end_date)}</dd>

                  <dt>Max Participants</dt>
                  <dd>{project.max_participants || 'Unlimited'}</dd>

                  <dt>Current Participants</dt>
                  <dd>{project.current_participants || 0}</dd>

                  <dt>Created</dt>
                  <dd>{formatDate(project.created_at)}</dd>
                </dl>
              </Card>

              {/* Target Roles Card */}
              {project.target_roles && project.target_roles.length > 0 && (
                <Card variant="outlined" padding="medium">
                  <Heading level="h3">Target Roles</Heading>
                  <ul className={styles.rolesList}>
                    {project.target_roles.map((role, index) => (
                      <li key={index} className={styles.roleTag}>
                        {role}
                      </li>
                    ))}
                  </ul>
                </Card>
              )}

              {/* Quick Actions Card */}
              <Card variant="outlined" padding="medium">
                <Heading level="h3">Quick Actions</Heading>
                <div className={styles.quickActions}>
                  <Link to={`/organization/projects/${projectId}/enrollments`}>
                    <Button variant="secondary" size="small" fullWidth>
                      <i className="fas fa-users" aria-hidden="true"></i>
                      View Enrollments
                    </Button>
                  </Link>
                  <Link to={`/organization/projects/${projectId}/analytics`}>
                    <Button variant="secondary" size="small" fullWidth>
                      <i className="fas fa-chart-bar" aria-hidden="true"></i>
                      View Analytics
                    </Button>
                  </Link>
                  <Link to={`/organization/projects/${projectId}/schedule`}>
                    <Button variant="secondary" size="small" fullWidth>
                      <i className="fas fa-calendar-alt" aria-hidden="true"></i>
                      View Schedule
                    </Button>
                  </Link>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </DashboardLayout>
    </>
  );
};
