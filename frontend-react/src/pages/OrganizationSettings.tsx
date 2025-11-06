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
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { useAppSelector } from '../store/hooks';

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

  const [settings, setSettings] = useState<OrganizationSettings>(mockSettings);
  const [activeTab, setActiveTab] = useState<'profile' | 'branding' | 'training' | 'integrations' | 'subscription'>('profile');
  const [isSaving, setIsSaving] = useState(false);

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
            ⚠️ Danger Zone
          </p>
          <p style={{ fontSize: '0.875rem', color: '#991b1b', marginBottom: '1rem' }}>
            Permanently delete your organization and all associated data. This action cannot be undone.
          </p>
          <Button variant="danger">
            Delete Organization
          </Button>
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
        {activeTab === 'subscription' && renderSubscriptionTab()}
      </main>
    </DashboardLayout>
  );
};
