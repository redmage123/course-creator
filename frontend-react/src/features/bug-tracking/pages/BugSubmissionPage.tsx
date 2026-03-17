/**
 * Bug Submission Page
 *
 * BUSINESS CONTEXT:
 * Page wrapper for the bug submission form.
 * Provides context and navigation for bug reporting.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses DashboardLayout for consistent navigation.
 * Accessible to all authenticated users.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { BugSubmissionForm } from '../components/BugSubmissionForm';
import styles from './BugSubmissionPage.module.css';

/**
 * Bug Submission Page Component
 *
 * Features:
 * - Page header with breadcrumb navigation
 * - Bug submission form
 * - Link to view submitted bugs
 */
export const BugSubmissionPage: React.FC = () => {
  return (
    <div className={styles.page}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.breadcrumb}>
          <Link to="/dashboard">Dashboard</Link>
          <span className={styles.separator}>/</span>
          <span>Report Bug</span>
        </div>
        <div className={styles.titleRow}>
          <h1 className={styles.title}>Report a Bug</h1>
          <Link to="/bugs/my" className={styles.viewBugsLink}>
            View My Bug Reports
          </Link>
        </div>
        <p className={styles.subtitle}>
          Help us improve the platform by reporting bugs. Our AI system will analyze your report
          and attempt to automatically generate a fix.
        </p>
      </div>

      {/* Form Container */}
      <div className={styles.content}>
        <BugSubmissionForm />
      </div>
    </div>
  );
};

export default BugSubmissionPage;
