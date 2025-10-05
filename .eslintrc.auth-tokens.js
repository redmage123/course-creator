/**
 * ESLint Custom Rules for Authentication Token Consistency
 *
 * BUSINESS CONTEXT:
 * Prevents developers from using inconsistent localStorage keys for auth tokens,
 * which causes redirect loops and authentication failures in production.
 *
 * TECHNICAL IMPLEMENTATION:
 * Custom ESLint rules to enforce 'authToken' naming convention
 *
 * TDD METHODOLOGY:
 * These rules catch token key inconsistencies at development time,
 * before they reach production.
 */

module.exports = {
    plugins: ['no-restricted-syntax'],
    rules: {
        /**
         * RULE: Enforce authToken naming convention
         * REQUIREMENT: All localStorage auth keys must use 'authToken' not 'auth_token'
         */
        'no-restricted-syntax': [
            'error',
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='getItem'] > Literal[value='auth_token']",
                message: "Use 'authToken' instead of 'auth_token' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='setItem'] > Literal[value='auth_token']",
                message: "Use 'authToken' instead of 'auth_token' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='removeItem'] > Literal[value='auth_token']",
                message: "Use 'authToken' instead of 'auth_token' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='getItem'] > Literal[value='access_token']",
                message: "Use 'authToken' instead of 'access_token' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='setItem'] > Literal[value='access_token']",
                message: "Use 'authToken' instead of 'access_token' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='removeItem'] > Literal[value='access_token']",
                message: "Use 'authToken' instead of 'access_token' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='getItem'] > Literal[value='user_data']",
                message: "Use 'currentUser' instead of 'user_data' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='setItem'] > Literal[value='user_data']",
                message: "Use 'currentUser' instead of 'user_data' for localStorage key consistency"
            },
            {
                selector: "CallExpression[callee.object.name='localStorage'][callee.property.name='removeItem'] > Literal[value='user_data']",
                message: "Use 'currentUser' instead of 'user_data' for localStorage key consistency"
            }
        ]
    }
};
