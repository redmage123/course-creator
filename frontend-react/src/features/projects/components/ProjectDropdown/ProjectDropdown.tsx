/**
 * Project Dropdown Component
 *
 * BUSINESS CONTEXT:
 * Provides a searchable dropdown for selecting projects within an organization.
 * Used throughout the platform where project context is needed, including:
 * - Project Builder integration
 * - Content assignment
 * - Analytics filtering
 * - Track management
 *
 * FEATURES:
 * - Searchable project list
 * - Shows project hierarchy (main project + sub-projects)
 * - Displays project status indicators
 * - Keyboard navigation support
 * - Loading and error states
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useAuth } from '../../../../hooks/useAuth';
import { apiClient } from '../../../../services/apiClient';
import styles from './ProjectDropdown.module.css';

interface Project {
  id: string;
  name: string;
  description?: string;
  organizationId: string;
  parentProjectId?: string;
  status: 'active' | 'archived' | 'draft';
  trackCount?: number;
  locationName?: string;
  createdAt: string;
}

interface ProjectDropdownProps {
  value?: string | null;
  onChange: (projectId: string | null, project: Project | null) => void;
  placeholder?: string;
  label?: string;
  required?: boolean;
  disabled?: boolean;
  showSubProjects?: boolean;
  includeArchived?: boolean;
  organizationId?: string;
  className?: string;
  error?: string;
}

/**
 * Project Dropdown Component
 *
 * WHY THIS APPROACH:
 * - Searchable for quick filtering in large project lists
 * - Hierarchical display shows project structure
 * - Keyboard accessible for a11y compliance
 * - Lazy loads projects on mount for performance
 */
