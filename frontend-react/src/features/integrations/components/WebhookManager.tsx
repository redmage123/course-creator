/**
 * WebhookManager Component
 *
 * What: Outbound and inbound webhook configuration management
 * Where: Used in IntegrationsSettings for webhook integrations
 * Why: Enables event notifications to external services (Zapier, custom apps)
 *
 * BUSINESS CONTEXT:
 * Webhooks enable real-time event streaming to external systems for:
 * - Custom reporting and analytics
 * - Integration with HR systems
 * - Zapier workflows and automations
 * - Third-party notification services
 * - Custom business logic triggers
 *
 * @module features/integrations/components/WebhookManager
 */

import React, { useState } from 'react';
import { integrationsService } from '../../../services/integrationsService';
import type {
  OutboundWebhook,
  InboundWebhook,
  CreateOutboundWebhookRequest,
} from '../../../services/integrationsService';
import IntegrationStatusBadge from './IntegrationStatusBadge';
import styles from './WebhookManager.module.css';

export interface WebhookManagerProps {
  organizationId: string;
  outboundWebhooks: OutboundWebhook[];
  inboundWebhooks: InboundWebhook[];
  onRefresh: () => void;
}

export const WebhookManager: React.FC<WebhookManagerProps> = ({
  organizationId,
  outboundWebhooks,
  inboundWebhooks,
  onRefresh,
}) => {
  const [activeTab, setActiveTab] = useState<'outbound' | 'inbound'>('outbound');
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState<CreateOutboundWebhookRequest>({
    name: '',
    target_url: '',
    auth_type: 'none',
    event_types: [],
  });

  const handleCreateOutbound = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await integrationsService.createOutboundWebhook(organizationId, formData);
      setShowAddForm(false);
      setFormData({ name: '', target_url: '', auth_type: 'none', event_types: [] });
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to create webhook');
    }
  };

  const handleTestWebhook = async (webhookId: string) => {
    try {
      const result = await integrationsService.testOutboundWebhook(webhookId);
      alert(result.success ? `Success! Status: ${result.status_code}` : `Failed: ${result.message}`);
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to test webhook');
    }
  };

  const handleDeleteWebhook = async (webhookId: string) => {
    if (!window.confirm('Delete this webhook?')) return;

    try {
      await integrationsService.deleteOutboundWebhook(webhookId);
      onRefresh();
    } catch (error: any) {
      alert(error.response?.data?.message || 'Failed to delete webhook');
    }
  };

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>🔗 Webhooks</h2>
          <p className={styles.description}>
            Send and receive events to/from external services
          </p>
        </div>
        {activeTab === 'outbound' && (
          <button
            className={styles.addButton}
            onClick={() => setShowAddForm(!showAddForm)}
          >
            {showAddForm ? 'Cancel' : '+ Add Webhook'}
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'outbound' ? styles.active : ''}`}
          onClick={() => setActiveTab('outbound')}
        >
          Outbound ({outboundWebhooks.length})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'inbound' ? styles.active : ''}`}
          onClick={() => setActiveTab('inbound')}
        >
          Inbound ({inboundWebhooks.length})
        </button>
      </div>

      {/* Add webhook form */}
      {showAddForm && activeTab === 'outbound' && (
        <form onSubmit={handleCreateOutbound} className={styles.form}>
          <div className={styles.formGroup}>
            <label>Webhook Name *</label>
            <input
              type="text"
              className={styles.input}
              placeholder="e.g., Zapier Enrollment Sync"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>Target URL *</label>
            <input
              type="url"
              className={styles.input}
              placeholder="https://hooks.zapier.com/..."
              value={formData.target_url}
              onChange={(e) => setFormData({ ...formData, target_url: e.target.value })}
              required
            />
          </div>
          <div className={styles.formGroup}>
            <label>Authentication Type</label>
            <select
              className={styles.select}
              value={formData.auth_type}
              onChange={(e) =>
                setFormData({ ...formData, auth_type: e.target.value as any })
              }
            >
              <option value="none">None</option>
              <option value="bearer">Bearer Token</option>
              <option value="basic">Basic Auth</option>
              <option value="hmac">HMAC Signature</option>
              <option value="api_key">API Key</option>
            </select>
          </div>
          <div className={styles.formActions}>
            <button type="button" className={styles.cancelButton} onClick={() => setShowAddForm(false)}>
              Cancel
            </button>
            <button type="submit" className={styles.submitButton}>
              Create Webhook
            </button>
          </div>
        </form>
      )}

      {/* Outbound webhooks */}
      {activeTab === 'outbound' && (
        <div className={styles.webhookList}>
          {outboundWebhooks.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No outbound webhooks configured</p>
            </div>
          ) : (
            outboundWebhooks.map((webhook) => (
              <div key={webhook.id} className={styles.webhookCard}>
                <div className={styles.webhookHeader}>
                  <div>
                    <h3 className={styles.webhookName}>{webhook.name}</h3>
                    <p className={styles.webhookUrl}>{webhook.target_url}</p>
                  </div>
                  <IntegrationStatusBadge
                    status={webhook.is_active ? 'connected' : 'disconnected'}
                    lastSync={webhook.last_triggered_at}
                  />
                </div>
                <div className={styles.webhookStats}>
                  <span>Success: {webhook.success_count}</span>
                  <span>Failed: {webhook.failure_count}</span>
                  <span>Auth: {webhook.auth_type}</span>
                </div>
                <div className={styles.webhookActions}>
                  <button
                    className={styles.testButton}
                    onClick={() => handleTestWebhook(webhook.id)}
                  >
                    Test
                  </button>
                  <button
                    className={styles.deleteButton}
                    onClick={() => handleDeleteWebhook(webhook.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Inbound webhooks */}
      {activeTab === 'inbound' && (
        <div className={styles.webhookList}>
          {inboundWebhooks.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No inbound webhooks configured</p>
            </div>
          ) : (
            inboundWebhooks.map((webhook) => (
              <div key={webhook.id} className={styles.webhookCard}>
                <div className={styles.webhookHeader}>
                  <div>
                    <h3 className={styles.webhookName}>{webhook.name}</h3>
                    <code className={styles.webhookToken}>
                      {window.location.origin}/webhooks/{webhook.webhook_token}
                    </code>
                  </div>
                  <IntegrationStatusBadge
                    status={webhook.is_active ? 'connected' : 'disconnected'}
                    lastSync={webhook.last_received_at}
                  />
                </div>
                <div className={styles.webhookStats}>
                  <span>Received: {webhook.total_received}</span>
                  <span>Processed: {webhook.total_processed}</span>
                  <span>Failed: {webhook.total_failed}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default WebhookManager;
