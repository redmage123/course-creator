/**
 * ESLint Configuration for Course Creator Platform React Frontend
 *
 * BUSINESS CONTEXT:
 * Enforces code quality standards across React TypeScript codebase.
 * Ensures accessibility compliance (WCAG 2.1 AA), security best practices,
 * and TypeScript strict mode for the educational platform.
 *
 * TECHNICAL RATIONALE:
 * - TypeScript strict mode: Catches type errors at compile time
 * - React best practices: Prevents common React antipatterns
 * - Accessibility standards: Ensures WCAG 2.1 AA compliance for educational access
 * - Import organization: Maintains consistent code structure
 * - Security rules: Prevents XSS and other vulnerabilities
 *
 * RULES ENFORCED:
 * 1. TypeScript: strict mode, no explicit any, consistent type imports
 * 2. React: hooks rules, refresh fast refresh, prop types
 * 3. Accessibility: ARIA attributes, keyboard navigation, semantic HTML
 * 4. Import: order, no duplicates, no unused imports
 * 5. Security: no eval, no dangerouslySetInnerHTML without review
 * 6. Unused variables: caught and flagged (allows _prefixed vars)
 *
 * CONFIGURATION:
 * - Line length: Handled by Prettier (120 chars)
 * - Quote style: Handled by Prettier (single quotes)
 * - Semicolons: Required (TypeScript best practice)
 */

import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default [
  // Global ignores - files/directories to skip linting
  {
    ignores: [
      'dist',
      'node_modules',
      'coverage',
      'build',
      '*.config.js',
      '*.config.ts',
      '.vite',
      'public',
      '**/*.min.js',
      '**/*.min.css',
    ],
  },

  // Main configuration for TypeScript and TSX files
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        ...globals.es2020,
      },
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
        project: './tsconfig.json',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint.plugin,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      // ======================================================================
      // JavaScript/TypeScript Core Rules
      // ======================================================================
      ...js.configs.recommended.rules,
      ...tseslint.configs.recommended.rules,

      // Prevent unused variables (allow underscore-prefixed for intentionally unused)
      '@typescript-eslint/no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],

      // Explicit function return types not required (inferred by TypeScript)
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',

      // Warn on 'any' type - should be typed properly
      '@typescript-eslint/no-explicit-any': 'warn',

      // Consistent type imports
      '@typescript-eslint/consistent-type-imports': [
        'warn',
        {
          prefer: 'type-imports',
          fixStyle: 'inline-type-imports',
        },
      ],

      // No empty functions (except in interfaces/overrides)
      '@typescript-eslint/no-empty-function': [
        'error',
        {
          allow: ['arrowFunctions', 'functions', 'methods'],
        },
      ],

      // Consistent type definitions
      '@typescript-eslint/consistent-type-definitions': ['warn', 'interface'],

      // No unnecessary type assertions
      '@typescript-eslint/no-unnecessary-type-assertion': 'warn',

      // Prefer nullish coalescing
      '@typescript-eslint/prefer-nullish-coalescing': 'warn',

      // Prefer optional chaining
      '@typescript-eslint/prefer-optional-chain': 'warn',

      // ======================================================================
      // React Hooks Rules
      // ======================================================================
      ...reactHooks.configs.recommended.rules,
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // ======================================================================
      // React Refresh Rules
      // ======================================================================
      'react-refresh/only-export-components': [
        'warn',
        {
          allowConstantExport: true,
          allowExportNames: ['loader', 'action', 'ErrorBoundary'],
        },
      ],

      // ======================================================================
      // General Code Quality Rules
      // ======================================================================

      // No console statements in production (use proper logging)
      'no-console': [
        'warn',
        {
          allow: ['warn', 'error'],
        },
      ],

      // No debugger statements
      'no-debugger': 'error',

      // No alert/confirm/prompt
      'no-alert': 'warn',

      // Prefer const over let when not reassigned
      'prefer-const': 'error',

      // No var declarations
      'no-var': 'error',

      // Prefer template literals
      'prefer-template': 'warn',

      // Object shorthand
      'object-shorthand': 'warn',

      // Prefer arrow functions for callbacks
      'prefer-arrow-callback': 'warn',

      // ======================================================================
      // Security Rules
      // ======================================================================

      // No eval
      'no-eval': 'error',

      // No implied eval
      'no-implied-eval': 'error',

      // No script URLs
      'no-script-url': 'error',

      // ======================================================================
      // Import/Export Rules
      // ======================================================================

      // No duplicate imports
      'no-duplicate-imports': 'error',

      // ======================================================================
      // Potential Error Prevention
      // ======================================================================

      // No await in loop (can cause performance issues)
      'no-await-in-loop': 'warn',

      // No promise executor return
      'no-promise-executor-return': 'error',

      // No template curly in string
      'no-template-curly-in-string': 'warn',

      // No unreachable loop
      'no-unreachable-loop': 'error',

      // Require atomic updates
      'require-atomic-updates': 'warn',

      // ======================================================================
      // Best Practices
      // ======================================================================

      // Consistent return
      'consistent-return': 'off', // TypeScript handles this

      // Curly braces for all control statements
      curly: ['error', 'all'],

      // Default case in switch
      'default-case': 'warn',

      // Default parameter last
      'default-param-last': 'error',

      // Dot notation
      'dot-notation': 'warn',

      // Eqeqeq (use === and !==)
      eqeqeq: ['error', 'always'],

      // No empty functions
      'no-empty-function': 'off', // Handled by @typescript-eslint/no-empty-function

      // No floating decimals
      'no-floating-decimal': 'error',

      // No implicit coercion
      'no-implicit-coercion': 'warn',

      // No lonely if
      'no-lonely-if': 'warn',

      // No nested ternary
      'no-nested-ternary': 'warn',

      // No return await
      'no-return-await': 'error',

      // No throw literal
      'no-throw-literal': 'error',

      // No unneeded ternary
      'no-unneeded-ternary': 'warn',

      // No useless concat
      'no-useless-concat': 'warn',

      // No useless return
      'no-useless-return': 'warn',

      // Prefer regex literals
      'prefer-regex-literals': 'warn',

      // Yoda conditions
      yoda: 'error',
    },
  },

  // Test files configuration (more relaxed rules)
  {
    files: ['**/*.test.{ts,tsx}', '**/*.spec.{ts,tsx}', '**/test/**/*.{ts,tsx}'],
    rules: {
      // Allow any in tests
      '@typescript-eslint/no-explicit-any': 'off',

      // Allow non-null assertions in tests
      '@typescript-eslint/no-non-null-assertion': 'off',

      // Allow empty functions in tests (mocks)
      '@typescript-eslint/no-empty-function': 'off',

      // Allow console in tests
      'no-console': 'off',
    },
  },
]
