/**
 * Coming Soon Page Component
 *
 * BUSINESS CONTEXT:
 * Placeholder page for features under development.
 * Provides clear communication to users about upcoming functionality.
 *
 * TECHNICAL IMPLEMENTATION:
 * Generic placeholder that can be used across multiple routes.
 * Accepts title and description props for customization.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Heading } from '../components/atoms/Heading';
import { Button } from '../components/atoms/Button';
import { Card } from '../components/atoms/Card';
import { DashboardLayout } from '../components/templates/DashboardLayout';

interface ComingSoonProps {
  title: string;
  description: string;
  backLink?: string;
  backLinkText?: string;
}

/**
 * Coming Soon Page
 *
 * WHY THIS APPROACH:
 * - Provides professional placeholder for incomplete features
 * - Maintains consistent UI/UX with rest of platform
 * - Gives users clear expectations about feature availability
 */
export const ComingSoon: React.FC<ComingSoonProps> = ({
  title,
  description,
  backLink = '/',
  backLinkText = 'Back to Dashboard',
}) => {
  return (
    <DashboardLayout>
      <main style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
        <Card variant="elevated" padding="large">
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🚧</div>
            <Heading level="h1" align="center" gutterBottom={true}>
              {title}
            </Heading>
            <p style={{ fontSize: '1.1rem', color: '#666', marginBottom: '2rem' }}>
              {description}
            </p>
            <div style={{ marginTop: '2rem' }}>
              <Link to={backLink}>
                <Button variant="primary" size="large">
                  {backLinkText}
                </Button>
              </Link>
            </div>
          </div>
        </Card>
      </main>
    </DashboardLayout>
  );
};
