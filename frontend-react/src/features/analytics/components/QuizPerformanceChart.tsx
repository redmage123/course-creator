/**
 * QuizPerformanceChart Component
 *
 * Displays quiz performance data using Chart.js doughnut chart.
 * Shows pass/fail ratio and average score trends.
 *
 * BUSINESS CONTEXT:
 * Visualizes assessment performance to identify knowledge gaps
 * and areas requiring additional instruction or practice.
 *
 * @module features/analytics/components/QuizPerformanceChart
 */

import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import styles from './QuizPerformanceChart.module.css';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export interface QuizPerformanceDataPoint {
  quiz_name: string;
  score: number;
  passed: boolean;
  date: string;
}

export interface QuizPerformanceChartProps {
  data: QuizPerformanceDataPoint[];
}

/**
 * QuizPerformanceChart Component
 *
 * WHY THIS APPROACH:
 * - Doughnut chart provides clear pass/fail visualization
 * - Shows overall quiz performance at a glance
 * - Color-coded for success (green) and failure (red)
 * - Displays average score in center
 */
export const QuizPerformanceChart: React.FC<QuizPerformanceChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No quiz performance data available</p>
      </div>
    );
  }

  // Calculate pass/fail counts
  const passedCount = data.filter((point) => point.passed).length;
  const failedCount = data.length - passedCount;
  const averageScore = Math.round(
    data.reduce((sum, point) => sum + point.score, 0) / data.length
  );

  // Prepare chart data
  const chartData = {
    labels: ['Passed', 'Failed'],
    datasets: [
      {
        label: 'Quiz Results',
        data: [passedCount, failedCount],
        backgroundColor: ['#4caf50', '#f44336'],
        borderColor: ['#fff', '#fff'],
        borderWidth: 3,
        hoverOffset: 10
      }
    ]
  };

  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: {
      legend: {
        display: true,
        position: 'bottom' as const,
        labels: {
          padding: 20,
          font: {
            size: 13
          }
        }
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            const percentage = ((value / data.length) * 100).toFixed(1);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    }
  };

  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartWrapper}>
        <Doughnut data={chartData} options={options} />
        <div className={styles.centerText}>
          <div className={styles.centerValue}>{averageScore}%</div>
          <div className={styles.centerLabel}>Avg Score</div>
        </div>
      </div>

      {/* Stats */}
      <div className={styles.stats}>
        <div className={styles.statItem}>
          <span className={styles.statValue}>{passedCount}</span>
          <span className={styles.statLabel}>Passed</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statValue}>{failedCount}</span>
          <span className={styles.statLabel}>Failed</span>
        </div>
        <div className={styles.statItem}>
          <span className={styles.statValue}>{data.length}</span>
          <span className={styles.statLabel}>Total</span>
        </div>
      </div>
    </div>
  );
};

export default QuizPerformanceChart;
