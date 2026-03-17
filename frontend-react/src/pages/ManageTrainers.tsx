/**
 * Manage Trainers Page
 *
 * BUSINESS CONTEXT:
 * Org Admin feature for managing instructor/trainer accounts within organization.
 * Trainers create and manage training programs for the organization.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Organization-scoped user management (instructors only)
 * - Role-based access control (can only manage instructors, not other admins)
 * - Invite workflow for onboarding new trainers
 * - Activity tracking and course assignment views
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';
import { Modal } from '../components/atoms/Modal';
import { useAppSelector } from '../store/hooks';

/**
 * Trainer Interface
 * Represents an instructor in the organization
 */
interface Trainer {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'inactive' | 'pending';
  coursesCount: number;
  studentsCount: number;
  joinedDate: string;
  lastActive?: string;
}

/**
 * Mock trainer data
 * In production, this would come from the API
 */
const mockTrainers: Trainer[] = [
  {
    id: '1',
    name: 'John Smith',
    email: 'john.smith@company.com',
    status: 'active',
    coursesCount: 12,
    studentsCount: 145,
    joinedDate: '2024-01-15',
    lastActive: '2025-11-04'
  },
  {
    id: '2',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@company.com',
    status: 'active',
    coursesCount: 8,
    studentsCount: 98,
    joinedDate: '2024-03-22',
    lastActive: '2025-11-05'
  },
  {
    id: '3',
    name: 'Michael Chen',
    email: 'michael.chen@company.com',
    status: 'inactive',
    coursesCount: 5,
    studentsCount: 34,
    joinedDate: '2024-06-10',
    lastActive: '2025-10-20'
  }
];

/**
 * Manage Trainers Page Component
 *
 * WHY THIS APPROACH:
 * - Organization-centric view of all instructors
 * - Quick stats for trainer performance
 * - Invite workflow for seamless onboarding
 * - Status management for access control
 */
export const ManageTrainers: React.FC = () => {
  const user = useAppSelector(state => state.user.profile);

  const [trainers] = useState<Trainer[]>(mockTrainers);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'pending'>('all');
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteName, setInviteName] = useState('');

  /**
   * Filter trainers based on search and status
   */
  const filteredTrainers = trainers.filter(trainer => {
    const matchesSearch = trainer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         trainer.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || trainer.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  /**
   * Handle invite submission
   */
  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement API call to invite trainer
    console.log('Inviting trainer:', { inviteName, inviteEmail });
    alert(`Invitation sent to ${inviteEmail}!`);
    setInviteEmail('');
    setInviteName('');
    setIsInviteModalOpen(false);
  };

  /**
   * Handle trainer status change
   */
  const handleStatusChange = (trainerId: string, newStatus: 'active' | 'inactive') => {
    // TODO: Implement API call to update trainer status
    console.log('Updating trainer status:', { trainerId, newStatus });
    alert(`Trainer status updated to ${newStatus}`);
  };

  /**
   * Format date for display
   */
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  /**
   * Get status badge color
   */
  const getStatusColor = (status: Trainer['status']) => {
    switch (status) {
      case 'active': return '#10b981';
      case 'inactive': return '#6b7280';
      case 'pending': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <Heading level="h1" gutterBottom={true}>
              Manage Trainers
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              Manage instructor accounts and permissions for {user?.organizationId || 'your organization'}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Button variant="primary" onClick={() => setIsInviteModalOpen(true)}>
              + Invite Trainer
            </Button>
            <Link to="/dashboard/org-admin">
              <Button variant="secondary">
                Back to Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Trainers</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
              {trainers.length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Active</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
              {trainers.filter(t => t.status === 'active').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Courses</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
              {trainers.reduce((sum, t) => sum + t.coursesCount, 0)}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Students</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
              {trainers.reduce((sum, t) => sum + t.studentsCount, 0)}
            </p>
          </Card>
        </div>

        {/* Filters */}
        <Card variant="outlined" padding="large" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem' }}>
            <div>
              <Input
                id="search"
                name="search"
                type="text"
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '0.875rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  backgroundColor: 'white'
                }}
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Trainers Table */}
        <Card variant="outlined" padding="none">
          {filteredTrainers.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1rem' }}>
                {searchQuery || statusFilter !== 'all'
                  ? 'No trainers match your filters'
                  : 'No trainers yet'}
              </p>
              <Button variant="primary" onClick={() => setIsInviteModalOpen(true)}>
                Invite Your First Trainer
              </Button>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Trainer</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Status</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Courses</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Students</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Joined</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Last Active</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTrainers.map((trainer) => (
                    <tr key={trainer.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '1rem' }}>
                        <div>
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                            {trainer.name}
                          </div>
                          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                            {trainer.email}
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                          backgroundColor: `${getStatusColor(trainer.status)}20`,
                          color: getStatusColor(trainer.status)
                        }}>
                          {trainer.status}
                        </span>
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem' }}>
                        {trainer.coursesCount}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem' }}>
                        {trainer.studentsCount}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        {formatDate(trainer.joinedDate)}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        {trainer.lastActive ? formatDate(trainer.lastActive) : 'Never'}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <Link to={`/organization/trainers/${trainer.id}`}>
                            <Button variant="secondary" size="small">
                              View
                            </Button>
                          </Link>
                          {trainer.status === 'active' ? (
                            <Button
                              variant="secondary"
                              size="small"
                              onClick={() => handleStatusChange(trainer.id, 'inactive')}
                            >
                              Deactivate
                            </Button>
                          ) : (
                            <Button
                              variant="primary"
                              size="small"
                              onClick={() => handleStatusChange(trainer.id, 'active')}
                            >
                              Activate
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>

        {/* Info Card */}
        <Card variant="outlined" padding="large" style={{ marginTop: '1.5rem', backgroundColor: '#f0f9ff', border: '1px solid #bae6fd' }}>
          <Heading level="h3" style={{ fontSize: '1.1rem', marginBottom: '0.75rem', color: '#0c4a6e' }}>
            💡 Trainer Management Tips
          </Heading>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#0c4a6e', lineHeight: '1.6' }}>
            <li>Trainers can create and manage training programs for your organization</li>
            <li>Each trainer has full control over their courses and enrolled students</li>
            <li>Deactivating a trainer preserves their courses but prevents new content creation</li>
            <li>Invited trainers receive an email with instructions to set up their account</li>
          </ul>
        </Card>

        {/* Invite Modal */}
        <Modal
          isOpen={isInviteModalOpen}
          onClose={() => setIsInviteModalOpen(false)}
          title="Invite Trainer"
        >
          <form onSubmit={handleInvite}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="inviteName" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                Full Name *
              </label>
              <Input
                id="inviteName"
                name="inviteName"
                type="text"
                placeholder="John Smith"
                value={inviteName}
                onChange={(e) => setInviteName(e.target.value)}
                required
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label htmlFor="inviteEmail" style={{ display: 'block', fontWeight: 500, marginBottom: '0.5rem' }}>
                Email Address *
              </label>
              <Input
                id="inviteEmail"
                name="inviteEmail"
                type="email"
                placeholder="john.smith@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                required
              />
              <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                An invitation email will be sent with setup instructions.
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', paddingTop: '1rem', borderTop: '1px solid #e5e7eb' }}>
              <Button
                type="button"
                variant="secondary"
                onClick={() => setIsInviteModalOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                Send Invitation
              </Button>
            </div>
          </form>
        </Modal>
      </main>
    </DashboardLayout>
  );
};
