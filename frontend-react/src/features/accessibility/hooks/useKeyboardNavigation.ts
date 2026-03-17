/**
 * useKeyboardNavigation Hook
 *
 * BUSINESS CONTEXT:
 * Manages keyboard navigation and shortcuts for accessible interaction.
 * Enables keyboard-only users to navigate efficiently through the application.
 *
 * TECHNICAL IMPLEMENTATION:
 * Registers keyboard event listeners with proper cleanup.
 * Provides helpers for common keyboard navigation patterns.
 * Supports customizable keyboard shortcuts.
 *
 * WCAG 2.1 AA Compliance:
 * - 2.1.1 Keyboard - All functionality available via keyboard
 * - 2.1.4 Character Key Shortcuts - Prevents conflicts with AT
 * - 2.4.3 Focus Order - Maintains logical focus sequence
 */

import { useEffect, useCallback, useRef, useState } from 'react';
import {
  accessibilityService,
  KeyboardShortcut,
} from '@services/accessibilityService';

/**
 * Keyboard Event Handler Type
 *
 * What: Callback function for keyboard events
 * Where: Passed to useKeyboardNavigation
 * Why: Enables custom keyboard handling
 */
export type KeyboardEventHandler = (event: KeyboardEvent) => void | boolean;

/**
 * Keyboard Navigation Options
 *
 * What: Configuration for keyboard navigation behavior
 * Where: Options parameter for useKeyboardNavigation
 * Why: Customizes keyboard handling
 */
export interface KeyboardNavigationOptions {
  /** Whether keyboard shortcuts are enabled */
  enabled?: boolean;
  /** Context for filtering shortcuts (global, modal, form, etc.) */
  context?: string;
  /** Whether to prevent default browser behavior */
  preventDefault?: boolean;
  /** Whether to stop event propagation */
  stopPropagation?: boolean;
}

/**
 * Keyboard Navigation Hook Return Type
 *
 * What: Return value from useKeyboardNavigation
 * Where: Destructured in components using the hook
 * Why: Provides keyboard navigation utilities
 */
export interface UseKeyboardNavigationReturn {
  /** Available keyboard shortcuts */
  shortcuts: KeyboardShortcut[];
  /** Register a keyboard event handler */
  registerHandler: (key: string, modifiers: string[], handler: KeyboardEventHandler) => void;
  /** Unregister a keyboard event handler */
  unregisterHandler: (key: string, modifiers: string[]) => void;
  /** Handle keyboard event */
  handleKeyDown: (event: React.KeyboardEvent) => void;
  /** Check if a key combination is pressed */
  isKeyPressed: (key: string) => boolean;
  /** Currently pressed keys */
  pressedKeys: Set<string>;
}

/**
 * useKeyboardNavigation Hook
 *
 * BUSINESS LOGIC:
 * Provides keyboard navigation functionality for components.
 * Loads user's keyboard shortcuts and enables custom handlers.
 *
 * USAGE:
 * ```tsx
 * const { handleKeyDown, registerHandler } = useKeyboardNavigation({
 *   enabled: true,
 *   context: 'modal'
 * });
 *
 * // Register custom handler
 * useEffect(() => {
 *   registerHandler('Enter', [], (e) => {
 *     console.log('Enter pressed');
 *     return true; // Handled
 *   });
 * }, []);
 *
 * return <div onKeyDown={handleKeyDown}>...</div>;
 * ```
 *
 * @param options - Keyboard navigation options
 * @returns Keyboard navigation utilities
 */
