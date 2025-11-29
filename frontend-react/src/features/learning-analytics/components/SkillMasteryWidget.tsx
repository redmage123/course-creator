/**
 * Skill Mastery Widget Component
 *
 * WHAT: Displays skill mastery levels with visual progress indicators
 * WHERE: Learning Analytics Dashboard skill tracking section
 * WHY: Shows skill proficiency, practice time, and review scheduling
 *
 * BUSINESS CONTEXT:
 * Provides comprehensive skill mastery visualization:
 * - Mastery level (novice through master)
 * - Mastery score percentage
 * - Assessment performance (passed/completed)
 * - Practice time and streaks
 * - Spaced repetition schedule (SM-2 algorithm)
 * - Retention estimates
 *
 * TECHNICAL IMPLEMENTATION:
 * - Radar chart for multi-skill comparison
 * - Progress bars for individual skill mastery
 * - Color-coded mastery levels
 * - Spaced repetition interval display
 * - Sortable skill list
 *
 * @module features/learning-analytics/components/SkillMasteryWidget
 */

import React, { useState } from 'react';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';
import type { SkillMastery, MasteryLevel } from '../../../services/learningAnalyticsService';
import styles from './SkillMasteryWidget.module.css';

// Register Chart.js components
ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

/**
 * Component Props Interface
 */
export interface SkillMasteryWidgetProps {
  skills: SkillMastery[];
}

/**
 * Sort Options Type
 */
type SortOption = 'mastery' | 'recent' | 'name' | 'review';

/**
 * Skill Mastery Widget Component
 *
 * WHY THIS APPROACH:
 * - Radar chart shows overall skill profile
 * - Individual skill cards provide detailed metrics
 * - Sortable list enables quick identification of priorities
 * - Color coding provides instant visual feedback
 * - Spaced repetition data supports review planning
 */
