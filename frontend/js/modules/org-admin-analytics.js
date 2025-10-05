/**
 * Organization Admin Analytics Module - Metadata-Driven Insights
 *
 * BUSINESS CONTEXT:
 * Provides metadata-driven analytics and insights for organization administrators.
 * Enables data-driven decisions about content, instructors, and student learning paths.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Integrates with metadata service for intelligent analytics
 * - Provides popular tags, content gaps, and trending topics
 * - Offers search pattern analysis and content discovery metrics
 *
 * @module org-admin-analytics
 */

import { metadataClient } from '../metadata-client.js';
import { showNotification, showLoading, hideLoading } from './org-admin-utils.js';

/**
 * LOAD CONTENT ANALYTICS - METADATA-DRIVEN
 * PURPOSE: Display metadata-driven analytics for content management
 * WHY: Helps org admins understand content usage and identify gaps
 */
export async function loadContentAnalytics() {
    showLoading('analytics-container');

    try {
        const [popularTags, coursesAnalytics, studentEngagement] = await Promise.all([
            metadataClient.getPopularTags('course', 20),
            loadCoursesAnalytics(),
            loadStudentEngagementAnalytics()
        ]);

        displayContentAnalytics({
            popularTags,
            coursesAnalytics,
            studentEngagement
        });

    } catch (error) {
        console.error('Error loading content analytics:', error);
        showNotification('Error loading analytics: ' + error.message, 'error');
    } finally {
        hideLoading('analytics-container');
    }
}

/**
 * LOAD COURSES ANALYTICS - METADATA ENRICHED
 * PURPOSE: Get analytics about courses with metadata insights
 * WHY: Provides deeper understanding of course distribution and topics
 */
async function loadCoursesAnalytics() {
    try {
        // Get all course metadata
        const allCourses = await metadataClient.search('', {
            entity_types: ['course'],
            limit: 1000
        });

        // Analyze course distribution by difficulty
        const byDifficulty = {
            beginner: 0,
            intermediate: 0,
            advanced: 0,
            expert: 0
        };

        // Analyze topics coverage
        const topicsMap = new Map();

        allCourses.forEach(course => {
            const difficulty = course.metadata?.educational?.difficulty || 'beginner';
            if (byDifficulty.hasOwnProperty(difficulty)) {
                byDifficulty[difficulty]++;
            }

            const topics = course.metadata?.educational?.topics || [];
            topics.forEach(topic => {
                topicsMap.set(topic, (topicsMap.get(topic) || 0) + 1);
            });
        });

        return {
            total: allCourses.length,
            byDifficulty,
            topTopics: Array.from(topicsMap.entries())
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .map(([topic, count]) => ({ topic, count }))
        };

    } catch (error) {
        console.error('Error loading courses analytics:', error);
        return {
            total: 0,
            byDifficulty: {},
            topTopics: []
        };
    }
}

/**
 * LOAD STUDENT ENGAGEMENT ANALYTICS
 * PURPOSE: Track how students are engaging with content
 * WHY: Helps identify popular courses and learning patterns
 */
async function loadStudentEngagementAnalytics() {
    try {
        // This would integrate with course management service
        // For now, return placeholder data
        return {
            activeStudents: 0,
            completionRate: 0,
            averageProgress: 0
        };
    } catch (error) {
        console.error('Error loading student engagement:', error);
        return {
            activeStudents: 0,
            completionRate: 0,
            averageProgress: 0
        };
    }
}

/**
 * DISPLAY CONTENT ANALYTICS - METADATA INSIGHTS
 * PURPOSE: Render analytics dashboard with metadata insights
 * WHY: Visualizes content health and opportunities
 */
