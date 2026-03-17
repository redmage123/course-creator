/**
 * DemoPage - Full-Page Demo Experience
 *
 * BUSINESS PURPOSE:
 * Provides an immersive demo experience for potential customers
 * to explore the Course Creator Platform's capabilities through
 * professionally narrated video walkthroughs.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Full viewport layout with centered demo player
 * - Background gradient matching platform branding
 * - Links to registration/contact after demo completion
 */

import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DemoPlayer } from '../components/DemoPlayer';
import styles from './DemoPage.module.css';

export const DemoPage: React.FC = () => {
  const navigate = useNavigate();
  const [demoCompleted, setDemoCompleted] = useState(false);

  const handleDemoComplete = useCallback(() => {
    setDemoCompleted(true);
  }, []);

  const handleGetStarted = useCallback(() => {
    navigate('/register');
  }, [navigate]);

  const handleContactSales = useCallback(() => {
    // Open contact form or navigate to contact page
    window.location.href = 'mailto:sales@coursecreator.com?subject=Demo%20Follow-up';
  }, []);

  return (
    <div className={styles.demoPageContainer}>
      <div className={styles.demoWrapper}>
        <DemoPlayer
          autoPlay={false}
          showSubtitles={true}
          onComplete={handleDemoComplete}
        />

        {/* Call-to-Action Section (shown after demo) */}
        {demoCompleted && (
          <div className={styles.ctaSection}>
            <h2 className={styles.ctaTitle}>Ready to Transform Your Training?</h2>
            <p className={styles.ctaDescription}>
              Join thousands of organizations using Course Creator Platform
              to build engaging, AI-powered learning experiences.
            </p>
            <div className={styles.ctaButtons}>
              <button
                className={`${styles.ctaButton} ${styles.primary}`}
                onClick={handleGetStarted}
              >
                Get Started Free
              </button>
              <button
                className={styles.ctaButton}
                onClick={handleContactSales}
              >
                Contact Sales
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Back to Home Link */}
      <div className={styles.backLink}>
        <a href="/" className={styles.link}>
          Back to Home
        </a>
      </div>
    </div>
  );
};

export default DemoPage;
