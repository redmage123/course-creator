/**
 * Create Organization Page
 *
 * BUSINESS CONTEXT:
 * Site Admin feature for onboarding new organizations.
 * Multi-step workflow for creating corporate training customers with initial configuration.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Multi-step form for organization setup
 * - Admin account creation
 * - Subscription plan selection
 * - Initial limits configuration
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { useAuth } from '../hooks/useAuth';
import { organizationService } from '../services';

/**
 * Form data interface for organization creation
 */
interface OrganizationFormData {
  // Step 1: Basic Information
  organizationName: string;
  contactEmail: string;
  contactPhone: string;
  website: string;
  address: string;

  // Step 2: Admin Account
  adminFirstName: string;
  adminLastName: string;
  adminEmail: string;
  adminPhone: string;
  adminPassword: string;

  // Step 3: Subscription
  subscriptionPlan: 'Trial' | 'Professional' | 'Enterprise';
  maxTrainers: number;
  maxStudents: number;
  storageLimit: number;
  subscriptionMonths: number;
}

/**
 * Subscription plan presets
 */
const PLAN_PRESETS = {
  Trial: {
    maxTrainers: 3,
    maxStudents: 25,
    storageLimit: 10,
    subscriptionMonths: 1
  },
  Professional: {
    maxTrainers: 10,
    maxStudents: 200,
    storageLimit: 50,
    subscriptionMonths: 12
  },
  Enterprise: {
    maxTrainers: 50,
    maxStudents: 1000,
    storageLimit: 200,
    subscriptionMonths: 12
  }
};

/**
 * Create Organization Page Component
 *
 * WHY THIS APPROACH:
 * - Multi-step form reduces complexity per screen
 * - Plan presets simplify configuration
 * - Admin account creation ensures immediate access
 * - Validation at each step prevents errors
 */
