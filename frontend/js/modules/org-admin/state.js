/**
 * Organization Admin Dashboard - State Management Module
 *
 * BUSINESS CONTEXT:
 * Centralizes all application state for the organization admin dashboard,
 * following Single Responsibility Principle by managing only state.
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Manages only application state
 * - Open/Closed: New state properties can be added without modifying consumers
 * - Dependency Inversion: Provides state abstraction through getters/setters
 *
 * ARCHITECTURE:
 * This module extracts state management from the monolithic org-admin-dashboard.js (3,273 lines)
 * to improve testability, maintainability, and prevent global state pollution.
 */

// Configuration
export const ORG_API_BASE = window.CONFIG?.API_URLS.ORGANIZATION;

// Application State
const state = {
    currentOrganization: null,
    currentTab: 'overview',
    currentProjectStep: 1,
    selectedTrackTemplates: [],
    ragSuggestionsCache: null,
    selectedProjectForAction: null,
    instructorAssignments: {
        tracks: {},
        modules: {}
    },
    selectedStudents: [],
    availableInstructors: [],
    currentAnalyticsProject: null,
    selectedStudentsForUnenrollment: [],
    selectedInstructorsForRemoval: []
};

// State Getters
export function getCurrentOrganization() {
    return state.currentOrganization;
}

export function getCurrentTab() {
    return state.currentTab;
}

export function getCurrentProjectStep() {
    return state.currentProjectStep;
}

export function getSelectedTrackTemplates() {
    return state.selectedTrackTemplates;
}

export function getRAGSuggestionsCache() {
    return state.ragSuggestionsCache;
}

export function getSelectedProjectForAction() {
    return state.selectedProjectForAction;
}

export function getInstructorAssignments() {
    return state.instructorAssignments;
}

export function getSelectedStudents() {
    return state.selectedStudents;
}

export function getAvailableInstructors() {
    return state.availableInstructors;
}

export function getCurrentAnalyticsProject() {
    return state.currentAnalyticsProject;
}

export function getSelectedStudentsForUnenrollment() {
    return state.selectedStudentsForUnenrollment;
}

export function getSelectedInstructorsForRemoval() {
    return state.selectedInstructorsForRemoval;
}

// State Setters
export function setCurrentOrganization(org) {
    state.currentOrganization = org;
}

export function setCurrentTab(tab) {
    state.currentTab = tab;
}

export function setCurrentProjectStep(step) {
    state.currentProjectStep = step;
}

export function setSelectedTrackTemplates(templates) {
    state.selectedTrackTemplates = templates;
}

export function setRAGSuggestionsCache(cache) {
    state.ragSuggestionsCache = cache;
}

export function setSelectedProjectForAction(projectId) {
    state.selectedProjectForAction = projectId;
}

export function setInstructorAssignments(assignments) {
    state.instructorAssignments = assignments;
}

export function setSelectedStudents(students) {
    state.selectedStudents = students;
}

export function setAvailableInstructors(instructors) {
    state.availableInstructors = instructors;
}

export function setCurrentAnalyticsProject(projectId) {
    state.currentAnalyticsProject = projectId;
}

export function setSelectedStudentsForUnenrollment(students) {
    state.selectedStudentsForUnenrollment = students;
}

export function setSelectedInstructorsForRemoval(instructors) {
    state.selectedInstructorsForRemoval = instructors;
}

// State Mutations (for complex state operations)
export function addSelectedTrackTemplate(templateId) {
    if (!state.selectedTrackTemplates.includes(templateId)) {
        state.selectedTrackTemplates.push(templateId);
    }
}

export function removeSelectedTrackTemplate(templateId) {
    state.selectedTrackTemplates = state.selectedTrackTemplates.filter(id => id !== templateId);
}

export function clearSelectedTrackTemplates() {
    state.selectedTrackTemplates = [];
}

export function toggleStudentSelection(studentId) {
    const index = state.selectedStudents.indexOf(studentId);
    if (index > -1) {
        state.selectedStudents.splice(index, 1);
    } else {
        state.selectedStudents.push(studentId);
    }
}

export function clearSelectedStudents() {
    state.selectedStudents = [];
}

export function toggleStudentForUnenrollment(studentId) {
    const index = state.selectedStudentsForUnenrollment.indexOf(studentId);
    if (index > -1) {
        state.selectedStudentsForUnenrollment.splice(index, 1);
    } else {
        state.selectedStudentsForUnenrollment.push(studentId);
    }
}

export function toggleInstructorForRemoval(instructorId) {
    const index = state.selectedInstructorsForRemoval.indexOf(instructorId);
    if (index > -1) {
        state.selectedInstructorsForRemoval.splice(index, 1);
    } else {
        state.selectedInstructorsForRemoval.push(instructorId);
    }
}

export function resetProjectCreationState() {
    state.currentProjectStep = 1;
    state.selectedTrackTemplates = [];
    state.ragSuggestionsCache = null;
}

export function resetInstructorAssignments() {
    state.instructorAssignments = {
        tracks: {},
        modules: {}
    };
}

// Export all state for backward compatibility (will be removed in future)
export default state;
