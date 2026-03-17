/**
 * RiskAssessmentCard Component
 *
 * Displays student risk assessment indicators for instructors.
 * Shows risk level, contributing factors, and recommended interventions.
 *
 * BUSINESS CONTEXT:
 * Helps instructors identify at-risk students early and take proactive measures
 * to improve student success rates.
 *
 * @module features/analytics/components/RiskAssessmentCard
 */

import React from 'react';
import styles from './RiskAssessmentCard.module.css';

export interface RiskFactor {
  factor: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

export interface RiskAssessment {
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  factors: RiskFactor[];
  recommendations: string[];
  last_updated: string;
}

export interface RiskAssessmentCardProps {
  riskData: RiskAssessment;
}

/**
 * RiskAssessmentCard Component
 *
 * WHY THIS APPROACH:
 * - Color-coded risk levels for quick visual assessment
 * - Shows specific risk factors to identify root causes
 * - Provides actionable recommendations for intervention
 * - Severity indicators help prioritize which students need attention
 */
export const RiskAssessmentCard: React.FC<RiskAssessmentCardProps> = ({ riskData }) => {
  const getRiskLevelColor = (): string => {
    switch (riskData.risk_level) {
      case 'low':
        return '#4caf50';
      case 'medium':
        return '#ff9800';
      case 'high':
        return '#f44336';
      case 'critical':
        return '#d32f2f';
      default:
        return '#999';
    }
  };

  const getRiskLevelLabel = (): string => {
    return riskData.risk_level.charAt(0).toUpperCase() + riskData.risk_level.slice(1);
  };

  const getSeverityIcon = (severity: string): string => {
    switch (severity) {
      case 'low':
        return '○';
      case 'medium':
        return '◐';
      case 'high':
        return '●';
      default:
        return '○';
    }
  };

  return (
    <div className={styles.riskCard}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h2 className={styles.title}>Risk Assessment</h2>
          <p className={styles.lastUpdated}>
            Last updated: {new Date(riskData.last_updated).toLocaleDateString()}
          </p>
        </div>
        <div
          className={styles.riskBadge}
          style={{ backgroundColor: getRiskLevelColor() }}
        >
          <span className={styles.riskLevel}>{getRiskLevelLabel()}</span>
          <span className={styles.riskScore}>{riskData.risk_score}/100</span>
        </div>
      </div>

      {/* Risk Factors */}
      {riskData.factors && riskData.factors.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Contributing Factors</h3>
          <div className={styles.factorsList}>
            {riskData.factors.map((factor, index) => (
              <div key={index} className={styles.factorItem}>
                <div className={styles.factorHeader}>
                  <span
                    className={`${styles.severityIcon} ${styles[factor.severity]}`}
                  >
                    {getSeverityIcon(factor.severity)}
                  </span>
                  <span className={styles.factorName}>{factor.factor}</span>
                </div>
                <p className={styles.factorDescription}>{factor.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {riskData.recommendations && riskData.recommendations.length > 0 && (
        <div className={styles.section}>
          <h3 className={styles.sectionTitle}>Recommended Actions</h3>
          <ul className={styles.recommendationsList}>
            {riskData.recommendations.map((recommendation, index) => (
              <li key={index} className={styles.recommendationItem}>
                {recommendation}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default RiskAssessmentCard;
