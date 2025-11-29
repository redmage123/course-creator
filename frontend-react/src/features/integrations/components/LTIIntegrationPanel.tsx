/**
 * LTIIntegrationPanel Component
 *
 * What: LTI 1.3 platform registration and management interface
 * Where: Used in IntegrationsSettings page for LMS integration
 * Why: Enables connecting external LMS platforms (Canvas, Moodle, Blackboard)
 *
 * BUSINESS CONTEXT:
 * LTI (Learning Tools Interoperability) integration allows external LMS platforms
 * to launch into our platform as an LTI tool. This enables:
 * - Deep linking for content selection
 * - Grade passback to external gradebook
 * - Roster synchronization
 * - Single sign-on for seamless user experience
 *
 * @module features/integrations/components/LTIIntegrationPanel
 */

import React, { useState } from 'react';
import { integrationsService } from '../../../services/integrationsService';
import type { LTIPlatform, CreateLTIPlatformRequest } from '../../../services/integrationsService';
import IntegrationStatusBadge from './IntegrationStatusBadge';
import styles from './LTIIntegrationPanel.module.css';

export interface LTIIntegrationPanelProps {
  /** Organization ID */
  organizationId: string;
  /** Existing LTI platforms */
  platforms: LTIPlatform[];
  /** Refresh callback after changes */
  onRefresh: () => void;
}

/**
 * LTIIntegrationPanel Component
 *
 * WHY THIS APPROACH:
 * - Form-based LTI platform registration
 * - Platform list with verification status
 * - Test connection functionality
 * - Clear instructions for LMS admin configuration
 * - Comprehensive field validation with helpful error messages
 */
