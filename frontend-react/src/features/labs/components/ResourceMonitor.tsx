/**
 * Resource Monitor Component
 *
 * Real-time resource usage monitoring for lab environment
 * Displays:
 * - CPU usage percentage
 * - Memory usage (used/total)
 * - Disk usage (used/total)
 * - Network I/O
 * - Session time
 *
 * Updates every 2 seconds via WebSocket or polling
 *
 * @module features/labs/components/ResourceMonitor
 */

import React, { useEffect, useState } from 'react';
import styles from './ResourceMonitor.module.css';

export interface ResourceUsage {
  cpu: number; // Percentage 0-100
  memory: {
    used: number; // MB
    total: number; // MB
    percentage: number; // 0-100
  };
  disk: {
    used: number; // GB
    total: number; // GB
    percentage: number; // 0-100
  };
  network?: {
    rx: number; // MB/s
    tx: number; // MB/s
  };
}

export interface ResourceMonitorProps {
  resourceUsage: ResourceUsage;
  sessionTime: number; // seconds
  isLive?: boolean;
  onRefresh?: () => void;
}

export const ResourceMonitor: React.FC<ResourceMonitorProps> = ({
  resourceUsage,
  sessionTime,
  isLive = true,
  onRefresh
}) => {
  const [displayTime, setDisplayTime] = useState(sessionTime);

  // Update session timer
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      setDisplayTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isLive]);

  // Format time as HH:MM:SS
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return [hours, minutes, secs]
      .map(v => v.toString().padStart(2, '0'))
      .join(':');
  };

  // Format bytes to human-readable
  const formatBytes = (mb: number): string => {
    if (mb < 1024) {
      return `${mb.toFixed(1)} MB`;
    }
    return `${(mb / 1024).toFixed(1)} GB`;
  };

  // Get usage level class for styling
  const getUsageLevel = (percentage: number): string => {
    if (percentage >= 90) return styles.critical;
    if (percentage >= 75) return styles.warning;
    return styles.normal;
  };

  return (
    <div className={styles.resourceMonitor} id="resource-monitor">
      <div className={styles.monitorHeader}>
        <span className={styles.monitorTitle}>Resources</span>
        {isLive && <span className={styles.liveIndicator}>● Live</span>}
        {onRefresh && (
          <button
            id="refresh-resources-btn"
            className={styles.refreshBtn}
            onClick={onRefresh}
            title="Refresh Resources"
          >
            🔄
          </button>
        )}
      </div>

      <div className={styles.metricsContainer}>
        {/* Session Time */}
        <div className={styles.metric}>
          <div className={styles.metricHeader}>
            <span className={styles.metricIcon}>⏱️</span>
            <span className={styles.metricLabel}>Session Time</span>
          </div>
          <div className={styles.metricValue}>
            {formatTime(displayTime)}
          </div>
        </div>

        {/* CPU Usage */}
        <div className={styles.metric}>
          <div className={styles.metricHeader}>
            <span className={styles.metricIcon}>💻</span>
            <span className={styles.metricLabel}>CPU</span>
          </div>
          <div className={styles.metricValue}>
            {resourceUsage.cpu.toFixed(1)}%
          </div>
          <div className={styles.progressBar}>
            <div
              className={`${styles.progressFill} ${getUsageLevel(resourceUsage.cpu)}`}
              style={{ width: `${resourceUsage.cpu}%` }}
            />
          </div>
        </div>

        {/* Memory Usage */}
        <div className={styles.metric}>
          <div className={styles.metricHeader}>
            <span className={styles.metricIcon}>🧠</span>
            <span className={styles.metricLabel}>Memory</span>
          </div>
          <div className={styles.metricValue}>
            {formatBytes(resourceUsage.memory.used)} / {formatBytes(resourceUsage.memory.total)}
          </div>
          <div className={styles.progressBar}>
            <div
              className={`${styles.progressFill} ${getUsageLevel(resourceUsage.memory.percentage)}`}
              style={{ width: `${resourceUsage.memory.percentage}%` }}
            />
          </div>
          <div className={styles.metricSubtext}>
            {resourceUsage.memory.percentage.toFixed(1)}% used
          </div>
        </div>

        {/* Disk Usage */}
        <div className={styles.metric}>
          <div className={styles.metricHeader}>
            <span className={styles.metricIcon}>💾</span>
            <span className={styles.metricLabel}>Disk</span>
          </div>
          <div className={styles.metricValue}>
            {resourceUsage.disk.used.toFixed(1)} GB / {resourceUsage.disk.total.toFixed(1)} GB
          </div>
          <div className={styles.progressBar}>
            <div
              className={`${styles.progressFill} ${getUsageLevel(resourceUsage.disk.percentage)}`}
              style={{ width: `${resourceUsage.disk.percentage}%` }}
            />
          </div>
          <div className={styles.metricSubtext}>
            {resourceUsage.disk.percentage.toFixed(1)}% used
          </div>
        </div>

        {/* Network I/O (optional) */}
        {resourceUsage.network && (
          <div className={styles.metric}>
            <div className={styles.metricHeader}>
              <span className={styles.metricIcon}>🌐</span>
              <span className={styles.metricLabel}>Network</span>
            </div>
            <div className={styles.networkMetrics}>
              <div className={styles.networkMetric}>
                <span className={styles.networkLabel}>↓ RX:</span>
                <span className={styles.networkValue}>
                  {resourceUsage.network.rx.toFixed(2)} MB/s
                </span>
              </div>
              <div className={styles.networkMetric}>
                <span className={styles.networkLabel}>↑ TX:</span>
                <span className={styles.networkValue}>
                  {resourceUsage.network.tx.toFixed(2)} MB/s
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Resource Alerts */}
      {(resourceUsage.cpu >= 90 ||
        resourceUsage.memory.percentage >= 90 ||
        resourceUsage.disk.percentage >= 90) && (
        <div className={styles.alertContainer}>
          <div className={styles.alert}>
            <span className={styles.alertIcon}>⚠️</span>
            <span className={styles.alertText}>
              High resource usage detected. Performance may be impacted.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResourceMonitor;
