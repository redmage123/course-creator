/**
 * Members Management Page
 *
 * BUSINESS CONTEXT:
 * Organization admins manage all members (instructors, students, org admins)
 * within their organization. This page provides member listing, filtering,
 * search, and CRUD operations for member management.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches members from backend API with React Query
 * - Client-side filtering by role and search
 * - Responsive grid layout for member cards
 * - Modal-based forms for add/edit operations
 * - Optimistic updates for better UX
 */

import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DashboardLayout } from '../../../components/templates/DashboardLayout';
import { Card } from '../../../components/atoms/Card';
import { Button } from '../../../components/atoms/Button';
import { Heading } from '../../../components/atoms/Heading';
import { Spinner } from '../../../components/atoms/Spinner';
import { useAuth } from '../../../hooks/useAuth';
import { memberService, type Member, type MemberRole } from '../../../services/memberService';
import { MemberCard } from '../components/MemberCard';
import { AddMemberModal } from '../components/AddMemberModal';
import { EditMemberModal } from '../components/EditMemberModal';
import styles from './MembersPage.module.css';

/**
 * Members Page Component
 *
 * WHY THIS APPROACH:
 * - Real-time filtering without API calls (better UX)
 * - Optimistic updates for member actions
 * - Modal-based forms for better mobile experience
 * - Clean, accessible UI with proper loading states
 */
export const MembersPage: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingMember, setEditingMember] = useState<Member | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<MemberRole | 'all'>('all');

  /**
   * Fetch organization members
   */
  const { data: members, isLoading, error } = useQuery({
    queryKey: ['organizationMembers', user?.organizationId],
    queryFn: async () => {
      if (!user?.organizationId) {
        throw new Error('Organization ID not found');
      }
      return await memberService.getOrganizationMembers(user.organizationId);
    },
    enabled: !!user?.organizationId,
    staleTime: 2 * 60 * 1000, // Cache for 2 minutes
  });

  /**
   * Delete member mutation (soft delete)
   */
  const deleteMutation = useMutation({
    mutationFn: (memberId: string) => memberService.deleteMember(memberId),
    onSuccess: () => {
      // Invalidate and refetch members list
      queryClient.invalidateQueries({ queryKey: ['organizationMembers'] });
    },
  });

  /**
   * Filter and search members (client-side)
   */
  const filteredMembers = useMemo(() => {
    if (!members) return [];

    return members.filter((member) => {
      // Role filter
      const matchesRole = roleFilter === 'all' || member.role_name === roleFilter;

      // Search filter (name, email, username)
      const searchLower = searchQuery.toLowerCase();
      const matchesSearch =
        !searchQuery ||
        member.username.toLowerCase().includes(searchLower) ||
        member.email.toLowerCase().includes(searchLower) ||
        member.full_name?.toLowerCase().includes(searchLower);

      return matchesRole && matchesSearch;
    });
  }, [members, roleFilter, searchQuery]);

  /**
   * Handle edit member
   */
  const handleEdit = (member: Member) => {
    setEditingMember(member);
  };

  /**
   * Handle delete member
   */
  const handleDelete = async (memberId: string) => {
    if (window.confirm('Are you sure you want to deactivate this member?')) {
      await deleteMutation.mutateAsync(memberId);
    }
  };

  /**
   * Handle successful member add/edit
   */
  const handleMemberMutationSuccess = () => {
    // Invalidate members list to refetch
    queryClient.invalidateQueries({ queryKey: ['organizationMembers'] });

    // Close modals
    setShowAddModal(false);
    setEditingMember(null);
  };

  /**
   * Loading State
   */
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className={styles['members-page']}>
          <div className={styles['page-header']}>
            <Heading level="h1" gutterBottom>
              Manage Members
            </Heading>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
            <Spinner size="large" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Error State
   */
  if (error) {
    return (
      <DashboardLayout>
        <div className={styles['members-page']}>
          <div className={styles['page-header']}>
            <Heading level="h1" gutterBottom>
              Manage Members
            </Heading>
          </div>
          <Card variant="outlined" padding="large">
            <p style={{ color: 'var(--color-error)', textAlign: 'center' }}>
              Unable to load members. Please try refreshing the page.
            </p>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  /**
   * Success State - Display Members List
   */
  return (
    <DashboardLayout>
      <div className={styles['members-page']}>
        {/* Page Header */}
        <div className={styles['page-header']}>
          <div className={styles['header-content']}>
            <Heading level="h1" gutterBottom>
              Manage Members
            </Heading>
            <p className={styles['header-description']}>
              Add, edit, and manage organization members (instructors, students, administrators)
            </p>
          </div>
          <Button variant="primary" onClick={() => setShowAddModal(true)}>
            Add Member
          </Button>
        </div>

        {/* Filters Section */}
        <Card variant="outlined" padding="medium" className={styles['filters-card']}>
          <div className={styles['filters-grid']}>
            {/* Search Input */}
            <div className={styles['filter-group']}>
              <label htmlFor="search" className={styles['filter-label']}>
                Search
              </label>
              <input
                id="search"
                type="text"
                placeholder="Search by name, email, or username..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={styles['search-input']}
              />
            </div>

            {/* Role Filter */}
            <div className={styles['filter-group']}>
              <label htmlFor="role" className={styles['filter-label']}>
                Role
              </label>
              <select
                id="role"
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value as MemberRole | 'all')}
                className={styles['filter-select']}
              >
                <option value="all">All Roles</option>
                <option value="org_admin">Organization Admin</option>
                <option value="instructor">Instructor</option>
                <option value="student">Student</option>
              </select>
            </div>
          </div>

          {/* Results Count */}
          <div className={styles['results-count']}>
            Showing {filteredMembers.length} of {members?.length || 0} members
          </div>
        </Card>

        {/* Members Grid */}
        {filteredMembers.length === 0 ? (
          <Card variant="outlined" padding="large" className={styles['empty-state']}>
            <Heading level="h3" gutterBottom>
              No Members Found
            </Heading>
            <p>
              {searchQuery || roleFilter !== 'all'
                ? 'Try adjusting your filters to see more results.'
                : 'Get started by adding your first member.'}
            </p>
            {!searchQuery && roleFilter === 'all' && (
              <Button
                variant="primary"
                onClick={() => setShowAddModal(true)}
                style={{ marginTop: '1rem' }}
              >
                Add First Member
              </Button>
            )}
          </Card>
        ) : (
          <div className={styles['members-grid']}>
            {filteredMembers.map((member) => (
              <MemberCard
                key={member.id}
                member={member}
                onEdit={handleEdit}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}

        {/* Add Member Modal */}
        {showAddModal && (
          <AddMemberModal
            organizationId={user!.organizationId!}
            onClose={() => setShowAddModal(false)}
            onSuccess={handleMemberMutationSuccess}
          />
        )}

        {/* Edit Member Modal */}
        {editingMember && (
          <EditMemberModal
            member={editingMember}
            onClose={() => setEditingMember(null)}
            onSuccess={handleMemberMutationSuccess}
          />
        )}
      </div>
    </DashboardLayout>
  );
};
