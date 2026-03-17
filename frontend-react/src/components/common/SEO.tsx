/**
 * SEO Component
 *
 * Provides a reusable component for managing page-specific SEO meta tags.
 * Uses react-helmet-async to update the document head dynamically.
 *
 * @example
 * <SEO
 *   title="Login"
 *   description="Sign in to your Course Creator account"
 *   keywords="login, authentication, sign in"
 * />
 */

import { Helmet } from 'react-helmet-async';

interface SEOProps {
  /**
   * Page title (will be appended with " | Course Creator Platform")
   */
  title?: string;

  /**
   * Page description for search engines
   */
  description?: string;

  /**
   * Comma-separated keywords for the page
   */
  keywords?: string;

  /**
   * Canonical URL for the page
   */
  canonical?: string;

  /**
   * Open Graph image URL
   */
  ogImage?: string;
}

export const SEO: React.FC<SEOProps> = ({
  title = 'Course Creator Platform',
  description = 'Comprehensive learning management system with AI-powered content generation, multi-IDE labs, and analytics.',
  keywords = 'education, learning management, course creation, online courses, AI-powered',
  canonical,
  ogImage,
}) => {
  const fullTitle = title === 'Course Creator Platform'
    ? title
    : `${title} | Course Creator Platform`;

  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />

      {canonical && <link rel="canonical" href={canonical} />}

      {/* Open Graph / Facebook */}
      <meta property="og:type" content="website" />
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      {ogImage && <meta property="og:image" content={ogImage} />}

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      {ogImage && <meta name="twitter:image" content={ogImage} />}
    </Helmet>
  );
};