function displayContentAnalytics(analytics) {
    const container = document.getElementById('analytics-container');
    if (!container) return;

    container.innerHTML = `
        <div class="analytics-dashboard">
            <!-- Popular Tags Cloud -->
            <div class="analytics-card">
                <h3><i class="fas fa-tags"></i> Popular Tags</h3>
                <div class="tags-cloud">
                    ${analytics.popularTags.map(({ tag, count }) => {
                        const size = Math.min(100 + (count * 5), 200);
                        return `
                            <span class="tag-item" style="font-size: ${size}%;"
                                  onclick="OrgAdmin.Analytics.filterByTag('${tag}')">
                                ${tag}
                                <span class="tag-count">(${count})</span>
                            </span>
                        `;
                    }).join('')}
                </div>
            </div>

            <!-- Course Distribution -->
            <div class="analytics-card">
                <h3><i class="fas fa-chart-bar"></i> Course Distribution</h3>
                <div class="course-stats">
                    <div class="stat-item">
                        <div class="stat-label">Total Courses</div>
                        <div class="stat-value">${analytics.coursesAnalytics.total}</div>
                    </div>
                    <div class="difficulty-distribution">
                        ${Object.entries(analytics.coursesAnalytics.byDifficulty).map(([level, count]) => {
                            const percentage = analytics.coursesAnalytics.total > 0
                                ? Math.round((count / analytics.coursesAnalytics.total) * 100)
                                : 0;
                            return `
                                <div class="difficulty-bar">
                                    <div class="difficulty-label">${level}</div>
                                    <div class="progress-bar">
                                        <div class="progress-fill ${level}"
                                             style="width: ${percentage}%"></div>
                                    </div>
                                    <div class="difficulty-count">${count} (${percentage}%)</div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>

            <!-- Top Topics -->
            <div class="analytics-card">
                <h3><i class="fas fa-book"></i> Top Topics</h3>
                <div class="topics-list">
                    ${analytics.coursesAnalytics.topTopics.map(({ topic, count }) => `
                        <div class="topic-item">
                            <span class="topic-name">${topic}</span>
                            <span class="topic-count">${count} courses</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Content Gaps Analysis -->
            <div class="analytics-card">
                <h3><i class="fas fa-exclamation-triangle"></i> Content Gaps</h3>
                <div class="gaps-analysis">
                    <p>Identify areas where more content is needed:</p>
                    <button class="btn btn-primary" onclick="OrgAdmin.Analytics.analyzeContentGaps()">
                        <i class="fas fa-search"></i> Analyze Content Gaps
                    </button>
                </div>
            </div>

            <!-- Search Trends -->
            <div class="analytics-card">
                <h3><i class="fas fa-search"></i> Search Insights</h3>
                <div class="search-insights">
                    <p>Track what students are searching for to identify content needs.</p>
                    <button class="btn btn-secondary" onclick="OrgAdmin.Analytics.viewSearchTrends()">
                        <i class="fas fa-chart-line"></i> View Search Trends
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * FILTER CONTENT BY TAG - METADATA-DRIVEN
 * PURPOSE: Filter courses/content by selected tag
 * WHY: Enables quick navigation to tagged content
 */
export async function filterByTag(tag) {
    try {
        const results = await metadataClient.getByTags([tag], {
            entity_type: 'course',
            limit: 100
        });

        displayTagFilterResults(tag, results);
    } catch (error) {
        console.error('Error filtering by tag:', error);
        showNotification('Error filtering content: ' + error.message, 'error');
    }
}

/**
 * DISPLAY TAG FILTER RESULTS
 * PURPOSE: Show courses matching selected tag
 */
function displayTagFilterResults(tag, results) {
    const container = document.getElementById('tag-filter-results');
    if (!container) {
        showNotification(`Found ${results.length} courses with tag: ${tag}`, 'info');
        return;
    }

    container.innerHTML = `
        <div class="filter-results">
            <h3>Courses tagged with: ${tag}</h3>
            <div class="results-count">${results.length} courses found</div>
            <div class="results-list">
                ${results.map(course => `
                    <div class="course-result-card">
                        <h4>${course.title || `Course ${course.entity_id}`}</h4>
                        <p>${course.description || 'No description'}</p>
                        <div class="course-tags">
                            ${course.tags.map(t => `<span class="tag">${t}</span>`).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * ANALYZE CONTENT GAPS - METADATA INTELLIGENCE
 * PURPOSE: Identify topics with insufficient course coverage
 * WHY: Helps org admins prioritize content creation
 */
export async function analyzeContentGaps() {
    showLoading('gaps-analysis');

    try {
        // Get all popular tags
        const popularTags = await metadataClient.getPopularTags('course', 50);

        // Get all courses to analyze coverage
        const allCourses = await metadataClient.search('', {
            entity_types: ['course'],
            limit: 1000
        });

        // Identify tags with low course count (potential gaps)
        const gaps = popularTags
            .filter(({ count }) => count < 3)
            .map(({ tag, count }) => ({
                tag,
                courseCount: count,
                recommendation: `Only ${count} course(s) available. Consider creating more content.`
            }));

        // Analyze difficulty level gaps
        const difficultyGaps = analyzeDifficultyGaps(allCourses);

        displayContentGaps({ topicGaps: gaps, difficultyGaps });

    } catch (error) {
        console.error('Error analyzing content gaps:', error);
        showNotification('Error analyzing content gaps: ' + error.message, 'error');
    } finally {
        hideLoading('gaps-analysis');
    }
}

/**
 * ANALYZE DIFFICULTY LEVEL GAPS
 * PURPOSE: Identify difficulty levels with insufficient courses
 */
function analyzeDifficultyGaps(courses) {
    const distribution = {
        beginner: 0,
        intermediate: 0,
        advanced: 0,
        expert: 0
    };

    courses.forEach(course => {
        const difficulty = course.metadata?.educational?.difficulty || 'beginner';
        if (distribution.hasOwnProperty(difficulty)) {
            distribution[difficulty]++;
        }
    });

    const gaps = [];
    const total = courses.length;
    const idealPercentage = 25; // 25% for each difficulty level

    Object.entries(distribution).forEach(([level, count]) => {
        const percentage = total > 0 ? (count / total) * 100 : 0;
        if (percentage < idealPercentage - 10) {
            gaps.push({
                level,
                count,
                percentage: percentage.toFixed(1),
                recommendation: `Underrepresented (${percentage.toFixed(1)}%). Aim for ~${idealPercentage}%.`
            });
        }
    });

    return gaps;
}

/**
 * DISPLAY CONTENT GAPS ANALYSIS
 * PURPOSE: Show identified content gaps to admin
 */
function displayContentGaps({ topicGaps, difficultyGaps }) {
    const container = document.getElementById('gaps-analysis') || document.getElementById('analytics-container');
    if (!container) return;

    const gapsHTML = `
        <div class="content-gaps-analysis">
            <h3><i class="fas fa-exclamation-triangle"></i> Content Gaps Analysis</h3>

            ${topicGaps.length > 0 ? `
                <div class="gaps-section">
                    <h4>Topic Gaps</h4>
                    <div class="gaps-list">
                        ${topicGaps.map(gap => `
                            <div class="gap-item">
                                <div class="gap-tag">${gap.tag}</div>
                                <div class="gap-info">
                                    <span class="gap-count">${gap.courseCount} courses</span>
                                    <span class="gap-recommendation">${gap.recommendation}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : '<p>No significant topic gaps identified.</p>'}

            ${difficultyGaps.length > 0 ? `
                <div class="gaps-section">
                    <h4>Difficulty Level Gaps</h4>
                    <div class="gaps-list">
                        ${difficultyGaps.map(gap => `
                            <div class="gap-item">
                                <div class="gap-difficulty ${gap.level}">${gap.level}</div>
                                <div class="gap-info">
                                    <span class="gap-count">${gap.count} courses (${gap.percentage}%)</span>
                                    <span class="gap-recommendation">${gap.recommendation}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : '<p>No significant difficulty gaps identified.</p>'}
        </div>
    `;

    container.innerHTML = gapsHTML;
}

/**
 * VIEW SEARCH TRENDS - METADATA ANALYTICS
 * PURPOSE: Display search pattern analytics
 * WHY: Understand what students are looking for
 */
export function viewSearchTrends() {
    showNotification('Search trends analytics - feature coming soon', 'info');
    // This would integrate with search logging to show trending queries
}

/**
 * GENERATE CONTENT RECOMMENDATIONS - AI-POWERED
 * PURPOSE: Suggest new content based on gaps and student needs
 * WHY: Helps org admins prioritize content creation
 */
export async function generateContentRecommendations() {
    try {
        // Analyze existing content
        const allCourses = await metadataClient.search('', {
            entity_types: ['course'],
            limit: 1000
        });

        // Get popular tags
        const popularTags = await metadataClient.getPopularTags('course', 20);

        // Generate recommendations based on gaps
        const recommendations = [];

        // Recommendation 1: Fill topic gaps
        popularTags
            .filter(({ count }) => count < 3)
            .slice(0, 3)
            .forEach(({ tag }) => {
                recommendations.push({
                    type: 'topic_gap',
                    priority: 'high',
                    title: `Create ${tag} course`,
                    description: `Limited ${tag} content available. High student interest.`,
                    actionable: `Create intermediate ${tag} course`
                });
            });

        return recommendations;

    } catch (error) {
        console.error('Error generating recommendations:', error);
        return [];
    }
}

// Export all analytics functions
export default {
    loadContentAnalytics,
    filterByTag,
    analyzeContentGaps,
    viewSearchTrends,
    generateContentRecommendations
};
