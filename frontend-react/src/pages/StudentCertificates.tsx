/**
 * Student Certificates Page
 *
 * BUSINESS CONTEXT:
 * Displays certificates earned by students upon course completion.
 * Students can view, download (PDF), and share their certificates.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches certificates from analytics/progress API
 * - Displays empty state when no certificates exist
 * - Provides download and share functionality
 * - Protected route (student role only)
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Spinner } from '../components/atoms/Spinner';
import { SEO } from '../components/common/SEO';
import { useAuth } from '../hooks/useAuth';
import { analyticsService } from '../services';
import styles from './StudentCertificates.module.css';

/**
 * Certificate Interface
 */
export interface Certificate {
  id: string;
  course_id: string;
  course_name: string;
  course_title: string;
  earned_date: string;
  certificate_id: string;
  pdf_url?: string;
  share_url?: string;
  completion_percentage: number;
  grade?: string;
}

/**
 * Student Certificates Page Component
 *
 * WHY THIS APPROACH:
 * - Shows achievements to motivate students
 * - Provides shareable credentials
 * - Empty state encourages course enrollment
 * - Download functionality for portfolio use
 */
export const StudentCertificates: React.FC = () => {
  const { user } = useAuth();

  // Fetch certificates from API
  const {
    data: certificates = [],
    isLoading,
    error,
  } = useQuery<Certificate[]>({
    queryKey: ['certificates', user?.id],
    queryFn: async () => {
      // TODO: Replace with actual API call when endpoint is ready
      // return await analyticsService.getStudentCertificates(user!.id);

      // Mock data for now
      return [];
    },
    enabled: !!user?.id,
  });

  /**
   * Handle certificate download
   */
  const handleDownload = async (certificate: Certificate) => {
    if (certificate.pdf_url) {
      window.open(certificate.pdf_url, '_blank');
    } else {
      // Generate PDF via API
      try {
        const response = await fetch(`/api/v1/certificates/${certificate.id}/download`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `certificate-${certificate.certificate_id}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }
      } catch (error) {
        console.error('Failed to download certificate:', error);
        alert('Failed to download certificate. Please try again.');
      }
    }
  };

  /**
   * Handle certificate share
   */
  const handleShare = (certificate: Certificate) => {
    const shareUrl = certificate.share_url || `${window.location.origin}/certificates/verify/${certificate.certificate_id}`;

    if (navigator.share) {
      navigator.share({
        title: `Certificate: ${certificate.course_name}`,
        text: `I earned a certificate in ${certificate.course_name}!`,
        url: shareUrl,
      }).catch((error) => console.log('Error sharing:', error));
    } else {
      // Fallback: Copy to clipboard
      navigator.clipboard.writeText(shareUrl).then(() => {
        alert('Certificate link copied to clipboard!');
      });
    }
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const seoElement = (
    <SEO
      title="My Certificates"
      description="View and download your earned course completion certificates"
      keywords="certificates, achievements, course completion, credentials"
    />
  );

  return (
    <DashboardLayout seo={seoElement}>
      <div className={styles.certificatesContainer}>
        <div className={styles.header}>
          <Heading level={1} className={styles.pageTitle}>
            My Certificates
          </Heading>
          <Link to="/dashboard/student" className={styles.backLink}>
            <i className="fas fa-arrow-left"></i>
            Back to Dashboard
          </Link>
        </div>

        {isLoading ? (
          <div className={styles.loadingState}>
            <Spinner size="large" />
            <p>Loading your certificates...</p>
          </div>
        ) : error ? (
          <Card className={styles.errorState}>
            <i className="fas fa-exclamation-circle"></i>
            <p>Failed to load certificates. Please refresh the page.</p>
          </Card>
        ) : certificates.length === 0 ? (
          // Empty State
          <Card className={styles.noCertificates}>
            <div className={styles.noCertificatesIcon}>
              <i className="fas fa-certificate"></i>
            </div>
            <Heading level={2} className={styles.noCertificatesTitle}>
              No Certificates Yet
            </Heading>
            <p className={styles.noCertificatesMessage}>
              Complete your courses to earn certificates and showcase your achievements!
            </p>
            <Link to="/courses/my-courses">
              <Button variant="primary" size="large">
                <i className="fas fa-book"></i>
                Browse Your Courses
              </Button>
            </Link>
          </Card>
        ) : (
          // Certificates Grid
          <div className={styles.certificatesGrid}>
            {certificates.map((certificate) => (
              <Card key={certificate.id} className={styles.certificateCard}>
                <div className={styles.certificateHeader}>
                  <div className={styles.certificateBadge}>
                    <i className="fas fa-award"></i>
                  </div>

                  <div className={styles.certificateInfo}>
                    <Heading level={3} className={styles.certificateTitle}>
                      {certificate.course_name}
                    </Heading>

                    <div className={styles.certificateDate}>
                      <i className="fas fa-calendar"></i>
                      <span>Earned on {formatDate(certificate.earned_date)}</span>
                    </div>

                    {certificate.grade && (
                      <div className={styles.certificateGrade}>
                        <i className="fas fa-star"></i>
                        <span>Final Grade: {certificate.grade}</span>
                      </div>
                    )}

                    <div className={styles.certificateId}>
                      Certificate ID: {certificate.certificate_id}
                    </div>
                  </div>

                  <div className={styles.certificateActions}>
                    <Button
                      onClick={() => handleDownload(certificate)}
                      variant="secondary"
                      size="small"
                      className={styles.downloadBtn}
                    >
                      <i className="fas fa-download"></i>
                      Download
                    </Button>

                    <Button
                      onClick={() => handleShare(certificate)}
                      variant="secondary"
                      size="small"
                      className={styles.shareBtn}
                    >
                      <i className="fas fa-share"></i>
                      Share
                    </Button>
                  </div>
                </div>

                {certificate.completion_percentage === 100 && (
                  <div className={styles.completionBadge}>
                    <i className="fas fa-check-circle"></i>
                    100% Complete
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};
