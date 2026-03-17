/**
 * Privacy Policy Page
 *
 * BUSINESS CONTEXT:
 * Privacy policy for the Course Creator Platform.
 * Required for GDPR, CCPA, and other privacy compliance.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../components/atoms/Card';
import { Heading } from '../components/atoms/Heading';
import styles from './LegalPage.module.css';

export const PrivacyPolicy: React.FC = () => {
  return (
    <div className={styles.legalContainer}>
      <Link to="/" className={styles.backLink}>
        <i className="fas fa-arrow-left"></i>
        Back to Homepage
      </Link>

      <Card className={styles.legalCard}>
        <Heading level="h1" className={styles.title}>
          Privacy Policy
        </Heading>
        <p className={styles.lastUpdated}>Last Updated: November 30, 2025</p>

        <div className={styles.content}>
          <section className={styles.section}>
            <Heading level="h2">1. Introduction</Heading>
            <p>
              Course Creator Platform ("we", "us", "our") is committed to protecting your privacy.
              This Privacy Policy explains how we collect, use, disclose, and safeguard your
              information when you use our Service.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">2. Information We Collect</Heading>

            <Heading level="h3">2.1 Information You Provide</Heading>
            <ul>
              <li><strong>Account Information:</strong> Name, email, username, password, phone number</li>
              <li><strong>Organization Information:</strong> Organization name, address, domain, contact details</li>
              <li><strong>Profile Information:</strong> Job title, bio, profile picture</li>
              <li><strong>Content:</strong> Courses, materials, assessments you create or upload</li>
              <li><strong>Communications:</strong> Messages, feedback, support requests</li>
            </ul>

            <Heading level="h3">2.2 Information Collected Automatically</Heading>
            <ul>
              <li><strong>Usage Data:</strong> Pages visited, features used, time spent</li>
              <li><strong>Device Information:</strong> Browser type, operating system, device identifiers</li>
              <li><strong>Log Data:</strong> IP address, access times, referring URLs</li>
              <li><strong>Learning Analytics:</strong> Course progress, assessment scores, completion rates</li>
            </ul>
          </section>

          <section className={styles.section}>
            <Heading level="h2">3. How We Use Your Information</Heading>
            <p>We use collected information to:</p>
            <ul>
              <li>Provide, maintain, and improve the Service</li>
              <li>Process registrations and manage accounts</li>
              <li>Personalize your learning experience</li>
              <li>Generate analytics and reports for organizations</li>
              <li>Send service-related communications</li>
              <li>Provide customer support</li>
              <li>Ensure security and prevent fraud</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section className={styles.section}>
            <Heading level="h2">4. Information Sharing</Heading>
            <p>We may share your information with:</p>
            <ul>
              <li><strong>Your Organization:</strong> Administrators can view member data and learning progress</li>
              <li><strong>Instructors:</strong> Can view enrolled students' progress and submissions</li>
              <li><strong>Service Providers:</strong> Third parties who assist in operating the Service</li>
              <li><strong>Legal Requirements:</strong> When required by law or to protect rights</li>
            </ul>
            <p>We do not sell your personal information to third parties.</p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">5. Data Security</Heading>
            <p>
              We implement industry-standard security measures to protect your information:
            </p>
            <ul>
              <li>Encryption in transit (TLS/SSL) and at rest</li>
              <li>Secure authentication and access controls</li>
              <li>Regular security audits and monitoring</li>
              <li>Employee training on data protection</li>
            </ul>
          </section>

          <section className={styles.section}>
            <Heading level="h2">6. Your Rights (GDPR/CCPA)</Heading>
            <p>Depending on your location, you may have the right to:</p>
            <ul>
              <li><strong>Access:</strong> Request a copy of your personal data</li>
              <li><strong>Rectification:</strong> Correct inaccurate or incomplete data</li>
              <li><strong>Erasure:</strong> Request deletion of your data</li>
              <li><strong>Portability:</strong> Receive your data in a portable format</li>
              <li><strong>Restriction:</strong> Limit how we process your data</li>
              <li><strong>Objection:</strong> Object to certain processing activities</li>
              <li><strong>Withdraw Consent:</strong> Withdraw previously given consent</li>
            </ul>
            <p>
              To exercise these rights, contact us at privacy@coursecreator.com or use
              the privacy settings in your account dashboard.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">7. Data Retention</Heading>
            <p>
              We retain your information for as long as your account is active or as needed
              to provide the Service. When you delete your account, we will delete or anonymize
              your personal data within 30 days, except where retention is required by law.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">8. Cookies and Tracking</Heading>
            <p>
              We use cookies and similar technologies to improve your experience:
            </p>
            <ul>
              <li><strong>Essential Cookies:</strong> Required for basic functionality</li>
              <li><strong>Analytics Cookies:</strong> Help us understand usage patterns</li>
              <li><strong>Preference Cookies:</strong> Remember your settings</li>
            </ul>
            <p>
              You can control cookies through your browser settings. Note that disabling
              certain cookies may limit functionality.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">9. International Data Transfers</Heading>
            <p>
              Your information may be transferred to and processed in countries other than
              your own. We ensure appropriate safeguards are in place for such transfers,
              including Standard Contractual Clauses where required.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">10. Children's Privacy</Heading>
            <p>
              The Service is not intended for children under 13. We do not knowingly collect
              personal information from children under 13. If we learn we have collected such
              information, we will delete it promptly.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">11. Changes to This Policy</Heading>
            <p>
              We may update this Privacy Policy periodically. We will notify you of significant
              changes via email or through the Service. Your continued use after changes
              constitutes acceptance.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">12. Contact Us</Heading>
            <p>
              For privacy-related questions or to exercise your rights:
            </p>
            <p className={styles.contactInfo}>
              <strong>Email:</strong> privacy@coursecreator.com<br />
              <strong>Data Protection Officer:</strong> dpo@coursecreator.com<br />
              <strong>Address:</strong> Course Creator Platform, Privacy Team
            </p>
          </section>
        </div>

        <div className={styles.footer}>
          <Link to="/terms" className={styles.relatedLink}>
            View Terms of Service
          </Link>
          <Link to="/organization/register" className={styles.relatedLink}>
            Register Your Organization
          </Link>
        </div>
      </Card>
    </div>
  );
};
