/**
 * Terms of Service Page
 *
 * BUSINESS CONTEXT:
 * Legal terms of service for the Course Creator Platform.
 * Required for organization registration compliance.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../components/atoms/Card';
import { Heading } from '../components/atoms/Heading';
import styles from './LegalPage.module.css';

export const TermsOfService: React.FC = () => {
  return (
    <div className={styles.legalContainer}>
      <Link to="/" className={styles.backLink}>
        <i className="fas fa-arrow-left"></i>
        Back to Homepage
      </Link>

      <Card className={styles.legalCard}>
        <Heading level="h1" className={styles.title}>
          Terms of Service
        </Heading>
        <p className={styles.lastUpdated}>Last Updated: November 30, 2025</p>

        <div className={styles.content}>
          <section className={styles.section}>
            <Heading level="h2">1. Acceptance of Terms</Heading>
            <p>
              By accessing or using the Course Creator Platform ("Service"), you agree to be bound
              by these Terms of Service ("Terms"). If you do not agree to these Terms, you may not
              use the Service.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">2. Description of Service</Heading>
            <p>
              Course Creator Platform is a comprehensive learning management system that enables
              organizations to create, manage, and deliver educational content. The Service includes:
            </p>
            <ul>
              <li>Course creation and content management tools</li>
              <li>Student enrollment and progress tracking</li>
              <li>Assessment and certification features</li>
              <li>AI-powered content generation assistance</li>
              <li>Lab environments for hands-on learning</li>
              <li>Analytics and reporting dashboards</li>
            </ul>
          </section>

          <section className={styles.section}>
            <Heading level="h2">3. User Accounts</Heading>
            <p>
              To use certain features of the Service, you must register for an account. You agree to:
            </p>
            <ul>
              <li>Provide accurate and complete information during registration</li>
              <li>Maintain the security of your account credentials</li>
              <li>Notify us immediately of any unauthorized access</li>
              <li>Accept responsibility for all activities under your account</li>
            </ul>
          </section>

          <section className={styles.section}>
            <Heading level="h2">4. Organization Responsibilities</Heading>
            <p>
              Organizations using the Service are responsible for:
            </p>
            <ul>
              <li>Managing their users and access permissions</li>
              <li>Ensuring compliance with applicable laws and regulations</li>
              <li>Maintaining appropriate content standards</li>
              <li>Protecting student data and privacy</li>
            </ul>
          </section>

          <section className={styles.section}>
            <Heading level="h2">5. Intellectual Property</Heading>
            <p>
              Content created by users remains their intellectual property. By uploading content,
              you grant us a license to host and display that content as necessary to provide
              the Service. The Course Creator Platform software, design, and branding remain
              our exclusive property.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">6. Acceptable Use</Heading>
            <p>
              You agree not to use the Service to:
            </p>
            <ul>
              <li>Upload illegal, harmful, or offensive content</li>
              <li>Violate any applicable laws or regulations</li>
              <li>Infringe on intellectual property rights</li>
              <li>Distribute malware or engage in hacking activities</li>
              <li>Harass or harm other users</li>
              <li>Attempt to gain unauthorized access to systems</li>
            </ul>
          </section>

          <section className={styles.section}>
            <Heading level="h2">7. Service Availability</Heading>
            <p>
              We strive to maintain high availability but do not guarantee uninterrupted service.
              We may modify, suspend, or discontinue features with reasonable notice when possible.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">8. Limitation of Liability</Heading>
            <p>
              To the maximum extent permitted by law, we shall not be liable for any indirect,
              incidental, special, consequential, or punitive damages arising from your use of
              the Service.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">9. Termination</Heading>
            <p>
              We may terminate or suspend access to the Service for violations of these Terms
              or for any other reason with appropriate notice. Upon termination, your right to
              use the Service ceases immediately.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">10. Changes to Terms</Heading>
            <p>
              We reserve the right to modify these Terms at any time. We will notify users of
              significant changes via email or through the Service. Continued use after changes
              constitutes acceptance of the new Terms.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">11. Contact Information</Heading>
            <p>
              For questions about these Terms, please contact us at:
            </p>
            <p className={styles.contactInfo}>
              <strong>Email:</strong> legal@coursecreator.com<br />
              <strong>Address:</strong> Course Creator Platform, Legal Department
            </p>
          </section>
        </div>

        <div className={styles.footer}>
          <Link to="/privacy" className={styles.relatedLink}>
            View Privacy Policy
          </Link>
          <Link to="/organization/register" className={styles.relatedLink}>
            Register Your Organization
          </Link>
        </div>
      </Card>
    </div>
  );
};
