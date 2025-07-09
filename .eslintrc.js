module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true
  },
  extends: [
    'eslint:recommended'
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module'
  },
  rules: {
    // Allow console.log for debugging (warning only)
    'no-console': 'off',
    
    // Allow unused variables with underscore prefix
    'no-unused-vars': ['error', { 'argsIgnorePattern': '^_' }],
    
    // Allow function declarations after use (for onclick handlers)
    'no-use-before-define': ['error', { 'functions': false }],
    
    // Prefer const/let over var
    'no-var': 'error',
    'prefer-const': 'warn',
    
    // Semicolons required
    'semi': ['error', 'always'],
    
    // Consistent quotes
    'quotes': ['warn', 'single', { 'allowTemplateLiterals': true }],
    
    // No duplicate function declarations
    'no-redeclare': 'error',
    
    // No unreachable code
    'no-unreachable': 'error'
  },
  globals: {
    // Global variables for our application
    'API_BASE': 'readonly',
    'AUTH_API_BASE': 'readonly',
    'currentUser': 'writable',
    'authToken': 'writable',
    
    // Functions that might be called from HTML onclick
    'showLoginModal': 'readonly',
    'showRegisterModal': 'readonly',
    'toggleAccountDropdown': 'readonly',
    'logout': 'readonly',
    'loadCourses': 'readonly',
    'showHome': 'readonly',
    'showCreateCourse': 'readonly',
    'viewCourse': 'readonly',
    'handleNavigation': 'readonly'
  },
  ignorePatterns: [
    'node_modules/',
    'coverage/',
    'test-reports/',
    '*.min.js'
  ]
};