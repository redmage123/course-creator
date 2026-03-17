/**
 * IDE Selector Component
 *
 * Allows switching between different IDE environments:
 * - VSCode (code editor)
 * - Jupyter (notebook interface)
 * - Terminal (command line)
 *
 * @module features/labs/components/IDESelector
 */

import React from 'react';
import type { IDEType } from '../LabEnvironment';
import styles from './IDESelector.module.css';

export interface IDESelectorProps {
  selectedIDE: IDEType;
  onIDEChange: (ide: IDEType) => void;
  disabled?: boolean;
}

export const IDESelector: React.FC<IDESelectorProps> = ({
  selectedIDE,
  onIDEChange,
  disabled = false
}) => {
  const ides: Array<{ type: IDEType; label: string; icon: string }> = [
    { type: 'vscode', label: 'VS Code', icon: '📝' },
    { type: 'jupyter', label: 'Jupyter', icon: '📓' },
    { type: 'terminal', label: 'Terminal', icon: '💻' }
  ];

  return (
    <div className={styles.ideSelector}>
      <span className={styles.ideLabel}>IDE:</span>
      <div className={styles.ideTabs}>
        {ides.map(({ type, label, icon }) => (
          <button
            key={type}
            className={`${styles.ideTab} ${selectedIDE === type ? styles.active : ''}`}
            onClick={() => onIDEChange(type)}
            disabled={disabled}
            data-ide={type}
            aria-label={`Switch to ${label}`}
            aria-pressed={selectedIDE === type}
          >
            <span className={styles.ideIcon}>{icon}</span>
            <span className={styles.ideText}>{label}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default IDESelector;
