/**
 * Keyboard Shortcuts Panel Component
 *
 * BUSINESS CONTEXT:
 * Displays available keyboard shortcuts for platform navigation. Helps users
 * discover and learn keyboard navigation. Implements WCAG 2.1.1 (Keyboard).
 *
 * TECHNICAL IMPLEMENTATION:
 * Loads shortcuts from accessibility service. Displays in accessible table
 * format with clear labels.
 *
 * WCAG 2.1 AA Compliance:
 * - 2.1.1 Keyboard (Level A)
 * - Clear keyboard shortcut documentation
 * - Accessible table structure
 */

import React, { useEffect, useState } from 'react';
import { accessibilityService, KeyboardShortcut } from '@services/accessibilityService';
import styles from './KeyboardShortcutsPanel.module.css';

/**
 * Keyboard Shortcuts Panel Component
 */
export const KeyboardShortcutsPanel: React.FC = () => {
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadShortcuts = async () => {
      try {
        const loaded = await accessibilityService.getKeyboardShortcuts();
        setShortcuts(loaded);
      } catch (error) {
        console.error('[KeyboardShortcutsPanel] Failed to load shortcuts:', error);
        setShortcuts(accessibilityService.getDefaultShortcuts());
      } finally {
        setIsLoading(false);
      }
    };

    loadShortcuts();
  }, []);

  const formatShortcut = (shortcut: KeyboardShortcut): string => {
    const parts = [...shortcut.modifiers.map(m => m.charAt(0).toUpperCase() + m.slice(1))];
    const key = shortcut.key.replace('Key', '');
    parts.push(key);
    return parts.join(' + ');
  };

  if (isLoading) {
    return (
      <div className={styles.loading}>
        Loading keyboard shortcuts...
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Available Keyboard Shortcuts</h3>
      <table className={styles.table}>
        <thead>
          <tr>
            <th scope="col" className={styles.headerCell}>Shortcut</th>
            <th scope="col" className={styles.headerCell}>Action</th>
          </tr>
        </thead>
        <tbody>
          {shortcuts.map((shortcut) => (
            <tr key={shortcut.id} className={styles.row}>
              <td className={styles.cell}>
                <kbd className={styles.kbd}>{formatShortcut(shortcut)}</kbd>
              </td>
              <td className={styles.cell}>{shortcut.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
