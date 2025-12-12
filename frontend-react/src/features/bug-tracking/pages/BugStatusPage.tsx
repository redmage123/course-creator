/**
 * Bug Status Page
 *
 * BUSINESS CONTEXT:
 * Displays detailed status of a bug report including:
 * - Bug information and description
 * - Analysis results from Claude AI
 * - Fix attempt details and PR link
 * - Progress timeline
 *
 * TECHNICAL IMPLEMENTATION:
 * Fetches bug details from API and renders analysis/fix information.
 * Uses polling to update status for in-progress bugs.
 */

import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { bugService, BugDetail, BugStatus as BugStatusType } from '../../../services/bugService';
import { Button } from '../../../components/atoms/Button';
import { Spinner } from '../../../components/atoms/Spinner';
import styles from './BugStatusPage.module.css';

// ============================================================
// Helper Functions
// ============================================================

/**
 * Get status badge class based on bug status
 */
const getStatusBadgeClass = (status: BugStatusType): string => {
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

/**
 * Get severity badge class
 */
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

/**
 * Format status for display
 */
const formatStatus = (status: BugStatusType): string => {
  return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

/**
 * Format date for display
 */
const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};

// ============================================================
// Component Implementation
// ============================================================

/**
 * Bug Status Page Component
 */
export const BugStatusPage: React.FC = () => {
  const { bugId } = useParams<{ bugId: string }>();
  const [bugDetail, setBugDetail] = useState<BugDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requestingReanalysis, setRequestingReanalysis] = useState(false);

  /**
   * Fetch bug details
   */
  const fetchBugDetails = useCallback(async () => {
    if (!bugId) return;

    try {
      const details = await bugService.getBug(bugId);
      setBugDetail(details);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bug details');
    } finally {
      setLoading(false);
    }
  }, [bugId]);

  /**
   * Initial fetch and polling for in-progress bugs
   */
  useEffect(() => {
    fetchBugDetails();

    // Poll for updates if bug is being processed
    const pollInterval = setInterval(() => {
      if (bugDetail?.bug.status === 'analyzing' || bugDetail?.bug.status === 'fixing') {
        fetchBugDetails();
      }
    }, 5000);

    return () => clearInterval(pollInterval);
  }, [fetchBugDetails, bugDetail?.bug.status]);

  /**
   * Handle re-analysis request
   */
  const handleReanalysis = async () => {
    if (!bugId) return;

    setRequestingReanalysis(true);
    try {
      await bugService.requestReanalysis(bugId);
      fetchBugDetails();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to request re-analysis');
    } finally {
      setRequestingReanalysis(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="large" />
        <p>Loading bug details...</p>
      </div>
    );
  }

  // Error state
  if (error || !bugDetail) {
    return (
      <div className={styles.errorContainer}>
        <h2>Error</h2>
        <p>{error || 'Bug not found'}</p>
        <Link to="/bugs/submit">
          <Button variant="primary">Submit New Bug</Button>
        </Link>
      </div>
    );
  }

  const { bug, analysis, fix_attempt } = bugDetail;

  return (
    <div className={styles.page}>
      {/* Breadcrumb */}
      <div className={styles.breadcrumb}>
        <Link to="/dashboard">Dashboard</Link>
        <span className={styles.separator}>/</span>
        <Link to="/bugs/my">My Bugs</Link>
        <span className={styles.separator}>/</span>
        <span>{bug.id.slice(0, 8)}...</span>
      </div>

      {/* Bug Header */}
      <div className={styles.header}>
        <div className={styles.headerTop}>
          <span className={`${styles.statusBadge} ${getStatusBadgeClass(bug.status)}`}>
            {formatStatus(bug.status)}
          </span>
          <span className={`${styles.severityBadge} ${getSeverityBadgeClass(bug.severity)}`}>
            {bug.severity.toUpperCase()}
          </span>
        </div>
        <h1 className={styles.title}>{bug.title}</h1>
        <div className={styles.meta}>
          <span>ID: <code>{bug.id}</code></span>
          <span>Submitted: {formatDate(bug.created_at)}</span>
          {bug.affected_component && <span>Component: {bug.affected_component}</span>}
        </div>
      </div>

      {/* Bug Description */}
      <section className={styles.section}>
        <h2>Description</h2>
        <p className={styles.description}>{bug.description}</p>
      </section>

      {/* Steps to Reproduce */}
      {bug.steps_to_reproduce && (
        <section className={styles.section}>
          <h2>Steps to Reproduce</h2>
          <pre className={styles.preformatted}>{bug.steps_to_reproduce}</pre>
        </section>
      )}

      {/* Expected vs Actual */}
      {(bug.expected_behavior || bug.actual_behavior) && (
        <section className={styles.section}>
          <div className={styles.twoColumn}>
            {bug.expected_behavior && (
              <div>
                <h3>Expected Behavior</h3>
                <p>{bug.expected_behavior}</p>
              </div>
            )}
            {bug.actual_behavior && (
              <div>
                <h3>Actual Behavior</h3>
                <p>{bug.actual_behavior}</p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Analysis Results */}
      {analysis && (
        <section className={styles.analysisSection}>
          <div className={styles.sectionHeader}>
            <h2>AI Analysis</h2>
            <div className={styles.confidenceMeter}>
              <span className={styles.confidenceLabel}>Confidence:</span>
              <span className={styles.confidenceScore}>{Math.round(analysis.confidence_score)}%</span>
              <div className={styles.confidenceBar}>
                <div
                  className={styles.confidenceFill}
                  style={{ width: `${analysis.confidence_score}%` }}
                />
              </div>
            </div>
          </div>

          {/* Root Cause */}
          <div className={styles.analysisBlock}>
            <h3>Root Cause Analysis</h3>
            <div className={styles.analysisContent}>
              {analysis.root_cause_analysis}
            </div>
          </div>

          {/* Suggested Fix */}
          <div className={styles.analysisBlock}>
            <h3>Suggested Fix</h3>
            <div className={styles.codeBlock}>
              {analysis.suggested_fix}
            </div>
          </div>

          {/* Affected Files */}
          <div className={styles.analysisBlock}>
            <h3>Affected Files</h3>
            <ul className={styles.fileList}>
              {analysis.affected_files.map((file, index) => (
                <li key={index} className={styles.fileItem}>
                  <span className={styles.fileIcon}>📄</span>
                  <code>{file}</code>
                </li>
              ))}
            </ul>
          </div>

          {/* Analysis Meta */}
          <div className={styles.analysisMeta}>
            <span>Complexity: {analysis.complexity_estimate}</span>
            <span>Model: {analysis.claude_model_used}</span>
            <span>Tokens: {analysis.tokens_used.toLocaleString()}</span>
            {analysis.analysis_completed_at && (
              <span>Completed: {formatDate(analysis.analysis_completed_at)}</span>
            )}
          </div>
        </section>
      )}

      {/* Fix Attempt / PR */}
      {fix_attempt && (
        <section className={styles.fixSection}>
          <h2>Fix Attempt</h2>

          {fix_attempt.pr_url ? (
            <div className={styles.prSuccess}>
              <div className={styles.prHeader}>
                <span className={styles.prIcon}>✅</span>
                <h3>Pull Request Created</h3>
              </div>
              <p>An automated fix has been generated and submitted for review.</p>
              <a
                href={fix_attempt.pr_url}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.prLink}
              >
                View PR #{fix_attempt.pr_number} on GitHub
              </a>
              <div className={styles.prStats}>
                <span>📝 {fix_attempt.files_changed.length} files</span>
                <span>➕ {fix_attempt.lines_added} added</span>
                <span>➖ {fix_attempt.lines_removed} removed</span>
                <span>✅ {fix_attempt.tests_passed} tests passed</span>
                {fix_attempt.tests_failed > 0 && (
                  <span className={styles.testsFailed}>❌ {fix_attempt.tests_failed} tests failed</span>
                )}
              </div>
            </div>
          ) : fix_attempt.error_message ? (
            <div className={styles.fixError}>
              <h3>⚠️ Fix Generation Failed</h3>
              <p>{fix_attempt.error_message}</p>
              <p className={styles.fixErrorHint}>
                A manual fix may be required. The analysis above provides guidance for resolving this issue.
              </p>
            </div>
          ) : fix_attempt.status === 'in_progress' ? (
            <div className={styles.fixInProgress}>
              <Spinner size="small" />
              <span>Generating fix...</span>
            </div>
          ) : null}
        </section>
      )}

      {/* Actions */}
      <section className={styles.actions}>
        {bug.status === 'analysis_complete' && !fix_attempt && (
          <Button
            variant="primary"
            onClick={handleReanalysis}
            disabled={requestingReanalysis}
          >
            {requestingReanalysis ? 'Requesting...' : 'Request Re-Analysis'}
          </Button>
        )}
        <Link to="/bugs/submit">
          <Button variant="secondary">Submit Another Bug</Button>
        </Link>
        <Link to="/bugs/my">
          <Button variant="outline">View All My Bugs</Button>
        </Link>
      </section>
    </div>
  );
};

export default BugStatusPage;
