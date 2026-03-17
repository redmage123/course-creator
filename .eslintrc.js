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
        // Allow console statements
        'no-console': 'warn',
        // Allow unused variables for debugging
        'no-unused-vars': 'warn',
        // Allow undefined variables (for global objects)
        'no-undef': 'warn',
        // Allow semicolons
        'semi': ['error', 'always'],
        // Allow quotes preference
        'quotes': ['warn', 'single', { 'allowTemplateLiterals': true }]
    },
    globals: {
        // Frontend globals
        'App': 'readonly',
        'Auth': 'readonly',
        'Navigation': 'readonly',
        'showNotification': 'readonly',
        'UIComponents': 'readonly',
        'CONFIG': 'readonly',
        'window': 'readonly',
        'document': 'readonly',
        'fetch': 'readonly',
        'localStorage': 'readonly',
        'sessionStorage': 'readonly',
        'alert': 'readonly',
        'confirm': 'readonly',
        'console': 'readonly'
    }
};