/**
 * Breadcrumb Component - Navigation Aid
 *
 * BUSINESS CONTEXT:
 * Provides hierarchical navigation trail for users to understand their
 * location within the application and navigate back to parent pages.
 * Essential for deep navigation structures (3+ levels).
 *
 * TECHNICAL IMPLEMENTATION:
 * - Semantic HTML with nav and ordered list
 * - ARIA breadcrumb pattern for accessibility
 * - Automatic current page indication
 * - Responsive truncation for mobile
 *
 * DESIGN PRINCIPLES:
 * - Platform gray (#64748b) for inactive items
 * - Platform blue (#2563eb) for interactive items
 * - Chevron separators for clear hierarchy
 * - Touch-friendly spacing
 */

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styles from './Breadcrumb.module.css';

export interface BreadcrumbItem {
  /**
   * Display label for the breadcrumb item
   */
  label: string;

  /**
   * Route path for navigation (optional for current page)
   */
  path?: string;

  /**
   * Icon to display before label (optional)
   */
  icon?: React.ReactNode;
}

export interface BreadcrumbProps {
  /**
   * Array of breadcrumb items from root to current page
   */
  items: BreadcrumbItem[];

  /**
   * Separator between items
   * @default '/'
   */
  separator?: React.ReactNode;

  /**
   * Maximum number of items to display (truncates middle items)
   * @default undefined (no truncation)
   */
  maxItems?: number;

  /**
   * Additional CSS class name
   */
  className?: string;

  /**
   * Show home icon for first item
   * @default true
   */
  showHomeIcon?: boolean;
}

/**
 * Chevron separator icon
 */
const ChevronSeparator: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    aria-hidden="true"
    className={styles.separator}
  >
    <path
      d="M6 4L10 8L6 12"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * Home icon for first breadcrumb
 */
const HomeIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    aria-hidden="true"
    className={styles['home-icon']}
  >
    <path
      d="M2 6L8 1L14 6V13C14 13.5304 13.7893 14.0391 13.4142 14.4142C13.0391 14.7893 12.5304 15 12 15H4C3.46957 15 2.96086 14.7893 2.58579 14.4142C2.21071 14.0391 2 13.5304 2 13V6Z"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M6 15V8H10V15"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

/**
 * Ellipsis for truncated items
 */
const Ellipsis: React.FC = () => (
  <span className={styles.ellipsis} aria-label="More items">
    ...
  </span>
);

/**
 * Breadcrumb Component
 *
 * WHY THIS APPROACH:
 * - Semantic nav element with aria-label for screen readers
 * - Ordered list represents hierarchical structure
 * - Current page marked with aria-current="page"
 * - Truncation maintains usability on mobile
 * - Links use React Router for SPA navigation
 *
 * @example
 * ```tsx
 * <Breadcrumb
 *   items={[
 *     { label: 'Dashboard', path: '/dashboard' },
 *     { label: 'Courses', path: '/courses' },
 *     { label: 'Python 101' }  // Current page (no path)
 *   ]}
 * />
 * ```
 */
export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  separator,
  maxItems,
  className,
  showHomeIcon = true,
}) => {
  const location = useLocation();

  /**
   * Process items for truncation if needed
   */
  const processedItems = React.useMemo(() => {
    if (!maxItems || items.length <= maxItems) {
      return items;
    }

    // Keep first and last items, truncate middle
    const firstItems = items.slice(0, 1);
    const lastItems = items.slice(-(maxItems - 1));

    return [
      ...firstItems,
      { label: '...', path: undefined } as BreadcrumbItem,
      ...lastItems,
    ];
  }, [items, maxItems]);

  /**
   * Check if an item is the current page
   */
  const isCurrent = (item: BreadcrumbItem, index: number): boolean => {
    // Last item is always current if it has no path
    if (index === processedItems.length - 1 && !item.path) {
      return true;
    }

    // Check if path matches current location
    if (item.path) {
      return location.pathname === item.path;
    }

    return false;
  };

  if (items.length === 0) {
    return null;
  }

  const classes = [styles.breadcrumb, className].filter(Boolean).join(' ');

  return (
    <nav aria-label="Breadcrumb" className={classes} data-testid="breadcrumb">
      <ol className={styles['breadcrumb-list']}>
        {processedItems.map((item, index) => {
          const isCurrentItem = isCurrent(item, index);
          const isFirst = index === 0;
          const isEllipsis = item.label === '...';

          return (
            <li
              key={item.path || item.label}
              className={styles['breadcrumb-item']}
            >
              {/* Separator (not before first item) */}
              {index > 0 && (
                separator || <ChevronSeparator />
              )}

              {/* Ellipsis indicator */}
              {isEllipsis ? (
                <Ellipsis />
              ) : isCurrentItem ? (
                /* Current page (not a link) */
                <span
                  className={styles['breadcrumb-current']}
                  aria-current="page"
                >
                  {item.icon && (
                    <span className={styles['item-icon']} aria-hidden="true">
                      {item.icon}
                    </span>
                  )}
                  {item.label}
                </span>
              ) : item.path ? (
                /* Link to ancestor page */
                <Link
                  to={item.path}
                  className={styles['breadcrumb-link']}
                >
                  {isFirst && showHomeIcon ? (
                    <>
                      <HomeIcon />
                      <span className={styles['home-label']}>{item.label}</span>
                    </>
                  ) : (
                    <>
                      {item.icon && (
                        <span className={styles['item-icon']} aria-hidden="true">
                          {item.icon}
                        </span>
                      )}
                      {item.label}
                    </>
                  )}
                </Link>
              ) : (
                /* Non-navigable item */
                <span className={styles['breadcrumb-text']}>
                  {item.icon && (
                    <span className={styles['item-icon']} aria-hidden="true">
                      {item.icon}
                    </span>
                  )}
                  {item.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

Breadcrumb.displayName = 'Breadcrumb';
