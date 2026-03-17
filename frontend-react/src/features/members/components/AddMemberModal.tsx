/**
 * Add Member Modal Component
 *
 * BUSINESS CONTEXT:
 * Organization admins add new members (instructors, students, org admins)
 * to their organization. This modal provides a form for creating new user accounts
 * with role assignment and organization association.
 *
 * TECHNICAL IMPLEMENTATION:
 * - React Hook Form for form management
 * - Zod for schema validation
 * - React Query mutation for API calls
 * - Toast notifications for success/error feedback
 */

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { Modal } from '../../../components/atoms/Modal';
import { Button } from '../../../components/atoms/Button';
import { Input } from '../../../components/atoms/Input';
import { Select } from '../../../components/atoms/Select';
import { Spinner } from '../../../components/atoms/Spinner';
import { memberService, type MemberRole } from '../../../services/memberService';
import styles from './AddMemberModal.module.css';

/**
 * Add Member Form Schema
 * Validates all required fields with business rules
 */
const addMemberSchema = z.object({
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_-]+$/, 'Username can only contain letters, numbers, hyphens, and underscores'),
  email: z
    .string()
    .email('Invalid email address')
    .min(1, 'Email is required'),
  full_name: z
    .string()
    .min(1, 'Full name is required')
    .max(100, 'Full name must be less than 100 characters'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  password_confirm: z
    .string()
    .min(1, 'Please confirm password'),
  role_name: z.enum(['org_admin', 'instructor', 'student'], {
    errorMap: () => ({ message: 'Please select a role' }),
  }),
}).refine((data) => data.password === data.password_confirm, {
  message: 'Passwords do not match',
  path: ['password_confirm'],
});

type AddMemberFormData = z.infer<typeof addMemberSchema>;

/**
 * Add Member Modal Props
 */
export interface AddMemberModalProps {
  organizationId: string;
  onClose: () => void;
  onSuccess: () => void;
}

/**
 * Add Member Modal Component
 *
 * WHY THIS APPROACH:
 * - React Hook Form reduces boilerplate and improves performance
 * - Zod provides type-safe validation with clear error messages
 * - Optimistic updates improve perceived performance
 * - Clear validation feedback guides users to fix errors
 */
export const AddMemberModal: React.FC<AddMemberModalProps> = ({
  organizationId,
  onClose,
  onSuccess,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);

  /**
   * React Hook Form setup with Zod validation
   */
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AddMemberFormData>({
    resolver: zodResolver(addMemberSchema),
    mode: 'onBlur', // Validate on blur for better UX
  });

  /**
   * Create member mutation
   */
  const createMutation = useMutation({
    mutationFn: (data: AddMemberFormData) => {
      const { password_confirm, ...memberData } = data;
      return memberService.createMember({
        ...memberData,
        organization_id: organizationId,
      });
    },
    onSuccess: () => {
      onSuccess();
      onClose();
    },
    onError: (error: Error) => {
      setSubmitError(error.message || 'Failed to create member. Please try again.');
    },
  });

  /**
   * Handle form submission
   */
  const onSubmit = async (data: AddMemberFormData) => {
    setSubmitError(null);
    await createMutation.mutateAsync(data);
  };

  /**
   * Available roles for selection
   */
  const roleOptions = [
    { value: 'student', label: 'Student' },
    { value: 'instructor', label: 'Instructor' },
    { value: 'org_admin', label: 'Organization Admin' },
  ];

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Add New Member"
      size="medium"
      preventClose={createMutation.isPending}
    >
      <form onSubmit={handleSubmit(onSubmit)} className={styles['add-member-form']}>
        {/* Form Fields */}
        <div className={styles['form-body']}>
          {/* Username */}
          <Input
            label="Username"
            placeholder="johndoe"
            error={errors.username?.message}
            required
            disabled={createMutation.isPending}
            {...register('username')}
          />

          {/* Email */}
          <Input
            label="Email"
            type="email"
            placeholder="john.doe@example.com"
            error={errors.email?.message}
            required
            disabled={createMutation.isPending}
            {...register('email')}
          />

          {/* Full Name */}
          <Input
            label="Full Name"
            placeholder="John Doe"
            error={errors.full_name?.message}
            required
            disabled={createMutation.isPending}
            {...register('full_name')}
          />

          {/* Role */}
          <div className={styles['form-field']}>
            <label htmlFor="role_name" className={styles['field-label']}>
              Role <span className={styles['required']}>*</span>
            </label>
            <select
              id="role_name"
              className={`${styles['select-input']} ${errors.role_name ? styles['select-error'] : ''}`}
              disabled={createMutation.isPending}
              {...register('role_name')}
            >
              <option value="">Select a role</option>
              {roleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.role_name && (
              <span className={styles['error-text']}>{errors.role_name.message}</span>
            )}
          </div>

          {/* Password */}
          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            helperText="At least 8 characters with uppercase, lowercase, and number"
            error={errors.password?.message}
            required
            disabled={createMutation.isPending}
            {...register('password')}
          />

          {/* Confirm Password */}
          <Input
            label="Confirm Password"
            type="password"
            placeholder="••••••••"
            error={errors.password_confirm?.message}
            required
            disabled={createMutation.isPending}
            {...register('password_confirm')}
          />

          {/* Submit Error */}
          {submitError && (
            <div className={styles['error-message']}>
              {submitError}
            </div>
          )}
        </div>

        {/* Form Footer */}
        <div className={styles['form-footer']}>
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? (
              <>
                <Spinner size="small" />
                <span style={{ marginLeft: '0.5rem' }}>Creating...</span>
              </>
            ) : (
              'Create Member'
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
