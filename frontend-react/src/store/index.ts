/**
 * Redux Store Configuration
 *
 * BUSINESS CONTEXT:
 * Centralized state management for the Course Creator Platform. Manages global
 * application state including authentication, user data, and UI state.
 *
 * TECHNICAL IMPLEMENTATION:
 * Uses Redux Toolkit for simplified Redux setup with excellent TypeScript support.
 * Configured with middleware for async operations and dev tools support.
 */

import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import userReducer from './slices/userSlice';
import uiReducer from './slices/uiSlice';

/**
 * Configure Redux store with all reducers
 *
 * WHY THIS APPROACH:
 * - Redux Toolkit simplifies store configuration
 * - Automatic Redux DevTools integration
 * - Built-in thunk middleware for async operations
 * - TypeScript inference for state and dispatch
 */
export const store = configureStore({
  reducer: {
    auth: authReducer,
    user: userReducer,
    ui: uiReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types for serialization check
        ignoredActions: ['auth/loginSuccess', 'auth/refreshToken'],
      },
    }),
  devTools: process.env.NODE_ENV !== 'production',
});

// Export types for TypeScript
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
