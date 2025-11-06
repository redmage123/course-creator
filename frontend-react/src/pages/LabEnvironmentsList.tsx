/**
 * Lab Environments List Page
 *
 * BUSINESS CONTEXT:
 * Student feature for viewing and accessing interactive lab environments.
 * Provides hands-on coding practice in sandboxed Docker containers with multiple IDE options.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Lists all available labs from enrolled courses
 * - Shows lab status (available, active, completed)
 * - Provides lab launch functionality
 * - Tracks lab progress and completion
 * - Multi-IDE support (VSCode, JupyterLab, RStudio, Terminal)
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { DashboardLayout } from '../components/templates/DashboardLayout';
import { Card } from '../components/atoms/Card';
import { Button } from '../components/atoms/Button';
import { Heading } from '../components/atoms/Heading';
import { Input } from '../components/atoms/Input';

/**
 * Lab Environment Interface
 * Represents an interactive coding lab environment
 */
interface LabEnvironment {
  id: string;
  title: string;
  courseName: string;
  courseId: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: number; // minutes
  technology: string;
  ideType: 'vscode' | 'jupyter' | 'rstudio' | 'terminal';
  status: 'available' | 'in-progress' | 'completed';
  progressPercentage: number;
  lastAccessedAt?: string;
  completedAt?: string;
  containerUrl?: string; // URL to access running container
  objectives: string[];
}

/**
 * Mock lab environment data
 * In production, this would come from the Lab Manager Service API (port 8005)
 */
const mockLabEnvironments: LabEnvironment[] = [
  {
    id: '1',
    title: 'Python Basics - Variables and Data Types',
    courseName: 'Introduction to Python Programming',
    courseId: 'course-1',
    description: 'Learn Python fundamentals by working with variables, strings, numbers, and basic operations in an interactive environment.',
    difficulty: 'beginner',
    estimatedTime: 30,
    technology: 'Python 3.11',
    ideType: 'jupyter',
    status: 'completed',
    progressPercentage: 100,
    lastAccessedAt: '2025-10-28',
    completedAt: '2025-10-28',
    objectives: [
      'Create and use variables',
      'Work with different data types',
      'Perform basic arithmetic operations',
      'Use string formatting'
    ]
  },
  {
    id: '2',
    title: 'Python Functions and Modules',
    courseName: 'Introduction to Python Programming',
    courseId: 'course-1',
    description: 'Master function definitions, parameters, return values, and importing modules in this hands-on lab.',
    difficulty: 'beginner',
    estimatedTime: 45,
    technology: 'Python 3.11',
    ideType: 'jupyter',
    status: 'in-progress',
    progressPercentage: 60,
    lastAccessedAt: '2025-11-02',
    containerUrl: 'https://lab.example.com/containers/student123-lab2',
    objectives: [
      'Define and call functions',
      'Use function parameters and return values',
      'Import and use standard library modules',
      'Create custom modules'
    ]
  },
  {
    id: '3',
    title: 'Data Structures - Lists and Dictionaries',
    courseName: 'Introduction to Python Programming',
    courseId: 'course-1',
    description: 'Explore Python\'s powerful built-in data structures through practical exercises.',
    difficulty: 'intermediate',
    estimatedTime: 60,
    technology: 'Python 3.11',
    ideType: 'vscode',
    status: 'available',
    progressPercentage: 0,
    objectives: [
      'Create and manipulate lists',
      'Use list comprehensions',
      'Work with dictionaries',
      'Combine data structures'
    ]
  },
  {
    id: '4',
    title: 'JavaScript ES6+ Features',
    courseName: 'Modern JavaScript Development',
    courseId: 'course-2',
    description: 'Learn modern JavaScript syntax including arrow functions, destructuring, spread operators, and more.',
    difficulty: 'intermediate',
    estimatedTime: 50,
    technology: 'Node.js 18',
    ideType: 'vscode',
    status: 'available',
    progressPercentage: 0,
    objectives: [
      'Use arrow functions',
      'Apply destructuring syntax',
      'Work with spread and rest operators',
      'Understand template literals'
    ]
  },
  {
    id: '5',
    title: 'React Components and State',
    courseName: 'Modern JavaScript Development',
    courseId: 'course-2',
    description: 'Build interactive React components and manage state in this practical lab environment.',
    difficulty: 'advanced',
    estimatedTime: 90,
    technology: 'React 18 + TypeScript',
    ideType: 'vscode',
    status: 'available',
    progressPercentage: 0,
    objectives: [
      'Create functional components',
      'Use React hooks (useState, useEffect)',
      'Handle events',
      'Manage component state'
    ]
  },
  {
    id: '6',
    title: 'Data Analysis with R',
    courseName: 'Statistical Computing',
    courseId: 'course-3',
    description: 'Analyze datasets using R programming language and create visualizations.',
    difficulty: 'intermediate',
    estimatedTime: 75,
    technology: 'R 4.3',
    ideType: 'rstudio',
    status: 'available',
    progressPercentage: 0,
    objectives: [
      'Import and clean data',
      'Perform statistical analysis',
      'Create visualizations with ggplot2',
      'Generate reports with R Markdown'
    ]
  },
  {
    id: '7',
    title: 'Linux Command Line Basics',
    courseName: 'DevOps Fundamentals',
    courseId: 'course-4',
    description: 'Master essential Linux commands and shell scripting in a real terminal environment.',
    difficulty: 'beginner',
    estimatedTime: 40,
    technology: 'Ubuntu 22.04',
    ideType: 'terminal',
    status: 'completed',
    progressPercentage: 100,
    lastAccessedAt: '2025-10-25',
    completedAt: '2025-10-25',
    objectives: [
      'Navigate the file system',
      'Manage files and directories',
      'Use pipes and redirection',
      'Write basic shell scripts'
    ]
  },
  {
    id: '8',
    title: 'Docker Containers and Images',
    courseName: 'DevOps Fundamentals',
    courseId: 'course-4',
    description: 'Learn Docker fundamentals by building, running, and managing containers.',
    difficulty: 'advanced',
    estimatedTime: 120,
    technology: 'Docker 24',
    ideType: 'terminal',
    status: 'available',
    progressPercentage: 0,
    objectives: [
      'Build Docker images',
      'Run and manage containers',
      'Work with Docker Compose',
      'Understand container networking'
    ]
  }
];