export const ProjectDropdown: React.FC<ProjectDropdownProps> = ({
  value,
  onChange,
  placeholder = 'Select a project...',
  label,
  required = false,
  disabled = false,
  showSubProjects = true,
  includeArchived = false,
  organizationId,
  className = '',
  error
}) => {
  const { user } = useAuth();

  // State
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);

  // Refs
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  // Use organization ID from props or user context
  const effectiveOrgId = organizationId || user?.organizationId;

  /**
   * Fetch projects from API
   */
  const fetchProjects = useCallback(async () => {
    if (!effectiveOrgId) return;

    setIsLoading(true);
    setLoadError(null);

    try {
      const params = new URLSearchParams({
        organization_id: effectiveOrgId,
        include_sub_projects: showSubProjects.toString(),
        include_archived: includeArchived.toString()
      });

      const response = await apiClient.get<{ projects: Project[] }>(
        `/api/v1/projects?${params}`
      );

      setProjects(response.data.projects || []);
    } catch (err) {
      console.error('Failed to fetch projects:', err);
      setLoadError('Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  }, [effectiveOrgId, showSubProjects, includeArchived]);

  // Load projects on mount
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  /**
   * Get selected project
   */
  const selectedProject = useMemo(() => {
    return projects.find((p) => p.id === value) || null;
  }, [projects, value]);

  /**
   * Filter projects by search term
   */
  const filteredProjects = useMemo(() => {
    if (!searchTerm.trim()) return projects;

    const term = searchTerm.toLowerCase();
    return projects.filter(
      (project) =>
        project.name.toLowerCase().includes(term) ||
        project.description?.toLowerCase().includes(term) ||
        project.locationName?.toLowerCase().includes(term)
    );
  }, [projects, searchTerm]);

  /**
   * Group projects by parent for hierarchy display
   */
  const groupedProjects = useMemo(() => {
    const mainProjects = filteredProjects.filter((p) => !p.parentProjectId);
    const subProjectsMap = new Map<string, Project[]>();

    filteredProjects
      .filter((p) => p.parentProjectId)
      .forEach((p) => {
        const existing = subProjectsMap.get(p.parentProjectId!) || [];
        existing.push(p);
        subProjectsMap.set(p.parentProjectId!, existing);
      });

    return { mainProjects, subProjectsMap };
  }, [filteredProjects]);

  /**
   * Handle project selection
   */
  const handleSelect = useCallback(
    (project: Project) => {
      onChange(project.id, project);
      setIsOpen(false);
      setSearchTerm('');
      setHighlightedIndex(-1);
    },
    [onChange]
  );

  /**
   * Handle clear selection
   */
  const handleClear = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onChange(null, null);
      setSearchTerm('');
    },
    [onChange]
  );

  /**
   * Handle keyboard navigation
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen && (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown')) {
        e.preventDefault();
        setIsOpen(true);
        return;
      }

      if (!isOpen) return;

      const totalItems = filteredProjects.length;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setHighlightedIndex((prev) => (prev < totalItems - 1 ? prev + 1 : prev));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : prev));
          break;
        case 'Enter':
          e.preventDefault();
          if (highlightedIndex >= 0 && highlightedIndex < totalItems) {
            handleSelect(filteredProjects[highlightedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          setIsOpen(false);
          setHighlightedIndex(-1);
          break;
        case 'Tab':
          setIsOpen(false);
          break;
      }
    },
    [isOpen, filteredProjects, highlightedIndex, handleSelect]
  );

  /**
   * Scroll highlighted item into view
   */
  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('[role="option"]');
      items[highlightedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightedIndex]);

  /**
   * Close on outside click
   */
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /**
   * Get status badge color
   */
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'active':
        return '#10b981';
      case 'draft':
        return '#f59e0b';
      case 'archived':
        return '#6b7280';
      default:
        return '#9ca3af';
    }
  };

  /**
   * Render project item
   */
  const renderProjectItem = (project: Project, index: number, isSubProject = false) => {
    const isHighlighted = highlightedIndex === index;
    const isSelected = project.id === value;

    return (
      <li
        key={project.id}
        role="option"
        aria-selected={isSelected}
        className={`${styles.option} ${isSubProject ? styles.subProject : ''} ${
          isHighlighted ? styles.highlighted : ''
        } ${isSelected ? styles.selected : ''}`}
        onClick={() => handleSelect(project)}
        onMouseEnter={() => setHighlightedIndex(index)}
      >
        <div className={styles.optionContent}>
          <span className={styles.projectName}>
            {isSubProject && <span className={styles.subProjectIndicator}>↳</span>}
            {project.name}
          </span>
          {project.locationName && (
            <span className={styles.locationBadge}>{project.locationName}</span>
          )}
        </div>
        <div className={styles.optionMeta}>
          {project.trackCount !== undefined && (
            <span className={styles.trackCount}>
              {project.trackCount} {project.trackCount === 1 ? 'track' : 'tracks'}
            </span>
          )}
          <span
            className={styles.statusBadge}
            style={{ backgroundColor: getStatusColor(project.status) }}
          >
            {project.status}
          </span>
        </div>
      </li>
    );
  };

  return (
    <div
      ref={containerRef}
      className={`${styles.container} ${className} ${disabled ? styles.disabled : ''}`}
    >
      {label && (
        <label className={styles.label}>
          {label}
          {required && <span className={styles.required}>*</span>}
        </label>
      )}

      <div
        className={`${styles.trigger} ${isOpen ? styles.open : ''} ${error ? styles.error : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        tabIndex={disabled ? -1 : 0}
        role="combobox"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        aria-controls="project-listbox"
        aria-label={label || 'Select project'}
      >
        {selectedProject ? (
          <div className={styles.selectedValue}>
            <span className={styles.selectedName}>{selectedProject.name}</span>
            {selectedProject.locationName && (
              <span className={styles.selectedLocation}>{selectedProject.locationName}</span>
            )}
            {!disabled && (
              <button
                type="button"
                className={styles.clearBtn}
                onClick={handleClear}
                aria-label="Clear selection"
              >
                ✕
              </button>
            )}
          </div>
        ) : (
          <span className={styles.placeholder}>{placeholder}</span>
        )}

        <span className={styles.arrow}>{isOpen ? '▲' : '▼'}</span>
      </div>

      {isOpen && (
        <div className={styles.dropdown}>
          {/* Search input */}
          <div className={styles.searchContainer}>
            <input
              ref={inputRef}
              type="text"
              className={styles.searchInput}
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setHighlightedIndex(0);
              }}
              onKeyDown={handleKeyDown}
              autoFocus
            />
          </div>

          {/* Projects list */}
          <ul
            ref={listRef}
            id="project-listbox"
            role="listbox"
            className={styles.optionsList}
            aria-label="Projects"
          >
            {isLoading && (
              <li className={styles.loadingState}>
                <span className={styles.spinner}></span>
                Loading projects...
              </li>
            )}

            {loadError && (
              <li className={styles.errorState}>
                <span className={styles.errorIcon}>⚠️</span>
                {loadError}
                <button onClick={fetchProjects} className={styles.retryBtn}>
                  Retry
                </button>
              </li>
            )}

            {!isLoading && !loadError && filteredProjects.length === 0 && (
              <li className={styles.emptyState}>
                {searchTerm ? 'No projects match your search' : 'No projects available'}
              </li>
            )}

            {!isLoading &&
              !loadError &&
              filteredProjects.map((project, index) =>
                renderProjectItem(project, index, !!project.parentProjectId)
              )}
          </ul>
        </div>
      )}

      {error && <div className={styles.errorMessage}>{error}</div>}
    </div>
  );
};

export default ProjectDropdown;