export const CreateOrganization: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [formData, setFormData] = useState<OrganizationFormData>({
    organizationName: '',
    contactEmail: '',
    contactPhone: '',
    website: '',
    address: '',
    adminFirstName: '',
    adminLastName: '',
    adminEmail: '',
    adminPhone: '',
    adminPassword: '',
    subscriptionPlan: 'Professional',
    maxTrainers: 10,
    maxStudents: 200,
    storageLimit: 50,
    subscriptionMonths: 12
  });

  /**
   * Handle input change
   */
  const handleInputChange = (field: keyof OrganizationFormData, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  /**
   * Handle plan selection
   */
  const handlePlanSelect = (plan: 'Trial' | 'Professional' | 'Enterprise') => {
    const preset = PLAN_PRESETS[plan];
    setFormData(prev => ({
      ...prev,
      subscriptionPlan: plan,
      maxTrainers: preset.maxTrainers,
      maxStudents: preset.maxStudents,
      storageLimit: preset.storageLimit,
      subscriptionMonths: preset.subscriptionMonths
    }));
  };

  /**
   * Generate URL-friendly slug from organization name
   */
  const generateSlug = (name: string): string => {
    return name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .substring(0, 100);
  };

  /**
   * Handle form submission - calls real API
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (currentStep < 3) {
      setCurrentStep((currentStep + 1) as 1 | 2 | 3);
      return;
    }

    try {
      setIsSubmitting(true);

      const payload = {
        name: formData.organizationName,
        slug: generateSlug(formData.organizationName),
        contact_email: formData.contactEmail,
        contact_phone: formData.contactPhone,
        address: formData.address || undefined,
        domain: formData.website ? formData.website.replace(/^https?:\/\//, '') : undefined,
        admin_full_name: `${formData.adminFirstName} ${formData.adminLastName}`.trim(),
        admin_email: formData.adminEmail,
        admin_phone: formData.adminPhone || undefined,
        admin_password: formData.adminPassword,
        admin_role: 'organization_admin',
      };

      await organizationService.registerOrganization(payload);

      // Invalidate memberships cache so new org appears in org switcher
      queryClient.invalidateQueries({ queryKey: ['user-memberships'] });
      queryClient.invalidateQueries({ queryKey: ['organizations'] });

      // Navigate to dashboard — user can switch to new org via org switcher
      navigate('/dashboard');
    } catch (err: any) {
      console.error('Failed to create organization:', err);
      const message = err?.response?.data?.detail || err?.message || 'Failed to create organization. Please try again.';
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * Progress indicator
   */
  const renderProgressBar = () => (
    <div style={{ marginBottom: '2rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
        {[1, 2, 3].map(step => (
          <div key={step} style={{
            flex: 1,
            textAlign: 'center',
            fontSize: '0.875rem',
            fontWeight: currentStep === step ? 600 : 400,
            color: currentStep >= step ? '#3b82f6' : '#9ca3af'
          }}>
            Step {step}
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        {[1, 2, 3].map(step => (
          <div key={step} style={{
            flex: 1,
            height: '4px',
            backgroundColor: currentStep >= step ? '#3b82f6' : '#e5e7eb',
            borderRadius: '2px',
            transition: 'background-color 0.3s'
          }} />
        ))}
      </div>
    </div>
  );

  /**
   * Step 1: Basic Information
   */
  const renderStep1 = () => (
    <>
      <Heading level="h2" style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>
        Basic Information
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div>
          <label htmlFor="organizationName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Organization Name *
          </label>
          <Input
            id="organizationName"
            name="organizationName"
            type="text"
            placeholder="Acme Corporation"
            value={formData.organizationName}
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
              placeholder="contact@acme.com"
              value={formData.contactEmail}
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
              placeholder="+1 (555) 123-4567"
              value={formData.contactPhone}
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
            placeholder="https://acme.com"
            value={formData.website}
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
            placeholder="123 Business St, City, State 12345"
            value={formData.address}
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
      </div>
    </>
  );

  /**
   * Step 2: Admin Account
   */
  const renderStep2 = () => (
    <>
      <Heading level="h2" style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>
        Administrator Account
      </Heading>

      <p style={{ fontSize: '0.875rem', color: '#666', marginBottom: '1.5rem' }}>
        Create the initial administrator account for this organization. They will receive an email with login instructions.
      </p>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="adminFirstName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              First Name *
            </label>
            <Input
              id="adminFirstName"
              name="adminFirstName"
              type="text"
              placeholder="John"
              value={formData.adminFirstName}
              onChange={(e) => handleInputChange('adminFirstName', e.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="adminLastName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Last Name *
            </label>
            <Input
              id="adminLastName"
              name="adminLastName"
              type="text"
              placeholder="Smith"
              value={formData.adminLastName}
              onChange={(e) => handleInputChange('adminLastName', e.target.value)}
              required
            />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
          <div>
            <label htmlFor="adminEmail" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Email Address *
            </label>
            <Input
              id="adminEmail"
              name="adminEmail"
              type="email"
              placeholder="john.smith@acme.com"
              value={formData.adminEmail}
              onChange={(e) => handleInputChange('adminEmail', e.target.value)}
              required
            />
            <p style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.25rem' }}>
              Login credentials will be sent to this email
            </p>
          </div>

          <div>
            <label htmlFor="adminPhone" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
              Phone Number
            </label>
            <Input
              id="adminPhone"
              name="adminPhone"
              type="tel"
              placeholder="+1 (555) 987-6543"
              value={formData.adminPhone}
              onChange={(e) => handleInputChange('adminPhone', e.target.value)}
            />
          </div>
        </div>

        <div>
          <label htmlFor="adminPassword" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
            Admin Password *
          </label>
          <Input
            id="adminPassword"
            name="adminPassword"
            type="password"
            placeholder="Minimum 8 characters"
            value={formData.adminPassword}
            onChange={(e) => handleInputChange('adminPassword', e.target.value)}
            required
          />
          <p style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.25rem' }}>
            Password for the organization admin account (min 8 characters)
          </p>
        </div>
      </div>
    </>
  );

  /**
   * Step 3: Subscription & Limits
   */
  const renderStep3 = () => (
    <>
      <Heading level="h2" style={{ fontSize: '1.5rem', marginBottom: '1.5rem' }}>
        Subscription & Limits
      </Heading>

      <div style={{ display: 'grid', gap: '1.5rem' }}>
        {/* Plan Selection */}
        <div>
          <label style={{ display: 'block', fontWeight: 500, marginBottom: '1rem' }}>
            Select Plan *
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            {Object.keys(PLAN_PRESETS).map(plan => (
              <button
                key={plan}
                type="button"
                onClick={() => handlePlanSelect(plan as any)}
                style={{
                  padding: '1.5rem',
                  border: formData.subscriptionPlan === plan ? '2px solid #3b82f6' : '1px solid #d1d5db',
                  borderRadius: '0.5rem',
                  backgroundColor: formData.subscriptionPlan === plan ? '#eff6ff' : 'white',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textAlign: 'left'
                }}
              >
                <p style={{ fontWeight: 600, fontSize: '1.1rem', margin: '0 0 0.5rem 0' }}>{plan}</p>
                <p style={{ fontSize: '0.875rem', color: '#666', margin: 0 }}>
                  {PLAN_PRESETS[plan as keyof typeof PLAN_PRESETS].maxTrainers} trainers<br />
                  {PLAN_PRESETS[plan as keyof typeof PLAN_PRESETS].maxStudents} students<br />
                  {PLAN_PRESETS[plan as keyof typeof PLAN_PRESETS].storageLimit} GB storage
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Custom Limits */}
        <div style={{ padding: '1rem', backgroundColor: '#f9fafb', borderRadius: '0.5rem' }}>
          <p style={{ fontWeight: 500, marginBottom: '1rem' }}>Custom Limits (Optional)</p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <div>
              <label htmlFor="maxTrainers" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                Max Trainers
              </label>
              <Input
                id="maxTrainers"
                name="maxTrainers"
                type="number"
                min="1"
                value={formData.maxTrainers}
                onChange={(e) => handleInputChange('maxTrainers', parseInt(e.target.value))}
              />
            </div>

            <div>
              <label htmlFor="maxStudents" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                Max Students
              </label>
              <Input
                id="maxStudents"
                name="maxStudents"
                type="number"
                min="1"
                value={formData.maxStudents}
                onChange={(e) => handleInputChange('maxStudents', parseInt(e.target.value))}
              />
            </div>

            <div>
              <label htmlFor="storageLimit" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                Storage (GB)
              </label>
              <Input
                id="storageLimit"
                name="storageLimit"
                type="number"
                min="1"
                value={formData.storageLimit}
                onChange={(e) => handleInputChange('storageLimit', parseInt(e.target.value))}
              />
            </div>

            <div>
              <label htmlFor="subscriptionMonths" style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                Duration (Months)
              </label>
              <Input
                id="subscriptionMonths"
                name="subscriptionMonths"
                type="number"
                min="1"
                max="36"
                value={formData.subscriptionMonths}
                onChange={(e) => handleInputChange('subscriptionMonths', parseInt(e.target.value))}
              />
            </div>
          </div>
        </div>

        {/* Summary */}
        <div style={{ padding: '1rem', backgroundColor: '#f0f9ff', border: '1px solid #bae6fd', borderRadius: '0.5rem' }}>
          <p style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#0c4a6e' }}>Summary</p>
          <p style={{ fontSize: '0.875rem', color: '#0c4a6e', margin: 0 }}>
            Organization: <strong>{formData.organizationName || 'Not specified'}</strong><br />
            Admin: <strong>{formData.adminFirstName} {formData.adminLastName}</strong> ({formData.adminEmail})<br />
            Plan: <strong>{formData.subscriptionPlan}</strong> - {formData.subscriptionMonths} month(s)<br />
            Limits: <strong>{formData.maxTrainers}</strong> trainers, <strong>{formData.maxStudents}</strong> students, <strong>{formData.storageLimit}</strong> GB
          </p>
        </div>
      </div>
    </>
  );

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <Heading level="h1" gutterBottom={true}>
              Create New Organization
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              Onboard a new corporate training customer
            </p>
          </div>
          <Link to={user?.role === 'site_admin' ? '/admin/organizations' : '/dashboard'}>
            <Button variant="secondary">
              Cancel
            </Button>
          </Link>
        </div>

        {/* Form */}
        <Card variant="outlined" padding="large">
          <form onSubmit={handleSubmit}>
            {renderProgressBar()}

            {currentStep === 1 && renderStep1()}
            {currentStep === 2 && renderStep2()}
            {currentStep === 3 && renderStep3()}

            {/* Error Display */}
            {submitError && (
              <div style={{
                padding: '0.75rem 1rem',
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: '0.375rem',
                color: '#dc2626',
                fontSize: '0.875rem',
                marginTop: '1rem'
              }}>
                {submitError}
              </div>
            )}

            {/* Navigation Buttons */}
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'space-between', paddingTop: '2rem', borderTop: '1px solid #e5e7eb', marginTop: '2rem' }}>
              <div>
                {currentStep > 1 && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => setCurrentStep((currentStep - 1) as 1 | 2 | 3)}
                  >
                    Previous
                  </Button>
                )}
              </div>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Creating...' : currentStep < 3 ? 'Next' : 'Create Organization'}
              </Button>
            </div>
          </form>
        </Card>
      </main>
    </DashboardLayout>
  );
};
