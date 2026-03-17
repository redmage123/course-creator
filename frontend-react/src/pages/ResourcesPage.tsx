/**
 * Resources Page
 *
 * BUSINESS CONTEXT:
 * Student-facing page to browse and download learning resources
 * from their enrolled courses. Includes course materials, videos,
 * documentation, and downloadable assets.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Fetches resources from student's enrolled courses
 * - Categorizes by type (video, document, code, etc.)
 * - Download functionality with progress tracking
 * - Search and filter capabilities
 */

import React, { useState, useMemo } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Spinner } from '../components/atoms/Spinner';
import { Input } from '../components/atoms/Input';
import { apiClient } from '../services/apiClient';

interface Resource {
  id: string;
  title: string;
  description: string;
  type: 'video' | 'document' | 'code' | 'slides' | 'dataset' | 'other';
  course_id: string;
  course_title: string;
  file_url: string;
  file_size_bytes: number;
  format: string;
  created_at: string;
}

interface ResourcesResponse {
  resources: Resource[];
  total: number;
}

/**
 * Resources Page Component
 *
 * WHY THIS APPROACH:
 * - Organized by resource type for easy navigation
 * - Download-focused with file size indicators
 * - Search functionality for large resource libraries
 * - Course filtering for targeted browsing
 */
export const ResourcesPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const downloadMode = searchParams.get('download') === 'true';

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());

  /**
   * Fetch student's resources from enrolled courses
   */
  const { data, isLoading, error } = useQuery<ResourcesResponse>({
    queryKey: ['studentResources'],
    queryFn: async () => {
      const response = await apiClient.get<ResourcesResponse>('/api/v1/resources/my-resources');
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  const resources = data?.resources || [];

  /**
   * Filter resources based on search and type
   */
  const filteredResources = useMemo(() => {
    return resources.filter(resource => {
      const matchesSearch = searchTerm === '' ||
        resource.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resource.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        resource.course_title.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesType = selectedType === 'all' || resource.type === selectedType;

      return matchesSearch && matchesType;
    });
  }, [resources, searchTerm, selectedType]);

  /**
   * Get resource type icon
   */
  const getTypeIcon = (type: Resource['type']) => {
    const icons: Record<string, string> = {
      video: '🎥',
      document: '📄',
      code: '💻',
      slides: '📊',
      dataset: '📊',
      other: '📁',
    };
    return icons[type] || '📁';
  };

  /**
   * Format file size
   */
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  /**
   * Handle resource download
   */
  const handleDownload = async (resource: Resource) => {
    setDownloadingIds(prev => new Set([...prev, resource.id]));

    try {
      const response = await apiClient.get(`/api/v1/resources/${resource.id}/download`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${resource.title}.${resource.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
      alert('Download failed. Please try again.');
    } finally {
      setDownloadingIds(prev => {
        const next = new Set(prev);
        next.delete(resource.id);
        return next;
      });
    }
  };

  /**
   * Get unique resource types for filter
   */
  const resourceTypes = useMemo(() => {
    const types = new Set(resources.map(r => r.type));
    return Array.from(types);
  }, [resources]);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Spinner size="large" />
        </div>
      </DashboardLayout>
    );
  }

  if (error) {
    return (
      <DashboardLayout>
        <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
          <Card variant="outlined" padding="large" style={{ textAlign: 'center' }}>
            <p style={{ color: '#dc2626', marginBottom: '1rem' }}>
              Unable to load resources. Please try refreshing the page.
            </p>
            <Button variant="primary" onClick={() => window.location.reload()}>
              Refresh Page
            </Button>
          </Card>
        </main>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <Heading level="h1" gutterBottom={true}>
            {downloadMode ? 'Download Materials' : 'Learning Resources'}
          </Heading>
          <p style={{ color: '#666', fontSize: '0.95rem' }}>
            {downloadMode
              ? 'Download course materials for offline access'
              : 'Access course materials, videos, and documentation'}
          </p>
        </div>

        {/* Search and Filter */}
        <Card variant="outlined" padding="medium" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ flex: 1, minWidth: '250px' }}>
              <Input
                type="search"
                placeholder="Search resources..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <Button
                variant={selectedType === 'all' ? 'primary' : 'secondary'}
                size="small"
                onClick={() => setSelectedType('all')}
              >
                All
              </Button>
              {resourceTypes.map(type => (
                <Button
                  key={type}
                  variant={selectedType === type ? 'primary' : 'secondary'}
                  size="small"
                  onClick={() => setSelectedType(type)}
                >
                  {getTypeIcon(type)} {type.charAt(0).toUpperCase() + type.slice(1)}
                </Button>
              ))}
            </div>
          </div>
        </Card>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
          <Card variant="elevated" padding="medium">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>{resources.length}</div>
              <div style={{ color: '#666', fontSize: '0.875rem' }}>Total Resources</div>
            </div>
          </Card>
          <Card variant="elevated" padding="medium">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
                {resources.filter(r => r.type === 'video').length}
              </div>
              <div style={{ color: '#666', fontSize: '0.875rem' }}>Videos</div>
            </div>
          </Card>
          <Card variant="elevated" padding="medium">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#8b5cf6' }}>
                {resources.filter(r => r.type === 'document').length}
              </div>
              <div style={{ color: '#666', fontSize: '0.875rem' }}>Documents</div>
            </div>
          </Card>
          <Card variant="elevated" padding="medium">
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
                {formatFileSize(resources.reduce((sum, r) => sum + r.file_size_bytes, 0))}
              </div>
              <div style={{ color: '#666', fontSize: '0.875rem' }}>Total Size</div>
            </div>
          </Card>
        </div>

        {/* Resource List */}
        {filteredResources.length > 0 ? (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {filteredResources.map(resource => (
              <Card key={resource.id} variant="outlined" padding="large">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
                  <div style={{ display: 'flex', gap: '1rem', flex: 1, minWidth: '200px' }}>
                    <div style={{ fontSize: '2.5rem' }}>{getTypeIcon(resource.type)}</div>
                    <div>
                      <Heading level="h3" style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>
                        {resource.title}
                      </Heading>
                      <p style={{ color: '#666', fontSize: '0.875rem', marginBottom: '0.5rem' }}>
                        {resource.description}
                      </p>
                      <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.75rem', color: '#666' }}>
                        <span>📚 {resource.course_title}</span>
                        <span>📁 {resource.format.toUpperCase()}</span>
                        <span>💾 {formatFileSize(resource.file_size_bytes)}</span>
                        <span>📅 {new Date(resource.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {resource.type === 'video' ? (
                      <Link to={`/courses/${resource.course_id}/videos/${resource.id}`}>
                        <Button variant="primary" size="medium">
                          ▶️ Watch
                        </Button>
                      </Link>
                    ) : null}
                    <Button
                      variant="secondary"
                      size="medium"
                      onClick={() => handleDownload(resource)}
                      disabled={downloadingIds.has(resource.id)}
                      data-action="download"
                    >
                      {downloadingIds.has(resource.id) ? (
                        <>
                          <Spinner size="small" /> Downloading...
                        </>
                      ) : (
                        '⬇️ Download'
                      )}
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        ) : (
          <Card variant="outlined" padding="large" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📚</div>
            <Heading level="h3" style={{ marginBottom: '0.5rem' }}>
              {searchTerm || selectedType !== 'all' ? 'No Resources Found' : 'No Resources Available'}
            </Heading>
            <p style={{ color: '#666', marginBottom: '1.5rem' }}>
              {searchTerm || selectedType !== 'all'
                ? 'Try adjusting your search or filters.'
                : 'Resources will appear here once your trainer adds them to your enrolled courses.'}
            </p>
            {(searchTerm || selectedType !== 'all') && (
              <Button variant="primary" onClick={() => { setSearchTerm(''); setSelectedType('all'); }}>
                Clear Filters
              </Button>
            )}
          </Card>
        )}
      </main>
    </DashboardLayout>
  );
};
