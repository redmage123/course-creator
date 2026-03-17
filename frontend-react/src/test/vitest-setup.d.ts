/**
 * Vitest Type Declarations
 *
 * Extends Vitest's expect API with @testing-library/jest-dom matchers
 * This allows TypeScript to recognize custom assertions like:
 * - toBeInTheDocument()
 * - toHaveClass()
 * - toHaveAttribute()
 * etc.
 */

import type { TestingLibraryMatchers } from '@testing-library/jest-dom/matchers';
import '@testing-library/jest-dom/vitest';

declare module 'vitest' {
  interface Assertion<T = any> extends TestingLibraryMatchers<T, void> {}
  interface AsymmetricMatchersContaining extends TestingLibraryMatchers {}
}
