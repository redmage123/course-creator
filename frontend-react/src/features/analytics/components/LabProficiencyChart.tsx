/**
 * LabProficiencyChart Component
 *
 * Displays lab proficiency skills using Chart.js radar chart.
 * Shows competency across different technical skills and concepts.
 *
 * BUSINESS CONTEXT:
 * Visualizes hands-on technical proficiency to identify strengths
 * and areas needing more practice or support.
 *
 * @module features/analytics/components/LabProficiencyChart
 */

import React from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import styles from './LabProficiencyChart.module.css';

// Register Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

export interface SkillProficiency {
  skill_name: string;
  proficiency_level: number;
  exercises_completed: number;
}

export interface LabProficiencyChartProps {
  data: SkillProficiency[];
}

/**
 * LabProficiencyChart Component
 *
 * WHY THIS APPROACH:
 * - Radar chart ideal for multi-dimensional skill assessment
 * - Shows relative strengths and weaknesses at a glance
 * - Color-coded proficiency levels
 * - Interactive tooltips show detailed exercise counts
 */
export const LabProficiencyChart: React.FC<LabProficiencyChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No lab proficiency data available</p>
      </div>
    );
  }

  // Prepare chart data
  const chartData = {
    labels: data.map((skill) => skill.skill_name),
    datasets: [
      {
        label: 'Proficiency Level',
        data: data.map((skill) => skill.proficiency_level),
        backgroundColor: 'rgba(156, 39, 176, 0.2)',
        borderColor: '#9c27b0',
        borderWidth: 2,
        pointBackgroundColor: data.map((skill) => {
          if (skill.proficiency_level >= 80) return '#4caf50';
          if (skill.proficiency_level >= 60) return '#ff9800';
          return '#f44336';
        }),
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8
      }
    ]
  };

  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20,
          callback: (value: any) => `${value}%`
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        pointLabels: {
          font: {
            size: 12
          }
        }
      }
    },
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const skill = data[context.dataIndex];
            return [
              `Proficiency: ${context.parsed.r}%`,
              `Exercises: ${skill.exercises_completed}`
            ];
          }
        }
      }
    }
  };

  return (
    <div className={styles.chartContainer}>
      <div className={styles.chartWrapper}>
        <Radar data={chartData} options={options} />
      </div>

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#4caf50' }}></span>
          <span>Advanced (80+)</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#ff9800' }}></span>
          <span>Intermediate (60-79)</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ backgroundColor: '#f44336' }}></span>
          <span>Beginner (&lt;60)</span>
        </div>
      </div>

      {/* Skill breakdown */}
      <div className={styles.skillsList}>
        {data.map((skill, index) => (
          <div key={index} className={styles.skillItem}>
            <div className={styles.skillHeader}>
              <span className={styles.skillName}>{skill.skill_name}</span>
              <span className={styles.skillValue}>{skill.proficiency_level}%</span>
            </div>
            <div className={styles.progressBar}>
              <div
                className={styles.progressFill}
                style={{
                  width: `${skill.proficiency_level}%`,
                  backgroundColor:
                    skill.proficiency_level >= 80
                      ? '#4caf50'
                      : skill.proficiency_level >= 60
                      ? '#ff9800'
                      : '#f44336'
                }}
              />
            </div>
            <div className={styles.skillMeta}>
              {skill.exercises_completed} exercises completed
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LabProficiencyChart;
