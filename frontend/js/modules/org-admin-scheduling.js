/**
 * Organization Admin Scheduling Module
 *
 * BUSINESS CONTEXT:
 * Manages course scheduling for organization admins. Allows scheduling courses with
 * instructors at specific times and locations, with conflict detection to prevent
 * double-booking instructors.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Weekly/monthly calendar views
 * - Schedule creation with time slots
 * - Conflict detection and visualization
 * - Filter by instructor/course/locations
 * - Recurring schedule support
 * - Integration with 7 scheduling API endpoints
 *
 * API ENDPOINTS:
 * - GET /api/v1/schedules - List all schedules
 * - POST /api/v1/schedules - Create schedule
 * - PUT /api/v1/schedules/{id} - Update schedule
 * - DELETE /api/v1/schedules/{id} - Delete schedule
 * - GET /api/v1/schedules/conflicts - Check conflicts
 * - GET /api/v1/instructors/{id}/schedules - Get instructor schedules
 * - GET /api/v1/courses/{id}/schedule - Get course schedule
 *
 * @module OrgAdminScheduling
 */

// Schedule state
let currentView = 'weekly';  // 'weekly' or 'monthly'
let currentDate = new Date();
let schedules = [];
let filteredSchedules = [];
let instructors = [];
let courses = [];
let locations = [];
let listenersAttached = false;

/**
 * Initialize scheduling module
 *
 * Sets up event listeners and loads initial data when schedules tab is accessed.
 */
export function initializeScheduling() {
    console.log('Initializing scheduling module');

    // Set up navigation event listener
    const schedulesTab = document.querySelector('[data-tab="schedules"]');
    if (schedulesTab) {
        schedulesTab.addEventListener('click', () => {
            // Set up event listeners when tab is clicked (ensures DOM is ready)
            // Using requestAnimationFrame for next paint cycle instead of setTimeout
            requestAnimationFrame(() => {
                if (!listenersAttached) {
                    setupEventListeners();
                    listenersAttached = true;
                }
                loadSchedulingData();
            });
        });
    }

    // Also set up global click handler as fallback
    document.addEventListener('click', (e) => {
        if (e.target && e.target.id === 'createScheduleBtn') {
            console.log('Create schedule button clicked via global handler');
            e.preventDefault();
            showCreateScheduleModal();
        }
    });
}

/**
 * Setup all event listeners for scheduling interface
 */
function setupEventListeners() {
    console.log('Setting up scheduling event listeners');

    // Create schedule button
    const createBtn = document.getElementById('createScheduleBtn');
    if (createBtn) {
        console.log('Create schedule button found, attaching listener');
        createBtn.addEventListener('click', showCreateScheduleModal);
    } else {
        console.warn('Create schedule button not found in DOM');
    }

    // View toggle buttons
    const weeklyBtn = document.getElementById('weeklyViewBtn');
    const monthlyBtn = document.getElementById('monthlyViewBtn');

    if (weeklyBtn) {
        weeklyBtn.addEventListener('click', () => switchView('weekly'));
    }
    if (monthlyBtn) {
        monthlyBtn.addEventListener('click', () => switchView('monthly'));
    }

    // Calendar navigation
    const prevBtn = document.getElementById('prevPeriodBtn');
    const nextBtn = document.getElementById('nextPeriodBtn');
    const todayBtn = document.getElementById('todayBtn');

    if (prevBtn) prevBtn.addEventListener('click', navigatePrevious);
    if (nextBtn) nextBtn.addEventListener('click', navigateNext);
    if (todayBtn) todayBtn.addEventListener('click', navigateToday);

    // Filters
    const instructorFilter = document.getElementById('instructorFilter');
    const courseFilter = document.getElementById('courseFilter');
    const locationFilter = document.getElementById('locationFilter');

    if (instructorFilter) instructorFilter.addEventListener('change', applyFilters);
    if (courseFilter) courseFilter.addEventListener('change', applyFilters);
    if (locationFilter) locationFilter.addEventListener('change', applyFilters);
}

/**
 * Load all data needed for scheduling interface
 *
 * Fetches schedules, instructors, courses, and locations from API.
 */
async function loadSchedulingData() {
    try {
        // Load schedules
        await loadSchedules();

        // Load filter options
        await loadFilterOptions();

        // Render calendar
        renderCalendar();

    } catch (error) {
        console.error('Error loading scheduling data:', error);
        if (window.showNotification) {
            window.showNotification('Failed to load scheduling data: ' + error.message, 'error');
        }
    }
}

