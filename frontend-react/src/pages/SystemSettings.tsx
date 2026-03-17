/**
 * System Settings Page
 *
 * BUSINESS CONTEXT:
 * Site Admin feature for platform-wide configuration.
 * Controls system behavior, integrations, security, and maintenance operations.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Platform-wide settings management
 * - Email, storage, and payment integrations
 * - Security and compliance configuration
 * - Maintenance mode and system operations
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';

/**
 * System Settings Interface
 * Represents platform-wide configuration
 */
interface SystemSettings {
  // General
  platformName: string;
  supportEmail: string;
  supportUrl: string;
  defaultLanguage: string;

  // Email Configuration
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpPassword: string;
  fromEmail: string;
  fromName: string;

  // Storage Configuration
  storageProvider: 'local' | 's3' | 'azure';
  s3Bucket?: string;
  s3Region?: string;
  s3AccessKey?: string;
  maxFileSize: number; // MB

  // Security
  sessionTimeout: number; // minutes
  passwordMinLength: number;
  requireMFA: boolean;
  allowPasswordReset: boolean;
  maxLoginAttempts: number;

  // Features
  enableCourseGeneration: boolean;
  enableLabEnvironments: boolean;
  enableCertificates: boolean;
  enableAnalytics: boolean;

  // Maintenance
  maintenanceMode: boolean;
  maintenanceMessage: string;
}

/**
 * Mock system settings
 * In production, this would come from the API
 */
const mockSettings: SystemSettings = {
  platformName: 'Course Creator Platform',
  supportEmail: 'support@example.com',
  supportUrl: 'https://support.example.com',
  defaultLanguage: 'en',
  smtpHost: 'smtp.example.com',
  smtpPort: 587,
  smtpUsername: 'noreply@example.com',
  smtpPassword: '••••••••',
  fromEmail: 'noreply@example.com',
  fromName: 'Course Creator',
  storageProvider: 's3',
  s3Bucket: 'course-creator-storage',
  s3Region: 'us-east-1',
  s3AccessKey: '••••••••',
  maxFileSize: 100,
  sessionTimeout: 60,
  passwordMinLength: 8,
  requireMFA: false,
  allowPasswordReset: true,
  maxLoginAttempts: 5,
  enableCourseGeneration: true,
  enableLabEnvironments: true,
  enableCertificates: true,
  enableAnalytics: true,
  maintenanceMode: false,
  maintenanceMessage: 'The platform is currently undergoing maintenance. Please check back soon.'
};

/**
 * System Settings Page Component
 *
 * WHY THIS APPROACH:
 * - Tabbed interface for logical grouping
 * - Critical settings clearly marked
 * - Confirmation for dangerous operations
 * - Comprehensive platform control
 */