export const SkillMasteryWidget: React.FC<SkillMasteryWidgetProps> = ({ skills }) => {
  const [sortBy, setSortBy] = useState<SortOption>('mastery');
  const [viewMode, setViewMode] = useState<'chart' | 'list'>('chart');

  /**
   * Empty State Handler
   */
  if (!skills || skills.length === 0) {
    return (
      <div className={styles.emptyState}>
        <p>No skills tracked yet</p>
        <span className={styles.emptyIcon}>🎯</span>
      </div>
    );
  }

  /**
   * Get Mastery Level Color
   *
   * WHAT: Maps mastery level to visual color
   * WHERE: Progress bars and badges
   * WHY: Provides instant visual feedback on skill level
   */
  const getMasteryColor = (level: MasteryLevel): string => {
    const colorMap: Record<MasteryLevel, string> = {
      novice: '#f44336',
      beginner: '#ff9800',
      intermediate: '#ffeb3b',
      proficient: '#8bc34a',
      expert: '#4caf50',
      master: '#2196f3',
    };
    return colorMap[level] || '#9e9e9e';
  };

  /**
   * Sort Skills
   *
   * WHAT: Sorts skills based on selected criterion
   * WHERE: Skill list display
   * WHY: Enables users to prioritize viewing
   */
  const sortedSkills = [...skills].sort((a, b) => {
    switch (sortBy) {
      case 'mastery':
        return b.mastery_score - a.mastery_score;
      case 'recent':
        if (!a.last_practiced_at) return 1;
        if (!b.last_practiced_at) return -1;
        return (
          new Date(b.last_practiced_at).getTime() -
          new Date(a.last_practiced_at).getTime()
        );
      case 'name':
        return a.skill_topic.localeCompare(b.skill_topic);
      case 'review':
        return a.current_interval_days - b.current_interval_days;
      default:
        return 0;
    }
  });

  /**
   * Radar Chart Data Configuration
   *
   * WHAT: Configures radar chart for top skills
   * WHERE: Chart view mode
   * WHY: Provides visual skill profile overview
   */
  const topSkills = sortedSkills.slice(0, 8); // Show top 8 skills
  const radarData = {
    labels: topSkills.map((skill) => skill.skill_topic),
    datasets: [
      {
        label: 'Mastery Score',
        data: topSkills.map((skill) => skill.mastery_score),
        backgroundColor: 'rgba(33, 150, 243, 0.2)',
        borderColor: '#2196f3',
        borderWidth: 2,
        pointBackgroundColor: '#2196f3',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  /**
   * Radar Chart Options
   */
  const radarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: {
          stepSize: 20,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)',
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context: any) => `Mastery: ${context.parsed.r}%`,
        },
      },
    },
  };

  return (
    <div className={styles.widgetContainer}>
      {/* View Mode Toggle */}
      <div className={styles.controls}>
        <div className={styles.viewToggle}>
          <button
            className={`${styles.toggleBtn} ${viewMode === 'chart' ? styles.active : ''}`}
            onClick={() => setViewMode('chart')}
            aria-pressed={viewMode === 'chart'}
          >
            Chart View
          </button>
          <button
            className={`${styles.toggleBtn} ${viewMode === 'list' ? styles.active : ''}`}
            onClick={() => setViewMode('list')}
            aria-pressed={viewMode === 'list'}
          >
            List View
          </button>
        </div>

        {/* Sort Options */}
        <div className={styles.sortSelector}>
          <label htmlFor="sort-skills">Sort by:</label>
          <select
            id="sort-skills"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className={styles.sortSelect}
          >
            <option value="mastery">Mastery Level</option>
            <option value="recent">Recently Practiced</option>
            <option value="name">Skill Name</option>
            <option value="review">Review Due</option>
          </select>
        </div>
      </div>

      {/* Chart View */}
      {viewMode === 'chart' && (
        <div className={styles.chartView}>
          <div className={styles.radarChart}>
            <Radar data={radarData} options={radarOptions} />
          </div>
          <p className={styles.chartNote}>Showing top 8 skills by mastery score</p>
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className={styles.listView}>
          {sortedSkills.map((skill) => (
            <div key={skill.id} className={styles.skillCard}>
              {/* Skill Header */}
              <div className={styles.skillHeader}>
                <h3 className={styles.skillName}>{skill.skill_topic}</h3>
                <span
                  className={styles.masteryBadge}
                  style={{ backgroundColor: getMasteryColor(skill.mastery_level) }}
                >
                  {skill.mastery_level.charAt(0).toUpperCase() +
                    skill.mastery_level.slice(1)}
                </span>
              </div>

              {/* Progress Bar */}
              <div className={styles.progressSection}>
                <div className={styles.progressBar}>
                  <div
                    className={styles.progressFill}
                    style={{
                      width: `${skill.mastery_score}%`,
                      backgroundColor: getMasteryColor(skill.mastery_level),
                    }}
                  />
                </div>
                <span className={styles.progressValue}>{skill.mastery_score}%</span>
              </div>

              {/* Skill Metrics */}
              <div className={styles.skillMetrics}>
                <div className={styles.metric}>
                  <span className={styles.metricLabel}>Assessments</span>
                  <span className={styles.metricValue}>
                    {skill.assessments_passed}/{skill.assessments_completed}
                  </span>
                </div>
                <div className={styles.metric}>
                  <span className={styles.metricLabel}>Practice Time</span>
                  <span className={styles.metricValue}>
                    {Math.round(skill.total_practice_time_minutes / 60)}h
                  </span>
                </div>
                <div className={styles.metric}>
                  <span className={styles.metricLabel}>Streak</span>
                  <span className={styles.metricValue}>{skill.practice_streak_days} days</span>
                </div>
              </div>

              {/* Spaced Repetition Info */}
              <div className={styles.repetitionInfo}>
                <div className={styles.repetitionMetric}>
                  <span className={styles.repetitionLabel}>Retention:</span>
                  <span className={styles.repetitionValue}>
                    {Math.round(skill.retention_estimate * 100)}%
                  </span>
                </div>
                <div className={styles.repetitionMetric}>
                  <span className={styles.repetitionLabel}>Review Interval:</span>
                  <span className={styles.repetitionValue}>
                    {skill.current_interval_days} days
                  </span>
                </div>
                <div className={styles.repetitionMetric}>
                  <span className={styles.repetitionLabel}>Ease Factor:</span>
                  <span className={styles.repetitionValue}>{skill.ease_factor.toFixed(2)}</span>
                </div>
              </div>

              {/* Last Practice Date */}
              {skill.last_practiced_at && (
                <p className={styles.lastPractice}>
                  Last practiced:{' '}
                  {new Date(skill.last_practiced_at).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      <div className={styles.summaryStats}>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Total Skills</span>
          <span className={styles.summaryValue}>{skills.length}</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Avg Mastery</span>
          <span className={styles.summaryValue}>
            {Math.round(
              skills.reduce((sum, skill) => sum + skill.mastery_score, 0) / skills.length
            )}
            %
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Total Practice</span>
          <span className={styles.summaryValue}>
            {Math.round(
              skills.reduce((sum, skill) => sum + skill.total_practice_time_minutes, 0) / 60
            )}
            h
          </span>
        </div>
      </div>
    </div>
  );
};

export default SkillMasteryWidget;
