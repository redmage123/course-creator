/**
 * Organization Registration Page
 *
 * BUSINESS CONTEXT:
 * Public self-service registration for organizations to join the platform.
 * After registration, the admin user is auto-logged in and redirected to org admin dashboard.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Multi-section form with validation
 * - File upload for organization logo
 * - Auto-generates slug from organization name
 * - Creates organization + admin account in single transaction
 * - JWT token auto-stored after successful registration
 *
 * SECURITY:
 * - Password strength requirements
 * - Email validation
 * - Duplicate org name/slug detection
 * - CSRF protection via API client
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { Textarea } from '../components/atoms/Textarea';
import { Select } from '../components/atoms/Select';
import { Spinner } from '../components/atoms/Spinner';
import { organizationService } from '../services/organizationService';
import { authService } from '../services/authService';
import styles from './OrganizationRegistration.module.css';

/**
 * Organization Registration Form Data Interface
 */
interface OrganizationRegistrationForm {
  // Organization Details
  name: string;
  slug: string;
  description: string;
  domain: string;
  logo: File | null;

  // Organization Address
  street_address: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;

  // Contact Information
  contact_phone_country: string;
  contact_phone: string;
  contact_email: string;

  // Admin Account
  admin_full_name: string;
  admin_username: string;
  admin_email: string;
  admin_password: string;
  admin_password_confirm: string;

  // Terms & Conditions
  terms_accepted: boolean;
  privacy_accepted: boolean;
}

/**
 * Form Validation Errors Interface
 */
interface FormErrors {
  [key: string]: string;
}

/**
 * Organization Registration Page Component
 *
 * WHY THIS APPROACH:
 * - Multi-section form for better UX (organization, contact, admin, terms)
 * - Real-time validation feedback
 * - Auto-slug generation from organization name
 * - Logo preview before upload
 * - Comprehensive error handling
 */