export const SystemSettings: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings>(mockSettings);
  const [activeTab, setActiveTab] = useState<'general' | 'email' | 'storage' | 'security' | 'features' | 'maintenance'>('general');
  const [isSaving, setIsSaving] = useState(false);

  /**
   * Handle settings update
   */
  const handleUpdateSettings = async (section: string) => {
    setIsSaving(true);
    try {
      // TODO: Implement API call to update system settings
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
  const handleInputChange = (field: keyof SystemSettings, value: any) => {
    setSettings(prev => ({ ...prev, [field]: value }));
  };

  /**
   * Tab navigation component
   */
  const renderTabs = () => {
    const tabs = [
      { id: 'general', label: 'General', icon: '⚙️' },
      { id: 'email', label: 'Email', icon: '📧' },
      { id: 'storage', label: 'Storage', icon: '💾' },
      { id: 'security', label: 'Security', icon: '🔒' },
      { id: 'features', label: 'Features', icon: '✨' },
      { id: 'maintenance', label: 'Maintenance', icon: '🔧' }
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
   * General settings tab
   */
  const renderGeneralTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        General Settings
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div>
          <label htmlFor="platformName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Platform Name *
          </label>
          <Input
            id="platformName"
            name="platformName"
            type="text"
            value={settings.platformName}
            onChange={(e) => handleInputChange('platformName', e.target.value)}
            required
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="supportEmail" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Support Email *
            </label>
            <Input
              id="supportEmail"
              name="supportEmail"
              type="email"
              value={settings.supportEmail}
              onChange={(e) => handleInputChange('supportEmail', e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="supportUrl" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Support URL
            </label>
            <Input
              id="supportUrl"
              name="supportUrl"
              type="url"
              value={settings.supportUrl}
              onChange={(e) => handleInputChange('supportUrl', e.target.value)}
            />
          </div>
        </div>

        <div>
          <label htmlFor="defaultLanguage" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Default Language
          </label>
          <select
            id="defaultLanguage"
            name="defaultLanguage"
            value={settings.defaultLanguage}
            onChange={(e) => handleInputChange('defaultLanguage', e.target.value)}
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '0.875rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              backgroundColor: 'white'
            }}
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="zh">Chinese</option>
          </select>
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('General')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save General Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Email settings tab
   */
  const renderEmailTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Email Configuration
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="smtpHost" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              SMTP Host *
            </label>
            <Input
              id="smtpHost"
              name="smtpHost"
              type="text"
              placeholder="smtp.example.com"
              value={settings.smtpHost}
              onChange={(e) => handleInputChange('smtpHost', e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="smtpPort" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              SMTP Port *
            </label>
            <Input
              id="smtpPort"
              name="smtpPort"
              type="number"
              value={settings.smtpPort}
              onChange={(e) => handleInputChange('smtpPort', parseInt(e.target.value))}
              required
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="smtpUsername" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              SMTP Username
            </label>
            <Input
              id="smtpUsername"
              name="smtpUsername"
              type="text"
              value={settings.smtpUsername}
              onChange={(e) => handleInputChange('smtpUsername', e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="smtpPassword" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              SMTP Password
            </label>
            <Input
              id="smtpPassword"
              name="smtpPassword"
              type="password"
              value={settings.smtpPassword}
              onChange={(e) => handleInputChange('smtpPassword', e.target.value)}
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="fromEmail" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              From Email *
            </label>
            <Input
              id="fromEmail"
              name="fromEmail"
              type="email"
              placeholder="noreply@example.com"
              value={settings.fromEmail}
              onChange={(e) => handleInputChange('fromEmail', e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="fromName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              From Name *
            </label>
            <Input
              id="fromName"
              name="fromName"
              type="text"
              placeholder="Course Creator"
              value={settings.fromName}
              onChange={(e) => handleInputChange('fromName', e.target.value)}
              required
            />
          </div>
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Email')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Email Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Storage settings tab
   */
  const renderStorageTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Storage Configuration
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div>
          <label htmlFor="storageProvider" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Storage Provider *
          </label>
          <select
            id="storageProvider"
            name="storageProvider"
            value={settings.storageProvider}
            onChange={(e) => handleInputChange('storageProvider', e.target.value)}
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '0.875rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              backgroundColor: 'white'
            }}
          >
            <option value="local">Local Storage</option>
            <option value="s3">Amazon S3</option>
            <option value="azure">Azure Blob Storage</option>
          </select>
        </div>

        {settings.storageProvider === 's3' && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
              <div>
                <label htmlFor="s3Bucket" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                  S3 Bucket Name
                </label>
                <Input
                  id="s3Bucket"
                  name="s3Bucket"
                  type="text"
                  value={settings.s3Bucket}
                  onChange={(e) => handleInputChange('s3Bucket', e.target.value)}
                />
              </div>

              <div>
                <label htmlFor="s3Region" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                  S3 Region
                </label>
                <Input
                  id="s3Region"
                  name="s3Region"
                  type="text"
                  value={settings.s3Region}
                  onChange={(e) => handleInputChange('s3Region', e.target.value)}
                />
              </div>
            </div>

            <div>
              <label htmlFor="s3AccessKey" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                S3 Access Key
              </label>
              <Input
                id="s3AccessKey"
                name="s3AccessKey"
                type="password"
                value={settings.s3AccessKey}
                onChange={(e) => handleInputChange('s3AccessKey', e.target.value)}
              />
            </div>
          </>
        )}

        <div>
          <label htmlFor="maxFileSize" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Max File Size (MB)
          </label>
          <Input
            id="maxFileSize"
            name="maxFileSize"
            type="number"
            min="1"
            max="1000"
            value={settings.maxFileSize}
            onChange={(e) => handleInputChange('maxFileSize', parseInt(e.target.value))}
          />
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Storage')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Storage Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Security settings tab
   */
  const renderSecurityTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Security Settings
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="sessionTimeout" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Session Timeout (minutes)
            </label>
            <Input
              id="sessionTimeout"
              name="sessionTimeout"
              type="number"
              min="5"
              max="1440"
              value={settings.sessionTimeout}
              onChange={(e) => handleInputChange('sessionTimeout', parseInt(e.target.value))}
            />
          </div>

          <div>
            <label htmlFor="passwordMinLength" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Min Password Length
            </label>
            <Input
              id="passwordMinLength"
              name="passwordMinLength"
              type="number"
              min="6"
              max="32"
              value={settings.passwordMinLength}
              onChange={(e) => handleInputChange('passwordMinLength', parseInt(e.target.value))}
            />
          </div>

          <div>
            <label htmlFor="maxLoginAttempts" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Max Login Attempts
            </label>
            <Input
              id="maxLoginAttempts"
              name="maxLoginAttempts"
              type="number"
              min="3"
              max="10"
              value={settings.maxLoginAttempts}
              onChange={(e) => handleInputChange('maxLoginAttempts', parseInt(e.target.value))}
            />
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Require Multi-Factor Authentication (MFA)</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              All users must enable MFA to access the platform
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.requireMFA}
            onChange={(e) => handleInputChange('requireMFA', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Allow Password Reset</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Users can request password reset via email
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.allowPasswordReset}
            onChange={(e) => handleInputChange('allowPasswordReset', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Security')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Security Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Features settings tab
   */
  const renderFeaturesTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Platform Features
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>AI Course Generation</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Enable AI-powered course and content generation
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.enableCourseGeneration}
            onChange={(e) => handleInputChange('enableCourseGeneration', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Lab Environments</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Enable interactive coding lab environments
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.enableLabEnvironments}
            onChange={(e) => handleInputChange('enableLabEnvironments', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Certificates</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Enable course completion certificates
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.enableCertificates}
            onChange={(e) => handleInputChange('enableCertificates', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Analytics</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Enable learning analytics and reporting
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.enableAnalytics}
            onChange={(e) => handleInputChange('enableAnalytics', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="primary"
            onClick={() => handleUpdateSettings('Features')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Feature Settings'}
          </Button>
        </div>
      </div>
    </Card>
  );

  /**
   * Maintenance settings tab
   */
  const renderMaintenanceTab = () => (
    <Card variant="outlined" padding="large">
      <Heading level="h2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
        Maintenance Mode
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ padding: '1rem', backgroundColor: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.5rem' }}>
          <p style={{ fontWeight: 600, margin: 0, marginBottom: '0.5rem', color: '#991b1b' }}>
            ⚠️ Warning: Maintenance Mode
          </p>
          <p style={{ fontSize: '0.875rem', color: '#991b1b', margin: 0 }}>
            Enabling maintenance mode will prevent all users (except site admins) from accessing the platform.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.375rem' }}>
          <div>
            <p style={{ fontWeight: 500, margin: 0, marginBottom: '0.25rem' }}>Enable Maintenance Mode</p>
            <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
              Put the platform in maintenance mode
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.maintenanceMode}
            onChange={(e) => handleInputChange('maintenanceMode', e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
        </div>

        <div>
          <label htmlFor="maintenanceMessage" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Maintenance Message
          </label>
          <textarea
            id="maintenanceMessage"
            name="maintenanceMessage"
            value={settings.maintenanceMessage}
            onChange={(e) => handleInputChange('maintenanceMessage', e.target.value)}
            rows={4}
            style={{
              width: '100%',
              padding: '0.75rem',
              fontSize: '0.875rem',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              fontFamily: 'inherit'
            }}
          />
          <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
            This message will be displayed to users during maintenance
          </p>
        </div>

        <div style={{ paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
          <Button
            variant="danger"
            onClick={() => handleUpdateSettings('Maintenance')}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Update Maintenance Settings'}
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
              System Settings
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              Configure platform-wide settings and integrations
            </p>
          </div>
          <Link to="/dashboard/site-admin">
            <Button variant="secondary">
              Back to Dashboard
            </Button>
          </Link>
        </div>

        {/* Tabs */}
        {renderTabs()}

        {/* Tab Content */}
        {activeTab === 'general' && renderGeneralTab()}
        {activeTab === 'email' && renderEmailTab()}
        {activeTab === 'storage' && renderStorageTab()}
        {activeTab === 'security' && renderSecurityTab()}
        {activeTab === 'features' && renderFeaturesTab()}
        {activeTab === 'maintenance' && renderMaintenanceTab()}
      </main>
    </DashboardLayout>
  );
};
