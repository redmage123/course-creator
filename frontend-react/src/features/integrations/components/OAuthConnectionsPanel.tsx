/**
 * OAuthConnectionsPanel Component
 *
 * What: OAuth token management and third-party service connections
 * Where: Used in IntegrationsSettings for OAuth provider management
 * Why: Displays and manages OAuth tokens for Google, Microsoft, Slack, GitHub, Zoom
 *
 * BUSINESS CONTEXT:
 * OAuth connections enable seamless integration with third-party services.
 * Users can view connection status, refresh expired tokens, and revoke access.
 * Supports both user-level and organization-level OAuth tokens.
 *
 * @module features/integrations/components/OAuthConnectionsPanel
 */

import React from 'react';
import { integrationsService } from '../../../services/integrationsService';
import type { OAuthToken } from '../../../services/integrationsService';
import IntegrationStatusBadge from './IntegrationStatusBadge';
import styles from './OAuthConnectionsPanel.module.css';

export interface OAuthConnectionsPanelProps {
  userId?: string;
  organizationId?: string;
  tokens: OAuthToken[];
  onRefresh: () => void;
}

/**
 * Provider configuration with display info
 */
const PROVIDERS = [
  { id: 'google', name: 'Google', icon: '🔵', color: '#4285F4' },
  { id: 'microsoft', name: 'Microsoft', icon: '🟦', color: '#00A4EF' },
  { id: 'slack', name: 'Slack', icon: '💬', color: '#4A154B' },
  { id: 'github', name: 'GitHub', icon: '🐙', color: '#181717' },
  { id: 'zoom', name: 'Zoom', icon: '🎥', color: '#2D8CFF' },
] as const;

export const OAuthConnectionsPanel: React.FC<OAuthConnectionsPanelProps> = ({
  userId,
  organizationId,
  tokens,
  onRefresh,
}) => {
  /**
   * Handle OAuth connection
   */
  const handleConnect = (provider: 'google' | 'microsoft' | 'slack' | 'github' | 'zoom') => {
    const redirectUri = `${window.location.origin}/integrations/oauth/callback`;
    const scopesMap = {
      google: ['profile', 'email', 'openid'],
      microsoft: ['User.Read', 'Calendars.ReadWrite'],
      slack: ['identity.basic'],
      github: ['read:user'],
      zoom: ['user:read'],
    };

    integrationsService.initiateOAuthFlow(
      provider,
      scopesMap[provider],
      redirectUri
    );
  };

  /**
   * Handle token revocation
   */
  const handleRevoke = async (tokenId: string, providerName: string) => {
    if (!window.confirm(`Revoke ${providerName} connection?`)) return;

    try {
      await integrationsService.revokeOAuthToken(tokenId);
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to revoke connection');
    }
  };

  /**
   * Handle token refresh
   */
  const handleRefresh = async (tokenId: string) => {
    try {
      await integrationsService.refreshOAuthToken(tokenId);
      alert('Token refreshed successfully');
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to refresh token');
    }
  };

  /**
   * Get token for provider
   */
  const getTokenForProvider = (
    providerId: string
  ): OAuthToken | undefined => {
    return tokens.find((t) => t.provider === providerId);
  };

  /**
   * Check if token is expired
   */
  const isTokenExpired = (token: OAuthToken): boolean => {
    if (!token.expires_at) return false;
    return new Date(token.expires_at) < new Date();
  };

  /**
   * Format token expiration
   */
  const formatExpiration = (expiresAt: string | undefined): string => {
    if (!expiresAt) return 'Never expires';

    const date = new Date(expiresAt);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMs < 0) return 'Expired';
    if (diffDays === 0) return 'Expires today';
    if (diffDays === 1) return 'Expires tomorrow';
    if (diffDays < 7) return `Expires in ${diffDays} days`;

    return `Expires ${date.toLocaleDateString()}`;
  };

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>🔐 OAuth Connections</h2>
          <p className={styles.description}>
            Manage connected third-party services and access tokens
          </p>
        </div>
      </div>

      {/* Provider list */}
      <div className={styles.providerList}>
        {PROVIDERS.map((provider) => {
          const token = getTokenForProvider(provider.id);
          const isExpired = token ? isTokenExpired(token) : false;

          return (
            <div key={provider.id} className={styles.providerCard}>
              <div className={styles.providerHeader}>
                <div className={styles.providerInfo}>
                  <span className={styles.providerIcon}>{provider.icon}</span>
                  <div>
                    <h3 className={styles.providerName}>{provider.name}</h3>
                    {token && (
                      <p className={styles.providerDetails}>
                        {formatExpiration(token.expires_at)}
                      </p>
                    )}
                  </div>
                </div>
                {token ? (
                  <IntegrationStatusBadge
                    status={
                      !token.is_valid
                        ? 'error'
                        : isExpired
                        ? 'error'
                        : 'connected'
                    }
                    lastSync={token.last_used_at}
                    errorMessage={token.last_error || undefined}
                  />
                ) : (
                  <IntegrationStatusBadge status="disconnected" />
                )}
              </div>

              {/* Token info */}
              {token && (
                <div className={styles.tokenInfo}>
                  <div className={styles.tokenStats}>
                    <span>
                      Scopes: {token.scopes.length > 0 ? token.scopes.join(', ') : 'None'}
                    </span>
                    {token.consecutive_failures > 0 && (
                      <span className={styles.errorBadge}>
                        {token.consecutive_failures} failed attempt(s)
                      </span>
                    )}
                  </div>
                  {token.last_error && (
                    <div className={styles.tokenError}>
                      <strong>Last Error:</strong> {token.last_error}
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className={styles.providerActions}>
                {!token ? (
                  <button
                    className={styles.connectButton}
                    onClick={() => handleConnect(provider.id as any)}
                  >
                    Connect
                  </button>
                ) : (
                  <>
                    {isExpired && (
                      <button
                        className={styles.refreshButton}
                        onClick={() => handleRefresh(token.id)}
                      >
                        Refresh Token
                      </button>
                    )}
                    <button
                      className={styles.revokeButton}
                      onClick={() => handleRevoke(token.id, provider.name)}
                    >
                      Revoke Access
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Information */}
      <div className={styles.infoBox}>
        <h4 className={styles.infoTitle}>About OAuth Connections</h4>
        <p>
          OAuth connections allow this platform to access external services on your behalf.
          Tokens are encrypted and stored securely. You can revoke access at any time.
        </p>
        <ul className={styles.infoList}>
          <li>
            <strong>Google:</strong> Used for Calendar sync and Google Drive integration
          </li>
          <li>
            <strong>Microsoft:</strong> Used for Outlook Calendar and OneDrive integration
          </li>
          <li>
            <strong>Slack:</strong> Used for workspace notifications and commands
          </li>
          <li>
            <strong>GitHub:</strong> Used for code repository integration and version control
          </li>
          <li>
            <strong>Zoom:</strong> Used for virtual classroom and meeting scheduling
          </li>
        </ul>
      </div>
    </div>
  );
};

export default OAuthConnectionsPanel;
