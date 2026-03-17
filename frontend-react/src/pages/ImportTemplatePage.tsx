/**
 * Import Template Page
 *
 * BUSINESS CONTEXT:
 * Org Admin feature for importing organization templates that contain
 * pre-configured projects, tracks, and courses. Supports JSON templates
 * and AI-assisted automatic project creation from uploaded templates.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Uses file upload for JSON/YAML templates
 * - Supports drag-and-drop functionality
 * - AI-powered auto-creation of projects from templates
 * - Progress feedback during import process
 */

import React, { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Spinner } from '../components/atoms/Spinner';
import { useAppSelector } from '../store/hooks';
import { apiClient } from '../services/apiClient';

interface ImportResult {
  success: boolean;
  projectsCreated: number;
  tracksCreated: number;
  coursesCreated: number;
  errors: string[];
}

/**
 * Import Template Page Component
 *
 * WHY THIS APPROACH:
 * - Drag-and-drop for intuitive file uploads
 * - JSON/YAML template support for flexibility
 * - AI processing for intelligent project creation
 * - Detailed progress and results reporting
 */
export const ImportTemplatePage: React.FC = () => {
  const navigate = useNavigate();
  const user = useAppSelector(state => state.user.profile);

  // File state
  const [templateFile, setTemplateFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Import state
  const [isImporting, setIsImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  /**
   * Handle file drop
   */
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      const validTypes = ['application/json', 'text/yaml', 'application/x-yaml'];
      const validExtensions = ['.json', '.yaml', '.yml'];
      const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));

      if (validTypes.includes(file.type) || hasValidExtension) {
        setTemplateFile(file);
        setError(null);
      } else {
        setError('Please upload a JSON or YAML file.');
      }
    }
  }, []);

  /**
   * Handle drag events
   */
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  /**
   * Handle file input change
   */
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setTemplateFile(file);
      setError(null);
    }
  };

  /**
   * Handle template import
   */
  const handleImport = async () => {
    if (!templateFile || !user?.organizationId) return;

    setIsImporting(true);
    setError(null);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('template', templateFile);
      formData.append('organization_id', user.organizationId);

      const response = await apiClient.post<ImportResult>(
        '/api/v1/organizations/import-template',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setImportResult(response.data);

      if (response.data.success) {
        setTimeout(() => navigate('/dashboard/org-admin'), 3000);
      }
    } catch (err: any) {
      console.error('Failed to import template:', err);
      setError(err.response?.data?.message || 'Failed to import template. Please check the file format and try again.');
    } finally {
      setIsImporting(false);
    }
  };

  /**
   * Download sample template
   */
  const downloadSampleTemplate = () => {
    const sampleTemplate = {
      name: "Sample Organization Template",
      version: "1.0",
      description: "A sample template for creating training projects and tracks",
      projects: [
        {
          name: "AI Fundamentals Training",
          description: "Comprehensive AI training program for corporate teams",
          tracks: [
            {
              name: "Machine Learning Basics",
              description: "Introduction to ML concepts",
              courses: [
                {
                  title: "Introduction to Machine Learning",
                  description: "Learn ML fundamentals",
                  difficulty_level: "beginner",
                  duration_hours: 8
                }
              ]
            }
          ]
        }
      ]
    };

    const blob = new Blob([JSON.stringify(sampleTemplate, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'organization_template_sample.json';
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <Heading level="h1" gutterBottom={true}>
            Import Organization Template
          </Heading>
          <p style={{ color: '#666', fontSize: '0.95rem', marginBottom: '1rem' }}>
            Import a template to automatically create projects, tracks, and courses for your organization
          </p>
          <Card variant="outlined" padding="medium" style={{ backgroundColor: '#eff6ff' }}>
            <p style={{ margin: 0, fontSize: '0.9rem', color: '#1e40af' }}>
              <strong>💡 Tip:</strong> Templates can define complete training programs with multiple tracks and courses.
              AI will help populate course content based on the template structure.
            </p>
          </Card>
        </div>

        {/* Error Message */}
        {error && (
          <Card variant="outlined" padding="medium" style={{ marginBottom: '1.5rem', borderColor: '#ef4444', backgroundColor: '#fee2e2' }}>
            <p style={{ color: '#dc2626', margin: 0, fontWeight: 500 }}>{error}</p>
          </Card>
        )}

        {/* Import Result */}
        {importResult && (
          <Card
            variant="elevated"
            padding="large"
            style={{
              marginBottom: '1.5rem',
              backgroundColor: importResult.success ? '#d1fae5' : '#fee2e2',
              borderColor: importResult.success ? '#10b981' : '#ef4444'
            }}
          >
            <Heading level="h3" style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>
              {importResult.success ? '✅ Import Successful!' : '⚠️ Import Completed with Issues'}
            </Heading>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#666' }}>Projects Created</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  {importResult.projectsCreated}
                </p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#666' }}>Tracks Created</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  {importResult.tracksCreated}
                </p>
              </div>
              <div>
                <p style={{ margin: 0, fontSize: '0.875rem', color: '#666' }}>Courses Created</p>
                <p style={{ margin: '0.25rem 0 0', fontSize: '1.5rem', fontWeight: 'bold' }}>
                  {importResult.coursesCreated}
                </p>
              </div>
            </div>
            {importResult.errors.length > 0 && (
              <div style={{ marginTop: '1rem', padding: '1rem', backgroundColor: '#fff', borderRadius: '0.5rem' }}>
                <p style={{ margin: '0 0 0.5rem', fontWeight: 500, color: '#dc2626' }}>Errors:</p>
                <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                  {importResult.errors.map((err, idx) => (
                    <li key={idx} style={{ color: '#dc2626', fontSize: '0.875rem' }}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        )}

        {/* File Upload Area */}
        <Card variant="outlined" padding="large" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <Heading level="h2" style={{ fontSize: '1.25rem', margin: 0 }}>
              Upload Template File
            </Heading>
            <Button
              variant="text"
              size="small"
              onClick={downloadSampleTemplate}
            >
              📥 Download Sample Template
            </Button>
          </div>

          {/* Drag and Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            style={{
              border: `2px dashed ${isDragging ? '#3b82f6' : '#d1d5db'}`,
              borderRadius: '0.5rem',
              padding: '3rem 2rem',
              textAlign: 'center',
              backgroundColor: isDragging ? '#eff6ff' : '#f9fafb',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onClick={() => document.getElementById('templateFile')?.click()}
          >
            <input
              id="templateFile"
              type="file"
              accept=".json,.yaml,.yml"
              onChange={handleFileChange}
              style={{ display: 'none' }}
              disabled={isImporting}
            />
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
            {templateFile ? (
              <div>
                <p style={{ fontSize: '1.1rem', fontWeight: 500, color: '#10b981', marginBottom: '0.5rem' }}>
                  ✅ {templateFile.name}
                </p>
                <p style={{ fontSize: '0.875rem', color: '#666' }}>
                  {(templateFile.size / 1024).toFixed(2)} KB • Click to replace
                </p>
              </div>
            ) : (
              <div>
                <p style={{ fontSize: '1.1rem', fontWeight: 500, marginBottom: '0.5rem' }}>
                  Drag & drop your template file here
                </p>
                <p style={{ fontSize: '0.875rem', color: '#666' }}>
                  or click to browse • Supports JSON, YAML
                </p>
              </div>
            )}
          </div>

          {/* Template Format Info */}
          <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#f0f9ff', borderRadius: '0.375rem', border: '1px solid #bae6fd' }}>
            <p style={{ margin: '0 0 0.5rem', fontWeight: 500, fontSize: '0.875rem', color: '#0c4a6e' }}>
              Template Structure:
            </p>
            <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#0c4a6e' }}>
              <li><code style={{ backgroundColor: '#e0f2fe', padding: '0.125rem 0.25rem', borderRadius: '0.25rem' }}>projects[]</code> - Array of training projects</li>
              <li><code style={{ backgroundColor: '#e0f2fe', padding: '0.125rem 0.25rem', borderRadius: '0.25rem' }}>tracks[]</code> - Learning tracks within projects</li>
              <li><code style={{ backgroundColor: '#e0f2fe', padding: '0.125rem 0.25rem', borderRadius: '0.25rem' }}>courses[]</code> - Courses within tracks</li>
              <li>AI will generate content for courses based on titles and descriptions</li>
            </ul>
          </div>
        </Card>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
          <Link to="/dashboard/org-admin">
            <Button variant="secondary" disabled={isImporting}>
              Cancel
            </Button>
          </Link>
          <Button
            variant="primary"
            onClick={handleImport}
            disabled={!templateFile || isImporting}
          >
            {isImporting ? (
              <>
                <Spinner size="small" /> Importing...
              </>
            ) : (
              '🚀 Import Template'
            )}
          </Button>
        </div>
      </main>
    </DashboardLayout>
  );
};