/**
 * Lab Environments List Page Component
 *
 * WHY THIS APPROACH:
 * - Comprehensive lab listing with filtering by course and status
 * - Clear visual indicators for lab status and progress
 * - Quick access to resume in-progress labs
 * - IDE type badges help students identify lab environment type
 * - Difficulty and time estimates help with planning
 */
export const LabEnvironmentsList: React.FC = () => {
  const [labs] = useState<LabEnvironment[]>(mockLabEnvironments);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'available' | 'in-progress' | 'completed'>('all');
  const [courseFilter, setCourseFilter] = useState<string>('all');
  const [difficultyFilter, setDifficultyFilter] = useState<'all' | 'beginner' | 'intermediate' | 'advanced'>('all');

  /**
   * Get unique course list for filter dropdown
   */
  const uniqueCourses = Array.from(new Set(labs.map(lab => lab.courseName)));

  /**
   * Filter labs based on search and filters
   */
  const filteredLabs = labs.filter(lab => {
    const matchesSearch = lab.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         lab.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         lab.courseName.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || lab.status === statusFilter;
    const matchesCourse = courseFilter === 'all' || lab.courseName === courseFilter;
    const matchesDifficulty = difficultyFilter === 'all' || lab.difficulty === difficultyFilter;
    return matchesSearch && matchesStatus && matchesCourse && matchesDifficulty;
  });

  /**
   * Handle lab launch
   */
  const handleLaunchLab = (labId: string) => {
    // TODO: Implement API call to Lab Manager Service (port 8005) to create/resume lab container
    console.log('Launching lab:', labId);
    alert('Lab environment is being prepared. This will open in a new window once ready.');
  };

  /**
   * Handle lab resume
   */
  const handleResumeLab = (labId: string, containerUrl: string) => {
    // TODO: Open lab container in new window
    console.log('Resuming lab:', labId, 'at', containerUrl);
    window.open(containerUrl, '_blank');
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
  const getStatusColor = (status: LabEnvironment['status']) => {
    switch (status) {
      case 'available': return '#3b82f6';
      case 'in-progress': return '#f59e0b';
      case 'completed': return '#10b981';
      default: return '#6b7280';
    }
  };

  /**
   * Get difficulty badge color
   */
  const getDifficultyColor = (difficulty: LabEnvironment['difficulty']) => {
    switch (difficulty) {
      case 'beginner': return '#10b981';
      case 'intermediate': return '#f59e0b';
      case 'advanced': return '#ef4444';
      default: return '#6b7280';
    }
  };

  /**
   * Get IDE type badge color and icon
   */
  const getIdeInfo = (ideType: LabEnvironment['ideType']) => {
    switch (ideType) {
      case 'vscode': return { color: '#007acc', icon: '💻', label: 'VS Code' };
      case 'jupyter': return { color: '#f37726', icon: '📊', label: 'Jupyter' };
      case 'rstudio': return { color: '#75aadb', icon: '📈', label: 'RStudio' };
      case 'terminal': return { color: '#2d2d2d', icon: '⌨️', label: 'Terminal' };
      default: return { color: '#6b7280', icon: '💻', label: 'IDE' };
    }
  };

  /**
   * Summary statistics
   */
  const stats = {
    total: labs.length,
    available: labs.filter(l => l.status === 'available').length,
    inProgress: labs.filter(l => l.status === 'in-progress').length,
    completed: labs.filter(l => l.status === 'completed').length
  };

  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <Heading level="h1" gutterBottom={true}>
              Lab Environments
            </Heading>
            <p style={{ color: '#666', fontSize: '0.95rem' }}>
              Interactive coding environments for hands-on practice
            </p>
          </div>
          <Link to="/dashboard/student">
            <Button variant="secondary">
              Back to Dashboard
            </Button>
          </Link>
        </div>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Total Labs</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#1f2937' }}>
              {stats.total}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Available</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
              {stats.available}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>In Progress</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#f59e0b' }}>
              {stats.inProgress}
            </p>
          </Card>
          <Card variant="elevated" padding="medium">
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#666' }}>Completed</p>
            <p style={{ margin: '0.5rem 0 0', fontSize: '2rem', fontWeight: 'bold', color: '#10b981' }}>
              {stats.completed}
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
                placeholder="Search labs..."
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
                <option value="available">Available</option>
                <option value="in-progress">In Progress</option>
                <option value="completed">Completed</option>
              </select>
            </div>
            <div>
              <select
                value={courseFilter}
                onChange={(e) => setCourseFilter(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '0.875rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  backgroundColor: 'white'
                }}
              >
                <option value="all">All Courses</option>
                {uniqueCourses.map(course => (
                  <option key={course} value={course}>{course}</option>
                ))}
              </select>
            </div>
            <div>
              <select
                value={difficultyFilter}
                onChange={(e) => setDifficultyFilter(e.target.value as any)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '0.875rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  backgroundColor: 'white'
                }}
              >
                <option value="all">All Difficulties</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Labs Grid */}
        {filteredLabs.length === 0 ? (
          <Card variant="outlined" padding="large">
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '1rem' }}>
                {searchQuery || statusFilter !== 'all' || courseFilter !== 'all' || difficultyFilter !== 'all'
                  ? 'No labs match your filters'
                  : 'No lab environments available yet'}
              </p>
              <Link to="/dashboard/student">
                <Button variant="primary">
                  Go to Dashboard
                </Button>
              </Link>
            </div>
          </Card>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '1.5rem' }}>
            {filteredLabs.map((lab) => {
              const ideInfo = getIdeInfo(lab.ideType);
              return (
                <Card key={lab.id} variant="elevated" padding="large">
                  {/* Lab Header */}
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                      <Heading level="h3" style={{ fontSize: '1.1rem', margin: 0 }}>
                        {lab.title}
                      </Heading>
                      <span style={{
                        display: 'inline-block',
                        padding: '0.25rem 0.75rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textTransform: 'capitalize',
                        backgroundColor: `${getStatusColor(lab.status)}20`,
                        color: getStatusColor(lab.status),
                        whiteSpace: 'nowrap'
                      }}>
                        {lab.status === 'in-progress' ? 'In Progress' : lab.status}
                      </span>
                    </div>
                    <p style={{ margin: '0.25rem 0', fontSize: '0.875rem', color: '#6b7280' }}>
                      {lab.courseName}
                    </p>
                  </div>

                  {/* Lab Description */}
                  <p style={{ fontSize: '0.875rem', color: '#374151', lineHeight: '1.5', marginBottom: '1rem' }}>
                    {lab.description}
                  </p>

                  {/* Lab Metadata */}
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor: `${ideInfo.color}20`,
                      color: ideInfo.color
                    }}>
                      {ideInfo.icon} {ideInfo.label}
                    </span>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      textTransform: 'capitalize',
                      backgroundColor: `${getDifficultyColor(lab.difficulty)}20`,
                      color: getDifficultyColor(lab.difficulty)
                    }}>
                      {lab.difficulty}
                    </span>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor: '#e5e7eb',
                      color: '#374151'
                    }}>
                      ⏱️ {lab.estimatedTime} min
                    </span>
                    <span style={{
                      display: 'inline-block',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '9999px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      backgroundColor: '#e5e7eb',
                      color: '#374151'
                    }}>
                      {lab.technology}
                    </span>
                  </div>

                  {/* Progress Bar (for in-progress and completed labs) */}
                  {lab.status !== 'available' && (
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Progress</span>
                        <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#1f2937' }}>
                          {lab.progressPercentage}%
                        </span>
                      </div>
                      <div style={{
                        width: '100%',
                        height: '8px',
                        backgroundColor: '#e5e7eb',
                        borderRadius: '9999px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          width: `${lab.progressPercentage}%`,
                          height: '100%',
                          backgroundColor: getStatusColor(lab.status),
                          borderRadius: '9999px',
                          transition: 'width 0.3s ease'
                        }} />
                      </div>
                    </div>
                  )}

                  {/* Learning Objectives */}
                  <div style={{ marginBottom: '1rem' }}>
                    <p style={{ fontSize: '0.875rem', fontWeight: 600, color: '#374151', marginBottom: '0.5rem' }}>
                      Learning Objectives:
                    </p>
                    <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#6b7280', lineHeight: '1.6' }}>
                      {lab.objectives.slice(0, 3).map((objective, index) => (
                        <li key={index}>{objective}</li>
                      ))}
                      {lab.objectives.length > 3 && (
                        <li style={{ color: '#3b82f6' }}>+{lab.objectives.length - 3} more...</li>
                      )}
                    </ul>
                  </div>

                  {/* Last Accessed / Completed Info */}
                  {(lab.lastAccessedAt || lab.completedAt) && (
                    <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '1rem' }}>
                      {lab.completedAt && `✅ Completed on ${formatDate(lab.completedAt)}`}
                      {!lab.completedAt && lab.lastAccessedAt && `Last accessed on ${formatDate(lab.lastAccessedAt)}`}
                    </p>
                  )}

                  {/* Action Button */}
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {lab.status === 'available' && (
                      <Button
                        variant="primary"
                        fullWidth={true}
                        onClick={() => handleLaunchLab(lab.id)}
                      >
                        🚀 Start Lab
                      </Button>
                    )}
                    {lab.status === 'in-progress' && lab.containerUrl && (
                      <>
                        <Button
                          variant="primary"
                          fullWidth={true}
                          onClick={() => handleResumeLab(lab.id, lab.containerUrl!)}
                        >
                          ▶️ Resume Lab
                        </Button>
                      </>
                    )}
                    {lab.status === 'completed' && (
                      <Button
                        variant="secondary"
                        fullWidth={true}
                        onClick={() => handleLaunchLab(lab.id)}
                      >
                        🔄 Retry Lab
                      </Button>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        )}

        {/* Info Card */}
        <Card variant="outlined" padding="large" style={{ marginTop: '2rem', backgroundColor: '#f0f9ff', border: '1px solid #bae6fd' }}>
          <Heading level="h3" style={{ fontSize: '1.1rem', marginBottom: '0.75rem', color: '#0c4a6e' }}>
            💡 Lab Environment Tips
          </Heading>
          <ul style={{ margin: 0, paddingLeft: '1.5rem', fontSize: '0.875rem', color: '#0c4a6e', lineHeight: '1.6' }}>
            <li>Each lab runs in an isolated Docker container for security</li>
            <li>Your progress is automatically saved as you work</li>
            <li>Labs remain active for 2 hours of inactivity before auto-suspension</li>
            <li>You can resume suspended labs to continue from where you left off</li>
            <li>Completed labs can be retried to practice and improve your skills</li>
          </ul>
        </Card>
      </main>
    </DashboardLayout>
  );
};