export const OrganizationRegistration: React.FC = () => {
  const navigate = useNavigate();
  const logoInputRef = useRef<HTMLInputElement>(null);

  // Form state
  const [formData, setFormData] = useState<OrganizationRegistrationForm>({
    name: '',
    slug: '',
    description: '',
    domain: '',
    logo: null,
    street_address: '',
    city: '',
    state_province: '',
    postal_code: '',
    country: '',
    contact_phone_country: '+1',
    contact_phone: '',
    contact_email: '',
    admin_full_name: '',
    admin_username: '',
    admin_email: '',
    admin_password: '',
    admin_password_confirm: '',
    terms_accepted: false,
    privacy_accepted: false,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [slugGenerated, setSlugGenerated] = useState(false);

  /**
   * Auto-generate slug from organization name
   */
  useEffect(() => {
    if (formData.name && !slugGenerated) {
      const generatedSlug = formData.name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');

      setFormData(prev => ({ ...prev, slug: generatedSlug }));
    }
  }, [formData.name, slugGenerated]);

  /**
   * Handle input changes
   */
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }

    // If user manually edits slug, mark as manually edited
    if (name === 'slug') {
      setSlugGenerated(true);
    }
  };

  /**
   * Handle Select component changes
   * Select components pass value directly, not as an event
   */
  const handleSelectChange = (name: string) => (value: string | string[]) => {
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  /**
   * Handle logo file selection
   */
  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];

    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setErrors(prev => ({ ...prev, logo: 'Please select an image file' }));
        return;
      }

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setErrors(prev => ({ ...prev, logo: 'Logo file must be less than 5MB' }));
        return;
      }

      setFormData(prev => ({ ...prev, logo: file }));

      // Generate preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);

      // Clear logo error
      if (errors.logo) {
        setErrors(prev => {
          const newErrors = { ...prev };
          delete newErrors.logo;
          return newErrors;
        });
      }
    }
  };

  /**
   * Remove selected logo
   */
  const handleRemoveLogo = () => {
    setFormData(prev => ({ ...prev, logo: null }));
    setLogoPreview(null);
    if (logoInputRef.current) {
      logoInputRef.current.value = '';
    }
  };

  /**
   * Validate form fields
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Required organization fields
    if (!formData.name.trim()) {
      newErrors.name = 'Organization name is required';
    }
    if (!formData.slug.trim()) {
      newErrors.slug = 'Organization slug is required';
    }
    if (!formData.domain.trim()) {
      newErrors.domain = 'Organization domain is required';
    }
    if (!formData.country) {
      newErrors.country = 'Country is required';
    }

    // Required contact fields
    if (!formData.contact_email.trim()) {
      newErrors.contact_email = 'Contact email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      newErrors.contact_email = 'Invalid email format';
    }

    // Required admin fields
    if (!formData.admin_full_name.trim()) {
      newErrors.admin_full_name = 'Admin name is required';
    }
    if (!formData.admin_username.trim()) {
      newErrors.admin_username = 'Admin username is required';
    }
    if (!formData.admin_email.trim()) {
      newErrors.admin_email = 'Admin email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
      newErrors.admin_email = 'Invalid email format';
    }

    // Password validation
    if (!formData.admin_password) {
      newErrors.admin_password = 'Password is required';
    } else if (formData.admin_password.length < 8) {
      newErrors.admin_password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.admin_password)) {
      newErrors.admin_password = 'Password must contain uppercase, lowercase, and number';
    }

    if (formData.admin_password !== formData.admin_password_confirm) {
      newErrors.admin_password_confirm = 'Passwords do not match';
    }

    // Terms acceptance
    if (!formData.terms_accepted) {
      newErrors.terms_accepted = 'You must accept the Terms of Service';
    }
    if (!formData.privacy_accepted) {
      newErrors.privacy_accepted = 'You must accept the Privacy Policy';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      setSubmitError('Please fix the errors above before submitting');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Create FormData for file upload
      const submitData = new FormData();

      // Append organization fields
      submitData.append('name', formData.name);
      submitData.append('slug', formData.slug);
      submitData.append('description', formData.description);
      submitData.append('domain', formData.domain);
      if (formData.logo) {
        submitData.append('logo', formData.logo);
      }

      // Append address fields
      submitData.append('street_address', formData.street_address);
      submitData.append('city', formData.city);
      submitData.append('state_province', formData.state_province);
      submitData.append('postal_code', formData.postal_code);
      submitData.append('country', formData.country);

      // Append contact fields
      submitData.append('contact_phone_country', formData.contact_phone_country);
      submitData.append('contact_phone', formData.contact_phone);
      submitData.append('contact_email', formData.contact_email);

      // Append admin fields
      submitData.append('admin_full_name', formData.admin_full_name);
      submitData.append('admin_username', formData.admin_username);
      submitData.append('admin_email', formData.admin_email);
      submitData.append('admin_password', formData.admin_password);

      // Call organization registration API
      const response = await organizationService.registerOrganization(submitData);

      // Registration successful - redirect to login page
      // Note: Backend creates admin user but doesn't return access token for security
      // User must log in manually with the credentials they provided
      navigate('/login?message=registration_success');
    } catch (error: any) {
      console.error('Organization registration error:', error);

      if (error.response?.data?.detail) {
        setSubmitError(error.response.data.detail);
      } else if (error.response?.data?.message) {
        setSubmitError(error.response.data.message);
      } else {
        setSubmitError('Failed to register organization. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.registrationContainer}>
      <Link to="/" className={styles.backLink}>
        <i className="fas fa-arrow-left"></i>
        Back to Homepage
      </Link>

      <Card className={styles.registrationCard}>
        <div className={styles.registrationHeader}>
          <Heading level="h1" className={styles.title}>
            Register Your Organization
          </Heading>
          <p className={styles.subtitle}>
            Join the Course Creator Platform and start delivering world-class training programs
          </p>
          <div className={styles.professionalBadge}>
            <i className="fas fa-check-circle"></i>
            Professional Training Platform
          </div>
        </div>

        <form onSubmit={handleSubmit} className={styles.form}>
          {/* Organization Details Section */}
          <div className={styles.formSection}>
            <div className={styles.sectionTitle}>
              <i className="fas fa-building"></i>
              Organization Details
            </div>

            <div className={styles.formGrid}>
              <Input
                label="Organization Name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                error={errors.name}
                required
                placeholder="Enter your organization name"
              />

              <Input
                label="Organization Slug"
                name="slug"
                value={formData.slug}
                onChange={handleInputChange}
                error={errors.slug}
                required
                placeholder="organization-slug"
                helpText="Used in URLs. Auto-generated from name."
              />
            </div>

            <div className={styles.formGridSingle}>
              <Textarea
                label="Organization Description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                error={errors.description}
                placeholder="Brief description of your organization"
                helpText="Optional: Tell us about your organization"
              />

              <Input
                label="Organization Domain"
                name="domain"
                value={formData.domain}
                onChange={handleInputChange}
                error={errors.domain}
                required
                placeholder="example.com"
                helpText="Your organization's website domain"
              />
            </div>

            {/* Logo Upload */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>
                Organization Logo
                <span className={styles.optional}>(Optional)</span>
              </label>

              <div className={styles.logoUploadArea} onClick={() => logoInputRef.current?.click()}>
                {logoPreview ? (
                  <div className={styles.logoPreview}>
                    <img src={logoPreview} alt="Logo preview" className={styles.previewImage} />
                    <Button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveLogo();
                      }}
                      variant="danger"
                      size="small"
                      className={styles.removeLogo}
                    >
                      <i className="fas fa-times"></i>
                      Remove
                    </Button>
                  </div>
                ) : (
                  <div className={styles.uploadPlaceholder}>
                    <i className="fas fa-cloud-upload-alt fa-3x"></i>
                    <p>Click to upload logo or drag and drop</p>
                    <small>PNG, JPG, GIF up to 5MB</small>
                  </div>
                )}
              </div>

              <input
                ref={logoInputRef}
                type="file"
                accept="image/*"
                onChange={handleLogoChange}
                className={styles.hiddenFileInput}
              />

              {errors.logo && <p className={styles.error}>{errors.logo}</p>}
            </div>
          </div>

          {/* Organization Address Section */}
          <div className={styles.formSection}>
            <div className={styles.sectionTitle}>
              <i className="fas fa-map-marker-alt"></i>
              Organization Address
            </div>

            <div className={styles.formGridSingle}>
              <Input
                label="Street Address"
                name="street_address"
                value={formData.street_address}
                onChange={handleInputChange}
                error={errors.street_address}
                placeholder="Street address"
              />
            </div>

            <div className={styles.formGrid}>
              <Input
                label="City"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                error={errors.city}
                placeholder="City"
              />

              <Input
                label="State/Province"
                name="state_province"
                value={formData.state_province}
                onChange={handleInputChange}
                error={errors.state_province}
                placeholder="State or Province"
              />

              <Input
                label="Postal Code"
                name="postal_code"
                value={formData.postal_code}
                onChange={handleInputChange}
                error={errors.postal_code}
                placeholder="Postal code"
              />

              <Select
                label="Country"
                name="country"
                value={formData.country}
                onChange={handleSelectChange('country')}
                error={errors.country}
                required
                options={[
                  { value: '', label: 'Select Country' },
                  { value: 'US', label: 'United States' },
                  { value: 'CA', label: 'Canada' },
                  { value: 'GB', label: 'United Kingdom' },
                  { value: 'AU', label: 'Australia' },
                  { value: 'DE', label: 'Germany' },
                  { value: 'FR', label: 'France' },
                  { value: 'IN', label: 'India' },
                  { value: 'JP', label: 'Japan' },
                  { value: 'Other', label: 'Other' },
                ]}
              />
            </div>
          </div>

          {/* Contact Information Section */}
          <div className={styles.formSection}>
            <div className={styles.sectionTitle}>
              <i className="fas fa-phone"></i>
              Contact Information
            </div>

            <div className={styles.formGrid}>
              <div className={styles.phoneGroup}>
                <Select
                  label="Phone Country"
                  name="contact_phone_country"
                  value={formData.contact_phone_country}
                  onChange={handleSelectChange('contact_phone_country')}
                  required
                  options={[
                    { value: '+1', label: '+1 (US/CA)' },
                    { value: '+44', label: '+44 (UK)' },
                    { value: '+61', label: '+61 (AU)' },
                    { value: '+49', label: '+49 (DE)' },
                    { value: '+33', label: '+33 (FR)' },
                    { value: '+91', label: '+91 (IN)' },
                    { value: '+81', label: '+81 (JP)' },
                  ]}
                  className={styles.countryCodeSelect}
                />

                <Input
                  label="Phone Number"
                  name="contact_phone"
                  value={formData.contact_phone}
                  onChange={handleInputChange}
                  error={errors.contact_phone}
                  placeholder="Phone number"
                  type="tel"
                />
              </div>

              <Input
                label="Contact Email"
                name="contact_email"
                value={formData.contact_email}
                onChange={handleInputChange}
                error={errors.contact_email}
                required
                placeholder="contact@example.com"
                type="email"
              />
            </div>
          </div>

          {/* Admin Account Section */}
          <div className={styles.formSection}>
            <div className={styles.sectionTitle}>
              <i className="fas fa-user-shield"></i>
              Administrator Account
            </div>

            <p className={styles.sectionDescription}>
              Create the primary administrator account for your organization. This account will have full access to manage users, courses, and settings.
            </p>

            <div className={styles.formGrid}>
              <Input
                label="Full Name"
                name="admin_full_name"
                value={formData.admin_full_name}
                onChange={handleInputChange}
                error={errors.admin_full_name}
                required
                placeholder="John Doe"
              />

              <Input
                label="Username"
                name="admin_username"
                value={formData.admin_username}
                onChange={handleInputChange}
                error={errors.admin_username}
                required
                placeholder="admin_username"
              />

              <Input
                label="Email"
                name="admin_email"
                value={formData.admin_email}
                onChange={handleInputChange}
                error={errors.admin_email}
                required
                placeholder="admin@example.com"
                type="email"
              />

              <div></div> {/* Empty grid cell for layout */}

              <Input
                label="Password"
                name="admin_password"
                value={formData.admin_password}
                onChange={handleInputChange}
                error={errors.admin_password}
                required
                placeholder="Create a strong password"
                type="password"
                helpText="Min 8 chars, uppercase, lowercase, and number"
              />

              <Input
                label="Confirm Password"
                name="admin_password_confirm"
                value={formData.admin_password_confirm}
                onChange={handleInputChange}
                error={errors.admin_password_confirm}
                required
                placeholder="Confirm your password"
                type="password"
              />
            </div>
          </div>

          {/* Terms & Conditions */}
          <div className={styles.formSection}>
            <div className={styles.sectionTitle}>
              <i className="fas fa-file-contract"></i>
              Terms & Conditions
            </div>

            <div className={styles.checkboxGroup}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="terms_accepted"
                  checked={formData.terms_accepted}
                  onChange={handleInputChange}
                  className={styles.checkbox}
                />
                <span>
                  I accept the <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a>
                  <span className={styles.required}>*</span>
                </span>
              </label>
              {errors.terms_accepted && <p className={styles.error}>{errors.terms_accepted}</p>}

              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  name="privacy_accepted"
                  checked={formData.privacy_accepted}
                  onChange={handleInputChange}
                  className={styles.checkbox}
                />
                <span>
                  I accept the <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
                  <span className={styles.required}>*</span>
                </span>
              </label>
              {errors.privacy_accepted && <p className={styles.error}>{errors.privacy_accepted}</p>}
            </div>
          </div>

          {/* Submit Section */}
          <div className={styles.submitSection}>
            {submitError && (
              <div className={styles.submitError}>
                <i className="fas fa-exclamation-circle"></i>
                {submitError}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              size="large"
              disabled={isSubmitting}
              className={styles.submitButton}
            >
              {isSubmitting ? (
                <>
                  <Spinner size="small" />
                  Creating Organization...
                </>
              ) : (
                <>
                  <i className="fas fa-check-circle"></i>
                  Complete Registration
                </>
              )}
            </Button>

            <p className={styles.loginLink}>
              Already have an account? <Link to="/login">Sign in here</Link>
            </p>
          </div>
        </form>
      </Card>
    </div>
  );
};
