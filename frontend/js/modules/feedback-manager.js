/**
 * Feedback Management Module
 * Handles both student course feedback and instructor student feedback
 */

class FeedbackManager {
    constructor() {
        this.courseManagementURL = 'http://localhost:8004';
        this.currentUser = null;
        this.currentUserRole = null;
    }

    /**
     * Initialize the feedback manager
     */
    async initialize() {
        // Get current user info from auth module if available
        if (window.authModule && window.authModule.getCurrentUser) {
            this.currentUser = window.authModule.getCurrentUser();
            this.currentUserRole = this.currentUser?.role;
        }
    }

    /**
     * Submit course feedback (students)
     */
    async submitCourseFeedback(courseId, feedbackData) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.courseManagementURL}/feedback/course`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    course_id: courseId,
                    ...feedbackData
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit feedback');
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error submitting course feedback:', error);
            throw error;
        }
    }

    /**
     * Submit student feedback (instructors)
     */
    async submitStudentFeedback(studentId, courseId, feedbackData) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.courseManagementURL}/feedback/student`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    student_id: studentId,
                    course_id: courseId,
                    ...feedbackData
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit student feedback');
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error('Error submitting student feedback:', error);
            throw error;
        }
    }

    /**
     * Get course feedback (instructors)
     */
    async getCourseFeedback(courseId) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.courseManagementURL}/feedback/course/${courseId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get course feedback');
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting course feedback:', error);
            throw error;
        }
    }

    /**
     * Get student feedback (both instructors and students)
     */
    async getStudentFeedback(studentId, courseId) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.courseManagementURL}/feedback/student/${studentId}/course/${courseId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get student feedback');
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting student feedback:', error);
            throw error;
        }
    }

    /**
     * Get all students feedback for a course (instructors)
     */
    async getAllStudentsFeedback(courseId) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.courseManagementURL}/feedback/course/${courseId}/students`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get students feedback');
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting students feedback:', error);
            throw error;
        }
    }

    /**
     * Toggle feedback sharing with student (instructors)
     */
    async toggleFeedbackSharing(feedbackId, share) {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) {
                throw new Error('Authentication required');
            }

            const response = await fetch(`${this.courseManagementURL}/feedback/student/${feedbackId}/share?share=${share}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update feedback sharing');
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating feedback sharing:', error);
            throw error;
        }
    }

    /**
     * Create course feedback form HTML
     */
    createCourseFeedbackForm(courseId, courseName, existingFeedback = null) {
        const isEdit = existingFeedback !== null;
        const feedback = existingFeedback || {};

        return `
            <div class="feedback-form-container">
                <div class="feedback-form-header">
                    <h3>${isEdit ? 'Update' : 'Submit'} Course Feedback</h3>
                    <p class="course-name">${courseName}</p>
                </div>

                <form id="courseFeedbackForm" class="feedback-form">
                    <input type="hidden" id="courseId" value="${courseId}">
                    
                    <!-- Overall Rating (Required) -->
                    <div class="form-group required">
                        <label for="overallRating">Overall Rating *</label>
                        <div class="rating-input">
                            ${this.createStarRating('overallRating', feedback.overall_rating || 0)}
                        </div>
                    </div>

                    <!-- Detailed Ratings -->
                    <div class="form-group">
                        <label for="contentQuality">Content Quality</label>
                        <div class="rating-input">
                            ${this.createStarRating('contentQuality', feedback.content_quality || 0)}
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="instructorEffectiveness">Instructor Effectiveness</label>
                        <div class="rating-input">
                            ${this.createStarRating('instructorEffectiveness', feedback.instructor_effectiveness || 0)}
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="difficultyAppropriateness">Difficulty Level</label>
                        <div class="rating-input">
                            ${this.createStarRating('difficultyAppropriateness', feedback.difficulty_appropriateness || 0)}
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="labQuality">Lab Quality</label>
                        <div class="rating-input">
                            ${this.createStarRating('labQuality', feedback.lab_quality || 0)}
                        </div>
                    </div>

                    <!-- Text Feedback -->
                    <div class="form-group">
                        <label for="positiveAspects">What did you like about this course?</label>
                        <textarea id="positiveAspects" rows="3" placeholder="Share what you found valuable or enjoyable...">${feedback.positive_aspects || ''}</textarea>
                    </div>

                    <div class="form-group">
                        <label for="areasForImprovement">What could be improved?</label>
                        <textarea id="areasForImprovement" rows="3" placeholder="Suggestions for course improvement...">${feedback.areas_for_improvement || ''}</textarea>
                    </div>

                    <div class="form-group">
                        <label for="additionalComments">Additional Comments</label>
                        <textarea id="additionalComments" rows="3" placeholder="Any other feedback you'd like to share...">${feedback.additional_comments || ''}</textarea>
                    </div>

                    <!-- Recommendation -->
                    <div class="form-group">
                        <label>Would you recommend this course to others?</label>
                        <div class="radio-group">
                            <label class="radio-label">
                                <input type="radio" name="wouldRecommend" value="true" ${feedback.would_recommend === true ? 'checked' : ''}>
                                Yes
                            </label>
                            <label class="radio-label">
                                <input type="radio" name="wouldRecommend" value="false" ${feedback.would_recommend === false ? 'checked' : ''}>
                                No
                            </label>
                            <label class="radio-label">
                                <input type="radio" name="wouldRecommend" value="" ${feedback.would_recommend === null || feedback.would_recommend === undefined ? 'checked' : ''}>
                                Not sure
                            </label>
                        </div>
                    </div>

                    <!-- Anonymous Option -->
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="isAnonymous" ${feedback.is_anonymous ? 'checked' : ''}>
                            Submit this feedback anonymously
                        </label>
                    </div>

                    <!-- Submit Button -->
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeFeedbackForm()">Cancel</button>
                        <button type="submit" class="btn btn-primary">${isEdit ? 'Update' : 'Submit'} Feedback</button>
                    </div>
                </form>
            </div>
        `;
    }

    /**
     * Create star rating input HTML
     */
    createStarRating(name, currentRating = 0) {
        let html = '<div class="star-rating">';
        for (let i = 1; i <= 5; i++) {
            const checked = i <= currentRating ? 'checked' : '';
            html += `
                <input type="radio" id="${name}_${i}" name="${name}" value="${i}" ${checked}>
                <label for="${name}_${i}" class="star">★</label>
            `;
        }
        html += '</div>';
        return html;
    }

    /**
     * Create student feedback form HTML (for instructors)
     */
    createStudentFeedbackForm(studentId, studentName, courseId, courseName, existingFeedback = null) {
        const isEdit = existingFeedback !== null;
        const feedback = existingFeedback || {};

        return `
            <div class="feedback-form-container">
                <div class="feedback-form-header">
                    <h3>${isEdit ? 'Update' : 'Provide'} Student Feedback</h3>
                    <p class="student-info">Student: ${studentName}</p>
                    <p class="course-info">Course: ${courseName}</p>
                </div>

                <form id="studentFeedbackForm" class="feedback-form">
                    <input type="hidden" id="studentId" value="${studentId}">
                    <input type="hidden" id="courseId" value="${courseId}">
                    
                    <!-- Performance Ratings -->
                    <div class="form-section">
                        <h4>Performance Assessment</h4>
                        
                        <div class="form-group">
                            <label for="overallPerformance">Overall Performance</label>
                            <div class="rating-input">
                                ${this.createStarRating('overallPerformance', feedback.overall_performance || 0)}
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="participation">Class Participation</label>
                            <div class="rating-input">
                                ${this.createStarRating('participation', feedback.participation || 0)}
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="labPerformance">Lab Performance</label>
                            <div class="rating-input">
                                ${this.createStarRating('labPerformance', feedback.lab_performance || 0)}
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="quizPerformance">Quiz Performance</label>
                            <div class="rating-input">
                                ${this.createStarRating('quizPerformance', feedback.quiz_performance || 0)}
                            </div>
                        </div>

                        <div class="form-group">
                            <label for="improvementTrend">Improvement Trend</label>
                            <div class="rating-input">
                                ${this.createStarRating('improvementTrend', feedback.improvement_trend || 0)}
                            </div>
                        </div>
                    </div>

                    <!-- Qualitative Assessment -->
                    <div class="form-section">
                        <h4>Qualitative Assessment</h4>
                        
                        <div class="form-group">
                            <label for="progressAssessment">Progress Assessment</label>
                            <select id="progressAssessment">
                                <option value="">Select...</option>
                                <option value="excellent" ${feedback.progress_assessment === 'excellent' ? 'selected' : ''}>Excellent</option>
                                <option value="good" ${feedback.progress_assessment === 'good' ? 'selected' : ''}>Good</option>
                                <option value="satisfactory" ${feedback.progress_assessment === 'satisfactory' ? 'selected' : ''}>Satisfactory</option>
                                <option value="needs_improvement" ${feedback.progress_assessment === 'needs_improvement' ? 'selected' : ''}>Needs Improvement</option>
                                <option value="poor" ${feedback.progress_assessment === 'poor' ? 'selected' : ''}>Poor</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="expectedOutcome">Expected Outcome</label>
                            <select id="expectedOutcome">
                                <option value="">Select...</option>
                                <option value="exceeds_expectations" ${feedback.expected_outcome === 'exceeds_expectations' ? 'selected' : ''}>Exceeds Expectations</option>
                                <option value="meets_expectations" ${feedback.expected_outcome === 'meets_expectations' ? 'selected' : ''}>Meets Expectations</option>
                                <option value="below_expectations" ${feedback.expected_outcome === 'below_expectations' ? 'selected' : ''}>Below Expectations</option>
                                <option value="at_risk" ${feedback.expected_outcome === 'at_risk' ? 'selected' : ''}>At Risk</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="feedbackType">Feedback Type</label>
                            <select id="feedbackType">
                                <option value="regular" ${feedback.feedback_type === 'regular' ? 'selected' : ''}>Regular</option>
                                <option value="midterm" ${feedback.feedback_type === 'midterm' ? 'selected' : ''}>Midterm</option>
                                <option value="final" ${feedback.feedback_type === 'final' ? 'selected' : ''}>Final</option>
                                <option value="intervention" ${feedback.feedback_type === 'intervention' ? 'selected' : ''}>Intervention</option>
                            </select>
                        </div>
                    </div>

                    <!-- Detailed Comments -->
                    <div class="form-section">
                        <h4>Detailed Feedback</h4>
                        
                        <div class="form-group">
                            <label for="strengths">Strengths</label>
                            <textarea id="strengths" rows="3" placeholder="What is the student doing well?">${feedback.strengths || ''}</textarea>
                        </div>

                        <div class="form-group">
                            <label for="areasForImprovement">Areas for Improvement</label>
                            <textarea id="areasForImprovement" rows="3" placeholder="What areas need development?">${feedback.areas_for_improvement || ''}</textarea>
                        </div>

                        <div class="form-group">
                            <label for="specificRecommendations">Specific Recommendations</label>
                            <textarea id="specificRecommendations" rows="3" placeholder="Specific actions the student can take...">${feedback.specific_recommendations || ''}</textarea>
                        </div>

                        <div class="form-group">
                            <label for="notableAchievements">Notable Achievements</label>
                            <textarea id="notableAchievements" rows="2" placeholder="Highlight any notable accomplishments...">${feedback.notable_achievements || ''}</textarea>
                        </div>

                        <div class="form-group">
                            <label for="concerns">Concerns</label>
                            <textarea id="concerns" rows="2" placeholder="Any concerns or issues to address...">${feedback.concerns || ''}</textarea>
                        </div>
                    </div>

                    <!-- Sharing Options -->
                    <div class="form-group">
                        <label class="checkbox-label">
                            <input type="checkbox" id="isSharedWithStudent" ${feedback.is_shared_with_student ? 'checked' : ''}>
                            Share this feedback with the student
                        </label>
                    </div>

                    <!-- Submit Button -->
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="closeStudentFeedbackForm()">Cancel</button>
                        <button type="submit" class="btn btn-primary">${isEdit ? 'Update' : 'Submit'} Feedback</button>
                    </div>
                </form>
            </div>
        `;
    }

    /**
     * Handle course feedback form submission
     */
    async handleCourseFeedbackSubmit(event) {
        event.preventDefault();
        
        const form = document.getElementById('courseFeedbackForm');
        const formData = new FormData(form);
        
        const feedbackData = {
            overall_rating: parseInt(formData.get('overallRating')),
            content_quality: formData.get('contentQuality') ? parseInt(formData.get('contentQuality')) : null,
            instructor_effectiveness: formData.get('instructorEffectiveness') ? parseInt(formData.get('instructorEffectiveness')) : null,
            difficulty_appropriateness: formData.get('difficultyAppropriateness') ? parseInt(formData.get('difficultyAppropriateness')) : null,
            lab_quality: formData.get('labQuality') ? parseInt(formData.get('labQuality')) : null,
            positive_aspects: formData.get('positiveAspects') || null,
            areas_for_improvement: formData.get('areasForImprovement') || null,
            additional_comments: formData.get('additionalComments') || null,
            would_recommend: formData.get('wouldRecommend') === 'true' ? true : formData.get('wouldRecommend') === 'false' ? false : null,
            is_anonymous: formData.has('isAnonymous')
        };

        if (!feedbackData.overall_rating) {
            this.showError('Please provide an overall rating');
            return;
        }

        try {
            this.showLoading('Submitting feedback...');
            const courseId = document.getElementById('courseId').value;
            await this.submitCourseFeedback(courseId, feedbackData);
            this.showSuccess('Feedback submitted successfully!');
            
            // Close form and refresh if needed
            if (typeof closeFeedbackForm === 'function') {
                closeFeedbackForm();
            }
        } catch (error) {
            this.showError('Failed to submit feedback: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Handle student feedback form submission
     */
    async handleStudentFeedbackSubmit(event) {
        event.preventDefault();
        
        const form = document.getElementById('studentFeedbackForm');
        const formData = new FormData(form);
        
        const feedbackData = {
            overall_performance: formData.get('overallPerformance') ? parseInt(formData.get('overallPerformance')) : null,
            participation: formData.get('participation') ? parseInt(formData.get('participation')) : null,
            lab_performance: formData.get('labPerformance') ? parseInt(formData.get('labPerformance')) : null,
            quiz_performance: formData.get('quizPerformance') ? parseInt(formData.get('quizPerformance')) : null,
            improvement_trend: formData.get('improvementTrend') ? parseInt(formData.get('improvementTrend')) : null,
            strengths: formData.get('strengths') || null,
            areas_for_improvement: formData.get('areasForImprovement') || null,
            specific_recommendations: formData.get('specificRecommendations') || null,
            notable_achievements: formData.get('notableAchievements') || null,
            concerns: formData.get('concerns') || null,
            progress_assessment: formData.get('progressAssessment') || null,
            expected_outcome: formData.get('expectedOutcome') || null,
            feedback_type: formData.get('feedbackType') || 'regular',
            is_shared_with_student: formData.has('isSharedWithStudent')
        };

        try {
            this.showLoading('Submitting feedback...');
            const studentId = document.getElementById('studentId').value;
            const courseId = document.getElementById('courseId').value;
            await this.submitStudentFeedback(studentId, courseId, feedbackData);
            this.showSuccess('Student feedback submitted successfully!');
            
            // Close form and refresh if needed
            if (typeof closeStudentFeedbackForm === 'function') {
                closeStudentFeedbackForm();
            }
        } catch (error) {
            this.showError('Failed to submit feedback: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    /**
     * Show loading state
     */
    showLoading(message = 'Loading...') {
        // Create or update loading indicator
        let loading = document.getElementById('feedbackLoading');
        if (!loading) {
            loading = document.createElement('div');
            loading.id = 'feedbackLoading';
            loading.className = 'feedback-loading';
            document.body.appendChild(loading);
        }
        loading.innerHTML = `<div class="spinner"></div><p>${message}</p>`;
        loading.style.display = 'flex';
    }

    /**
     * Hide loading state
     */
    hideLoading() {
        const loading = document.getElementById('feedbackLoading');
        if (loading) {
            loading.style.display = 'none';
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showNotification(message, 'error');
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Use existing notification system if available
        if (window.notificationModule && window.notificationModule.show) {
            window.notificationModule.show(message, type);
            return;
        }

        // Fallback notification system
        const notification = document.createElement('div');
        notification.className = `feedback-notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize and export
const feedbackManager = new FeedbackManager();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => feedbackManager.initialize());
} else {
    feedbackManager.initialize();
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = feedbackManager;
} else {
    window.feedbackManager = feedbackManager;
}