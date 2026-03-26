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
        <p className={styles.lastUpdated}>Last Updated: March 23, 2026 — Updated to reflect GDPR Arts 13/14 transparency requirements (EDPB CEF 2026)</p>

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
            <Heading level="h2">3. Processing Purposes, Lawful Basis, and Retention</Heading>
            <p>
              We process your personal data only for the purposes described below. For each
              activity we identify the lawful basis under GDPR Article 6 and the retention
              period. Where we rely on legitimate interests (Art. 6(1)(f)), you may object
              at any time — see Section 6.
            </p>

            <Heading level="h3">3.1 Account Registration &amp; Enrolment</Heading>
            <ul>
              <li><strong>Data:</strong> Name, email, username, password hash, organisation affiliation, seat assignment</li>
              <li><strong>Purpose:</strong> Create and manage your account; grant access to courses you are enrolled in</li>
              <li><strong>Lawful basis:</strong> Performance of contract (Art. 6(1)(b))</li>
              <li><strong>Retention:</strong> Account data retained for the life of the account + 30 days after deletion; seat-assignment records retained for 3 years for audit purposes</li>
            </ul>

            <Heading level="h3">3.2 Learning Analytics</Heading>
            <ul>
              <li><strong>Data:</strong> Course progress, module completion timestamps, assessment scores, time-on-task, login frequency</li>
              <li><strong>Purpose:</strong> Track learner progress; generate reports for organisation administrators and instructors; improve course quality</li>
              <li><strong>Lawful basis:</strong> Performance of contract (Art. 6(1)(b)) for progress tracking; legitimate interests (Art. 6(1)(f)) for aggregate platform improvement analytics</li>
              <li><strong>Retention:</strong> Individual learning records retained for 3 years after course completion; aggregate anonymised analytics retained indefinitely</li>
            </ul>

            <Heading level="h3">3.3 AI-Powered Features</Heading>
            <ul>
              <li><strong>Data:</strong> Queries submitted to the AI assistant; course content you interact with; optional code submitted in lab environments</li>
              <li><strong>Purpose:</strong> Generate personalised course content (course-generator service); provide in-platform AI assistant responses; power semantic search (RAG service)</li>
              <li><strong>Lawful basis:</strong> Performance of contract (Art. 6(1)(b)) — AI features are a core service component</li>
              <li><strong>Retention:</strong> AI assistant conversation history is session-scoped and not stored server-side beyond your session. Course generation inputs are retained for 90 days for quality assurance</li>
              <li><strong>Note:</strong> AI features are powered by third-party large language model providers (see Section 10 — Subprocessors). Your queries may be transmitted to these providers solely to fulfil your request</li>
            </ul>

            <Heading level="h3">3.4 Service Communications</Heading>
            <ul>
              <li><strong>Data:</strong> Email address, notification preferences</li>
              <li><strong>Purpose:</strong> Send course invitations, password resets, enrolment confirmations, and service-critical notifications</li>
              <li><strong>Lawful basis:</strong> Performance of contract (Art. 6(1)(b)) for transactional emails; consent (Art. 6(1)(a)) for marketing/newsletter communications</li>
              <li><strong>Retention:</strong> Email logs retained for 90 days; newsletter subscription preference retained until you unsubscribe</li>
            </ul>

            <Heading level="h3">3.5 Payment Processing</Heading>
            <ul>
              <li><strong>Data:</strong> Subscription tier, billing contact details (name, email, billing address). Payment card data is handled exclusively by our payment processor — we do not store card numbers</li>
              <li><strong>Purpose:</strong> Manage subscriptions, process billing, issue receipts</li>
              <li><strong>Lawful basis:</strong> Performance of contract (Art. 6(1)(b)); legal obligation for tax/accounting records (Art. 6(1)(c))</li>
              <li><strong>Retention:</strong> Billing records retained for 7 years for tax compliance</li>
            </ul>

            <Heading level="h3">3.6 Security &amp; Fraud Prevention</Heading>
            <ul>
              <li><strong>Data:</strong> IP address, access logs, device identifiers, session tokens</li>
              <li><strong>Purpose:</strong> Detect and prevent unauthorised access, abuse, and fraud</li>
              <li><strong>Lawful basis:</strong> Legitimate interests (Art. 6(1)(f)) — security of the platform and its users</li>
              <li><strong>Retention:</strong> Security logs retained for 12 months</li>
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
              your own, including the United States. We ensure appropriate safeguards are in
              place for such transfers, including Standard Contractual Clauses (SCCs) adopted
              by the European Commission under GDPR Article 46(2)(c), supplemented by Transfer
              Impact Assessments (TIAs) where required by the EDPB.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">10. Subprocessors</Heading>
            <p>
              We engage the following third-party companies ("subprocessors") to provide
              services that involve processing personal data on our behalf. All subprocessors
              are bound by data processing agreements and must handle data only as instructed
              by us.
            </p>
            <table className={styles.subprocessorTable}>
              <thead>
                <tr>
                  <th>Subprocessor</th>
                  <th>Country</th>
                  <th>Purpose</th>
                  <th>Data categories</th>
                  <th>Transfer mechanism</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Anthropic (Claude API)</strong></td>
                  <td>USA</td>
                  <td>AI course generation; bug-fix assistance</td>
                  <td>Course content prompts; code snippets</td>
                  <td>SCCs + TIA</td>
                </tr>
                <tr>
                  <td><strong>OpenAI</strong></td>
                  <td>USA</td>
                  <td>Embeddings; AI assistant responses; course generation</td>
                  <td>Query text; course content prompts</td>
                  <td>SCCs + TIA</td>
                </tr>
                <tr>
                  <td><strong>Stripe</strong></td>
                  <td>USA</td>
                  <td>Payment processing; subscription billing</td>
                  <td>Billing name, email, address; transaction records</td>
                  <td>SCCs + TIA</td>
                </tr>
                <tr>
                  <td><strong>Mailgun (Sinch)</strong></td>
                  <td>USA</td>
                  <td>Transactional email delivery</td>
                  <td>Email address; email content</td>
                  <td>SCCs + TIA</td>
                </tr>
                <tr>
                  <td><strong>Mistral AI</strong></td>
                  <td>France (EU)</td>
                  <td>Alternative LLM provider for course generation</td>
                  <td>Course content prompts</td>
                  <td>No transfer (EU-based)</td>
                </tr>
                <tr>
                  <td><strong>Microsoft (Teams)</strong></td>
                  <td>USA</td>
                  <td>Optional video conferencing integration</td>
                  <td>Meeting metadata; participant emails (if integration enabled by org admin)</td>
                  <td>SCCs + TIA</td>
                </tr>
                <tr>
                  <td><strong>Zoom Video Communications</strong></td>
                  <td>USA</td>
                  <td>Optional video conferencing integration</td>
                  <td>Meeting metadata; participant emails (if integration enabled by org admin)</td>
                  <td>SCCs + TIA</td>
                </tr>
                <tr>
                  <td><strong>Slack (Salesforce)</strong></td>
                  <td>USA</td>
                  <td>Optional team messaging integration</td>
                  <td>Email addresses; channel metadata (if integration enabled by org admin)</td>
                  <td>SCCs + TIA</td>
                </tr>
              </tbody>
            </table>
            <p>
              Organisation integrations (Slack, Zoom, Teams) are opt-in and enabled only by
              your organisation administrator. If your organisation has not enabled these
              integrations, no data is shared with those providers.
            </p>
            <p>
              We do not use DeepSeek or any Chinese-domiciled AI providers for processing
              personal data of EU data subjects.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">11. Children's Privacy</Heading>
            <p>
              The Service is not intended for children under 13. We do not knowingly collect
              personal information from children under 13. If we learn we have collected such
              information, we will delete it promptly.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">12. Changes to This Policy</Heading>
            <p>
              We may update this Privacy Policy periodically. We will notify you of significant
              changes via email or through the Service. Your continued use after changes
              constitutes acceptance.
            </p>
          </section>

          <section className={styles.section}>
            <Heading level="h2">13. Contact Us</Heading>
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
