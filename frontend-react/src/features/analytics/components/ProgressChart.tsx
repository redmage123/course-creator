/**
 * ProgressChart Component
 *
 * Displays course progress over time using Chart.js bar chart.
 * Shows completion milestones and learning trajectory.
 *
 * BUSINESS CONTEXT:
 * Visualizes student progress through course content to track
 * completion rates and identify pacing issues.
 *
 * @module features/analytics/components/ProgressChart
 */

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import styles from './ProgressChart.module.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export interface ProgressDataPoint {
  date: string;
  completion_percentage: number;
  items_completed: number;
  label?: string;
}

export interface ProgressChartProps {
  data: ProgressDataPoint[];
}

/**
 * ProgressChart Component
 *
 * WHY THIS APPROACH:
 * - Bar chart clearly shows progress milestones
 * - Gradient fill indicates steady progression
 * - Tooltips show both percentage and item counts
 * - Responsive and accessible with Chart.js
 */
export const ProgressChart: React.FC<ProgressChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No progress data available</p>
      </div>
    );
  }

  // Format dates for labels
  const labels = data.map((point) => {
    const date = new Date(point.date);
    return `${date.getMonth() + 1}/${date.getDate()}`;
  });

  // Prepare chart data
  const chartData = {
    labels,
    datasets: [
      {
        label: 'Course Progress',
        data: data.map((point) => point.completion_percentage),
        backgroundColor: data.map((point) => {
          const percentage = point.completion_percentage;
          if (percentage === 100) return '#4caf50';
          if (percentage >= 75) return '#8bc34a';
          if (percentage >= 50) return '#ff9800';
          if (percentage >= 25) return '#ff5722';
          return '#f44336';
        }),
        borderColor: '#2196f3',
        borderWidth: 0,
        borderRadius: 4,
        barThickness: 40
      }
    ]
  };

  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const dataPoint = data[context.dataIndex];
            return [
              `Progress: ${context.parsed.y}%`,
              `Items Completed: ${dataPoint.items_completed}`
            ];
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: {
          callback: (value: any) => `${value}%`
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  };

  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartWrapper}>
        <Bar data={chartData} options={options} />
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#4caf50' }}></span>
          <span>Complete (100%)</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#8bc34a' }}></span>
          <span>High (75-99%)</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#ff9800' }}></span>
          <span>Medium (50-74%)</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#f44336' }}></span>
          <span>Low (&lt;50%)</span>
        </div>
      </div>
    </div>
  );
};

export default ProgressChart;
