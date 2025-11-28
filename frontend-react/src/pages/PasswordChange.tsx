/**
 * Password Change Page
 *
 * BUSINESS CONTEXT:
 * Allows authenticated users to change their password.
 * Requires current password for security verification.
 * Distinct from password reset flow (which uses token from email).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Protected route (authenticated users only)
 * - Validates current password with backend
 * - Enforces password strength requirements
 * - Updates password securely
 */

import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { Spinner } from '../components/atoms/Spinner';
import { SEO } from '../components/common/SEO';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services';
import styles from './PasswordChange.module.css';

interface PasswordChangeForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

interface FormErrors {
  [key: string]: string;
}

/**
 * Password Change Page Component
 *
 * WHY THIS APPROACH:
 * - Security-first design (requires current password)
 * - Real-time validation feedback
 * - Clear password requirements shown
 * - Success/error messaging
 */
export const PasswordChange: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [formData, setFormData] = useState<PasswordChangeForm>({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  /**
   * Handle input changes
   */
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;

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
   * Validate form
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.current_password) {
      newErrors.current_password = 'Current password is required';
    }

    if (!formData.new_password) {
      newErrors.new_password = 'New password is required';
    } else if (formData.new_password.length < 8) {
      newErrors.new_password = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.new_password)) {
      newErrors.new_password = 'Password must contain uppercase, lowercase, and number';
    }

    if (formData.new_password === formData.current_password) {
      newErrors.new_password = 'New password must be different from current password';
    }

    if (!formData.confirm_password) {
      newErrors.confirm_password = 'Please confirm your new password';
    } else if (formData.new_password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
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
      setSubmitError('Please fix the errors above');
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);

    try {
      await authService.changePassword({
        current_password: formData.current_password,
        new_password: formData.new_password,
      });

      setSubmitSuccess(true);

      // Clear form
      setFormData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });

      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);
    } catch (error: any) {
      console.error('Password change error:', error);

      if (error.response?.status === 401) {
        setSubmitError('Current password is incorrect');
      } else if (error.response?.data?.detail) {
        setSubmitError(error.response.data.detail);
      } else if (error.response?.data?.message) {
        setSubmitError(error.response.data.message);
      } else {
        setSubmitError('Failed to change password. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const seoElement = (
    <SEO
      title="Change Password"
      description="Update your account password securely"
      keywords="change password, account security, update password"
    />
  );

  return (
    <DashboardLayout seo={seoElement}>
      <div className={styles.passwordChangeContainer}>
        <Card className={styles.passwordChangeCard}>
          <div className={styles.header}>
            <Heading level={1} className={styles.title}>
              Change Password
            </Heading>
            <p className={styles.subtitle}>
              Update your password to keep your account secure
            </p>
          </div>

          <form onSubmit={handleSubmit} className={styles.form}>
            <Input
              label="Current Password"
              type="password"
              name="current_password"
              value={formData.current_password}
              onChange={handleInputChange}
              error={errors.current_password}
              required
              placeholder="Enter your current password"
              autoComplete="current-password"
            />

            <div className={styles.passwordRequirements}>
              <Heading level={3} className={styles.requirementsTitle}>
                New Password Requirements:
              </Heading>
              <ul className={styles.requirementsList}>
                <li className={formData.new_password.length >= 8 ? styles.met : ''}>
                  <i className={formData.new_password.length >= 8 ? 'fas fa-check-circle' : 'fas fa-circle'}></i>
                  At least 8 characters
                </li>
                <li className={/[A-Z]/.test(formData.new_password) ? styles.met : ''}>
                  <i className={/[A-Z]/.test(formData.new_password) ? 'fas fa-check-circle' : 'fas fa-circle'}></i>
                  At least one uppercase letter
                </li>
                <li className={/[a-z]/.test(formData.new_password) ? styles.met : ''}>
                  <i className={/[a-z]/.test(formData.new_password) ? 'fas fa-check-circle' : 'fas fa-circle'}></i>
                  At least one lowercase letter
                </li>
                <li className={/\d/.test(formData.new_password) ? styles.met : ''}>
                  <i className={/\d/.test(formData.new_password) ? 'fas fa-check-circle' : 'fas fa-circle'}></i>
                  At least one number
                </li>
              </ul>
            </div>

            <Input
              label="New Password"
              type="password"
              name="new_password"
              value={formData.new_password}
              onChange={handleInputChange}
              error={errors.new_password}
              required
              placeholder="Enter your new password"
              autoComplete="new-password"
            />

            <Input
              label="Confirm New Password"
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleInputChange}
              error={errors.confirm_password}
              required
              placeholder="Confirm your new password"
              autoComplete="new-password"
            />

            {submitError && (
              <div className={styles.submitError}>
                <i className="fas fa-exclamation-circle"></i>
                {submitError}
              </div>
            )}

            {submitSuccess && (
              <div className={styles.submitSuccess}>
                <i className="fas fa-check-circle"></i>
                Password changed successfully! Redirecting to dashboard...
              </div>
            )}

            <div className={styles.actions}>
              <Button
                type="submit"
                variant="primary"
                size="large"
                disabled={isSubmitting || submitSuccess}
                className={styles.submitButton}
              >
                {isSubmitting ? (
                  <>
                    <Spinner size="small" />
                    Changing Password...
                  </>
                ) : (
                  <>
                    <i className="fas fa-key"></i>
                    Change Password
                  </>
                )}
              </Button>

              <Link to="/dashboard">
                <Button variant="secondary" size="large" disabled={isSubmitting}>
                  Cancel
                </Button>
              </Link>
            </div>
          </form>

          <div className={styles.footer}>
            <p className={styles.footerText}>
              <i className="fas fa-info-circle"></i>
              Forgot your password? <Link to="/forgot-password">Reset it here</Link>
            </p>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
};
