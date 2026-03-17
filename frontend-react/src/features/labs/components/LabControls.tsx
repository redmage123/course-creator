/**
 * Lab Controls Component
 *
 * Provides lab session control buttons:
 * - Start Lab
 * - Pause Lab
 * - Resume Lab
 * - Stop Lab
 *
 * Buttons are context-aware based on current lab status
 *
 * @module features/labs/components/LabControls
 */

import React from 'react';
import { Button } from '@/components/atoms/Button';
import type { LabStatus } from '../LabEnvironment';
import styles from './LabControls.module.css';

export interface LabControlsProps {
  status: LabStatus;
  onStart: () => Promise<void>;
  onPause: () => Promise<void>;
  onResume: () => Promise<void>;
  onStop: () => Promise<void>;
}

export const LabControls: React.FC<LabControlsProps> = ({
  status,
  onStart,
  onPause,
  onResume,
  onStop
}) => {
  const [isLoading, setIsLoading] = React.useState(false);

  const handleAction = async (action: () => Promise<void>) => {
    setIsLoading(true);
    try {
      await action();
    } catch (error) {
      console.error('Lab control action failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.labControls}>
      {status === 'stopped' && (
        <Button
          id="start-lab-btn"
          variant="primary"
          size="small"
          onClick={() => handleAction(onStart)}
          disabled={isLoading}
        >
          ▶️ Start Lab
        </Button>
      )}

      {status === 'running' && (
        <>
          <Button
            id="pause-lab-btn"
            variant="secondary"
            size="small"
            onClick={() => handleAction(onPause)}
            disabled={isLoading}
          >
            ⏸️ Pause
          </Button>
          <Button
            id="stop-lab-btn"
            variant="danger"
            size="small"
            onClick={() => handleAction(onStop)}
            disabled={isLoading}
          >
            ⏹️ Stop
          </Button>
        </>
      )}

      {status === 'paused' && (
        <>
          <Button
            id="resume-lab-btn"
            variant="primary"
            size="small"
            onClick={() => handleAction(onResume)}
            disabled={isLoading}
          >
            ▶️ Resume
          </Button>
          <Button
            id="stop-lab-btn"
            variant="danger"
            size="small"
            onClick={() => handleAction(onStop)}
            disabled={isLoading}
          >
            ⏹️ Stop
          </Button>
        </>
      )}

      {(status === 'starting' || status === 'stopping') && (
        <div className={styles.statusMessage}>
          <span className={styles.spinner}></span>
          <span>{status === 'starting' ? 'Starting...' : 'Stopping...'}</span>
        </div>
      )}
    </div>
  );
};

export default LabControls;
