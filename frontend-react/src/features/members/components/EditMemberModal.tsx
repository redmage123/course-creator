/**
 * Edit Member Modal Component
 *
 * BUSINESS CONTEXT:
 * Organization admins can update member details including full name, role,
 * and active status. Password changes are handled separately for security.
 *
 * TECHNICAL IMPLEMENTATION:
 * - React Hook Form for form management
 * - Zod for schema validation
 * - React Query mutation for API calls
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
import { Checkbox } from '../../../components/atoms/Checkbox';
import { Spinner } from '../../../components/atoms/Spinner';
import { memberService, type Member, type MemberRole } from '../../../services';
import styles from './EditMemberModal.module.css';

/**
 * Edit Member Form Schema
 */
const editMemberSchema = z.object({
  full_name: z
    .string()
    .min(1, 'Full name is required')
    .max(100, 'Full name must be less than 100 characters'),
  role_name: z.enum(['org_admin', 'instructor', 'student'], {
    errorMap: () => ({ message: 'Please select a role' }),
  }),
  is_active: z.boolean(),
});

type EditMemberFormData = z.infer<typeof editMemberSchema>;

/**
 * Edit Member Modal Props
 */
export interface EditMemberModalProps {
  isOpen: boolean;
  member: Member;
  onClose: () => void;
  onSuccess: () => void;
}

/**
 * Edit Member Modal Component
 */
export const EditMemberModal: React.FC<EditMemberModalProps> = ({
  isOpen,
  member,
  onClose,
  onSuccess,
}) => {
  const [submitError, setSubmitError] = useState<string | null>(null);

  /**
   * React Hook Form setup
   */
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EditMemberFormData>({
    resolver: zodResolver(editMemberSchema),
    defaultValues: {
      full_name: member.full_name || '',
      role_name: member.role_name as 'org_admin' | 'instructor' | 'student',
      is_active: member.is_active,
    },
  });

  /**
   * Update member mutation
   */
  const updateMutation = useMutation({
    mutationFn: (data: EditMemberFormData) =>
      memberService.updateMember(member.id, data),
    onSuccess: () => {
      onSuccess();
      setSubmitError(null);
    },
    onError: (error: any) => {
      setSubmitError(error.message || 'Failed to update member');
    },
  });

  /**
   * Handle form submission
   */
  const onSubmit = (data: EditMemberFormData) => {
    setSubmitError(null);
    updateMutation.mutate(data);
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Edit Member"
      size="medium"
      footer={
        <>
          <Button variant="ghost" onClick={onClose} disabled={updateMutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit(onSubmit)}
            disabled={updateMutation.isPending}
          >
            {updateMutation.isPending ? <Spinner size="small" /> : 'Save Changes'}
          </Button>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
        {/* Read-only fields */}
        <div className={styles['form-section']}>
          <Input
            label="Username"
            value={member.username}
            disabled
            fullWidth
            helperText="Username cannot be changed"
          />

          <Input
            label="Email"
            value={member.email}
            disabled
            fullWidth
            helperText="Email cannot be changed"
          />
        </div>

        {/* Editable fields */}
        <Input
          {...register('full_name')}
          label="Full Name"
          type="text"
          placeholder="Enter full name"
          error={errors.full_name?.message}
          fullWidth
          required
        />

        <Select
          {...register('role_name')}
          label="Role"
          fullWidth
          required
          error={errors.role_name?.message}
        >
          <option value="">Select role</option>
          <option value="org_admin">Organization Admin</option>
          <option value="instructor">Instructor</option>
          <option value="student">Student</option>
        </Select>

        <div className={styles['checkbox-group']}>
          <Checkbox
            {...register('is_active')}
            label="Active"
            helperText="Inactive members cannot log in"
          />
        </div>

        {/* Error message */}
        {submitError && (
          <div className={styles.error} role="alert">
            {submitError}
          </div>
        )}

        {/* Info message */}
        <div className={styles.info}>
          <p>
            <strong>Note:</strong> Password changes must be done through the password reset
            flow for security reasons.
          </p>
        </div>
      </form>
    </Modal>
  );
};
