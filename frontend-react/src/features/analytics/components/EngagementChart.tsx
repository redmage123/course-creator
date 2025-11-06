/**
 * EngagementChart Component
 *
 * Displays student engagement metrics over time using Chart.js.
 * Shows trends in activity, participation, and learning commitment.
 *
 * BUSINESS CONTEXT:
 * Tracks student engagement patterns to identify declining participation
 * and enable early intervention.
 *
 * @module features/analytics/components/EngagementChart
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
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import styles from './EngagementChart.module.css';

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

export interface EngagementDataPoint {
  date: string;
  score: number;
  label?: string;
}

export interface EngagementChartProps {
  data: EngagementDataPoint[];
}

/**
 * EngagementChart Component
 *
 * WHY THIS APPROACH:
 * - Chart.js provides professional, interactive charts
 * - Responsive and accessible
 * - Color-coded thresholds (green > 70, yellow 50-70, red < 50)
 * - Built-in tooltips and animations
 */
export const EngagementChart: React.FC<EngagementChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No engagement data available</p>
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
        label: 'Engagement Score',
        data: data.map((point) => point.score),
        borderColor: '#2196f3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        pointBackgroundColor: data.map((point) => {
          if (point.score >= 70) return '#4caf50';
          if (point.score >= 50) return '#ff9800';
          return '#f44336';
        }),
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.3,
        fill: true
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
            return `Engagement: ${context.parsed.y}%`;
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
        <Line data={chartData} options={options} />
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#4caf50' }}></span>
          <span>High (70+)</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#ff9800' }}></span>
          <span>Medium (50-69)</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#f44336' }}></span>
          <span>Low (&lt;50)</span>
        </div>
      </div>
    </div>
  );
};

export default EngagementChart;
