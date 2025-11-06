/**
 * Manage Users Page
 *
 * BUSINESS CONTEXT:
 * Site Admin feature for managing all platform users.
 * Provides cross-organization user administration, role management, and activity monitoring.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Platform-wide user listing with advanced filtering
 * - Role management and assignment
 * - User status control (active/suspended)
 * - Organization affiliation tracking
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';

/**
 * User Interface
 * Represents a platform user
 */
interface User {
  id: string;
  name: string;
  email: string;
  role: 'site_admin' | 'org_admin' | 'instructor' | 'student';
  organizationName: string;
  status: 'active' | 'suspended';
  lastActive?: string;
  createdDate: string;
}

/**
 * Mock user data
 * In production, this would come from the API
 */
const mockUsers: User[] = [
  {
    id: '1',
    name: 'Alice Johnson',
    email: 'alice@example.com',
    role: 'site_admin',
    organizationName: 'Platform',
    status: 'active',
    lastActive: '2025-11-05',
    createdDate: '2024-01-01'
  },
  {
    id: '2',
    name: 'Bob Smith',
    email: 'bob@acme.com',
    role: 'org_admin',
    organizationName: 'Acme Corporation',
    status: 'active',
    lastActive: '2025-11-04',
    createdDate: '2024-01-15'
  },
  {
    id: '3',
    name: 'Carol Davis',
    email: 'carol@acme.com',
    role: 'instructor',
    organizationName: 'Acme Corporation',
    status: 'active',
    lastActive: '2025-11-05',
    createdDate: '2024-02-10'
  },
  {
    id: '4',
    name: 'David Wilson',
    email: 'david@techstart.io',
    role: 'instructor',
    organizationName: 'TechStart Inc',
    status: 'active',
    lastActive: '2025-11-03',
    createdDate: '2024-03-22'
  },
  {
    id: '5',
    name: 'Eve Martinez',
    email: 'eve@acme.com',
    role: 'student',
    organizationName: 'Acme Corporation',
    status: 'active',
    lastActive: '2025-11-05',
    createdDate: '2024-04-15'
  },
  {
    id: '6',
    name: 'Frank Brown',
    email: 'frank@legacysystems.com',
    role: 'instructor',
    organizationName: 'Legacy Systems Ltd',
    status: 'suspended',
    lastActive: '2025-09-20',
    createdDate: '2024-06-10'
  }
];

/**
 * Manage Users Page Component
 *
 * WHY THIS APPROACH:
 * - Platform-wide user visibility for site admins
 * - Multi-dimensional filtering (role, org, status)
 * - Quick actions for common admin tasks
 * - Activity monitoring for security
 */
