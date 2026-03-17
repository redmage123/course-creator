/**
 * Manage Organizations Page
 *
 * BUSINESS CONTEXT:
 * Site Admin feature for managing all platform organizations.
 * Provides oversight of multi-tenant organization operations, billing, and compliance.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Platform-wide organization listing
 * - Organization status management (active/suspended)
 * - Usage metrics and subscription tracking
 * - Quick access to organization administration
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';

/**
 * Organization Interface
 * Represents a tenant organization on the platform
 */
interface Organization {
  id: string;
  name: string;
  contactEmail: string;
  subscriptionPlan: string;
  status: 'active' | 'suspended' | 'trial';
  trainersCount: number;
  studentsCount: number;
  coursesCount: number;
  createdDate: string;
  subscriptionExpiresAt?: string;
}

/**
 * Mock organization data
 * In production, this would come from the API
 */
const mockOrganizations: Organization[] = [
  {
    id: '1',
    name: 'Acme Corporation',
    contactEmail: 'admin@acme.com',
    subscriptionPlan: 'Enterprise',
    status: 'active',
    trainersCount: 15,
    studentsCount: 450,
    coursesCount: 38,
    createdDate: '2024-01-15',
    subscriptionExpiresAt: '2025-01-14'
  },
  {
    id: '2',
    name: 'TechStart Inc',
    contactEmail: 'admin@techstart.io',
    subscriptionPlan: 'Professional',
    status: 'active',
    trainersCount: 8,
    studentsCount: 120,
    coursesCount: 15,
    createdDate: '2024-03-22',
    subscriptionExpiresAt: '2025-03-21'
  },
  {
    id: '3',
    name: 'Global Training Solutions',
    contactEmail: 'contact@globaltraining.com',
    subscriptionPlan: 'Trial',
    status: 'trial',
    trainersCount: 3,
    studentsCount: 25,
    coursesCount: 5,
    createdDate: '2025-10-01',
    subscriptionExpiresAt: '2025-11-01'
  },
  {
    id: '4',
    name: 'Legacy Systems Ltd',
    contactEmail: 'admin@legacysystems.com',
    subscriptionPlan: 'Professional',
    status: 'suspended',
    trainersCount: 5,
    studentsCount: 89,
    coursesCount: 12,
    createdDate: '2024-06-10',
    subscriptionExpiresAt: '2024-10-10'
  }
];

/**
 * Manage Organizations Page Component
 *
 * WHY THIS APPROACH:
 * - Platform-wide view for site administrators
 * - Quick status overview with filterable table
 * - Direct actions for common admin tasks
 * - Subscription and usage tracking
 */
export const ManageOrganizations: React.FC = () => {
  const [organizations] = useState<Organization[]>(mockOrganizations);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'suspended' | 'trial'>('all');

  /**
   * Filter organizations based on search and status
   */
  const filteredOrganizations = organizations.filter(org => {
    const matchesSearch = org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         org.contactEmail.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || org.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  /**
   * Handle organization status change
   */
  const handleStatusChange = (orgId: string, newStatus: 'active' | 'suspended') => {
    // TODO: Implement API call to update organization status
    console.log('Updating organization status:', { orgId, newStatus });
    alert(`Organization status updated to ${newStatus}`);
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
  const getStatusColor = (status: Organization['status']) => {
    switch (status) {
      case 'active': return '#10b981';
      case 'suspended': return '#ef4444';
      case 'trial': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  /**
   * Get subscription plan badge color
   */
  const getPlanColor = (plan: string) => {
    switch (plan.toLowerCase()) {
      case 'enterprise': return '#8b5cf6';
      case 'professional': return '#3b82f6';
      case 'trial': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <Heading level="h1" gutterBottom={true}>
              Manage Organizations
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              Platform-wide organization administration and oversight
            </p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/admin/organizations/create">
              <Button variant="primary">
                + Create Organization
              </Button>
            </Link>
            <Link to="/dashboard/site-admin">
              <Button variant="secondary">
                Back to Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Organizations</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
              {organizations.length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Active</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
              {organizations.filter(o => o.status === 'active').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Trainers</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
              {organizations.reduce((sum, o) => sum + o.trainersCount, 0)}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Students</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
              {organizations.reduce((sum, o) => sum + o.studentsCount, 0)}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Courses</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#8b5cf6' }}>
              {organizations.reduce((sum, o) => sum + o.coursesCount, 0)}
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
                placeholder="Search by organization name or email..."
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
                <option value="trial">Trial</option>
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Organizations Table */}
        <Card variant="outlined" padding="none">
          {filteredOrganizations.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1rem' }}>
                {searchQuery || statusFilter !== 'all'
                  ? 'No organizations match your filters'
                  : 'No organizations yet'}
              </p>
              <Link to="/admin/organizations/create">
                <Button variant="primary">
                  Create First Organization
                </Button>
              </Link>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Organization</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Plan</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Status</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Trainers</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Students</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Courses</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Created</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Expires</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrganizations.map((org) => (
                    <tr key={org.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '1rem' }}>
                        <div>
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                            {org.name}
                          </div>
                          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                            {org.contactEmail}
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
                          backgroundColor: `${getPlanColor(org.subscriptionPlan)}20`,
                          color: getPlanColor(org.subscriptionPlan)
                        }}>
                          {org.subscriptionPlan}
                        </span>
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                          backgroundColor: `${getStatusColor(org.status)}20`,
                          color: getStatusColor(org.status)
                        }}>
                          {org.status}
                        </span>
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', textAlign: 'center' }}>
                        {org.trainersCount}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', textAlign: 'center' }}>
                        {org.studentsCount}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', textAlign: 'center' }}>
                        {org.coursesCount}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        {formatDate(org.createdDate)}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        {org.subscriptionExpiresAt ? formatDate(org.subscriptionExpiresAt) : 'N/A'}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <Link to={`/admin/organizations/${org.id}`}>
                            <Button variant="secondary" size="small">
                              View
                            </Button>
                          </Link>
                          {org.status === 'active' ? (
                            <Button
                              variant="danger"
                              size="small"
                              onClick={() => handleStatusChange(org.id, 'suspended')}
                            >
                              Suspend
                            </Button>
                          ) : org.status === 'suspended' ? (
                            <Button
                              variant="primary"
                              size="small"
                              onClick={() => handleStatusChange(org.id, 'active')}
                            >
                              Activate
                            </Button>
                          ) : null}
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
            💡 Platform Administration Tips
          </Heading>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#0c4a6e', lineHeight: '1.6' }}>
            <li>Monitor organization usage to identify growth opportunities</li>
            <li>Suspend organizations for non-payment or policy violations</li>
            <li>Trial accounts automatically expire after 30 days unless upgraded</li>
            <li>Contact organizations proactively when approaching subscription renewal</li>
          </ul>
        </Card>
      </main>
    </DashboardLayout>
  );
};
