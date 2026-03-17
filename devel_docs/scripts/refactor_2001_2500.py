#!/usr/bin/env python3
"""
Refactor org-admin-dashboard.html lines 2001-2500
Removes all inline styles and replaces them with utility classes
"""

import re

def read_file(filepath):
    with open(filepath, 'r') as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, 'w') as f:
        f.write(content)

def main():
    filepath = '/home/bbrelin/course-creator/frontend/html/org-admin-dashboard.html'
    content = read_file(filepath)

    # Define replacements (old_pattern, new_replacement)
    replacements = [
        # Line 2004 - Button padding
        (r'style="padding: 0\.75rem 1\.5rem; white-space: nowrap;">',
         'class="btn-padding-custom whitespace-nowrap">'),

        # Line 2011-2027 - Summary Statistics
        (r'<div style="background: var\(--hover-color\); border-radius: 8px; padding: 1\.5rem; margin-bottom: 2rem;">',
         '<div class="summary-card">'),
        (r'<h4 style="margin: 0 0 1rem 0;">Project Summary:</h4>',
         '<h4 class="summary-card-title">Project Summary:</h4>'),
        (r'<div style="display: grid; grid-template-columns: repeat\(auto-fit, minmax\(200px, 1fr\)\); gap: 1rem;">',
         '<div class="summary-grid">'),
        (r'<div style="font-size: 0\.85rem; color: var\(--text-muted\);">Total Tracks</div>',
         '<div class="summary-stat-label">Total Tracks</div>'),
        (r'<div id="totalTracksCount" style="font-size: 1\.5rem; font-weight: 600; color: var\(--primary-color\);">0</div>',
         '<div id="totalTracksCount" class="summary-stat-value summary-stat-value--primary">0</div>'),
        (r'<div style="font-size: 0\.85rem; color: var\(--text-muted\);">Target Roles</div>',
         '<div class="summary-stat-label">Target Roles</div>'),
        (r'<div id="totalRolesCount" style="font-size: 1\.5rem; font-weight: 600; color: var\(--success-color\);">0</div>',
         '<div id="totalRolesCount" class="summary-stat-value summary-stat-value--success">0</div>'),
        (r'<div style="font-size: 0\.85rem; color: var\(--text-muted\);">Status</div>',
         '<div class="summary-stat-label">Status</div>'),
        (r'<div style="font-size: 1\.5rem; font-weight: 600; color: var\(--success-color\);">✓ Ready</div>',
         '<div class="summary-stat-value summary-stat-value--success">✓ Ready</div>'),

        # Line 2030-2052 - Multi-Locations Notice
        (r'<div id="multiLocationNotice" style="display: none; background: linear-gradient\(135deg, #667eea 0%, #764ba2 100%\); color: white; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 15px rgba\(102, 126, 234, 0\.3\);">',
         '<div id="multiLocationNotice" class="multi-locations-notice">'),
        (r'<div style="display: flex; align-items: start; gap: 1\.5rem;">',
         '<div class="multi-locations-notice-content">'),
        (r'<div style="font-size: 3rem;">🌍</div>',
         '<div class="multi-locations-icon">🌍</div>'),
        (r'<div style="flex: 1;">',
         '<div class="multi-locations-text">'),
        (r'<h4 style="margin: 0 0 0\.75rem 0; color: white; font-size: 1\.25rem;">Multi-Locations Project Setup</h4>',
         '<h4 class="multi-locations-title">Multi-Locations Project Setup</h4>'),
        (r'<p style="margin: 0 0 1rem 0; opacity: 0\.95; line-height: 1\.6;">',
         '<p class="multi-locations-description">'),
        (r'<div style="background: rgba\(255, 255, 255, 0\.2\); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">',
         '<div class="multi-locations-steps">'),
        (r'<strong style="display: block; margin-bottom: 0\.5rem;">📋 Next Steps:</strong>',
         '<strong class="multi-locations-steps-title">📋 Next Steps:</strong>'),
        (r'<ol style="margin: 0; padding-left: 1\.5rem; line-height: 1\.8;">',
         '<ol class="multi-locations-steps-list">'),
        (r'<p style="margin: 0; font-size: 0\.9rem; opacity: 0\.85;">',
         '<p class="multi-locations-tip">'),

        # Line 2057-2070 - Navigation Buttons
        (r'style="min-width: 120px; white-space: nowrap;"',
         'class="min-w-120 whitespace-nowrap"'),
        (r'style="min-width: 140px; white-space: nowrap;"',
         'class="min-w-140 whitespace-nowrap"'),
        (r'style="min-width: 200px; white-space: nowrap;"',
         'class="min-w-200 whitespace-nowrap"'),
        (r'style="min-width: 180px; white-space: nowrap;"',
         'class="min-w-180 whitespace-nowrap"'),

        # Line 2082-2084 - AI Chat button
        (r'style="background: none; border: none; cursor: pointer; font-size: 1\.2rem;"',
         'class="btn-icon-reset"'),

        # Line 2093-2106 - AI Chat messages
        (r'<div id="modalAIChatMessages" style="flex: 1; overflow-y: auto; border: 1px solid var\(--border-color\);\s+border-radius: 8px; padding: 1rem; margin-bottom: 1rem;\s+background: var\(--hover-color\); min-height: 300px;">',
         '<div id="modalAIChatMessages" class="modal-ai-chat-messages">'),
        (r'<div class="ai-message" style="margin-bottom: 1rem;">',
         '<div class="ai-message">'),
        (r'<strong style="color: var\(--primary-color\);">🤖 AI Assistant:</strong>',
         '<strong class="ai-message-author">🤖 AI Assistant:</strong>'),
        (r'<p style="margin: 0\.5rem 0 0 0; font-size: 0\.9rem;">',
         '<p class="ai-message-text">'),

        # Line 2109-2118 - Chat input
        (r'<div style="display: flex; gap: 0\.5rem;">',
         '<div class="chat-input-container">'),
        (r'style="flex: 1; padding: 0\.75rem; border: 1px solid var\(--border-color\);\s+border-radius: 4px; resize: none; min-height: 60px; max-height: 100px;"',
         'class="chat-textarea"'),
        (r'style="align-self: flex-end; white-space: nowrap;">',
         'class="chat-send-button whitespace-nowrap">'),

        # Line 2121-2124 - RAG context indicator
        (r'<div id="modalRagContextIndicator" style="margin-top: 0\.5rem; font-size: 0\.75rem;\s+color: var\(--text-muted\); display: none;">',
         '<div id="modalRagContextIndicator" class="rag-context-indicator">'),
        (r'<span style="color: var\(--success-color\);">✓</span>',
         '<span class="rag-context-check">✓</span>'),

        # Line 2132-2158 - Locations Modal
        (r'<div class="modal-content" style="max-width: 900px;">',
         '<div class="modal-content modal-content--lg">'),
        (r'<div class="draggable-handle" style="cursor: move; padding: 1rem; background: var\(--hover-color\); border-bottom: 1px solid var\(--border-color\); display: flex; justify-content: space-between; align-items: center;">',
         '<div class="locations-draggable-handle">'),
        (r'<h2 id="createLocationModalTitle" style="margin: 0;">🌍 Create New Locations</h2>',
         '<h2 id="createLocationModalTitle" class="locations-modal-title">🌍 Create New Locations</h2>'),
        (r'<div style="padding: 1rem; background: var\(--hover-color\); border-bottom: 1px solid var\(--border-color\);">',
         '<div class="locations-progress-container">'),
        (r'<div style="display: flex; justify-content: space-between; align-items: center; gap: 0\.5rem;">',
         '<div class="locations-progress-steps">'),

        # Line 2141-2155 - Wizard step indicators
        (r'<div class="wizard-step-indicator active" data-step="1" style="flex: 1; text-align: center; padding: 0\.5rem; border-radius: 4px; background: var\(--primary-color\); color: white; font-size: 0\.9rem;">',
         '<div class="wizard-step-indicator active" data-step="1">'),
        (r'<div class="wizard-step-indicator" data-step="2" style="flex: 1; text-align: center; padding: 0\.5rem; border-radius: 4px; background: var\(--hover-color\); color: var\(--text-muted\); font-size: 0\.9rem;">',
         '<div class="wizard-step-indicator" data-step="2">'),
        (r'<div class="wizard-step-indicator" data-step="3" style="flex: 1; text-align: center; padding: 0\.5rem; border-radius: 4px; background: var\(--hover-color\); color: var\(--text-muted\); font-size: 0\.9rem;">',
         '<div class="wizard-step-indicator" data-step="3">'),
        (r'<div class="wizard-step-indicator" data-step="4" style="flex: 1; text-align: center; padding: 0\.5rem; border-radius: 4px; background: var\(--hover-color\); color: var\(--text-muted\); font-size: 0\.9rem;">',
         '<div class="wizard-step-indicator" data-step="4">'),
        (r'<div class="wizard-step-indicator" data-step="5" style="flex: 1; text-align: center; padding: 0\.5rem; border-radius: 4px; background: var\(--hover-color\); color: var\(--text-muted\); font-size: 0\.9rem;">',
         '<div class="wizard-step-indicator" data-step="5">'),

        # Line 2159-2183 - Locations body and steps
        (r'<div style="padding: 2rem;">',
         '<div class="locations-modal-body">'),
        (r'<h3 style="margin-bottom: 1\.5rem;">📝 Basic Information</h3>',
         '<h3 class="locations-step-title">📝 Basic Information</h3>'),
        (r'<div style="display: flex; justify-content: flex-end; margin-top: 2rem; gap: 1rem;">',
         '<div class="locations-step-nav--end">'),

        # Line 2186-2243 - Locations step
        (r'<div id="locationStep2" class="wizard-step" style="display: none;">',
         '<div id="locationStep2" class="wizard-step">'),
        (r'<h3 style="margin-bottom: 1\.5rem;">📍 Locations Details</h3>',
         '<h3 class="locations-step-title">📍 Locations Details</h3>'),
        (r'<div style="display: flex; justify-content: space-between; margin-top: 2rem;">',
         '<div class="locations-step-nav">'),

        # Line 2247-2273 - Schedule step
        (r'<div id="locationStep3" class="wizard-step" style="display: none;">',
         '<div id="locationStep3" class="wizard-step">'),
        (r'<h3 style="margin-bottom: 1\.5rem;">📅 Schedule & Capacity</h3>',
         '<h3 class="locations-step-title">📅 Schedule & Capacity</h3>'),
        (r'style="background: var\(--hover-color\);"',
         'class="readonly-input"'),

        # Line 2276-2292 - Tracks step
        (r'<div id="locationStep4" class="wizard-step" style="display: none;">',
         '<div id="locationStep4" class="wizard-step">'),
        (r'<h3 style="margin-bottom: 1\.5rem;">📚 Select Tracks</h3>',
         '<h3 class="locations-step-title">📚 Select Tracks</h3>'),
        (r'<p style="color: var\(--text-muted\); margin-bottom: 1rem;">',
         '<p class="text-muted mb-md">'),
        (r'<div id="availableTracksList" style="margin-bottom: 1\.5rem;">',
         '<div id="availableTracksList" class="locations-tracks-list">'),
        (r'<div style="padding: 2rem; text-align: center; color: var\(--text-muted\); background: var\(--hover-color\); border-radius: 8px;">',
         '<div class="locations-tracks-placeholder">'),

        # Line 2295-2327 - Review step
        (r'<div id="locationStep5" class="wizard-step" style="display: none;">',
         '<div id="locationStep5" class="wizard-step">'),
        (r'<h3 style="margin-bottom: 1\.5rem;">✅ Review & Create</h3>',
         '<h3 class="locations-step-title">✅ Review & Create</h3>'),
        (r'<p style="color: var\(--text-muted\); margin-bottom: 1\.5rem;">',
         '<p class="subtitle-text">'),
        (r'<div id="reviewBasicInfo" style="margin-bottom: 1\.5rem; padding: 1rem; background: var\(--hover-color\); border-radius: 8px;">',
         '<div id="reviewBasicInfo" class="review-section">'),
        (r'<h4 style="margin-bottom: 0\.5rem;">Basic Information</h4>',
         '<h4 class="review-section-title">Basic Information</h4>'),
        (r'<p id="reviewName" style="margin: 0\.25rem 0;"></p>',
         '<p id="reviewName" class="review-text"></p>'),
        (r'<p id="reviewSlug" style="margin: 0\.25rem 0; color: var\(--text-muted\); font-size: 0\.9rem;"></p>',
         '<p id="reviewSlug" class="review-text--muted"></p>'),
        (r'<p id="reviewDescription" style="margin: 0\.5rem 0;"></p>',
         '<p id="reviewDescription" class="review-text--description"></p>'),
        (r'<div id="reviewLocation" style="margin-bottom: 1\.5rem; padding: 1rem; background: var\(--hover-color\); border-radius: 8px;">',
         '<div id="reviewLocation" class="review-section">'),
        (r'<h4 style="margin-bottom: 0\.5rem;">Locations</h4>',
         '<h4 class="review-section-title">Locations</h4>'),
        (r'<p id="reviewLocationDetails" style="margin: 0\.25rem 0;"></p>',
         '<p id="reviewLocationDetails" class="review-text"></p>'),
        (r'<p id="reviewTimezone" style="margin: 0\.25rem 0; color: var\(--text-muted\); font-size: 0\.9rem;"></p>',
         '<p id="reviewTimezone" class="review-text--muted"></p>'),
        (r'<div id="reviewSchedule" style="margin-bottom: 1\.5rem; padding: 1rem; background: var\(--hover-color\); border-radius: 8px;">',
         '<div id="reviewSchedule" class="review-section">'),
        (r'<h4 style="margin-bottom: 0\.5rem;">Schedule & Capacity</h4>',
         '<h4 class="review-section-title">Schedule & Capacity</h4>'),
        (r'<p id="reviewDates" style="margin: 0\.25rem 0;"></p>',
         '<p id="reviewDates" class="review-text"></p>'),
        (r'<p id="reviewCapacity" style="margin: 0\.25rem 0;"></p>',
         '<p id="reviewCapacity" class="review-text"></p>'),
        (r'<div id="reviewTracks" style="margin-bottom: 1\.5rem; padding: 1rem; background: var\(--hover-color\); border-radius: 8px;">',
         '<div id="reviewTracks" class="review-section">'),
        (r'<h4 style="margin-bottom: 0\.5rem;">Selected Tracks</h4>',
         '<h4 class="review-section-title">Selected Tracks</h4>'),

        # Project Detail View Modal - Lines 2333-2361
        (r'<div id="projectDetailView" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="projectDetailTitle" style="display: none;">',
         '<div id="projectDetailView" class="modal-backdrop project-detail-modal" role="dialog" aria-modal="true" aria-labelledby="projectDetailTitle">'),
        (r'<div class="modal-content" style="max-width: 1200px; max-height: 90vh; overflow-y: auto;">',
         '<div class="modal-content modal-content--2xl modal-content--full-height">'),
        (r'<div class="draggable-handle" style="cursor: move; padding: 1rem; background: var\(--hover-color\); border-bottom: 1px solid var\(--border-color\); display: flex; justify-content: space-between; align-items: center;">',
         '<div class="project-detail-handle">'),
        (r'<h2 id="projectDetailTitle" style="margin: 0;">📁 Project Details</h2>',
         '<h2 id="projectDetailTitle" class="project-detail-title">📁 Project Details</h2>'),
        (r'<div style="border-bottom: 1px solid var\(--border-color\); background: var\(--hover-color\);">',
         '<div class="project-detail-tabs">'),
        (r'<div style="display: flex; gap: 0\.5rem; padding: 0 1rem;">',
         '<div class="project-tabs-container">'),
        (r'<button class="tab-btn active" data-tab="overview" onclick="switchProjectDetailTab\(\'overview\'\)" style="padding: 1rem 1\.5rem; background: none; border: none; border-bottom: 3px solid transparent; cursor: pointer; font-weight: 500;">',
         '<button class="tab-btn active" data-tab="overview" onclick="switchProjectDetailTab(\'overview\')">'),
        (r'<button class="tab-btn" data-tab="locations" onclick="switchProjectDetailTab\(\'locations\'\)" style="padding: 1rem 1\.5rem; background: none; border: none; border-bottom: 3px solid transparent; cursor: pointer; font-weight: 500;">',
         '<button class="tab-btn" data-tab="locations" onclick="switchProjectDetailTab(\'locations\')">'),
        (r'<button class="tab-btn" data-tab="analytics" onclick="switchProjectDetailTab\(\'analytics\'\)" style="padding: 1rem 1\.5rem; background: none; border: none; border-bottom: 3px solid transparent; cursor: pointer; font-weight: 500;">',
         '<button class="tab-btn" data-tab="analytics" onclick="switchProjectDetailTab(\'analytics\')">'),
        (r'<div style="padding: 2rem;">',
         '<div class="project-detail-body">'),
        (r'<div id="projectDetailOverview" class="project-detail-tab" style="display: block;">',
         '<div id="projectDetailOverview" class="project-detail-tab active">'),
        (r'<p style="color: var\(--text-muted\);">Loading project details...</p>',
         '<p class="project-detail-loading">Loading project details...</p>'),
        (r'<div id="locationsTabContent" class="project-detail-tab" style="display: none;">',
         '<div id="locationsTabContent" class="project-detail-tab">'),

        # Locations Filters - Lines 2367-2417
        (r'<div style="background: var\(--hover-color\); padding: 1\.5rem; border-radius: 8px; margin-bottom: 2rem;">',
         '<div class="locations-filters-section">'),
        (r'<h3 style="margin-bottom: 1rem;">🔍 Filter Locations</h3>',
         '<h3 class="locations-filters-title">🔍 Filter Locations</h3>'),
        (r'<div style="display: grid; grid-template-columns: repeat\(auto-fit, minmax\(200px, 1fr\)\); gap: 1rem;">',
         '<div class="locations-filters-grid">'),
        (r'<div class="form-group" style="margin-bottom: 0;">',
         '<div class="form-group locations-filter-group">'),
        (r'style="width: 100%;"',
         'class="locations-filter-input"'),
        (r'<div style="margin-top: 1rem;">',
         '<div class="locations-filters-actions">'),

        # View Toggle - Lines 2420-2432
        (r'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1\.5rem;">',
         '<div class="locations-view-controls">'),
        (r'<div style="display: flex; gap: 0\.5rem;">',
         '<div class="locations-view-buttons">'),
        (r'<button id="locationListViewBtn" class="btn btn-secondary active" onclick="showLocationListView\(\)" style="display: flex; align-items: center; gap: 0\.5rem;">',
         '<button id="locationListViewBtn" class="btn btn-secondary active locations-view-btn" onclick="showLocationListView()">'),
        (r'<button id="locationTimelineViewBtn" class="btn btn-secondary" onclick="showLocationTimelineView\(\)" style="display: flex; align-items: center; gap: 0\.5rem;">',
         '<button id="locationTimelineViewBtn" class="btn btn-secondary locations-view-btn" onclick="showLocationTimelineView()">'),

        # Empty State - Lines 2442-2449
        (r'<div id="locationsEmptyState" class="empty-state" style="display: none; padding: 3rem; text-align: center; background: var\(--hover-color\); border-radius: 8px;">',
         '<div id="locationsEmptyState" class="locations-empty-state">'),
        (r'<div style="font-size: 3rem; margin-bottom: 1rem;">🌍</div>',
         '<div class="locations-empty-icon">🌍</div>'),
        (r'<h3 style="margin-bottom: 0\.5rem;">No Locations Created Yet</h3>',
         '<h3 class="locations-empty-title">No Locations Created Yet</h3>'),
        (r'<p style="color: var\(--text-muted\); margin-bottom: 1\.5rem;">',
         '<p class="locations-empty-description">'),

        # Timeline View - Lines 2453-2460
        (r'<div id="locationTimelineContainer" style="display: none;">',
         '<div id="locationTimelineContainer" class="locations-timeline-container">'),
        (r'<div style="background: var\(--card-background\); border: 1px solid var\(--border-color\); border-radius: 8px; padding: 2rem;">',
         '<div class="locations-timeline-content">'),
        (r'<p style="text-align: center; color: var\(--text-muted\);">Timeline view will display locations on a visual calendar.</p>',
         '<p class="locations-timeline-placeholder">Timeline view will display locations on a visual calendar.</p>'),

        # Comparison Controls - Lines 2463-2473
        (r'<div id="locationComparisonControls" style="display: none; position: fixed; bottom: 2rem; right: 2rem; background: var\(--primary-color\); color: white; padding: 1rem 1\.5rem; border-radius: 8px; box-shadow: 0 4px 12px rgba\(0,0,0,0\.2\); z-index: 999;">',
         '<div id="locationComparisonControls" class="locations-comparison-controls">'),
        (r'<div style="display: flex; align-items: center; gap: 1rem;">',
         '<div class="locations-comparison-inner">'),
        (r'<button id="compareLocationsBtn" class="btn" style="background: white; color: var\(--primary-color\);" onclick="openLocationComparison\(\)">',
         '<button id="compareLocationsBtn" class="btn locations-comparison-btn" onclick="openLocationComparison()">'),
        (r'<button class="btn" style="background: transparent; border: 1px solid white; color: white;" onclick="clearLocationSelection\(\)">',
         '<button class="btn locations-comparison-btn--clear" onclick="clearLocationSelection()">'),

        # Analytics Tab - Lines 2477-2482
        (r'<div id="projectDetailAnalytics" class="project-detail-tab" style="display: none;">',
         '<div id="projectDetailAnalytics" class="project-detail-tab">'),
        (r'<p style="color: var\(--text-muted\);">Project analytics will be displayed here.</p>',
         '<p class="project-detail-loading">Project analytics will be displayed here.</p>'),

        # Comparison Modal - Lines 2488-2500
        (r'<div id="locationComparisonModal" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="locationComparisonTitle" style="display: none;">',
         '<div id="locationComparisonModal" class="modal-backdrop locations-comparison-modal" role="dialog" aria-modal="true" aria-labelledby="locationComparisonTitle">'),
        (r'<div class="modal-content" style="max-width: 1000px;">',
         '<div class="modal-content modal-content--xl">'),
        (r'<div style="padding: 1rem; background: var\(--hover-color\); border-bottom: 1px solid var\(--border-color\); display: flex; justify-content: space-between; align-items: center;">',
         '<div class="locations-comparison-header">'),
        (r'<h2 id="locationComparisonTitle" style="margin: 0;">📊 Compare Locations</h2>',
         '<h2 id="locationComparisonTitle" class="locations-comparison-title">📊 Compare Locations</h2>'),
        (r'<div style="padding: 2rem; overflow-x: auto;">',
         '<div class="locations-comparison-body">'),
        (r'<table id="comparisonTable" class="data-table" style="width: 100%;">',
         '<table id="comparisonTable" class="data-table locations-comparison-table">'),
    ]

    # Apply all replacements
    for old, new in replacements:
        content = re.sub(old, new, content, flags=re.MULTILINE | re.DOTALL)

    # Write back
    write_file(filepath, content)

    print("Refactoring complete!")
    print(f"Applied {len(replacements)} replacements")

if __name__ == '__main__':
    main()