export const ManageUsers: React.FC = () => {
  const [users] = useState<User[]>(mockUsers);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<'all' | User['role']>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'suspended'>('all');

  /**
   * Filter users based on search, role, and status
   */
  const filteredUsers = users.filter(user => {
    const matchesSearch = user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         user.organizationName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || user.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });

  /**
   * Handle user status change
   */
  const handleStatusChange = (userId: string, newStatus: 'active' | 'suspended') => {
    // TODO: Implement API call to update user status
    console.log('Updating user status:', { userId, newStatus });
    alert(`User status updated to ${newStatus}`);
  };

  /**
   * Handle role change
   */
  const handleRoleChange = (userId: string, newRole: User['role']) => {
    // TODO: Implement API call to update user role
    console.log('Updating user role:', { userId, newRole });
    alert(`User role updated to ${newRole}`);
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
   * Get role badge color
   */
  const getRoleColor = (role: User['role']) => {
    switch (role) {
      case 'site_admin': return '#8b5cf6';
      case 'org_admin': return '#3b82f6';
      case 'instructor': return '#10b981';
      case 'student': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  /**
   * Get status badge color
   */
  const getStatusColor = (status: User['status']) => {
    switch (status) {
      case 'active': return '#10b981';
      case 'suspended': return '#ef4444';
      default: return '#6b7280';
    }
  };

  /**
   * Format role name for display
   */
  const formatRoleName = (role: User['role']) => {
    return role.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <Heading level="h1" gutterBottom={true}>
              Manage Platform Users
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              Platform-wide user administration and role management
            </p>
          </div>
          <Link to="/dashboard/site-admin">
            <Button variant="secondary">
              Back to Dashboard
            </Button>
          </Link>
        </div>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Users</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
              {users.length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Site Admins</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#8b5cf6' }}>
              {users.filter(u => u.role === 'site_admin').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Org Admins</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
              {users.filter(u => u.role === 'org_admin').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Instructors</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
              {users.filter(u => u.role === 'instructor').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Students</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
              {users.filter(u => u.role === 'student').length}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Active</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
              {users.filter(u => u.status === 'active').length}
            </p>
          </Card>
        </div>

        {/* Filters */}
        <Card variant="outlined" padding="large" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
            <div>
              <Input
                id="search"
                name="search"
                type="text"
                placeholder="Search by name, email, or organization..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value as any)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '0.875rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  backgroundColor: 'white'
                }}
              >
                <option value="all">All Roles</option>
                <option value="site_admin">Site Admin</option>
                <option value="org_admin">Org Admin</option>
                <option value="instructor">Instructor</option>
                <option value="student">Student</option>
              </select>
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
                <option value="suspended">Suspended</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Users Table */}
        <Card variant="outlined" padding="none">
          {filteredUsers.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1rem' }}>
                {searchQuery || roleFilter !== 'all' || statusFilter !== 'all'
                  ? 'No users match your filters'
                  : 'No users found'}
              </p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>User</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Role</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Organization</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Status</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Last Active</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Created</th>
                    <th style={{ padding: '1rem', textAlign: 'left', fontWeight: 600, fontSize: '0.875rem' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                      <td style={{ padding: '1rem' }}>
                        <div>
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                            {user.name}
                          </div>
                          <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                            {user.email}
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
                          backgroundColor: `${getRoleColor(user.role)}20`,
                          color: getRoleColor(user.role)
                        }}>
                          {formatRoleName(user.role)}
                        </span>
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem' }}>
                        {user.organizationName}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <span style={{
                          display: 'inline-block',
                          padding: '0.25rem 0.75rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                          backgroundColor: `${getStatusColor(user.status)}20`,
                          color: getStatusColor(user.status)
                        }}>
                          {user.status}
                        </span>
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        {user.lastActive ? formatDate(user.lastActive) : 'Never'}
                      </td>
                      <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                        {formatDate(user.createdDate)}
                      </td>
                      <td style={{ padding: '1rem' }}>
                        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                          <Link to={`/admin/users/${user.id}`}>
                            <Button variant="secondary" size="small">
                              View
                            </Button>
                          </Link>
                          <select
                            value={user.role}
                            onChange={(e) => handleRoleChange(user.id, e.target.value as User['role'])}
                            style={{
                              padding: '0.375rem 0.5rem',
                              fontSize: '0.875rem',
                              borderRadius: '0.375rem',
                              border: '1px solid #d1d5db',
                              backgroundColor: 'white',
                              cursor: 'pointer'
                            }}
                          >
                            <option value="site_admin">Site Admin</option>
                            <option value="org_admin">Org Admin</option>
                            <option value="instructor">Instructor</option>
                            <option value="student">Student</option>
                          </select>
                          {user.status === 'active' ? (
                            <Button
                              variant="danger"
                              size="small"
                              onClick={() => handleStatusChange(user.id, 'suspended')}
                            >
                              Suspend
                            </Button>
                          ) : (
                            <Button
                              variant="primary"
                              size="small"
                              onClick={() => handleStatusChange(user.id, 'active')}
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
            💡 User Management Tips
          </Heading>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#0c4a6e', lineHeight: '1.6' }}>
            <li>Site admins have full platform access and should be limited to trusted personnel</li>
            <li>Org admins can only manage users within their own organization</li>
            <li>Suspending a user immediately revokes all access but preserves their data</li>
            <li>Changing roles may require the user to log out and back in</li>
          </ul>
        </Card>
      </main>
    </DashboardLayout>
  );
};
