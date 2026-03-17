/**
 * Redux Store Hooks
 *
 * BUSINESS CONTEXT:
 * Provides typed versions of Redux hooks for use throughout the application.
 * Ensures type safety when accessing Redux state and dispatch.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Typed useAppSelector for type-safe state access
 * - Typed useAppDispatch for type-safe action dispatching
 * - Follows Redux Toolkit best practices
 */

import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './index';

/**
 * Typed version of useDispatch hook
 *
 * WHY THIS APPROACH:
 * - Provides TypeScript autocomplete for dispatched actions
 * - Ensures type safety for async thunks
 * - Single source of truth for dispatch typing
 */
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();

/**
 * Typed version of useSelector hook
 *
 * WHY THIS APPROACH:
 * - Provides TypeScript autocomplete for state access
 * - Ensures type safety when selecting from state
 * - Single source of truth for state typing
 */
export const useAppSelector = useSelector.withTypes<RootState>();
