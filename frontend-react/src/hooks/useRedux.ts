/**
 * Custom Redux Hooks
 *
 * BUSINESS CONTEXT:
 * Type-safe Redux hooks for accessing state and dispatching actions throughout
 * the application.
 *
 * TECHNICAL IMPLEMENTATION:
 * Pre-typed versions of useDispatch and useSelector hooks for TypeScript support.
 */

import { useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from '@store/index';

/**
 * Typed useDispatch hook
 *
 * WHY THIS APPROACH:
 * - Provides type inference for all dispatched actions
 * - Enables autocomplete for action creators
 * - Prevents dispatching invalid actions
 *
 * @returns Typed dispatch function
 */
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();

/**
 * Typed useSelector hook
 *
 * WHY THIS APPROACH:
 * - Provides type inference for selected state
 * - Autocomplete for state properties
 * - Compile-time errors for invalid selectors
 *
 * @returns Typed selector function
 */
export const useAppSelector = useSelector.withTypes<RootState>();