export const useKeyboardNavigation = (
  options: KeyboardNavigationOptions = {}
): UseKeyboardNavigationReturn => {
  const {
    enabled = true,
    context = 'global',
    preventDefault = false,
    stopPropagation = false,
  } = options;

  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([]);
  const [pressedKeys, setPressedKeys] = useState<Set<string>>(new Set());
  const handlersRef = useRef<Map<string, KeyboardEventHandler>>(new Map());

  /**
   * Load keyboard shortcuts
   *
   * BUSINESS LOGIC:
   * Fetches user's keyboard shortcuts from backend.
   * Falls back to default shortcuts if loading fails.
   */
  useEffect(() => {
    const loadShortcuts = async () => {
      try {
        const loadedShortcuts = await accessibilityService.getKeyboardShortcuts(
          undefined,
          context
        );
        setShortcuts(loadedShortcuts.filter(s => s.enabled));
      } catch (error) {
        console.error('[useKeyboardNavigation] Failed to load shortcuts:', error);
        // Fall back to defaults
        const defaultShortcuts = accessibilityService.getDefaultShortcuts();
        setShortcuts(defaultShortcuts.filter(s => s.context === context || s.context === 'global'));
      }
    };

    if (enabled) {
      loadShortcuts();
    }
  }, [enabled, context]);

  /**
   * Generate handler key
   *
   * TECHNICAL IMPLEMENTATION:
   * Creates unique key for handler map.
   *
   * @param key - Key code
   * @param modifiers - Modifier keys
   * @returns Unique handler key
   */
  const getHandlerKey = (key: string, modifiers: string[]): string => {
    const sortedMods = [...modifiers].sort();
    return `${sortedMods.join('+')}+${key}`;
  };

  /**
   * Register keyboard event handler
   *
   * BUSINESS LOGIC:
   * Registers a custom keyboard event handler for specific key combination.
   *
   * @param key - Key code (e.g., 'Enter', 'KeyS')
   * @param modifiers - Modifier keys (['ctrl', 'alt', 'shift'])
   * @param handler - Event handler function
   */
  const registerHandler = useCallback(
    (key: string, modifiers: string[], handler: KeyboardEventHandler): void => {
      const handlerKey = getHandlerKey(key, modifiers);
      handlersRef.current.set(handlerKey, handler);
    },
    []
  );

  /**
   * Unregister keyboard event handler
   *
   * BUSINESS LOGIC:
   * Removes a previously registered keyboard event handler.
   *
   * @param key - Key code
   * @param modifiers - Modifier keys
   */
  const unregisterHandler = useCallback(
    (key: string, modifiers: string[]): void => {
      const handlerKey = getHandlerKey(key, modifiers);
      handlersRef.current.delete(handlerKey);
    },
    []
  );

  /**
   * Handle keyboard event
   *
   * BUSINESS LOGIC:
   * Processes keyboard events and calls appropriate handlers.
   * Checks registered shortcuts and custom handlers.
   *
   * @param event - React keyboard event
   */
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent): void => {
      if (!enabled) return;

      const key = event.code || event.key;
      const modifiers: string[] = [];

      if (event.ctrlKey) modifiers.push('ctrl');
      if (event.altKey) modifiers.push('alt');
      if (event.shiftKey) modifiers.push('shift');
      if (event.metaKey) modifiers.push('meta');

      // Update pressed keys
      setPressedKeys(prev => new Set(prev).add(key));

      // Check custom handlers first
      const handlerKey = getHandlerKey(key, modifiers);
      const customHandler = handlersRef.current.get(handlerKey);
      if (customHandler) {
        const handled = customHandler(event.nativeEvent);
        if (handled) {
          event.preventDefault();
          event.stopPropagation();
          return;
        }
      }

      // Check registered shortcuts
      const matchingShortcut = shortcuts.find(shortcut => {
        const shortcutMods = new Set(shortcut.modifiers.map(m => m.toLowerCase()));
        const eventMods = new Set(modifiers);

        return (
          shortcut.key === key &&
          shortcutMods.size === eventMods.size &&
          [...shortcutMods].every(m => eventMods.has(m))
        );
      });

      if (matchingShortcut) {
        // Dispatch custom event for shortcut action
        const actionEvent = new CustomEvent('keyboard-shortcut', {
          detail: { action: matchingShortcut.action, shortcut: matchingShortcut },
        });
        window.dispatchEvent(actionEvent);

        if (preventDefault) {
          event.preventDefault();
        }
        if (stopPropagation) {
          event.stopPropagation();
        }
      }
    },
    [enabled, shortcuts, preventDefault, stopPropagation]
  );

  /**
   * Handle key up event
   *
   * TECHNICAL IMPLEMENTATION:
   * Removes key from pressed keys set.
   */
  useEffect(() => {
    const handleKeyUp = (event: KeyboardEvent): void => {
      const key = event.code || event.key;
      setPressedKeys(prev => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    };

    window.addEventListener('keyup', handleKeyUp);
    return () => window.removeEventListener('keyup', handleKeyUp);
  }, []);

  /**
   * Check if a key is currently pressed
   *
   * BUSINESS LOGIC:
   * Checks if a specific key is currently pressed down.
   *
   * @param key - Key code to check
   * @returns True if key is pressed
   */
  const isKeyPressed = useCallback(
    (key: string): boolean => {
      return pressedKeys.has(key);
    },
    [pressedKeys]
  );

  return {
    shortcuts,
    registerHandler,
    unregisterHandler,
    handleKeyDown,
    isKeyPressed,
    pressedKeys,
  };
};
