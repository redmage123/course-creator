/**
 * Organization Settings Page
 *
 * BUSINESS CONTEXT:
 * Org Admin feature for managing organization profile, branding, and configuration.
 * Allows customization of training policies, integrations, and organizational preferences.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Organization profile management
 * - Branding configuration (logo, colors, theme)
 * - Training policies and preferences
 * - Integration settings (SSO, LMS, notifications)
 * - Billing and subscription information
 * - AI Provider configuration for multi-LLM support
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { logout as logoutAction } from '../store/slices/authSlice';
import { clearUser } from '../store/slices/userSlice';
import { organizationService } from '../services';
import axios from 'axios';
import { tokenManager } from '../services/tokenManager';

/**
 * LLM Provider Configuration Interface
 * Represents an organization's configured AI provider
 */
interface LLMProviderConfig {
  id: string;
  organization_id: string;
  provider_name: string;
  model_name: string;
  is_active: boolean;
  is_default: boolean;
  created_at: string;
}

/**
 * Available LLM Providers
 * Static configuration of supported providers
 */
const AVAILABLE_PROVIDERS = [
  { name: 'openai', displayName: 'OpenAI', models: ['gpt-4-vision-preview', 'gpt-4-turbo', 'gpt-4o', 'gpt-4o-mini'], supportsVision: true },
  { name: 'anthropic', displayName: 'Anthropic', models: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'claude-3.5-sonnet'], supportsVision: true },
  { name: 'deepseek', displayName: 'Deepseek', models: ['deepseek-vl', 'deepseek-chat'], supportsVision: true },
  { name: 'qwen', displayName: 'Qwen (Alibaba)', models: ['qwen-vl-plus', 'qwen-vl-max'], supportsVision: true },
  { name: 'ollama', displayName: 'Ollama (Local)', models: ['llava', 'bakllava', 'llava-llama3'], supportsVision: true },
  { name: 'llama', displayName: 'Meta Llama', models: ['llama-3.2-vision-90b', 'llama-3.2-vision-11b'], supportsVision: true },
  { name: 'gemini', displayName: 'Google Gemini', models: ['gemini-pro-vision', 'gemini-1.5-pro', 'gemini-1.5-flash'], supportsVision: true },
  { name: 'mistral', displayName: 'Mistral', models: ['pixtral-12b', 'mistral-large'], supportsVision: true },
];

/**
 * Organization Settings Interface
 * Represents configurable organization settings
 */
interface OrganizationSettings {
  // Profile
  organizationName: string;
  contactEmail: string;
  contactPhone: string;
  website: string;
  address: string;

  // Branding
  logoUrl: string;
  primaryColor: string;
  secondaryColor: string;
  customDomain: string;

  // Training Policies
  requireCourseApproval: boolean;
  allowSelfEnrollment: boolean;
  certificateEnabled: boolean;
  minPassingScore: number;

  // Integrations
  ssoEnabled: boolean;
  ssoProvider: string;
  slackWebhookUrl: string;
  emailNotifications: boolean;

  // Subscription
  subscriptionPlan: string;
  maxTrainers: number;
  maxStudents: number;
  storageLimit: number; // GB
}

/**
 * Mock organization settings
 * In production, this would come from the API
 */
const mockSettings: OrganizationSettings = {
  organizationName: 'Acme Corporation',
  contactEmail: 'admin@acme.com',
  contactPhone: '+1 (555) 123-4567',
  website: 'https://acme.com',
  address: '123 Business St, City, State 12345',
  logoUrl: '',
  primaryColor: '#3b82f6',
  secondaryColor: '#10b981',
  customDomain: 'training.acme.com',
  requireCourseApproval: true,
  allowSelfEnrollment: false,
  certificateEnabled: true,
  minPassingScore: 70,
  ssoEnabled: false,
  ssoProvider: 'None',
  slackWebhookUrl: '',
  emailNotifications: true,
  subscriptionPlan: 'Enterprise',
  maxTrainers: 50,
  maxStudents: 1000,
  storageLimit: 100
};

