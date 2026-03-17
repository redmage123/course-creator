/**
 * Bug List Page
 *
 * BUSINESS CONTEXT:
 * Displays a list of bug reports submitted by the current user.
 * Shows status, severity, and quick access to details.
 *
 * TECHNICAL IMPLEMENTATION:
 * Fetches user's bugs from API with pagination and filtering.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { bugService, BugReport, BugStatus, BugSeverity, BugFilters } from '../../../services/bugService';
import { Button } from '../../../components/atoms/Button';
import { Select } from '../../../components/atoms/Select';
import { Spinner } from '../../../components/atoms/Spinner';
import styles from './BugListPage.module.css';

// ============================================================
// Helper Functions
// ============================================================

const getStatusBadgeClass = (status: BugStatus): string => {
  switch (status) {
    case 'submitted':
      return styles.statusSubmitted;
    case 'analyzing':
      return styles.statusAnalyzing;
    case 'analysis_complete':
      return styles.statusAnalysisComplete;
    case 'fixing':
      return styles.statusFixing;
    case 'fix_ready':
    case 'pr_opened':
      return styles.statusPrOpened;
    case 'resolved':
      return styles.statusResolved;
    case 'closed':
    case 'wont_fix':
      return styles.statusClosed;
    default:
      return '';
  }
};

const getSeverityBadgeClass = (severity: string): string => {
  switch (severity) {
    case 'critical':
      return styles.severityCritical;
    case 'high':
      return styles.severityHigh;
    case 'medium':
      return styles.severityMedium;
    case 'low':
      return styles.severityLow;
    default:
      return '';
  }
};

const formatStatus = (status: BugStatus): string => {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString();
};

// ============================================================
// Component Implementation
// ============================================================

/**
 * Bug List Page Component
 */
export const BugListPage: React.FC = () => {
  const [bugs, setBugs] = useState<BugReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<BugFilters>({});
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [total, setTotal] = useState(0);

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'submitted', label: 'Submitted' },
    { value: 'analyzing', label: 'Analyzing' },
    { value: 'analysis_complete', label: 'Analysis Complete' },
    { value: 'fixing', label: 'Fixing' },
    { value: 'pr_opened', label: 'PR Opened' },
    { value: 'resolved', label: 'Resolved' },
    { value: 'closed', label: 'Closed' },
  ];

  const severityOptions = [
    { value: '', label: 'All Severities' },
    { value: 'critical', label: 'Critical' },
    { value: 'high', label: 'High' },
    { value: 'medium', label: 'Medium' },
    { value: 'low', label: 'Low' },
  ];

  /**
   * Fetch bugs
   */
  const fetchBugs = useCallback(async () => {
    setLoading(true);
    try {
      const response = await bugService.listMyBugs({
        ...filters,
        page,
        limit: 10,
      });
      setBugs(response.bugs);
      setHasMore(response.has_more);
      setTotal(response.total);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bugs');
    } finally {
      setLoading(false);
    }
  }, [filters, page]);

  useEffect(() => {
    fetchBugs();
  }, [fetchBugs]);

  /**
   * Handle filter change
   */
  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value || undefined,
    }));
    setPage(1); // Reset to first page on filter change
  };

  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.breadcrumb}>
          <Link to="/dashboard">Dashboard</Link>
          <span className={styles.separator}>/</span>
          <span>My Bug Reports</span>
        </div>
        <div className={styles.titleRow}>
          <h1 className={styles.title}>My Bug Reports</h1>
          <Link to="/bugs/submit">
            <Button variant="primary">Report New Bug</Button>
          </Link>
        </div>
        <p className={styles.subtitle}>
          Track the status of your submitted bug reports
        </p>
      </div>

      {/* Filters */}
      <div className={styles.filters}>
        <div className={styles.filterGroup}>
          <label htmlFor="status-filter">Status</label>
          <Select
            id="status-filter"
            name="status"
            value={filters.status || ''}
            onChange={handleFilterChange}
            options={statusOptions}
          />
        </div>
        <div className={styles.filterGroup}>
          <label htmlFor="severity-filter">Severity</label>
          <Select
            id="severity-filter"
            name="severity"
            value={filters.severity || ''}
            onChange={handleFilterChange}
            options={severityOptions}
          />
        </div>
        <div className={styles.filterInfo}>
          Showing {bugs.length} of {total} bugs
        </div>
      </div>

      {/* Bug List */}
      {loading ? (
        <div className={styles.loadingContainer}>
          <Spinner size="large" />
        </div>
      ) : error ? (
        <div className={styles.errorContainer}>
          <p>{error}</p>
          <Button onClick={fetchBugs}>Retry</Button>
        </div>
      ) : bugs.length === 0 ? (
        <div className={styles.emptyState}>
          <h3>No Bug Reports</h3>
          <p>You haven&apos;t submitted any bug reports yet.</p>
          <Link to="/bugs/submit">
            <Button variant="primary">Submit Your First Bug</Button>
          </Link>
        </div>
      ) : (
        <>
          <div className={styles.bugList}>
            {bugs.map(bug => (
              <Link
                key={bug.id}
                to={`/bugs/${bug.id}`}
                className={styles.bugCard}
              >
                <div className={styles.bugCardHeader}>
                  <span className={`${styles.statusBadge} ${getStatusBadgeClass(bug.status)}`}>
                    {formatStatus(bug.status)}
                  </span>
                  <span className={`${styles.severityBadge} ${getSeverityBadgeClass(bug.severity)}`}>
                    {bug.severity.toUpperCase()}
                  </span>
                </div>
                <h3 className={styles.bugTitle}>{bug.title}</h3>
                <p className={styles.bugDescription}>
                  {bug.description.length > 150
                    ? `${bug.description.slice(0, 150)}...`
                    : bug.description}
                </p>
                <div className={styles.bugMeta}>
                  <span>ID: {bug.id.slice(0, 8)}...</span>
                  <span>{formatDate(bug.created_at)}</span>
                  {bug.affected_component && <span>{bug.affected_component}</span>}
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          <div className={styles.pagination}>
            <Button
              variant="outline"
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
            >
              Previous
            </Button>
            <span className={styles.pageInfo}>Page {page}</span>
            <Button
              variant="outline"
              disabled={!hasMore}
              onClick={() => setPage(p => p + 1)}
            >
              Next
            </Button>
          </div>
        </>
      )}
    </div>
  );
};

export default BugListPage;
