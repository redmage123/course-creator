/**
 * Member Card Component
 *
 * BUSINESS CONTEXT:
 * Displays individual member information in a card format.
 * Used in the members list for organization admins to view and manage members.
 * Shows member details, role, status, and provides edit/delete actions.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Reusable card component with member data
 * - Role-based badge styling
 * - Status indicators (active/inactive)
 * - Quick action buttons
 */

import React from 'react';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { type Member } from '../../../services/memberService';
import styles from './MemberCard.module.css';

/**
 * Member Card Props
 */
export interface MemberCardProps {
  member: Member;
  /** Callback when edit button is clicked */
  onEdit: (member: Member) => void;
  /** Callback when delete button is clicked */
  onDelete: (memberId: string) => void;
}

/**
 * Member Card Component
 *
 * WHY THIS APPROACH:
 * - Clean, scannable card layout
 * - Visual role differentiation with color-coded badges
 * - Clear status indicators
 * - Accessible action buttons
 * - Consistent with design system patterns
 */
export const MemberCard: React.FC<MemberCardProps> = ({
  member,
  onEdit,
  onDelete,
}) => {
  /**
   * Get role badge class for styling
   */
  const getRoleBadgeClass = () => {
    const roleClasses = {
      site_admin: styles['role-site-admin'],
      org_admin: styles['role-org-admin'],
      instructor: styles['role-instructor'],
      student: styles['role-student'],
      guest: styles['role-guest'],
    };
    return roleClasses[member.role_name] || styles['role-guest'];
  };

  /**
   * Get role display name
   */
  const getRoleDisplayName = () => {
    const roleNames = {
      site_admin: 'Site Admin',
      org_admin: 'Org Admin',
      instructor: 'Instructor',
      student: 'Student',
      guest: 'Guest',
    };
    return roleNames[member.role_name] || member.role_name;
  };

  /**
   * Format last login date
   */
  const formatLastLogin = () => {
    if (!member.last_login) return 'Never';

    const lastLogin = new Date(member.last_login);
    const now = new Date();
    const diffMs = now.getTime() - lastLogin.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return lastLogin.toLocaleDateString();
  };

  /**
   * Format created date
   */
  const formatCreatedDate = () => {
    const created = new Date(member.created_at);
    return created.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <Card variant="outlined" padding="medium" className={styles['member-card']}>
      {/* Card Header */}
      <div className={styles['card-header']}>
        <div className={styles['member-info']}>
          <div className={styles['member-name']}>
            {member.full_name || member.username}
          </div>
          <div className={styles['member-username']}>
            @{member.username}
          </div>
        </div>
        <div className={styles['badges']}>
          <span className={`${styles['role-badge']} ${getRoleBadgeClass()}`}>
            {getRoleDisplayName()}
          </span>
          <span
            className={`${styles['status-badge']} ${
              member.is_active ? styles['status-active'] : styles['status-inactive']
            }`}
          >
            {member.is_active ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {/* Card Body */}
      <div className={styles['card-body']}>
        {/* Email */}
        <div className={styles['info-row']}>
          <span className={styles['info-label']}>Email:</span>
          <span className={styles['info-value']}>{member.email}</span>
        </div>

        {/* Organization */}
        {member.organization_name && (
          <div className={styles['info-row']}>
            <span className={styles['info-label']}>Organization:</span>
            <span className={styles['info-value']}>{member.organization_name}</span>
          </div>
        )}

        {/* Last Login */}
        <div className={styles['info-row']}>
          <span className={styles['info-label']}>Last Login:</span>
          <span className={styles['info-value']}>{formatLastLogin()}</span>
        </div>

        {/* Joined Date */}
        <div className={styles['info-row']}>
          <span className={styles['info-label']}>Joined:</span>
          <span className={styles['info-value']}>{formatCreatedDate()}</span>
        </div>
      </div>

      {/* Card Footer - Action Buttons */}
      <div className={styles['card-footer']}>
        <Button
          variant="secondary"
          size="small"
          onClick={() => onEdit(member)}
        >
          Edit
        </Button>
        <Button
          variant="danger"
          size="small"
          onClick={() => onDelete(member.id)}
          disabled={!member.is_active}
        >
          {member.is_active ? 'Deactivate' : 'Deactivated'}
        </Button>
      </div>
    </Card>
  );
};