/**
 * Organization Settings Page Component
 *
 * WHY THIS APPROACH:
 * - Tabbed interface for logical grouping of settings
 * - Real-time preview for branding changes
 * - Clear validation and feedback
 * - Separate save buttons per section for granular control
 */
export const OrganizationSettings: React.FC = () => {
  const user = useAppSelector(state => state.user.profile);
  const organizationId = useAppSelector(state => state.auth.organizationId);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  const [settings, setSettings] = useState<OrganizationSettings>(mockSettings);
  const [activeTab, setActiveTab] = useState<'profile' | 'branding' | 'training' | 'integrations' | 'ai-providers' | 'subscription'>('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  // AI Provider state
  const [llmProviders, setLlmProviders] = useState<LLMProviderConfig[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);
  const [providerError, setProviderError] = useState<string | null>(null);
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [newProviderName, setNewProviderName] = useState('');
  const [newProviderModel, setNewProviderModel] = useState('');
  const [newProviderApiKey, setNewProviderApiKey] = useState('');
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState<{ success: boolean; message: string } | null>(null);

  /**
   * Load LLM providers for the organization
   */
  const loadLLMProviders = useCallback(async () => {
    const orgId = user?.organizationId;
    if (!orgId) return;

    setLoadingProviders(true);
    setProviderError(null);

    try {
      const response = await axios.get<{ configs: LLMProviderConfig[] }>(
        `/api/v1/organizations/${orgId}/llm-config`,
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );
      setLlmProviders(response.data.configs || []);
    } catch (err) {
      console.error('Failed to load LLM providers:', err);
      setProviderError('Failed to load AI provider configurations');
    } finally {
      setLoadingProviders(false);
    }
  }, [user?.organizationId]);

  // Load providers when tab is selected
  useEffect(() => {
    if (activeTab === 'ai-providers') {
      loadLLMProviders();
    }
  }, [activeTab, loadLLMProviders]);

  /**
   * Handle settings update
   */
  const handleUpdateSettings = async (section: string) => {
    setIsSaving(true);
    try {
      // TODO: Implement API call to update organization settings
      console.log('Updating settings:', { section, settings });
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      alert(`${section} settings updated successfully!`);
    } catch (err) {
      console.error('Failed to update settings:', err);
      alert('Failed to update settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Handle input change
   */
  const handleInputChange = (field: keyof OrganizationSettings, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  /**
   * Tab navigation component
   */
  const renderTabs = () => {
    const tabs = [
      { id: 'profile', label: 'Organization Profile', icon: '🏢' },
      { id: 'branding', label: 'Branding', icon: '🎨' },
      { id: 'training', label: 'Training Policies', icon: '📚' },
      { id: 'integrations', label: 'Integrations', icon: '🔌' },
      { id: 'ai-providers', label: 'AI Providers', icon: '🤖' },
      { id: 'subscription', label: 'Subscription', icon: '💳' }
    ];

    return (
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '1.5rem',
        borderBottom: '2px solid #e5e7eb',
        overflowX: 'auto',
        flexWrap: 'wrap'
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            style={{
              padding: '0.75rem 1.25rem',
              fontSize: '0.875rem',
              fontWeight: 500,
              border: 'none',
              borderBottom: activeTab === tab.id ? '3px solid #3b82f6' : '3px solid transparent',
              backgroundColor: 'transparent',
              color: activeTab === tab.id ? '#3b82f6' : '#6b7280',
              cursor: 'pointer',
              transition: 'all 0.2s',
              whiteSpace: 'nowrap'
            }}
          >
            <span style={{ marginRight: '0.5rem' }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
    );
  };

  /**
   * Profile settings tab
   */
  const renderProfileTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Organization Profile
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div>
          <label htmlFor="orgName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Organization Name *
          </label>
          <Input
            id="orgName"
            name="orgName"
            type="text"
            value={settings.organizationName}
            onChange={(e) => handleInputChange('organizationName', e.target.value)}
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="contactEmail" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Contact Email *
            </label>
            <Input
              id="contactEmail"
              name="contactEmail"
              type="email"
              value={settings.contactEmail}
              onChange={(e) => handleInputChange('contactEmail', e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="contactPhone" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Contact Phone
            </label>
            <Input
              id="contactPhone"
              name="contactPhone"
              type="tel"
              value={settings.contactPhone}
              onChange={(e) => handleInputChange('contactPhone', e.target.value)}
            />
          </div>
        </div>

        <div>
          <label htmlFor="website" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Website
          </label>
          <Input
            id="website"
            name="website"
            type="url"
            value={settings.website}
            onChange={(e) => handleInputChange('website', e.target.value)}
          />
        </div>

        <div>
          <label htmlFor="address" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Address
          </label>
          <textarea
            id="address"
            name="address"
            value={settings.address}
            onChange={(e) => handleInputChange('address', e.target.value)}
            rows={3}
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '0.875rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              fontFamily: 'inherit'
            }}
          />
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Profile')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Profile Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Branding settings tab
   */
  const renderBrandingTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Branding & Appearance
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div>
          <label htmlFor="logoUrl" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Organization Logo URL
          </label>
          <Input
            id="logoUrl"
            name="logoUrl"
            type="url"
            placeholder="https://example.com/logo.png"
            value={settings.logoUrl}
            onChange={(e) => handleInputChange('logoUrl', e.target.value)}
          />
          <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
            Upload your logo and paste the URL here. Recommended size: 200x50px
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="primaryColor" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Primary Color
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                id="primaryColor"
                name="primaryColor"
                type="color"
                value={settings.primaryColor}
                onChange={(e) => handleInputChange('primaryColor', e.target.value)}
                style={{ width: '60px', height: '40px', cursor: 'pointer', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
              />
              <Input
                type="text"
                value={settings.primaryColor}
                onChange={(e) => handleInputChange('primaryColor', e.target.value)}
                style={{ flex: 1 }}
              />
            </div>
          </div>

          <div>
            <label htmlFor="secondaryColor" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Secondary Color
            </label>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <input
                id="secondaryColor"
                name="secondaryColor"
                type="color"
                value={settings.secondaryColor}
                onChange={(e) => handleInputChange('secondaryColor', e.target.value)}
                style={{ width: '60px', height: '40px', cursor: 'pointer', border: '1px solid #d1d5db', borderRadius: '0.375rem' }}
              />
              <Input
                type="text"
                value={settings.secondaryColor}
                onChange={(e) => handleInputChange('secondaryColor', e.target.value)}
                style={{ flex: 1 }}
              />
            </div>
          </div>
        </div>

        <div>
          <label htmlFor="customDomain" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Custom Domain
          </label>
          <Input
            id="customDomain"
            name="customDomain"
            type="text"
            placeholder="training.yourcompany.com"
            value={settings.customDomain}
            onChange={(e) => handleInputChange('customDomain', e.target.value)}
          />
          <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
            Contact support to configure DNS settings for your custom domain
          </p>
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Branding')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Branding Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Training policies tab
   */
  const renderTrainingTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Training Policies
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Require Course Approval</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Trainers must get approval before publishing courses
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.requireCourseApproval}
            onChange={(e) => handleInputChange('requireCourseApproval', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Allow Self-Enrollment</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Students can enroll in courses without trainer approval
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.allowSelfEnrollment}
            onChange={(e) => handleInputChange('allowSelfEnrollment', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Enable Certificates</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Students receive certificates upon course completion
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.certificateEnabled}
            onChange={(e) => handleInputChange('certificateEnabled', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div>
          <label htmlFor="minPassingScore" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Minimum Passing Score (%)
          </label>
          <Input
            id="minPassingScore"
            name="minPassingScore"
            type="number"
            min="0"
            max="100"
            value={settings.minPassingScore}
            onChange={(e) => handleInputChange('minPassingScore', parseInt(e.target.value))}
          />
          <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
            Default minimum score required to pass quizzes and assessments
          </p>
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Training Policies')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Training Policies'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Integrations tab
   */
  const renderIntegrationsTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Integrations & Notifications
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Single Sign-On (SSO)</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Enable SSO authentication for your organization
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.ssoEnabled}
            onChange={(e) => handleInputChange('ssoEnabled', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        {settings.ssoEnabled && (
          <div>
            <label htmlFor="ssoProvider" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              SSO Provider
            </label>
            <select
              id="ssoProvider"
              name="ssoProvider"
              value={settings.ssoProvider}
              onChange={(e) => handleInputChange('ssoProvider', e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem',
                fontSize: '0.875rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                backgroundColor: 'white'
              }}
            >
              <option value="None">Select Provider</option>
              <option value="Google">Google Workspace</option>
              <option value="Microsoft">Microsoft Azure AD</option>
              <option value="Okta">Okta</option>
              <option value="SAML">Generic SAML 2.0</option>
            </select>
          </div>
        )}

        <div>
          <label htmlFor="slackWebhook" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Slack Webhook URL
          </label>
          <Input
            id="slackWebhook"
            name="slackWebhook"
            type="url"
            placeholder="https://hooks.slack.com/services/..."
            value={settings.slackWebhookUrl}
            onChange={(e) => handleInputChange('slackWebhookUrl', e.target.value)}
          />
          <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
            Receive notifications about course completions and enrollments
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Email Notifications</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Send email notifications for important events
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.emailNotifications}
            onChange={(e) => handleInputChange('emailNotifications', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Integrations')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Integration Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Add a new LLM provider configuration
   */
  const handleAddProvider = async () => {
    const orgId = user?.organizationId;
    if (!orgId || !newProviderName || !newProviderModel) {
      setProviderError('Please select a provider and model');
      return;
    }

    setIsSaving(true);
    setProviderError(null);

    try {
      await axios.post(
        `/api/v1/organizations/${orgId}/llm-config`,
        {
          provider_name: newProviderName,
          model_name: newProviderModel,
          api_key: newProviderApiKey,
          is_active: true,
          is_default: llmProviders.length === 0, // First provider is default
        },
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );

      // Reset form and reload providers
      setShowAddProvider(false);
      setNewProviderName('');
      setNewProviderModel('');
      setNewProviderApiKey('');
      setConnectionTestResult(null);
      await loadLLMProviders();
    } catch (err: any) {
      console.error('Failed to add provider:', err);
      setProviderError(err.response?.data?.detail || 'Failed to add AI provider');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Delete an LLM provider configuration
   */
  const handleDeleteProvider = async (configId: string) => {
    const orgId = user?.organizationId;
    if (!orgId) return;

    if (!confirm('Are you sure you want to remove this AI provider configuration?')) {
      return;
    }

    setIsSaving(true);
    try {
      await axios.delete(
        `/api/v1/organizations/${orgId}/llm-config/${configId}`,
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );
      await loadLLMProviders();
    } catch (err: any) {
      console.error('Failed to delete provider:', err);
      setProviderError(err.response?.data?.detail || 'Failed to delete provider');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Set a provider as default
   */
  const handleSetDefaultProvider = async (configId: string) => {
    const orgId = user?.organizationId;
    if (!orgId) return;

    setIsSaving(true);
    try {
      await axios.put(
        `/api/v1/organizations/${orgId}/llm-config/${configId}`,
        { is_default: true },
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );
      await loadLLMProviders();
    } catch (err: any) {
      console.error('Failed to set default provider:', err);
      setProviderError(err.response?.data?.detail || 'Failed to set default provider');
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Test connection to the provider
   */
  const handleTestConnection = async () => {
    const orgId = user?.organizationId;
    if (!orgId || !newProviderName || !newProviderApiKey) {
      setConnectionTestResult({ success: false, message: 'Provider and API key are required' });
      return;
    }

    setTestingConnection(true);
    setConnectionTestResult(null);

    try {
      const response = await axios.post(
        `/api/v1/organizations/${orgId}/llm-config/test`,
        {
          provider_name: newProviderName,
          model_name: newProviderModel || 'default',
          api_key: newProviderApiKey,
        },
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`,
          },
        }
      );

      setConnectionTestResult({
        success: response.data.success,
        message: response.data.message || 'Connection successful!',
      });
    } catch (err: any) {
      setConnectionTestResult({
        success: false,
        message: err.response?.data?.detail || 'Connection test failed',
      });
    } finally {
      setTestingConnection(false);
    }
  };

  /**
   * Get models for selected provider
   */
  const getModelsForProvider = (providerName: string) => {
    const provider = AVAILABLE_PROVIDERS.find(p => p.name === providerName);
    return provider?.models || [];
  };

  /**
   * AI Providers tab - Configure LLM providers for screenshot analysis
   */
  const renderAIProvidersTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        AI Provider Configuration
      </Heading>

      <p style={{ color: '#666', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
        Configure AI providers for screenshot analysis and course generation.
        These providers enable AI-powered features like extracting content from screenshots and generating course structures.
      </p>

      {providerError && (
        <div style={{
          padding: '0.75rem 1rem',
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '0.375rem',
          color: '#dc2626',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <span>⚠️</span>
          <span>{providerError}</span>
          <button
            onClick={() => setProviderError(null)}
            style={{
              marginLeft: 'auto',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '1.25rem',
              color: '#dc2626',
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* Current Providers List */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>Configured Providers</h3>
          <Button
            variant="primary"
            onClick={() => setShowAddProvider(true)}
            disabled={showAddProvider}
          >
            + Add Provider
          </Button>
        </div>

        {loadingProviders ? (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
            Loading providers...
          </div>
        ) : llmProviders.length === 0 ? (
          <div style={{
            padding: '2rem',
            backgroundColor: '#f9fafb',
            borderRadius: '0.5rem',
            textAlign: 'center',
            color: '#666',
          }}>
            <p style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>No AI providers configured</p>
            <p style={{ margin: 0, fontSize: '0.9rem' }}>
              Add an AI provider to enable screenshot-based course creation
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {llmProviders.map((config) => {
              const providerInfo = AVAILABLE_PROVIDERS.find(p => p.name === config.provider_name);
              return (
                <div
                  key={config.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '1rem',
                    backgroundColor: config.is_default ? '#f0f9ff' : '#f9fafb',
                    border: `1px solid ${config.is_default ? '#bae6fd' : '#e5e7eb'}`,
                    borderRadius: '0.5rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div
                      style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        backgroundColor: config.is_active ? '#10b981' : '#9ca3af',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '1.25rem',
                      }}
                    >
                      🤖
                    </div>
                    <div>
                      <p style={{ margin: 0, fontWeight: 600 }}>
                        {providerInfo?.displayName || config.provider_name}
                        {config.is_default && (
                          <span style={{
                            marginLeft: '0.5rem',
                            padding: '0.125rem 0.5rem',
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            borderRadius: '1rem',
                            fontSize: '0.7rem',
                            fontWeight: 500,
                          }}>
                            DEFAULT
                          </span>
                        )}
                      </p>
                      <p style={{ margin: '0.25rem 0 0', fontSize: '0.85rem', color: '#666' }}>
                        Model: {config.model_name}
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {!config.is_default && (
                      <Button
                        variant="secondary"
                        onClick={() => handleSetDefaultProvider(config.id)}
                        disabled={isSaving}
                      >
                        Set Default
                      </Button>
                    )}
                    <Button
                      variant="danger"
                      onClick={() => handleDeleteProvider(config.id)}
                      disabled={isSaving}
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Provider Form */}
      {showAddProvider && (
        <div style={{
          padding: '1.5rem',
          backgroundColor: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '0.5rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h4 style={{ margin: 0, fontWeight: 600 }}>Add New AI Provider</h4>
            <button
              onClick={() => {
                setShowAddProvider(false);
                setNewProviderName('');
                setNewProviderModel('');
                setNewProviderApiKey('');
                setConnectionTestResult(null);
              }}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.25rem',
                color: '#666',
              }}
            >
              ×
            </button>
          </div>

          <div style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <label htmlFor="providerName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                Provider *
              </label>
              <select
                id="providerName"
                value={newProviderName}
                onChange={(e) => {
                  setNewProviderName(e.target.value);
                  setNewProviderModel(''); // Reset model when provider changes
                }}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '0.875rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  backgroundColor: 'white',
                }}
              >
                <option value="">Select Provider</option>
                {AVAILABLE_PROVIDERS.map((provider) => (
                  <option key={provider.name} value={provider.name}>
                    {provider.displayName} {provider.supportsVision ? '(Vision)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {newProviderName && (
              <div>
                <label htmlFor="providerModel" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                  Model *
                </label>
                <select
                  id="providerModel"
                  value={newProviderModel}
                  onChange={(e) => setNewProviderModel(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    fontSize: '0.875rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem',
                    backgroundColor: 'white',
                  }}
                >
                  <option value="">Select Model</option>
                  {getModelsForProvider(newProviderName).map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label htmlFor="providerApiKey" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                API Key {newProviderName !== 'ollama' ? '*' : '(Optional for local)'}
              </label>
              <Input
                id="providerApiKey"
                name="providerApiKey"
                type="password"
                placeholder="Enter your API key"
                value={newProviderApiKey}
                onChange={(e) => setNewProviderApiKey(e.target.value)}
              />
              <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.25rem' }}>
                Your API key is encrypted and stored securely
              </p>
            </div>

            {/* Connection Test Result */}
            {connectionTestResult && (
              <div style={{
                padding: '0.75rem 1rem',
                backgroundColor: connectionTestResult.success ? '#f0fdf4' : '#fef2f2',
                border: `1px solid ${connectionTestResult.success ? '#86efac' : '#fecaca'}`,
                borderRadius: '0.375rem',
                color: connectionTestResult.success ? '#166534' : '#dc2626',
              }}>
                {connectionTestResult.success ? '✓' : '✗'} {connectionTestResult.message}
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.75rem', paddingTop: '0.5rem' }}>
              <Button
                variant="secondary"
                onClick={handleTestConnection}
                disabled={testingConnection || !newProviderName}
              >
                {testingConnection ? 'Testing...' : 'Test Connection'}
              </Button>
              <Button
                variant="primary"
                onClick={handleAddProvider}
                disabled={isSaving || !newProviderName || !newProviderModel || (newProviderName !== 'ollama' && !newProviderApiKey)}
              >
                {isSaving ? 'Adding...' : 'Add Provider'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Provider Info */}
      <div style={{
        marginTop: '1.5rem',
        padding: '1rem',
        backgroundColor: '#fffbeb',
        border: '1px solid #fcd34d',
        borderRadius: '0.5rem',
      }}>
        <h4 style={{ margin: '0 0 0.5rem 0', color: '#92400e', fontSize: '0.95rem' }}>
          📋 Supported Providers
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '0.5rem' }}>
          {AVAILABLE_PROVIDERS.map((provider) => (
            <div key={provider.name} style={{ fontSize: '0.85rem', color: '#78350f' }}>
              <strong>{provider.displayName}</strong>
              {provider.supportsVision && ' 📷'}
            </div>
          ))}
        </div>
        <p style={{ fontSize: '0.8rem', color: '#92400e', marginTop: '0.75rem', marginBottom: 0 }}>
          📷 = Supports vision/image analysis for screenshot-based course creation
        </p>
      </div>
    </Card>
  );

  /**
   * Subscription tab
   */
  const renderSubscriptionTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Subscription & Limits
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ padding: '1rem', backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '0.375rem' }}>
          <p style={{ fontWeight: 600, margin: 0, marginBottom: '0.5rem', color: '#0c4a6e' }}>
            Current Plan: {settings.subscriptionPlan}
          </p>
          <p style={{ fontSize: '0.875rem', color: '#0c4a6e', margin: 0 }}>
            Your organization is on the {settings.subscriptionPlan} plan with the following limits
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Max Trainers</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
              {settings.maxTrainers}
            </p>
          </Card>

          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Max Students</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
              {settings.maxStudents}
            </p>
          </Card>

          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Storage Limit</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
              {settings.storageLimit} GB
            </p>
          </Card>
        </div>

        <div style={{ padding: '1.5rem', backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: '0.375rem' }}>
          <Heading level="h3" style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
            Upgrade Your Plan
          </Heading>
          <p style={{ fontSize: '0.875rem', color: '#666', marginBottom: '1rem' }}>
            Need more trainers, students, or storage? Upgrade to a higher tier plan or contact our sales team for custom enterprise pricing.
          </p>
          <Button variant="primary">
            Contact Sales
          </Button>
        </div>

        <div style={{ padding: '1rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.375rem' }}>
          <p style={{ fontWeight: 600, margin: 0, marginBottom: '0.5rem', color: '#991b1b' }}>
            Danger Zone
          </p>
          <p style={{ fontSize: '0.875rem', color: '#991b1b', marginBottom: '1rem' }}>
            Permanently delete your organization and all associated data. This action cannot be undone.
          </p>
          {!showDeleteConfirm ? (
            <Button variant="danger" onClick={() => setShowDeleteConfirm(true)}>
              Delete Organization
            </Button>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p style={{ fontSize: '0.875rem', color: '#991b1b', fontWeight: 500, margin: 0 }}>
                Type <strong>DELETE</strong> to confirm:
              </p>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="Type DELETE to confirm"
                style={{
                  padding: '0.5rem 0.75rem',
                  border: '1px solid #fecaca',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                  maxWidth: '300px',
                }}
              />
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Button
                  variant="danger"
                  disabled={deleteConfirmText !== 'DELETE' || isDeleting}
                  loading={isDeleting}
                  onClick={async () => {
                    if (!organizationId) return;
                    setIsDeleting(true);
                    setDeleteError(null);
                    try {
                      await organizationService.deleteOrganization(organizationId);
                      dispatch(logoutAction());
                      dispatch(clearUser());
                      navigate('/login');
                    } catch (err) {
                      setDeleteError(
                        err instanceof Error ? err.message : 'Failed to delete organization.'
                      );
                    } finally {
                      setIsDeleting(false);
                    }
                  }}
                >
                  Permanently Delete
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeleteConfirmText('');
                    setDeleteError(null);
                  }}
                >
                  Cancel
                </Button>
              </div>
              {deleteError && (
                <p style={{ fontSize: '0.875rem', color: '#dc2626', margin: 0 }}>
                  {deleteError}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <Heading level="h1" gutterBottom={true}>
              Organization Settings
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              Configure your organization's profile, branding, and policies
            </p>
          </div>
          <Link to="/dashboard/org-admin">
            <Button variant="secondary">
              Back to Dashboard
            </Button>
          </Link>
        </div>

        {/* Tabs */}
        {renderTabs()}

        {/* Tab Content */}
        {activeTab === 'profile' && renderProfileTab()}
        {activeTab === 'branding' && renderBrandingTab()}
        {activeTab === 'training' && renderTrainingTab()}
        {activeTab === 'integrations' && renderIntegrationsTab()}
        {activeTab === 'ai-providers' && renderAIProvidersTab()}
        {activeTab === 'subscription' && renderSubscriptionTab()}
      </main>
    </DashboardLayout>
  );
};
