/**
 * CookieConsentBanner
 *
 * GDPR/CCPA-compliant cookie consent banner.
 *
 * Requirements:
 * - Reject All is as prominent as Accept All (GDPR Art. 7, ePrivacy Directive)
 * - Granular toggles per category (essential/analytics/preferences/marketing)
 * - No pre-ticked boxes for non-essential categories
 * - Persists consent in localStorage + calls backend consent API
 * - Re-prompts after 12 months (consent refresh)
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import styles from './CookieConsentBanner.module.css';

interface ConsentState {
  essential: true;        // Always true — cannot be toggled
  analytics: boolean;
  preferences: boolean;
  marketing: boolean;
}

interface StoredConsent {
  version: string;
  timestamp: number;
  consent: ConsentState;
}

const CONSENT_KEY = 'techuni_cookie_consent';
const CONSENT_VERSION = '1.0';
const CONSENT_MAX_AGE_MS = 365 * 24 * 60 * 60 * 1000; // 12 months

function getStoredConsent(): StoredConsent | null {
  try {
    const raw = localStorage.getItem(CONSENT_KEY);
    if (!raw) return null;
    const stored: StoredConsent = JSON.parse(raw);
    // Re-prompt if version changed or older than 12 months
    if (stored.version !== CONSENT_VERSION) return null;
    if (Date.now() - stored.timestamp > CONSENT_MAX_AGE_MS) return null;
    return stored;
  } catch {
    return null;
  }
}

function saveConsent(consent: ConsentState): void {
  const stored: StoredConsent = {
    version: CONSENT_VERSION,
    timestamp: Date.now(),
    consent,
  };
  localStorage.setItem(CONSENT_KEY, JSON.stringify(stored));
}

async function postConsentToBackend(consent: ConsentState): Promise<void> {
  try {
    await fetch('/api/v1/privacy/consent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        functional_cookies: consent.essential,
        analytics_cookies: consent.analytics,
        marketing_cookies: consent.marketing,
        preferences_cookies: consent.preferences,
        privacy_policy_version: CONSENT_VERSION,
      }),
    });
  } catch {
    // Non-blocking — local storage is the source of truth
  }
}

export const CookieConsentBanner: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [preferences, setPreferences] = useState<Omit<ConsentState, 'essential'>>({
    analytics: false,
    preferences: false,
    marketing: false,
  });

  useEffect(() => {
    const stored = getStoredConsent();
    if (!stored) {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  const handleAcceptAll = () => {
    const consent: ConsentState = {
      essential: true,
      analytics: true,
      preferences: true,
      marketing: true,
    };
    saveConsent(consent);
    postConsentToBackend(consent);
    setVisible(false);
  };

  const handleRejectAll = () => {
    const consent: ConsentState = {
      essential: true,
      analytics: false,
      preferences: false,
      marketing: false,
    };
    saveConsent(consent);
    postConsentToBackend(consent);
    setVisible(false);
  };

  const handleSavePreferences = () => {
    const consent: ConsentState = {
      essential: true,
      ...preferences,
    };
    saveConsent(consent);
    postConsentToBackend(consent);
    setVisible(false);
  };

  const toggle = (key: keyof typeof preferences) => {
    setPreferences(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className={styles.overlay} role="dialog" aria-modal="true" aria-labelledby="cookie-banner-title">
      <div className={styles.banner}>
        <div className={styles.header}>
          <span className={styles.icon}>🍪</span>
          <h2 id="cookie-banner-title" className={styles.title}>
            We use cookies
          </h2>
        </div>

        <p className={styles.description}>
          We use cookies and similar technologies to operate the platform, remember your
          preferences, and understand how you use our service. You can accept all, reject
          non-essential cookies, or manage your choices below.{' '}
          <Link to="/privacy" className={styles.privacyLink} target="_blank" rel="noopener">
            Privacy Policy
          </Link>
        </p>

        {showDetails && (
          <div className={styles.details} role="group" aria-label="Cookie category preferences">
            <div className={styles.category}>
              <div className={styles.categoryHeader}>
                <div className={styles.categoryInfo}>
                  <strong>Essential cookies</strong>
                  <span className={styles.categoryDesc}>
                    Required for login, security, and basic platform operation. Cannot be disabled.
                  </span>
                </div>
                <div className={styles.toggleWrapper}>
                  <input
                    type="checkbox"
                    id="cookie-essential"
                    checked
                    disabled
                    className={styles.toggle}
                    aria-label="Essential cookies — always active"
                  />
                  <label htmlFor="cookie-essential" className={`${styles.toggleLabel} ${styles.toggleLocked}`}>
                    Always active
                  </label>
                </div>
              </div>
            </div>

            <div className={styles.category}>
              <div className={styles.categoryHeader}>
                <div className={styles.categoryInfo}>
                  <strong>Analytics cookies</strong>
                  <span className={styles.categoryDesc}>
                    Help us understand how learners use the platform so we can improve it.
                    Lawful basis: legitimate interests. No data sold to third parties.
                  </span>
                </div>
                <div className={styles.toggleWrapper}>
                  <input
                    type="checkbox"
                    id="cookie-analytics"
                    checked={preferences.analytics}
                    onChange={() => toggle('analytics')}
                    className={styles.toggle}
                    aria-label="Analytics cookies"
                  />
                  <label htmlFor="cookie-analytics" className={styles.toggleLabel}>
                    {preferences.analytics ? 'On' : 'Off'}
                  </label>
                </div>
              </div>
            </div>

            <div className={styles.category}>
              <div className={styles.categoryHeader}>
                <div className={styles.categoryInfo}>
                  <strong>Preference cookies</strong>
                  <span className={styles.categoryDesc}>
                    Remember your settings such as language, theme, and display preferences
                    across sessions. Lawful basis: consent.
                  </span>
                </div>
                <div className={styles.toggleWrapper}>
                  <input
                    type="checkbox"
                    id="cookie-preferences"
                    checked={preferences.preferences}
                    onChange={() => toggle('preferences')}
                    className={styles.toggle}
                    aria-label="Preference cookies"
                  />
                  <label htmlFor="cookie-preferences" className={styles.toggleLabel}>
                    {preferences.preferences ? 'On' : 'Off'}
                  </label>
                </div>
              </div>
            </div>

            <div className={styles.category}>
              <div className={styles.categoryHeader}>
                <div className={styles.categoryInfo}>
                  <strong>Marketing cookies</strong>
                  <span className={styles.categoryDesc}>
                    Used to deliver relevant content and measure campaign effectiveness.
                    Lawful basis: consent. You may opt out at any time.
                  </span>
                </div>
                <div className={styles.toggleWrapper}>
                  <input
                    type="checkbox"
                    id="cookie-marketing"
                    checked={preferences.marketing}
                    onChange={() => toggle('marketing')}
                    className={styles.toggle}
                    aria-label="Marketing cookies"
                  />
                  <label htmlFor="cookie-marketing" className={styles.toggleLabel}>
                    {preferences.marketing ? 'On' : 'Off'}
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className={styles.actions}>
          {/* Reject All — equally prominent as Accept All (GDPR requirement) */}
          <button
            className={`${styles.btn} ${styles.btnReject}`}
            onClick={handleRejectAll}
            aria-label="Reject all non-essential cookies"
          >
            Reject all
          </button>

          <button
            className={`${styles.btn} ${styles.btnManage}`}
            onClick={() => setShowDetails(prev => !prev)}
            aria-expanded={showDetails}
            aria-controls="cookie-details"
          >
            {showDetails ? 'Hide options' : 'Manage options'}
          </button>

          {showDetails ? (
            <button
              className={`${styles.btn} ${styles.btnAccept}`}
              onClick={handleSavePreferences}
              aria-label="Save cookie preferences"
            >
              Save preferences
            </button>
          ) : (
            <button
              className={`${styles.btn} ${styles.btnAccept}`}
              onClick={handleAcceptAll}
              aria-label="Accept all cookies"
            >
              Accept all
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