export const LTIIntegrationPanel: React.FC<LTIIntegrationPanelProps> = ({
  organizationId,
  platforms,
  onRefresh,
}) => {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState<CreateLTIPlatformRequest>({
    platform_name: '',
    issuer: '',
    client_id: '',
    auth_login_url: '',
    auth_token_url: '',
    jwks_url: '',
    deployment_id: '',
    scopes: [],
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  /**
   * Validate form data
   *
   * What: Client-side validation of LTI configuration
   * Where: Called before form submission
   * Why: Provides immediate feedback on invalid URLs or missing fields
   */
  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.platform_name.trim()) {
      errors.platform_name = 'Platform name is required';
    }

    if (!formData.issuer.trim()) {
      errors.issuer = 'Issuer URL is required';
    } else if (!formData.issuer.startsWith('http')) {
      errors.issuer = 'Issuer must be a valid URL';
    }

    if (!formData.client_id.trim()) {
      errors.client_id = 'Client ID is required';
    }

    if (!formData.auth_login_url.trim()) {
      errors.auth_login_url = 'Auth login URL is required';
    } else if (!formData.auth_login_url.startsWith('http')) {
      errors.auth_login_url = 'Auth login URL must be a valid URL';
    }

    if (!formData.auth_token_url.trim()) {
      errors.auth_token_url = 'Auth token URL is required';
    } else if (!formData.auth_token_url.startsWith('http')) {
      errors.auth_token_url = 'Auth token URL must be a valid URL';
    }

    if (!formData.jwks_url.trim()) {
      errors.jwks_url = 'JWKS URL is required';
    } else if (!formData.jwks_url.startsWith('http')) {
      errors.jwks_url = 'JWKS URL must be a valid URL';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setSubmitting(true);
    setSuccessMessage('');

    try {
      await integrationsService.registerLTIPlatform(organizationId, formData);
      setSuccessMessage('LTI platform registered successfully!');
      setShowAddForm(false);
      setFormData({
        platform_name: '',
        issuer: '',
        client_id: '',
        auth_login_url: '',
        auth_token_url: '',
        jwks_url: '',
        deployment_id: '',
        scopes: [],
      });
      setFormErrors({});
      onRefresh();
    } catch (error: any) {
      setFormErrors({
        submit: error.response?.data?.message || 'Failed to register LTI platform',
      });
    } finally {
      setSubmitting(false);
    }
  };

  /**
   * Handle platform deactivation
   */
  const handleDeactivate = async (platformId: string) => {
    if (!window.confirm('Are you sure you want to deactivate this LTI platform?')) {
      return;
    }

    try {
      await integrationsService.deactivateLTIPlatform(platformId);
      setSuccessMessage('LTI platform deactivated successfully!');
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to deactivate LTI platform');
    }
  };

  /**
   * Handle platform verification
   */
  const handleVerify = async (platformId: string) => {
    try {
      await integrationsService.verifyLTIPlatform(platformId);
      setSuccessMessage('LTI platform verified successfully!');
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to verify LTI platform');
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>LTI 1.3 Integration</h2>
          <p className={styles.description}>
            Connect external LMS platforms (Canvas, Moodle, Blackboard) for seamless integration
          </p>
        </div>
        <button
          className={styles.addButton}
          onClick={() => setShowAddForm(!showAddForm)}
          disabled={submitting}
        >
          {showAddForm ? 'Cancel' : '+ Add LTI Platform'}
        </button>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className={styles.successMessage}>
          ✓ {successMessage}
        </div>
      )}

      {/* Add platform form */}
      {showAddForm && (
        <form onSubmit={handleSubmit} className={styles.form}>
          <h3 className={styles.formTitle}>Register LTI 1.3 Platform</h3>

          {/* Platform name */}
          <div className={styles.formGroup}>
            <label htmlFor="platform_name" className={styles.label}>
              Platform Name *
            </label>
            <input
              type="text"
              id="platform_name"
              className={styles.input}
              placeholder="e.g., Canvas LMS"
              value={formData.platform_name}
              onChange={(e) => setFormData({ ...formData, platform_name: e.target.value })}
            />
            {formErrors.platform_name && (
              <span className={styles.error}>{formErrors.platform_name}</span>
            )}
          </div>

          {/* Issuer */}
          <div className={styles.formGroup}>
            <label htmlFor="issuer" className={styles.label}>
              Issuer URL *
              <span className={styles.helpText}>
                The platform's issuer identifier (e.g., https://canvas.instructure.com)
              </span>
            </label>
            <input
              type="url"
              id="issuer"
              className={styles.input}
              placeholder="https://example.com"
              value={formData.issuer}
              onChange={(e) => setFormData({ ...formData, issuer: e.target.value })}
            />
            {formErrors.issuer && (
              <span className={styles.error}>{formErrors.issuer}</span>
            )}
          </div>

          {/* Client ID */}
          <div className={styles.formGroup}>
            <label htmlFor="client_id" className={styles.label}>
              Client ID *
              <span className={styles.helpText}>
                The OAuth 2.0 client identifier provided by the LMS
              </span>
            </label>
            <input
              type="text"
              id="client_id"
              className={styles.input}
              placeholder="Client ID from LMS"
              value={formData.client_id}
              onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
            />
            {formErrors.client_id && (
              <span className={styles.error}>{formErrors.client_id}</span>
            )}
          </div>

          {/* Auth Login URL */}
          <div className={styles.formGroup}>
            <label htmlFor="auth_login_url" className={styles.label}>
              Auth Login URL *
              <span className={styles.helpText}>
                OIDC login initiation endpoint
              </span>
            </label>
            <input
              type="url"
              id="auth_login_url"
              className={styles.input}
              placeholder="https://example.com/api/lti/authorize_redirect"
              value={formData.auth_login_url}
              onChange={(e) => setFormData({ ...formData, auth_login_url: e.target.value })}
            />
            {formErrors.auth_login_url && (
              <span className={styles.error}>{formErrors.auth_login_url}</span>
            )}
          </div>

          {/* Auth Token URL */}
          <div className={styles.formGroup}>
            <label htmlFor="auth_token_url" className={styles.label}>
              Auth Token URL *
              <span className={styles.helpText}>
                OAuth 2.0 token endpoint
              </span>
            </label>
            <input
              type="url"
              id="auth_token_url"
              className={styles.input}
              placeholder="https://example.com/login/oauth2/token"
              value={formData.auth_token_url}
              onChange={(e) => setFormData({ ...formData, auth_token_url: e.target.value })}
            />
            {formErrors.auth_token_url && (
              <span className={styles.error}>{formErrors.auth_token_url}</span>
            )}
          </div>

          {/* JWKS URL */}
          <div className={styles.formGroup}>
            <label htmlFor="jwks_url" className={styles.label}>
              JWKS URL *
              <span className={styles.helpText}>
                JSON Web Key Set endpoint for token verification
              </span>
            </label>
            <input
              type="url"
              id="jwks_url"
              className={styles.input}
              placeholder="https://example.com/api/lti/security/jwks"
              value={formData.jwks_url}
              onChange={(e) => setFormData({ ...formData, jwks_url: e.target.value })}
            />
            {formErrors.jwks_url && (
              <span className={styles.error}>{formErrors.jwks_url}</span>
            )}
          </div>

          {/* Deployment ID (optional) */}
          <div className={styles.formGroup}>
            <label htmlFor="deployment_id" className={styles.label}>
              Deployment ID (Optional)
              <span className={styles.helpText}>
                Platform deployment identifier (if required by LMS)
              </span>
            </label>
            <input
              type="text"
              id="deployment_id"
              className={styles.input}
              placeholder="Deployment ID (optional)"
              value={formData.deployment_id}
              onChange={(e) => setFormData({ ...formData, deployment_id: e.target.value })}
            />
          </div>

          {/* Submit error */}
          {formErrors.submit && (
            <div className={styles.submitError}>{formErrors.submit}</div>
          )}

          {/* Form actions */}
          <div className={styles.formActions}>
            <button
              type="button"
              className={styles.cancelButton}
              onClick={() => setShowAddForm(false)}
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={submitting}
            >
              {submitting ? 'Registering...' : 'Register Platform'}
            </button>
          </div>
        </form>
      )}

      {/* Platform list */}
      <div className={styles.platformList}>
        {platforms.length === 0 ? (
          <div className={styles.emptyState}>
            <p>No LTI platforms configured</p>
            <p className={styles.emptyStateHint}>
              Click "Add LTI Platform" to connect your first LMS
            </p>
          </div>
        ) : (
          platforms.map((platform) => (
            <div key={platform.id} className={styles.platformCard}>
              <div className={styles.platformHeader}>
                <div>
                  <h3 className={styles.platformName}>{platform.platform_name}</h3>
                  <p className={styles.platformIssuer}>{platform.issuer}</p>
                </div>
                <IntegrationStatusBadge
                  status={platform.is_active ? 'connected' : 'disconnected'}
                  lastSync={platform.last_connection_at}
                />
              </div>

              <div className={styles.platformDetails}>
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Client ID:</span>
                  <code className={styles.detailValue}>{platform.client_id}</code>
                </div>
                {platform.deployment_id && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>Deployment ID:</span>
                    <code className={styles.detailValue}>{platform.deployment_id}</code>
                  </div>
                )}
                <div className={styles.detailRow}>
                  <span className={styles.detailLabel}>Verified:</span>
                  <span className={styles.detailValue}>
                    {platform.verified_at ? (
                      <span className={styles.verified}>✓ Verified</span>
                    ) : (
                      <span className={styles.unverified}>Not verified</span>
                    )}
                  </span>
                </div>
              </div>

              <div className={styles.platformActions}>
                {!platform.verified_at && (
                  <button
                    className={styles.verifyButton}
                    onClick={() => handleVerify(platform.id)}
                  >
                    Verify Platform
                  </button>
                )}
                {platform.is_active && (
                  <button
                    className={styles.deactivateButton}
                    onClick={() => handleDeactivate(platform.id)}
                  >
                    Deactivate
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Setup instructions */}
      <div className={styles.instructions}>
        <h3 className={styles.instructionsTitle}>LTI 1.3 Setup Instructions</h3>
        <ol className={styles.instructionsList}>
          <li>In your LMS admin panel, navigate to LTI Developer Keys or External Apps</li>
          <li>Create a new LTI 1.3 configuration</li>
          <li>Use the following configuration values:</li>
          <ul className={styles.configValues}>
            <li><strong>Tool URL:</strong> <code>https://your-domain.com/lti/launch</code></li>
            <li><strong>Redirect URIs:</strong> <code>https://your-domain.com/lti/callback</code></li>
            <li><strong>Public JWK URL:</strong> <code>https://your-domain.com/lti/jwks</code></li>
          </ul>
          <li>Copy the Issuer, Client ID, and platform URLs from your LMS</li>
          <li>Click "Add LTI Platform" above and paste the values</li>
          <li>Test the connection by launching from your LMS</li>
        </ol>
      </div>
    </div>
  );
};

export default LTIIntegrationPanel;
