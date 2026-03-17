/**
 * Learning Progress Chart Component
 *
 * WHAT: Visualizes learning progress over time using line chart
 * WHERE: Learning Analytics Dashboard main widget
 * WHY: Shows learning trajectory, velocity, and engagement patterns
 *
 * BUSINESS CONTEXT:
 * Displays multi-dimensional progress tracking:
 * - Progress percentage (completion rate)
 * - Items completed (content consumption)
 * - Time spent (engagement depth)
 * - Engagement score (quality of interaction)
 *
 * TECHNICAL IMPLEMENTATION:
 * - Chart.js for interactive line chart visualization
 * - Multiple datasets for comprehensive progress view
 * - Responsive design with aspect ratio preservation
 * - Color-coded metrics for easy interpretation
 *
 * @module features/learning-analytics/components/LearningProgressChart
 */

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { LearningProgressDataPoint } from '../../../services/learningAnalyticsService';
import styles from './LearningProgressChart.module.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

/**
 * Component Props Interface
 */
export interface LearningProgressChartProps {
  data: LearningProgressDataPoint[];
}

/**
 * Learning Progress Chart Component
 *
 * WHY THIS APPROACH:
 * - Line chart clearly shows trends over time
 * - Multiple datasets enable comprehensive progress view
 * - Gradient fills indicate progress accumulation
 * - Tooltips show detailed metrics on hover
 * - Responsive and accessible with Chart.js
 */
export const LearningProgressChart: React.FC<LearningProgressChartProps> = ({ data }) => {
  /**
   * Empty State Handler
   *
   * WHAT: Displays message when no data available
   * WHERE: Shown when data array is empty
   * WHY: Prevents rendering errors and informs user
   */
  if (!data || data.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No progress data available</p>
        <span className={styles.emptyIcon}>📊</span>
      </div>
    );
  }

  /**
   * Format dates for chart labels
   *
   * WHAT: Converts ISO date strings to readable format
   * WHERE: X-axis labels
   * WHY: User-friendly date display
   */
  const labels = data.map((point) => {
    const date = new Date(point.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });

  /**
   * Chart Data Configuration
   *
   * WHAT: Defines datasets and their visual properties
   * WHERE: Passed to Chart.js Line component
   * WHY: Creates multi-line chart with progress metrics
   */
  const chartData = {
    labels,
    datasets: [
      {
        label: 'Progress %',
        data: data.map((point) => point.progress_percentage),
        borderColor: '#2196f3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#2196f3',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
      {
        label: 'Engagement Score',
        data: data.map((point) => point.engagement_score),
        borderColor: '#4caf50',
        backgroundColor: 'rgba(76, 175, 80, 0.1)',
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: '#4caf50',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
    ],
  };

  /**
   * Chart Options Configuration
   *
   * WHAT: Configures chart behavior and appearance
   * WHERE: Chart.js options object
   * WHY: Customizes interactivity, scaling, and tooltips
   */
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 15,
        },
      },
      tooltip: {
        callbacks: {
          title: (context: any) => {
            const index = context[0].dataIndex;
            const date = new Date(data[index].date);
            return date.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
            });
          },
          afterBody: (context: any) => {
            const index = context[0].dataIndex;
            const dataPoint = data[index];
            return [
              `\nItems Completed: ${dataPoint.items_completed}`,
              `Time Spent: ${Math.round(dataPoint.time_spent_minutes / 60)}h ${
                dataPoint.time_spent_minutes % 60
              }m`,
            ];
          },
        },
      },
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: {
          callback: (value: any) => `${value}%`,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      x: {
        grid: {
          display: false,
        },
      },
    },
  };

  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartWrapper}>
        <Line data={chartData} options={options} />
      </div>

      {/* Additional Stats */}
      <div className={styles.statsRow}>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Total Items</span>
          <span className={styles.statValue}>
            {data[data.length - 1]?.items_completed || 0}
          </span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Total Time</span>
          <span className={styles.statValue}>
            {Math.round(
              data.reduce((sum, point) => sum + point.time_spent_minutes, 0) / 60
            )}
            h
          </span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statLabel}>Avg Engagement</span>
          <span className={styles.statValue}>
            {Math.round(
              data.reduce((sum, point) => sum + point.engagement_score, 0) / data.length
            )}
            %
          </span>
        </div>
      </div>
    </div>
  );
};

export default LearningProgressChart;
