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

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { Textarea } from '../components/atoms/Textarea';
import { Select } from '../components/atoms/Select';
import { Spinner } from '../components/atoms/Spinner';
import { PhoneInput } from '../components/atoms/PhoneInput';
import { organizationService } from '../services/organizationService';
import { authService } from '../services/authService';
import { countries } from '../data/countries';
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
  logoPreviewUrl: string | null;

  // Organization Address
  street_address: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;

  // Organization Contact Information (defaults to admin if empty)
  contact_phone_country_code: string;
  contact_phone: string;
  contact_email: string;

  // Admin Account
  admin_full_name: string;
  admin_username: string;
  admin_email: string;
  admin_phone_country_code: string;
  admin_phone: string;
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
    logoPreviewUrl: null,
    street_address: '',
    city: '',
    state_province: '',
    postal_code: '',
    country: 'US',
    contact_phone_country_code: 'US',
    contact_phone: '',
    contact_email: '',
    admin_full_name: '',
    admin_username: '',
    admin_email: '',
    admin_phone_country_code: 'US',
    admin_phone: '',
    admin_password: '',
    admin_password_confirm: '',
    terms_accepted: false,
    privacy_accepted: false,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [slugGenerated, setSlugGenerated] = useState(false);

  // Track if org contact fields have been manually edited (to prevent auto-fill override)
  const [orgEmailManuallyEdited, setOrgEmailManuallyEdited] = useState(false);
  const [orgPhoneManuallyEdited, setOrgPhoneManuallyEdited] = useState(false);

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
   * Auto-default organization email from admin email (if not manually edited)
   */
  useEffect(() => {
    if (formData.admin_email && !orgEmailManuallyEdited && !formData.contact_email) {
      setFormData(prev => ({ ...prev, contact_email: formData.admin_email }));
    }
  }, [formData.admin_email, orgEmailManuallyEdited, formData.contact_email]);

  /**
   * Auto-default organization phone from admin phone (if not manually edited)
   */
  useEffect(() => {
    if (formData.admin_phone && !orgPhoneManuallyEdited && !formData.contact_phone) {
      setFormData(prev => ({
        ...prev,
        contact_phone: formData.admin_phone,
        contact_phone_country_code: formData.admin_phone_country_code,
      }));
    }
  }, [formData.admin_phone, formData.admin_phone_country_code, orgPhoneManuallyEdited, formData.contact_phone]);

  /**
   * Handle clipboard paste for logo image
   */
  const handlePaste = useCallback((e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.startsWith('image/')) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) {
          // Validate file size (max 5MB)
          if (file.size > 5 * 1024 * 1024) {
            setErrors(prev => ({ ...prev, logo: 'Logo file must be less than 5MB' }));
            return;
          }

          // Create preview URL
          const previewUrl = URL.createObjectURL(file);
          setFormData(prev => ({
            ...prev,
            logo: file,
            logoPreviewUrl: previewUrl,
          }));

          // Clear any logo errors
          if (errors.logo) {
            setErrors(prev => {
              const newErrors = { ...prev };
              delete newErrors.logo;
              return newErrors;
            });
          }
        }
        break;
      }
    }
  }, [errors.logo]);

  /**
   * Set up paste event listener for logo
   */
  useEffect(() => {
    document.addEventListener('paste', handlePaste);
    return () => {
      document.removeEventListener('paste', handlePaste);
      // Clean up object URL when component unmounts
      if (formData.logoPreviewUrl) {
        URL.revokeObjectURL(formData.logoPreviewUrl);
      }
    };
  }, [handlePaste, formData.logoPreviewUrl]);

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

    // Track manual editing of org contact fields
    if (name === 'contact_email' && value !== formData.admin_email) {
      setOrgEmailManuallyEdited(true);
    }
    if (name === 'contact_phone' && value !== formData.admin_phone) {
      setOrgPhoneManuallyEdited(true);
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

      // Clean up previous preview URL
      if (formData.logoPreviewUrl) {
        URL.revokeObjectURL(formData.logoPreviewUrl);
      }

      // Create new preview URL
      const previewUrl = URL.createObjectURL(file);
      setFormData(prev => ({
        ...prev,
        logo: file,
        logoPreviewUrl: previewUrl,
      }));

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
    // Clean up preview URL
    if (formData.logoPreviewUrl) {
      URL.revokeObjectURL(formData.logoPreviewUrl);
    }
    setFormData(prev => ({ ...prev, logo: null, logoPreviewUrl: null }));
    if (logoInputRef.current) {
      logoInputRef.current.value = '';
    }
  };

  /**
   * Handle admin phone number change
   */
  const handleAdminPhoneChange = (phone: string) => {
    setFormData(prev => ({ ...prev, admin_phone: phone }));
    if (errors.admin_phone) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.admin_phone;
        return newErrors;
      });
    }
  };

  /**
   * Handle admin phone country code change
   */
  const handleAdminPhoneCountryChange = (countryCode: string, dialCode: string) => {
    setFormData(prev => ({ ...prev, admin_phone_country_code: countryCode }));
  };

  /**
   * Handle organization contact phone number change
   */
  const handleContactPhoneChange = (phone: string) => {
    setFormData(prev => ({ ...prev, contact_phone: phone }));
    setOrgPhoneManuallyEdited(true);
    if (errors.contact_phone) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.contact_phone;
        return newErrors;
      });
    }
  };

  /**
   * Handle organization contact phone country code change
   */
  const handleContactPhoneCountryChange = (countryCode: string, dialCode: string) => {
    setFormData(prev => ({ ...prev, contact_phone_country_code: countryCode }));
    setOrgPhoneManuallyEdited(true);
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
    if (!formData.admin_phone.trim()) {
      newErrors.admin_phone = 'Admin phone number is required';
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

      // Get dial codes from country codes
      const contactCountry = countries.find(c => c.code === formData.contact_phone_country_code);
      const adminCountry = countries.find(c => c.code === formData.admin_phone_country_code);

      // Append contact fields (use admin values as defaults if not manually edited)
      submitData.append('contact_phone_country', contactCountry?.dialCode || '+1');
      submitData.append('contact_phone', formData.contact_phone || formData.admin_phone);
      submitData.append('contact_email', formData.contact_email || formData.admin_email);

      // Append admin fields
      submitData.append('admin_full_name', formData.admin_full_name);
      submitData.append('admin_username', formData.admin_username);
      submitData.append('admin_email', formData.admin_email);
      submitData.append('admin_phone_country', adminCountry?.dialCode || '+1');
      submitData.append('admin_phone', formData.admin_phone);
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

            {/* Logo Upload with Paste Support */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>
                Organization Logo
                <span className={styles.optional}>(Optional)</span>
              </label>

              <div className={styles.logoUploadArea} onClick={() => logoInputRef.current?.click()}>
                {formData.logoPreviewUrl ? (
                  <div className={styles.logoPreview}>
                    <img src={formData.logoPreviewUrl} alt="Logo preview" className={styles.previewImage} />
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
                    <p>Click to upload logo, drag and drop, or paste from clipboard</p>
                    <small>PNG, JPG, GIF up to 5MB • Ctrl+V to paste image</small>
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
                searchable
                options={countries.map(c => ({
                  value: c.code,
                  label: `${c.flag} ${c.name}`,
                }))}
              />
            </div>
          </div>

          {/* Contact Information Section */}
          <div className={styles.formSection}>
            <div className={styles.sectionTitle}>
              <i className="fas fa-phone"></i>
              Organization Contact Information
            </div>

            <p className={styles.sectionDescription}>
              These fields will default to the administrator's information if left empty.
            </p>

            <div className={styles.formGrid}>
              <PhoneInput
                label="Organization Phone Number"
                countryCode={formData.contact_phone_country_code}
                value={formData.contact_phone}
                onChange={handleContactPhoneChange}
                onCountryChange={handleContactPhoneCountryChange}
                error={errors.contact_phone}
                placeholder="Phone number (defaults to admin)"
                helperText="Leave empty to use admin's phone number"
              />

              <Input
                label="Organization Email"
                name="contact_email"
                value={formData.contact_email}
                onChange={handleInputChange}
                error={errors.contact_email}
                placeholder="contact@example.com (defaults to admin)"
                type="email"
                helperText="Leave empty to use admin's email"
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

              <PhoneInput
                label="Phone Number"
                countryCode={formData.admin_phone_country_code}
                value={formData.admin_phone}
                onChange={handleAdminPhoneChange}
                onCountryChange={handleAdminPhoneCountryChange}
                error={errors.admin_phone}
                required
                placeholder="Phone number"
                name="admin_phone"
              />

              <Input
                label="Password"
                name="admin_password"
                value={formData.admin_password}
                onChange={handleInputChange}
                error={errors.admin_password}
                required
                placeholder="Create a strong password"
                type="password"
                showPasswordToggle
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
                showPasswordToggle
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