/**
 * Load schedules from API
 */
async function loadSchedules() {
    try {
        const response = await fetch(`${window.API_BASE_URL}/api/v1/schedules`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Failed to fetch schedules');
        }

        schedules = await response.json();
        filteredSchedules = [...schedules];

    } catch (error) {
        console.error('Error loading schedules:', error);
        schedules = [];
        filteredSchedules = [];
    }
}

/**
 * Load filter options (instructors, courses, locations)
 */
async function loadFilterOptions() {
    try {
        // Load instructors
        const instructorResponse = await fetch(`${window.API_BASE_URL}/api/v1/instructors`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (instructorResponse.ok) {
            instructors = await instructorResponse.json();
            populateFilterDropdown('instructorFilter', instructors, 'All Instructors');
        }

        // Load courses
        const courseResponse = await fetch(`${window.API_BASE_URL}/api/v1/courses`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (courseResponse.ok) {
            courses = await courseResponse.json();
            populateFilterDropdown('courseFilter', courses, 'All Courses');
        }

        // Load locations
        const locationResponse = await fetch(`${window.API_BASE_URL}/api/v1/locations`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        if (locationResponse.ok) {
            locations = await locationResponse.json();
            populateFilterDropdown('locationFilter', locations, 'All Locations');
        }

    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}

/**
 * Populate a filter dropdown with options
 */
function populateFilterDropdown(dropdownId, items, defaultText) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;

    // Clear existing options except first
    dropdown.innerHTML = `<option value="">${defaultText}</option>`;

    // Add options
    items.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id || item.user_id;
        option.textContent = item.name || item.title || item.username;
        dropdown.appendChild(option);
    });
}

/**
 * Switch between weekly and monthly views
 */
function switchView(view) {
    currentView = view;

    // Update button states
    document.getElementById('weeklyViewBtn').classList.toggle('active', view === 'weekly');
    document.getElementById('monthlyViewBtn').classList.toggle('active', view === 'monthly');

    // Re-render calendar
    renderCalendar();
}

/**
 * Navigate to previous period
 */
function navigatePrevious() {
    if (currentView === 'weekly') {
        currentDate.setDate(currentDate.getDate() - 7);
    } else {
        currentDate.setMonth(currentDate.getMonth() - 1);
    }
    renderCalendar();
}

/**
 * Navigate to next period
 */
function navigateNext() {
    if (currentView === 'weekly') {
        currentDate.setDate(currentDate.getDate() + 7);
    } else {
        currentDate.setMonth(currentDate.getMonth() + 1);
    }
    renderCalendar();
}

/**
 * Navigate to today
 */
function navigateToday() {
    currentDate = new Date();
    renderCalendar();
}

/**
 * Apply filters to schedules
 */
function applyFilters() {
    const instructorId = document.getElementById('instructorFilter').value;
    const courseId = document.getElementById('courseFilter').value;
    const locationId = document.getElementById('locationFilter').value;

    filteredSchedules = schedules.filter(schedule => {
        if (instructorId && schedule.instructor_id !== instructorId) return false;
        if (courseId && schedule.course_id !== courseId) return false;
        if (locationId && schedule.location_id !== locationId) return false;
        return true;
    });

    renderCalendar();
}

/**
 * Render calendar based on current view
 */
function renderCalendar() {
    if (currentView === 'weekly') {
        renderWeeklyCalendar();
    } else {
        renderMonthlyCalendar();
    }

    // Update period label
    updatePeriodLabel();
}

/**
 * Update period label (e.g., "Week of Jan 1, 2025")
 */
function updatePeriodLabel() {
    const label = document.getElementById('currentPeriodLabel');
    if (!label) return;

    if (currentView === 'weekly') {
        const startOfWeek = getStartOfWeek(currentDate);
        const monthName = startOfWeek.toLocaleDateString('en-US', { month: 'short' });
        const day = startOfWeek.getDate();
        const year = startOfWeek.getFullYear();
        label.textContent = `Week of ${monthName} ${day}, ${year}`;
    } else {
        const monthName = currentDate.toLocaleDateString('en-US', { month: 'long' });
        const year = currentDate.getFullYear();
        label.textContent = `${monthName} ${year}`;
    }
}

/**
 * Get start of week (Sunday) for a given date
 */
function getStartOfWeek(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day;
    return new Date(d.setDate(diff));
}

/**
 * Render weekly calendar view
 */
function renderWeeklyCalendar() {
    const grid = document.getElementById('calendarGrid');
    if (!grid) return;

    const startOfWeek = getStartOfWeek(currentDate);
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const hours = Array.from({ length: 24 }, (_, i) => i);

    let html = '';

    // Header row - time column + day columns
    html += '<div class="calendar-header-cell">Time</div>';
    for (let i = 0; i < 7; i++) {
        const date = new Date(startOfWeek);
        date.setDate(startOfWeek.getDate() + i);
        const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        html += `<div class="calendar-header-cell">${days[i]}<br>${dateStr}</div>`;
    }

    // Time slots
    for (let hour = 0; hour < 24; hour++) {
        // Time label
        const timeStr = hour === 0 ? '12 AM' : hour < 12 ? `${hour} AM` : hour === 12 ? '12 PM' : `${hour - 12} PM`;
        html += `<div class="calendar-time-cell">${timeStr}</div>`;

        // Day cells
        for (let dayOffset = 0; dayOffset < 7; dayOffset++) {
            const cellDate = new Date(startOfWeek);
            cellDate.setDate(startOfWeek.getDate() + dayOffset);
            cellDate.setHours(hour, 0, 0, 0);

            // Find schedules for this time slot
            const cellSchedules = findSchedulesForTimeSlot(cellDate);

            html += `<div class="calendar-day-cell" data-date="${cellDate.toISOString()}" data-hour="${hour}" onclick="window.OrgAdmin.Scheduling.handleCellClick('${cellDate.toISOString()}')">`;

            // Render schedule items
            cellSchedules.forEach(schedule => {
                html += renderScheduleItem(schedule);
            });

            html += '</div>';
        }
    }

    grid.innerHTML = html;
}

/**
 * Find schedules that occur in a given time slot
 */
function findSchedulesForTimeSlot(date) {
    return filteredSchedules.filter(schedule => {
        const scheduleStart = new Date(schedule.start_datetime);
        const scheduleEnd = new Date(schedule.end_datetime);
        const slotStart = date;
        const slotEnd = new Date(date.getTime() + 60 * 60 * 1000); // +1 hour

        // Check if schedule overlaps with this time slot
        return scheduleStart < slotEnd && scheduleEnd > slotStart;
    });
}

/**
 * Render a schedule item
 */
function renderScheduleItem(schedule) {
    const courseName = schedule.course_title || schedule.course_name || 'Course';
    const instructorName = schedule.instructor_name || 'Instructor';
    const startTime = new Date(schedule.start_datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const endTime = new Date(schedule.end_datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

    const conflictClass = schedule.has_conflict ? 'schedule-conflict' : '';

    return `
        <div class="schedule-item ${conflictClass}" onclick="window.OrgAdmin.Scheduling.viewScheduleDetails('${schedule.id}')" data-schedule-id="${schedule.id}">
            <div class="schedule-item-title">${courseName}</div>
            <div class="schedule-item-time">${startTime} - ${endTime}</div>
            <div style="font-size: 0.65rem; opacity: 0.8;">${instructorName}</div>
            ${schedule.has_conflict ? '<div class="conflict-indicator"></div>' : ''}
        </div>
    `;
}

/**
 * Render monthly calendar view (simplified list view)
 */
function renderMonthlyCalendar() {
    const grid = document.getElementById('calendarGrid');
    if (!grid) return;

    // For monthly view, show a list of schedules grouped by day
    const month = currentDate.getMonth();
    const year = currentDate.getFullYear();

    const monthSchedules = filteredSchedules.filter(schedule => {
        const scheduleDate = new Date(schedule.start_datetime);
        return scheduleDate.getMonth() === month && scheduleDate.getFullYear() === year;
    });

    // Group by date
    const schedulesByDate = {};
    monthSchedules.forEach(schedule => {
        const dateKey = new Date(schedule.start_datetime).toDateString();
        if (!schedulesByDate[dateKey]) {
            schedulesByDate[dateKey] = [];
        }
        schedulesByDate[dateKey].push(schedule);
    });

    let html = '<div style="width: 100%;">';

    if (Object.keys(schedulesByDate).length === 0) {
        html += '<p class="text-center text-muted">No schedules this month</p>';
    } else {
        Object.keys(schedulesByDate).sort().forEach(dateKey => {
            const date = new Date(dateKey);
            const dateStr = date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

            html += `<div style="margin-bottom: 2rem;">`;
            html += `<h4 style="margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid var(--primary-color);">${dateStr}</h4>`;
            html += `<div style="display: flex; flex-direction: column; gap: 0.5rem;">`;

            schedulesByDate[dateKey].forEach(schedule => {
                const courseName = schedule.course_title || schedule.course_name || 'Course';
                const instructorName = schedule.instructor_name || 'Instructor';
                const startTime = new Date(schedule.start_datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                const endTime = new Date(schedule.end_datetime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
                const conflictBadge = schedule.has_conflict ? '<span class="badge badge-danger">Conflict</span>' : '';

                html += `
                    <div style="background: var(--card-background); padding: 1rem; border-radius: 8px; border: 1px solid var(--border-color); cursor: pointer;"
                         onclick="window.OrgAdmin.Scheduling.viewScheduleDetails('${schedule.id}')">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>${courseName}</strong> ${conflictBadge}
                                <div style="font-size: 0.875rem; color: var(--text-muted);">${instructorName}</div>
                            </div>
                            <div style="font-size: 0.875rem;">
                                ${startTime} - ${endTime}
                            </div>
                        </div>
                    </div>
                `;
            });

            html += `</div></div>`;
        });
    }

    html += '</div>';
    grid.innerHTML = html;
}

/**
 * Handle cell click to create schedule at specific time
 */
export function handleCellClick(dateTimeStr) {
    const dateTime = new Date(dateTimeStr);
    showCreateScheduleModal(dateTime);
}

/**
 * Show create schedule modal
 */
export async function showCreateScheduleModal(prefilledDateTime = null) {
    console.log('showCreateScheduleModal called');

    // Remove existing modal if present
    const existingModal = document.getElementById('scheduleModal');
    if (existingModal) {
        console.log('Removing existing modal');
        existingModal.remove();
    }

    // Default to next hour if no time specified
    const defaultDateTime = prefilledDateTime || new Date(Date.now() + 60 * 60 * 1000);
    const startDateStr = defaultDateTime.toISOString().split('T')[0];
    const startTimeStr = defaultDateTime.toTimeString().slice(0, 5);
    const endDateTime = new Date(defaultDateTime.getTime() + 90 * 60 * 1000); // +1.5 hours
    const endTimeStr = endDateTime.toTimeString().slice(0, 5);

    const modalHtml = `
        <div id="scheduleModal" class="modal" style="display: none;">
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background-color: rgba(0, 0, 0, 0.75); z-index: 10000;"
                 onclick="window.OrgAdmin.Scheduling.closeScheduleModal()"></div>

            <div class="modal-content" style="position: relative; z-index: 10001; max-width: 600px;
                        margin: 2rem auto; background: var(--surface-color); border-radius: 12px;">
                <div class="modal-header">
                    <h3>Create Schedule</h3>
                    <button class="modal-close" onclick="window.OrgAdmin.Scheduling.closeScheduleModal()">&times;</button>
                </div>

                <div class="modal-body">
                    <form id="scheduleForm">
                        <!-- Course Selection -->
                        <div class="form-group">
                            <label for="scheduleCourse">Course <span class="required">*</span></label>
                            <select id="scheduleCourse" class="form-control" required>
                                <option value="">-- Select a course --</option>
                            </select>
                        </div>

                        <!-- Instructor Selection -->
                        <div class="form-group">
                            <label for="scheduleInstructor">Instructor <span class="required">*</span></label>
                            <select id="scheduleInstructor" class="form-control" required>
                                <option value="">-- Select an instructor --</option>
                            </select>
                        </div>

                        <!-- Locations Selection -->
                        <div class="form-group">
                            <label for="scheduleLocation">Locations (Optional)</label>
                            <select id="scheduleLocation" class="form-control">
                                <option value="">-- No specific locations --</option>
                            </select>
                        </div>

                        <!-- Date and Time -->
                        <div class="form-group">
                            <label for="scheduleStartDate">Start Date <span class="required">*</span></label>
                            <input type="date" id="scheduleStartDate" class="form-control" value="${startDateStr}" required>
                        </div>

                        <div class="form-row" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                            <div class="form-group">
                                <label for="scheduleStartTime">Start Time <span class="required">*</span></label>
                                <input type="time" id="scheduleStartTime" class="form-control" value="${startTimeStr}" required>
                            </div>
                            <div class="form-group">
                                <label for="scheduleEndTime">End Time <span class="required">*</span></label>
                                <input type="time" id="scheduleEndTime" class="form-control" value="${endTimeStr}" required>
                            </div>
                        </div>

                        <!-- Recurrence -->
                        <div class="form-group">
                            <label for="scheduleRecurrence">Recurrence</label>
                            <select id="scheduleRecurrence" class="form-control">
                                <option value="none">Does not repeat</option>
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                            </select>
                        </div>

                        <!-- Days of Week (for weekly recurrence) -->
                        <div class="form-group" id="daysOfWeekGroup" style="display: none;">
                            <label>Days of Week</label>
                            <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                                <label class="checkbox-label"><input type="checkbox" name="daysOfWeek" value="0"> Sun</label>
                                <label class="checkbox-label"><input type="checkbox" name="daysOfWeek" value="1"> Mon</label>
                                <label class="checkbox-label"><input type="checkbox" name="daysOfWeek" value="2"> Tue</label>
                                <label class="checkbox-label"><input type="checkbox" name="daysOfWeek" value="3"> Wed</label>
                                <label class="checkbox-label"><input type="checkbox" name="daysOfWeek" value="4"> Thu</label>
                                <label class="checkbox-label"><input type="checkbox" name="daysOfWeek" value="5"> Fri</label>
                                <label class="checkbox-label"><input type="checkbox" name="daysOfWeek" value="6"> Sat</label>
                            </div>
                        </div>

                        <!-- Conflict Warning -->
                        <div id="conflictWarning" class="alert alert-warning" style="display: none;">
                            <strong>⚠️ Scheduling Conflict Detected</strong>
                            <div class="conflict-details" id="conflictDetails"></div>
                        </div>
                    </form>
                </div>

                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="window.OrgAdmin.Scheduling.closeScheduleModal()">
                        Cancel
                    </button>
                    <button id="submitScheduleBtn" class="btn btn-primary"
                            onclick="window.OrgAdmin.Scheduling.submitSchedule()">
                        Create Schedule
                    </button>
                </div>
            </div>
        </div>
    `;

    console.log('Inserting modal HTML into DOM');
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = document.getElementById('scheduleModal');
    if (modal) {
        console.log('Modal found, setting display to block');
        modal.style.display = 'block';
    } else {
        console.error('Modal not found after insertion!');
        return;
    }

    // Populate dropdowns
    console.log('Populating form dropdowns');
    await populateScheduleFormDropdowns();
    console.log('Modal setup complete');

    // Set up recurrence change listener
    document.getElementById('scheduleRecurrence').addEventListener('change', (e) => {
        const daysGroup = document.getElementById('daysOfWeekGroup');
        daysGroup.style.display = e.target.value === 'weekly' ? 'block' : 'none';
    });

    // Set up conflict detection on form changes
    ['scheduleCourse', 'scheduleInstructor', 'scheduleStartDate', 'scheduleStartTime', 'scheduleEndTime'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('change', checkForConflicts);
        }
    });
}

/**
 * Populate schedule form dropdowns
 */
async function populateScheduleFormDropdowns() {
    // Populate course dropdown
    const courseSelect = document.getElementById('scheduleCourse');
    courses.forEach(course => {
        const option = document.createElement('option');
        option.value = course.id;
        option.textContent = course.title || course.name;
        courseSelect.appendChild(option);
    });

    // Populate instructor dropdown
    const instructorSelect = document.getElementById('scheduleInstructor');
    instructors.forEach(instructor => {
        const option = document.createElement('option');
        option.value = instructor.id || instructor.user_id;
        option.textContent = instructor.name || instructor.username;
        instructorSelect.appendChild(option);
    });

    // Populate locations dropdown
    const locationSelect = document.getElementById('scheduleLocation');
    locations.forEach(locations => {
        const option = document.createElement('option');
        option.value = locations.id;
        option.textContent = locations.name;
        locationSelect.appendChild(option);
    });
}

/**
 * Check for scheduling conflicts
 */
async function checkForConflicts() {
    const instructorId = document.getElementById('scheduleInstructor').value;
    const startDate = document.getElementById('scheduleStartDate').value;
    const startTime = document.getElementById('scheduleStartTime').value;
    const endTime = document.getElementById('scheduleEndTime').value;

    if (!instructorId || !startDate || !startTime || !endTime) {
        return; // Not enough info to check
    }

    try {
        const startDateTime = `${startDate}T${startTime}:00`;
        const endDateTime = `${startDate}T${endTime}:00`;

        const response = await fetch(
            `${window.API_BASE_URL}/api/v1/schedules/conflicts?instructor_id=${instructorId}&start=${startDateTime}&end=${endDateTime}`,
            {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            }
        );

        if (response.ok) {
            const conflicts = await response.json();

            const warningDiv = document.getElementById('conflictWarning');
            const detailsDiv = document.getElementById('conflictDetails');

            if (conflicts && conflicts.length > 0) {
                // Show conflict warning
                warningDiv.style.display = 'block';
                detailsDiv.innerHTML = conflicts.map(conflict =>
                    `<p>Instructor is already scheduled for "${conflict.course_name}" at this time.</p>`
                ).join('');
            } else {
                warningDiv.style.display = 'none';
            }
        }

    } catch (error) {
        console.error('Error checking conflicts:', error);
    }
}

/**
 * Close schedule modal
 */
export function closeScheduleModal() {
    const modal = document.getElementById('scheduleModal');
    if (modal) {
        modal.style.display = 'none';
        setTimeout(() => modal.remove(), 300);
    }
}

/**
 * Submit schedule creation
 */
export async function submitSchedule() {
    const courseId = document.getElementById('scheduleCourse').value;
    const instructorId = document.getElementById('scheduleInstructor').value;
    const locationId = document.getElementById('scheduleLocation').value;
    const startDate = document.getElementById('scheduleStartDate').value;
    const startTime = document.getElementById('scheduleStartTime').value;
    const endTime = document.getElementById('scheduleEndTime').value;
    const recurrence = document.getElementById('scheduleRecurrence').value;

    // Validation
    if (!courseId || !instructorId || !startDate || !startTime || !endTime) {
        if (window.showNotification) {
            window.showNotification('Please fill in all required fields', 'error');
        }
        return;
    }

    const submitBtn = document.getElementById('submitScheduleBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating...';

    try {
        const scheduleData = {
            course_id: courseId,
            instructor_id: instructorId,
            location_id: locationId || null,
            start_datetime: `${startDate}T${startTime}:00`,
            end_datetime: `${startDate}T${endTime}:00`,
            recurrence: recurrence !== 'none' ? recurrence : null
        };

        // Add days of week for weekly recurrence
        if (recurrence === 'weekly') {
            const daysChecked = Array.from(document.querySelectorAll('input[name="daysOfWeek"]:checked'))
                .map(cb => parseInt(cb.value));
            scheduleData.days_of_week = daysChecked;
        }

        const response = await fetch(`${window.API_BASE_URL}/api/v1/schedules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(scheduleData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create schedule');
        }

        // Show success
        if (window.showNotification) {
            window.showNotification('Schedule created successfully', 'success');
        }

        // Close modal
        closeScheduleModal();

        // Reload schedules
        await loadSchedules();
        renderCalendar();

    } catch (error) {
        console.error('Error creating schedule:', error);
        if (window.showNotification) {
            window.showNotification('Failed to create schedule: ' + error.message, 'error');
        }

        submitBtn.disabled = false;
        submitBtn.textContent = 'Create Schedule';
    }
}

/**
 * View schedule details
 */
export function viewScheduleDetails(scheduleId) {
    const schedule = schedules.find(s => s.id === scheduleId);
    if (!schedule) return;

    // For now, show alert with details
    // TODO: Create a proper schedule details modal
    const details = `
Course: ${schedule.course_title || schedule.course_name}
Instructor: ${schedule.instructor_name}
Locations: ${schedule.location_name || 'N/A'}
Start: ${new Date(schedule.start_datetime).toLocaleString()}
End: ${new Date(schedule.end_datetime).toLocaleString()}
    `.trim();

    alert(details);
}

// Export functions to window.OrgAdmin.Scheduling namespace
if (!window.OrgAdmin) {
    window.OrgAdmin = {};
}

window.OrgAdmin.Scheduling = {
    initializeScheduling,
    showCreateScheduleModal,
    closeScheduleModal,
    submitSchedule,
    handleCellClick,
    viewScheduleDetails
};

// Auto-initialize when module loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeScheduling);
} else {
    initializeScheduling();
}
