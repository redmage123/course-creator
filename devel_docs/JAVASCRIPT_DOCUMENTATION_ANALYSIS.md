# JavaScript Function Documentation Analysis Report

## Summary
- **Total Files Analyzed**: 88
- **Total Undocumented Functions**: 1105

## Files Requiring Documentation

### frontend/js/site-admin-dashboard.js
**Undocumented Functions**: 78

- **Line 66**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 121**: `setupNetworkRecovery()` (method)
  ```javascript
  setupNetworkRecovery() {
  ```
- **Line 152**: `verifyNetworkConnectivity()` (method)
  ```javascript
  async verifyNetworkConnectivity() {
  ```
- **Line 179**: `handleNetworkRecovery()` (method)
  ```javascript
  handleNetworkRecovery() {
  ```
- **Line 198**: `showNetworkOfflineMessage()` (method)
  ```javascript
  showNetworkOfflineMessage() {
  ```
- **Line 232**: `validateSession()` (method)
  ```javascript
  validateSession() {
  ```
- **Line 306**: `getCurrentUser()` (method)
  ```javascript
  getCurrentUser() {
  ```
- **Line 336**: `formatPhoneNumber()` (method)
  ```javascript
  formatPhoneNumber(phone) {
  ```
- **Line 398**: `clearExpiredSession()` (method)
  ```javascript
  clearExpiredSession() {
  ```
- **Line 437**: `init()` (method)
  ```javascript
  async init() {
  ```
- **Line 481**: `loadCurrentUser()` (method)
  ```javascript
  async loadCurrentUser() {
  ```
- **Line 562**: `setupEventListeners()` (method)
  ```javascript
  setupEventListeners() {
  ```
- **Line 597**: `loadDashboardData()` (method)
  ```javascript
  async loadDashboardData() {
  ```
- **Line 615**: `loadPlatformStats()` (method)
  ```javascript
  async loadPlatformStats() {
  ```
- **Line 637**: `loadOrganizations()` (method)
  ```javascript
  async loadOrganizations() {
  ```
- **Line 660**: `loadRecentActivity()` (method)
  ```javascript
  async loadRecentActivity() {
  ```
- **Line 699**: `loadIntegrationStatus()` (method)
  ```javascript
  async loadIntegrationStatus() {
  ```
- **Line 721**: `showTab()` (method)
  ```javascript
  showTab(tabName) {
  ```
- **Line 745**: `updatePlatformStats()` (method)
  ```javascript
  updatePlatformStats() {
  ```
- **Line 760**: `showDefaultStats()` (method)
  ```javascript
  showDefaultStats() {
  ```
- **Line 769**: `renderOrganizations()` (method)
  ```javascript
  renderOrganizations() {
  ```
- **Line 936**: `renderRecentActivity()` (method)
  ```javascript
  renderRecentActivity(activities) {
  ```
- **Line 968**: `updateIntegrationStatus()` (method)
  ```javascript
  updateIntegrationStatus(health) {
  ```
- **Line 982**: `setDefaultIntegrationStatus()` (method)
  ```javascript
  setDefaultIntegrationStatus() {
  ```
- **Line 990**: `showDeleteOrganizationModal()` (method)
  ```javascript
  showDeleteOrganizationModal(orgId, orgName, memberCount, projectCount, meetingRoomCount) {
  ```
- **Line 1004**: `showModal()` (method)
  ```javascript
  showModal(modalId) {
  ```
- **Line 1009**: `closeModal()` (method)
  ```javascript
  closeModal(modalId) {
  ```
- **Line 1022**: `confirmDeleteOrganization()` (method)
  ```javascript
  async confirmDeleteOrganization() {
  ```
- **Line 1067**: `deactivateOrganization()` (method)
  ```javascript
  async deactivateOrganization(orgId) {
  ```
- **Line 1099**: `reactivateOrganization()` (method)
  ```javascript
  async reactivateOrganization(orgId) {
  ```
- **Line 1127**: `testTeamsIntegration()` (method)
  ```javascript
  async testTeamsIntegration() {
  ```
- **Line 1145**: `testZoomIntegration()` (method)
  ```javascript
  async testZoomIntegration() {
  ```
- **Line 1164**: `filterOrganizations()` (method)
  ```javascript
  filterOrganizations() {
  ```
- **Line 1177**: `searchOrganizations()` (method)
  ```javascript
  searchOrganizations() {
  ```
- **Line 1194**: `showOrganizationMembers()` (method)
  ```javascript
  async showOrganizationMembers(orgId, role) {
  ```
- **Line 1259**: `showMembersModal()` (method)
  ```javascript
  showMembersModal(orgId, members, roleFilter) {
  ```
- **Line 1322**: `renderMembers()` (method)
  ```javascript
  renderMembers(members, roleFilter) {
  ```
- **Line 1369**: `renderStudentEnrollments()` (method)
  ```javascript
  renderStudentEnrollments(enrollments) {
  ```
- **Line 1394**: `getRoleIcon()` (method)
  ```javascript
  getRoleIcon(role) {
  ```
- **Line 1409**: `formatRoleName()` (method)
  ```javascript
  formatRoleName(role) {
  ```
- **Line 1424**: `filterMembersByRole()` (method)
  ```javascript
  async filterMembersByRole(orgId) {
  ```
- **Line 1433**: `sortMembers()` (method)
  ```javascript
  sortMembers() {
  ```
- **Line 1461**: `closeMembersModal()` (method)
  ```javascript
  closeMembersModal() {
  ```
- **Line 1472**: `showOrganizationProjects()` (method)
  ```javascript
  async showOrganizationProjects(orgId) {
  ```
- **Line 1527**: `showProjectsModal()` (method)
  ```javascript
  showProjectsModal(orgId, projects) {
  ```
- **Line 1570**: `renderProjects()` (method)
  ```javascript
  renderProjects(projects) {
  ```
- **Line 1599**: `renderTracks()` (method)
  ```javascript
  renderTracks(tracks) {
  ```
- **Line 1621**: `sortProjects()` (method)
  ```javascript
  sortProjects() {
  ```
- **Line 1648**: `closeProjectsModal()` (method)
  ```javascript
  closeProjectsModal() {
  ```
- **Line 1658**: `getActivityIcon()` (method)
  ```javascript
  getActivityIcon(type) {
  ```
- **Line 1668**: `formatTimeAgo()` (method)
  ```javascript
  formatTimeAgo(timestamp) {
  ```
- **Line 1683**: `showLoadingOverlay()` (method)
  ```javascript
  showLoadingOverlay(show) {
  ```
- **Line 1687**: `showNotification()` (method)
  ```javascript
  showNotification(message, type = 'info') {
  ```
- **Line 1712**: `refreshPlatformStats()` (method)
  ```javascript
  async refreshPlatformStats() {
  ```
- **Line 1717**: `runHealthCheck()` (method)
  ```javascript
  async runHealthCheck() {
  ```
- **Line 1722**: `viewSystemLogs()` (method)
  ```javascript
  viewSystemLogs() {
  ```
- **Line 1726**: `exportPlatformReport()` (method)
  ```javascript
  exportPlatformReport() {
  ```
- **Line 1730**: `refreshOrganizations()` (method)
  ```javascript
  refreshOrganizations() {
  ```
- **Line 1736**: `loadUsers()` (method)
  ```javascript
  async loadUsers() {
  ```
- **Line 1798**: `renderUsersTable()` (method)
  ```javascript
  renderUsersTable(users) {
  ```
- **Line 1883**: `loadAuditLog()` (method)
  ```javascript
  async loadAuditLog() {
  ```
- **Line 1920**: `renderAuditLog()` (method)
  ```javascript
  renderAuditLog(entries) {
  ```
- **Line 1976**: `getAuditSeverityClass()` (method)
  ```javascript
  getAuditSeverityClass(action) {
  ```
- **Line 1985**: `getAuditIcon()` (method)
  ```javascript
  getAuditIcon(action) {
  ```
- **Line 2002**: `formatAuditAction()` (method)
  ```javascript
  formatAuditAction(action) {
  ```
- **Line 2008**: `formatTimestamp()` (method)
  ```javascript
  formatTimestamp(timestamp) {
  ```
- **Line 2020**: `loadMoreAuditEntries()` (method)
  ```javascript
  async loadMoreAuditEntries() {
  ```
- **Line 2025**: `filterAuditLog()` (method)
  ```javascript
  async filterAuditLog() {
  ```
- **Line 2080**: `exportAuditLog()` (method)
  ```javascript
  async exportAuditLog() {
  ```
- **Line 2136**: `viewOrganizationDetails()` (method)
  ```javascript
  viewOrganizationDetails(orgId) {
  ```
- **Line 2140**: `viewUserDetails()` (method)
  ```javascript
  async viewUserDetails(userId) {
  ```
- **Line 2162**: `showUserDetailsModal()` (method)
  ```javascript
  showUserDetailsModal(user) {
  ```
- **Line 2167**: `editUser()` (method)
  ```javascript
  async editUser(userId) {
  ```
- **Line 2172**: `activateUser()` (method)
  ```javascript
  async activateUser(userId) {
  ```
- **Line 2195**: `deactivateUser()` (method)
  ```javascript
  async deactivateUser(userId) {
  ```
- **Line 2222**: `configureTeamsIntegration()` (method)
  ```javascript
  configureTeamsIntegration() {
  ```
- **Line 2226**: `configureZoomIntegration()` (method)
  ```javascript
  configureZoomIntegration() {
  ```
- **Line 2230**: `logout()` (method)
  ```javascript
  logout() {
  ```

### frontend/js/org-admin-enhanced.js
**Undocumented Functions**: 62

- **Line 46**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 145**: `init()` (method)
  ```javascript
  async init() {
  ```
- **Line 168**: `loadCurrentUser()` (method)
  ```javascript
  async loadCurrentUser() {
  ```
- **Line 250**: `setupEventListeners()` (method)
  ```javascript
  setupEventListeners() {
  ```
- **Line 294**: `loadDashboardData()` (method)
  ```javascript
  async loadDashboardData() {
  ```
- **Line 319**: `loadMembers()` (method)
  ```javascript
  async loadMembers() {
  ```
- **Line 358**: `loadTracks()` (method)
  ```javascript
  async loadTracks() {
  ```
- **Line 398**: `loadMeetingRooms()` (method)
  ```javascript
  async loadMeetingRooms() {
  ```
- **Line 437**: `loadProjects()` (method)
  ```javascript
  async loadProjects() {
  ```
- **Line 470**: `showTab()` (method)
  ```javascript
  showTab(tabName) {
  ```
- **Line 552**: `renderMembers()` (method)
  ```javascript
  renderMembers() {
  ```
- **Line 599**: `renderTracks()` (method)
  ```javascript
  renderTracks() {
  ```
- **Line 658**: `renderProjects()` (method)
  ```javascript
  renderProjects() {
  ```
- **Line 721**: `renderMeetingRooms()` (method)
  ```javascript
  renderMeetingRooms() {
  ```
- **Line 785**: `updateOverviewStats()` (method)
  ```javascript
  async updateOverviewStats() {
  ```
- **Line 811**: `showAddMemberModal()` (method)
  ```javascript
  showAddMemberModal(roleType = 'instructor') {
  ```
- **Line 817**: `showAddStudentModal()` (method)
  ```javascript
  showAddStudentModal() {
  ```
- **Line 821**: `showCreateProjectModal()` (method)
  ```javascript
  showCreateProjectModal() {
  ```
- **Line 839**: `showCreateMeetingRoomModal()` (method)
  ```javascript
  showCreateMeetingRoomModal() {
  ```
- **Line 844**: `showModal()` (method)
  ```javascript
  showModal(modalId) {
  ```
- **Line 849**: `closeModal()` (method)
  ```javascript
  closeModal(modalId) {
  ```
- **Line 861**: `updateMemberRoleFields()` (method)
  ```javascript
  updateMemberRoleFields() {
  ```
- **Line 872**: `updateRoomTypeFields()` (method)
  ```javascript
  updateRoomTypeFields() {
  ```
- **Line 894**: `populateProjectSelects()` (method)
  ```javascript
  populateProjectSelects() {
  ```
- **Line 907**: `populateTrackSelects()` (method)
  ```javascript
  populateTrackSelects() {
  ```
- **Line 922**: `addMember()` (method)
  ```javascript
  async addMember() {
  ```
- **Line 963**: `addStudent()` (method)
  ```javascript
  async addStudent() {
  ```
- **Line 1008**: `createMeetingRoom()` (method)
  ```javascript
  async createMeetingRoom() {
  ```
- **Line 1057**: `createProject()` (method)
  ```javascript
  async createProject() {
  ```
- **Line 1128**: `selectProject()` (method)
  ```javascript
  selectProject(projectId) {
  ```
- **Line 1147**: `showProjectDetails()` (method)
  ```javascript
  showProjectDetails(project) {
  ```
- **Line 1168**: `displayProjectInfo()` (method)
  ```javascript
  displayProjectInfo(project) {
  ```
- **Line 1217**: `loadProjectData()` (method)
  ```javascript
  async loadProjectData(project) {
  ```
- **Line 1235**: `loadProjectMembers()` (method)
  ```javascript
  async loadProjectMembers(projectId) {
  ```
- **Line 1251**: `loadProjectTracks()` (method)
  ```javascript
  async loadProjectTracks(projectId) {
  ```
- **Line 1267**: `loadProjectMeetingRooms()` (method)
  ```javascript
  async loadProjectMeetingRooms(projectId) {
  ```
- **Line 1283**: `updateProjectStats()` (method)
  ```javascript
  updateProjectStats() {
  ```
- **Line 1294**: `renderProjectMembers()` (method)
  ```javascript
  renderProjectMembers() {
  ```
- **Line 1332**: `renderProjectTracks()` (method)
  ```javascript
  renderProjectTracks() {
  ```
- **Line 1379**: `renderProjectMeetingRooms()` (method)
  ```javascript
  renderProjectMeetingRooms() {
  ```
- **Line 1422**: `setupProjectContentTabs()` (method)
  ```javascript
  setupProjectContentTabs() {
  ```
- **Line 1448**: `backToProjects()` (method)
  ```javascript
  backToProjects() {
  ```
- **Line 1464**: `editProject()` (method)
  ```javascript
  editProject(projectId) {
  ```
- **Line 1469**: `manageProjectMembers()` (method)
  ```javascript
  manageProjectMembers(projectId) {
  ```
- **Line 1474**: `filterProjects()` (method)
  ```javascript
  filterProjects() {
  ```
- **Line 1487**: `viewReports()` (method)
  ```javascript
  viewReports() {
  ```
- **Line 1492**: `removeMember()` (method)
  ```javascript
  async removeMember(membershipId) {
  ```
- **Line 1525**: `deleteRoom()` (method)
  ```javascript
  async deleteRoom(roomId) {
  ```
- **Line 1559**: `filterMembers()` (method)
  ```javascript
  filterMembers() {
  ```
- **Line 1572**: `filterMeetingRooms()` (method)
  ```javascript
  filterMeetingRooms() {
  ```
- **Line 1593**: `getRoleIcon()` (method)
  ```javascript
  getRoleIcon(role) {
  ```
- **Line 1602**: `formatRoleName()` (method)
  ```javascript
  formatRoleName(role) {
  ```
- **Line 1611**: `formatRoomType()` (method)
  ```javascript
  formatRoomType(type) {
  ```
- **Line 1621**: `joinRoom()` (method)
  ```javascript
  joinRoom(joinUrl) {
  ```
- **Line 1627**: `showLoadingOverlay()` (method)
  ```javascript
  showLoadingOverlay(show) {
  ```
- **Line 1631**: `showNewOrganizationWelcome()` (method)
  ```javascript
  showNewOrganizationWelcome() {
  ```
- **Line 1979**: `loadAssignments()` (method)
  ```javascript
  async loadAssignments() {
  ```
- **Line 2028**: `loadSettings()` (method)
  ```javascript
  async loadSettings() {
  ```
- **Line 2080**: `bulkCreateInstructorRooms()` (method)
  ```javascript
  async bulkCreateInstructorRooms(platform) {
  ```
- **Line 2126**: `bulkCreateTrackRooms()` (method)
  ```javascript
  async bulkCreateTrackRooms(platform) {
  ```
- **Line 2172**: `showNotificationModal()` (method)
  ```javascript
  showNotificationModal() {
  ```
- **Line 2202**: `sendNotification()` (method)
  ```javascript
  async sendNotification() {
  ```

### frontend/js/student-dashboard.js
**Undocumented Functions**: 53

- **Line 64**: `initializeDashboard()` (function)
  ```javascript
  function initializeDashboard() {
  ```
- **Line 137**: `updateUserDisplay()` (function)
  ```javascript
  function updateUserDisplay() {
  ```
- **Line 154**: `setupNavigation()` (function)
  ```javascript
  function setupNavigation() {
  ```
- **Line 168**: `showSection()` (function)
  ```javascript
  function showSection(sectionName) {
  ```
- **Line 193**: `updateNavigation()` (function)
  ```javascript
  function updateNavigation(activeSection) {
  ```
- **Line 206**: `getSectionTitle()` (function)
  ```javascript
  function getSectionTitle(sectionName) {
  ```
- **Line 216**: `loadSectionData()` (function)
  ```javascript
  function loadSectionData(sectionName) {
  ```
- **Line 324**: `calculateProgressFromCourses()` (function)
  ```javascript
  function calculateProgressFromCourses() {
  ```
- **Line 340**: `updateDashboardMetrics()` (function)
  ```javascript
  function updateDashboardMetrics() {
  ```
- **Line 366**: `updateElement()` (function)
  ```javascript
  function updateElement(id, value) {
  ```
- **Line 371**: `loadDashboardData()` (function)
  ```javascript
  function loadDashboardData() {
  ```
- **Line 376**: `displayCurrentCourses()` (function)
  ```javascript
  function displayCurrentCourses() {
  ```
- **Line 438**: `displayRecommendations()` (function)
  ```javascript
  function displayRecommendations(recommendations) {
  ```
- **Line 538**: `displayRecentActivity()` (function)
  ```javascript
  function displayRecentActivity() {
  ```
- **Line 560**: `loadCoursesData()` (function)
  ```javascript
  function loadCoursesData() {
  ```
- **Line 564**: `displayStudentCourses()` (function)
  ```javascript
  function displayStudentCourses() {
  ```
- **Line 615**: `loadProgressData()` (function)
  ```javascript
  function loadProgressData() {
  ```
- **Line 619**: `displayCourseProgress()` (function)
  ```javascript
  function displayCourseProgress() {
  ```
- **Line 653**: `loadLabsData()` (function)
  ```javascript
  function loadLabsData() {
  ```
- **Line 660**: `launchSandboxedLab()` (function)
  ```javascript
  function launchSandboxedLab(labAccess, courseId) {
  ```
- **Line 736**: `generateSessionId()` (function)
  ```javascript
  function generateSessionId() {
  ```
- **Line 740**: `storeLabSession()` (function)
  ```javascript
  function storeLabSession(courseId, sessionId) {
  ```
- **Line 755**: `filterStudentCourses()` (function)
  ```javascript
  function filterStudentCourses() {
  ```
- **Line 788**: `searchStudentCourses()` (function)
  ```javascript
  function searchStudentCourses() {
  ```
- **Line 799**: `displayFilteredCourses()` (function)
  ```javascript
  function displayFilteredCourses(courses) {
  ```
- **Line 870**: `displayLabEnvironments()` (function)
  ```javascript
  function displayLabEnvironments(labs) {
  ```
- **Line 934**: `displayCourseModal()` (function)
  ```javascript
  function displayCourseModal(course, slides, exercises) {
  ```
- **Line 1014**: `launchLabEnvironment()` (function)
  ```javascript
  function launchLabEnvironment(labId, courseId) {
  ```
- **Line 1026**: `displayLabModal()` (function)
  ```javascript
  function displayLabModal(lab, courseId) {
  ```
- **Line 1112**: `displayLabExercises()` (function)
  ```javascript
  function displayLabExercises(exercises) {
  ```
- **Line 1177**: `displayAIResponse()` (function)
  ```javascript
  function displayAIResponse(question, response) {
  ```
- **Line 1200**: `viewLabDetails()` (function)
  ```javascript
  function viewLabDetails(labId) {
  ```
- **Line 1213**: `closeModal()` (function)
  ```javascript
  function closeModal() {
  ```
- **Line 1218**: `closeLabModal()` (function)
  ```javascript
  function closeLabModal() {
  ```
- **Line 1223**: `displayEmptyState()` (function)
  ```javascript
  function displayEmptyState(containerId, message) {
  ```
- **Line 1234**: `getInitials()` (function)
  ```javascript
  function getInitials(name) {
  ```
- **Line 1239**: `showNotification()` (function)
  ```javascript
  function showNotification(message, type = 'info') {
  ```
- **Line 1255**: `getCurrentUser()` (function)
  ```javascript
  function getCurrentUser() {
  ```
- **Line 1343**: `getLabStatus()` (function)
  ```javascript
  function getLabStatus(courseId) {
  ```
- **Line 1347**: `isLabReady()` (function)
  ```javascript
  function isLabReady(courseId) {
  ```
- **Line 1352**: `updateLabStatusIndicators()` (function)
  ```javascript
  function updateLabStatusIndicators() {
  ```
- **Line 1424**: `displayLabFiles()` (function)
  ```javascript
  function displayLabFiles(files) {
  ```
- **Line 1518**: `getCurrentLabId()` (function)
  ```javascript
  function getCurrentLabId() {
  ```
- **Line 1539**: `showLabFileLoading()` (function)
  ```javascript
  function showLabFileLoading() {
  ```
- **Line 1549**: `showLabFileError()` (function)
  ```javascript
  function showLabFileError(message) {
  ```
- **Line 1562**: `getFileIcon()` (function)
  ```javascript
  function getFileIcon(filename) {
  ```
- **Line 1572**: `formatFileSize()` (function)
  ```javascript
  function formatFileSize(bytes) {
  ```
- **Line 1580**: `formatDate()` (function)
  ```javascript
  function formatDate(dateString) {
  ```
- **Line 1587**: `openCourseFeedbackForm()` (function)
  ```javascript
  function openCourseFeedbackForm(courseId, courseName) {
  ```
- **Line 1620**: `closeFeedbackForm()` (function)
  ```javascript
  function closeFeedbackForm() {
  ```
- **Line 1627**: `openStudentFeedbackView()` (function)
  ```javascript
  function openStudentFeedbackView(studentId, courseId) {
  ```
- **Line 1645**: `showStudentFeedbackModal()` (function)
  ```javascript
  function showStudentFeedbackModal(feedback) {
  ```
- **Line 1693**: `closeStudentFeedbackView()` (function)
  ```javascript
  function closeStudentFeedbackView() {
  ```

### frontend/js/lab-template.js
**Undocumented Functions**: 47

- **Line 179**: `togglePanel()` (function)
  ```javascript
  function togglePanel(panelName) {
  ```
- **Line 201**: `updateLayout()` (function)
  ```javascript
  function updateLayout() {
  ```
- **Line 259**: `updateToggleButtons()` (function)
  ```javascript
  function updateToggleButtons() {
  ```
- **Line 347**: `initializeProgressTracking()` (function)
  ```javascript
  function initializeProgressTracking() {
  ```
- **Line 375**: `initializeSandbox()` (function)
  ```javascript
  function initializeSandbox() {
  ```
- **Line 635**: `displayExercises()` (function)
  ```javascript
  function displayExercises() {
  ```
- **Line 696**: `selectExercise()` (function)
  ```javascript
  function selectExercise(exerciseId) {
  ```
- **Line 763**: `showLabNotesModal()` (function)
  ```javascript
  function showLabNotesModal(exercise) {
  ```
- **Line 966**: `updateAIAssistantContext()` (function)
  ```javascript
  function updateAIAssistantContext(exercise) {
  ```
- **Line 1018**: `focusCodeEditor()` (function)
  ```javascript
  function focusCodeEditor() {
  ```
- **Line 1040**: `askAIForHelp()` (function)
  ```javascript
  function askAIForHelp(exerciseId) {
  ```
- **Line 1085**: `toggleSolution()` (function)
  ```javascript
  function toggleSolution(exerciseId) {
  ```
- **Line 1133**: `changeLanguage()` (function)
  ```javascript
  function changeLanguage() {
  ```
- **Line 1256**: `addToTerminal()` (function)
  ```javascript
  function addToTerminal(text, type = 'normal') {
  ```
- **Line 1296**: `runCode()` (function)
  ```javascript
  function runCode() {
  ```
- **Line 1381**: `clearCode()` (function)
  ```javascript
  function clearCode() {
  ```
- **Line 1470**: `addMessage()` (function)
  ```javascript
  function addMessage(message, type, extraClass = '') {
  ```
- **Line 1502**: `formatAssistantMessage()` (function)
  ```javascript
  function formatAssistantMessage(message) {
  ```
- **Line 1673**: `handleTerminalInput()` (function)
  ```javascript
  function handleTerminalInput(event) {
  ```
- **Line 1720**: `executeTerminalCommand()` (function)
  ```javascript
  function executeTerminalCommand(command) {
  ```
- **Line 1844**: `simulateLS()` (function)
  ```javascript
  function simulateLS(path) {
  ```
- **Line 1872**: `simulateCD()` (function)
  ```javascript
  function simulateCD(path) {
  ```
- **Line 1924**: `simulateCAT()` (function)
  ```javascript
  function simulateCAT(filename) {
  ```
- **Line 1953**: `simulateMKDIR()` (function)
  ```javascript
  function simulateMKDIR(dirname) {
  ```
- **Line 1971**: `simulateTOUCH()` (function)
  ```javascript
  function simulateTOUCH(filename) {
  ```
- **Line 1991**: `isCommandAllowed()` (function)
  ```javascript
  function isCommandAllowed(cmd) {
  ```
- **Line 2008**: `isPathAllowed()` (function)
  ```javascript
  function isPathAllowed(path) {
  ```
- **Line 2039**: `resolvePath()` (function)
  ```javascript
  function resolvePath(path) {
  ```
- **Line 2064**: `logCommandExecution()` (function)
  ```javascript
  function logCommandExecution(command) {
  ```
- **Line 2096**: `validateSandboxAccess()` (function)
  ```javascript
  function validateSandboxAccess(path) {
  ```
- **Line 2120**: `trackExerciseStart()` (function)
  ```javascript
  function trackExerciseStart(exerciseId) {
  ```
- **Line 2145**: `trackExerciseCompletion()` (function)
  ```javascript
  function trackExerciseCompletion(exerciseId) {
  ```
- **Line 2176**: `trackCodeExecution()` (function)
  ```javascript
  function trackCodeExecution(exerciseId, code) {
  ```
- **Line 2213**: `updateExerciseUI()` (function)
  ```javascript
  function updateExerciseUI(exerciseId, completed) {
  ```
- **Line 2280**: `loadProgressFromLocalStorage()` (function)
  ```javascript
  function loadProgressFromLocalStorage() {
  ```
- **Line 2304**: `saveProgressToLocalStorage()` (function)
  ```javascript
  function saveProgressToLocalStorage() {
  ```
- **Line 2373**: `calculateTotalLabTime()` (function)
  ```javascript
  function calculateTotalLabTime() {
  ```
- **Line 2397**: `getProgressSummary()` (function)
  ```javascript
  function getProgressSummary() {
  ```
- **Line 2423**: `checkForExerciseCompletion()` (function)
  ```javascript
  function checkForExerciseCompletion(exerciseId, code) {
  ```
- **Line 2476**: `extractKeywords()` (function)
  ```javascript
  function extractKeywords(code) {
  ```
- **Line 2511**: `updateProgressDisplay()` (function)
  ```javascript
  function updateProgressDisplay() {
  ```
- **Line 2533**: `clearTerminal()` (function)
  ```javascript
  function clearTerminal() {
  ```
- **Line 2567**: `focusTerminalInput()` (function)
  ```javascript
  function focusTerminalInput() {
  ```
- **Line 2586**: `updatePrompt()` (function)
  ```javascript
  function updatePrompt() {
  ```
- **Line 2602**: `scrollToBottom()` (function)
  ```javascript
  function scrollToBottom() {
  ```
- **Line 2618**: `initializeTerminal()` (function)
  ```javascript
  function initializeTerminal() {
  ```
- **Line 2666**: `initializeLabAfterDOM()` (function)
  ```javascript
  function initializeLabAfterDOM() {
  ```

### frontend/js/modules/accessibility-tester.js
**Undocumented Functions**: 38

- **Line 26**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 48**: `runAllTests()` (method)
  ```javascript
  async runAllTests() {
  ```
- **Line 98**: `testSemanticStructure()` (method)
  ```javascript
  async testSemanticStructure() {
  ```
- **Line 102**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 111**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 124**: `test()` (arrow_method)
  ```javascript
  test: () => document.querySelector('.skip-links') !== null
  ```
- **Line 128**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 162**: `testARIAImplementation()` (method)
  ```javascript
  async testARIAImplementation() {
  ```
- **Line 166**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 193**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 212**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 226**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 264**: `testKeyboardNavigation()` (method)
  ```javascript
  async testKeyboardNavigation() {
  ```
- **Line 268**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 292**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 300**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 347**: `testColorContrast()` (method)
  ```javascript
  async testColorContrast() {
  ```
- **Line 351**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 372**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 418**: `testFormAccessibility()` (method)
  ```javascript
  async testFormAccessibility() {
  ```
- **Line 422**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 441**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 454**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 497**: `testModalAccessibility()` (method)
  ```javascript
  async testModalAccessibility() {
  ```
- **Line 501**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 515**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 558**: `testScreenReaderSupport()` (method)
  ```javascript
  async testScreenReaderSupport() {
  ```
- **Line 562**: `test()` (arrow_method)
  ```javascript
  test: () => document.title && document.title.trim().length > 0
  ```
- **Line 566**: `test()` (arrow_method)
  ```javascript
  test: () => document.documentElement.getAttribute('lang')
  ```
- **Line 570**: `test()` (arrow_method)
  ```javascript
  test: () => document.querySelectorAll('.sr-only').length > 0
  ```
- **Line 574**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 606**: `testFocusManagement()` (method)
  ```javascript
  async testFocusManagement() {
  ```
- **Line 610**: `test()` (arrow_method)
  ```javascript
  test: () => window.a11y !== undefined
  ```
- **Line 614**: `test()` (arrow_method)
  ```javascript
  test: () => {
  ```
- **Line 656**: `getFocusableElements()` (method)
  ```javascript
  getFocusableElements(container) {
  ```
- **Line 692**: `addTestResult()` (method)
  ```javascript
  addTestResult(category, testName, passed, message = '') {
  ```
- **Line 723**: `generateReport()` (method)
  ```javascript
  generateReport() {
  ```
- **Line 793**: `testFeature()` (method)
  ```javascript
  async testFeature(featureName) {
  ```

### frontend/js/organization-registration.js
**Undocumented Functions**: 38

- **Line 14**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 31**: `initializeEventListeners()` (method)
  ```javascript
  initializeEventListeners() {
  ```
- **Line 89**: `initializeCountryDropdowns()` (method)
  ```javascript
  initializeCountryDropdowns() {
  ```
- **Line 115**: `enhanceCountrySelect()` (method)
  ```javascript
  enhanceCountrySelect(selectElement) {
  ```
- **Line 173**: `handleCountrySearch()` (method)
  ```javascript
  handleCountrySearch(key, selectElement, originalOptions) {
  ```
- **Line 221**: `highlightSelectedCountry()` (method)
  ```javascript
  highlightSelectedCountry(selectElement) {
  ```
- **Line 231**: `showCountrySearchFeedback()` (method)
  ```javascript
  showCountrySearchFeedback(selectElement, searchString, matchCount, searchType = 'starts_with') {
  ```
- **Line 275**: `hideCountrySearchFeedback()` (method)
  ```javascript
  hideCountrySearchFeedback(selectElement) {
  ```
- **Line 285**: `initializePasswordFields()` (method)
  ```javascript
  initializePasswordFields() {
  ```
- **Line 311**: `checkPasswordStrength()` (method)
  ```javascript
  checkPasswordStrength(password) {
  ```
- **Line 361**: `calculatePasswordStrength()` (method)
  ```javascript
  calculatePasswordStrength(password) {
  ```
- **Line 406**: `validatePasswordMatch()` (method)
  ```javascript
  validatePasswordMatch() {
  ```
- **Line 433**: `initializeRealTimeValidation()` (method)
  ```javascript
  initializeRealTimeValidation() {
  ```
- **Line 456**: `initializeLogoUpload()` (method)
  ```javascript
  initializeLogoUpload() {
  ```
- **Line 522**: `handleFileUpload()` (method)
  ```javascript
  handleFileUpload(file) {
  ```
- **Line 582**: `removeLogo()` (method)
  ```javascript
  removeLogo() {
  ```
- **Line 601**: `formatFileSize()` (method)
  ```javascript
  formatFileSize(bytes) {
  ```
- **Line 609**: `generateSlug()` (method)
  ```javascript
  generateSlug(name) {
  ```
- **Line 618**: `updateSlugPreview()` (method)
  ```javascript
  updateSlugPreview(slug) {
  ```
- **Line 630**: `formatPhoneNumber()` (method)
  ```javascript
  formatPhoneNumber(event) {
  ```
- **Line 665**: `validateProfessionalEmail()` (method)
  ```javascript
  validateProfessionalEmail(input) {
  ```
- **Line 705**: `validateField()` (method)
  ```javascript
  validateField(input) {
  ```
- **Line 794**: `getFieldLabel()` (method)
  ```javascript
  getFieldLabel(input) {
  ```
- **Line 799**: `showFieldError()` (method)
  ```javascript
  showFieldError(input, errorElement, message) {
  ```
- **Line 808**: `showFieldSuccess()` (method)
  ```javascript
  showFieldSuccess(input, errorElement, message = '') {
  ```
- **Line 816**: `clearFieldError()` (method)
  ```javascript
  clearFieldError(input, errorElement) {
  ```
- **Line 823**: `validateForm()` (method)
  ```javascript
  validateForm() {
  ```
- **Line 855**: `validatePasswords()` (method)
  ```javascript
  validatePasswords() {
  ```
- **Line 912**: `showFieldError()` (method)
  ```javascript
  showFieldError(fieldId, message) {
  ```
- **Line 923**: `clearFieldError()` (method)
  ```javascript
  clearFieldError(fieldId) {
  ```
- **Line 934**: `handleSubmit()` (method)
  ```javascript
  async handleSubmit(event) {
  ```
- **Line 1053**: `submitOrganization()` (method)
  ```javascript
  async submitOrganization(data) {
  ```
- **Line 1093**: `submitOrganizationWithFile()` (method)
  ```javascript
  async submitOrganizationWithFile(formData) {
  ```
- **Line 1128**: `handleValidationErrors()` (method)
  ```javascript
  handleValidationErrors(errors) {
  ```
- **Line 1163**: `setSubmitLoading()` (method)
  ```javascript
  setSubmitLoading(loading) {
  ```
- **Line 1168**: `showSuccess()` (method)
  ```javascript
  showSuccess(data) {
  ```
- **Line 1243**: `showGeneralError()` (method)
  ```javascript
  showGeneralError(message) {
  ```
- **Line 1270**: `initializeRegistration()` (arrow)
  ```javascript
  const initializeRegistration = () => {
  ```

### frontend/js/modules/projects/wizard/wizard-state.js
**Undocumented Functions**: 37

- **Line 52**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 99**: `getState()` (method)
  ```javascript
  getState() {
  ```
- **Line 112**: `setState()` (method)
  ```javascript
  setState(updates) {
  ```
- **Line 130**: `subscribe()` (method)
  ```javascript
  subscribe(callback) {
  ```
- **Line 153**: `notify()` (method)
  ```javascript
  notify(oldState, newState) {
  ```
- **Line 172**: `setCurrentStep()` (method)
  ```javascript
  setCurrentStep(stepNumber) {
  ```
- **Line 186**: `nextStep()` (method)
  ```javascript
  nextStep() {
  ```
- **Line 199**: `previousStep()` (method)
  ```javascript
  previousStep() {
  ```
- **Line 212**: `isFirstStep()` (method)
  ```javascript
  isFirstStep() {
  ```
- **Line 221**: `isLastStep()` (method)
  ```javascript
  isLastStep() {
  ```
- **Line 234**: `setProjectName()` (method)
  ```javascript
  setProjectName(name) {
  ```
- **Line 243**: `setProjectSlug()` (method)
  ```javascript
  setProjectSlug(slug) {
  ```
- **Line 252**: `setProjectDescription()` (method)
  ```javascript
  setProjectDescription(description) {
  ```
- **Line 261**: `setProjectObjectives()` (method)
  ```javascript
  setProjectObjectives(objectives) {
  ```
- **Line 272**: `updateStep1Data()` (method)
  ```javascript
  updateStep1Data(data) {
  ```
- **Line 290**: `validateStep1()` (method)
  ```javascript
  validateStep1() {
  ```
- **Line 310**: `setDurationWeeks()` (method)
  ```javascript
  setDurationWeeks(weeks) {
  ```
- **Line 319**: `setMaxParticipants()` (method)
  ```javascript
  setMaxParticipants(max) {
  ```
- **Line 328**: `setTargetRoles()` (method)
  ```javascript
  setTargetRoles(roles) {
  ```
- **Line 339**: `setProjectType()` (method)
  ```javascript
  setProjectType(type) {
  ```
- **Line 348**: `setLocations()` (method)
  ```javascript
  setLocations(locations) {
  ```
- **Line 359**: `addLocation()` (method)
  ```javascript
  addLocation(location) {
  ```
- **Line 369**: `removeLocation()` (method)
  ```javascript
  removeLocation(index) {
  ```
- **Line 379**: `updateStep2Data()` (method)
  ```javascript
  updateStep2Data(data) {
  ```
- **Line 400**: `validateStep2()` (method)
  ```javascript
  validateStep2() {
  ```
- **Line 419**: `setProposedTracks()` (method)
  ```javascript
  setProposedTracks(tracks) {
  ```
- **Line 430**: `setApprovedTracks()` (method)
  ```javascript
  setApprovedTracks(tracks) {
  ```
- **Line 444**: `validateStep3()` (method)
  ```javascript
  validateStep3() {
  ```
- **Line 458**: `setAISuggestionsLoading()` (method)
  ```javascript
  setAISuggestionsLoading(loading) {
  ```
- **Line 467**: `setAISuggestions()` (method)
  ```javascript
  setAISuggestions(suggestions) {
  ```
- **Line 493**: `setOrganizationId()` (method)
  ```javascript
  setOrganizationId(organizationId) {
  ```
- **Line 502**: `setLoading()` (method)
  ```javascript
  setLoading(loading) {
  ```
- **Line 511**: `setError()` (method)
  ```javascript
  setError(error) {
  ```
- **Line 527**: `setCreatedProject()` (method)
  ```javascript
  setCreatedProject(project) {
  ```
- **Line 538**: `reset()` (method)
  ```javascript
  reset() {
  ```
- **Line 571**: `getProjectData()` (method)
  ```javascript
  getProjectData() {
  ```
- **Line 594**: `canSubmit()` (method)
  ```javascript
  canSubmit() {
  ```

### frontend/js/modules/onboarding-system.js
**Undocumented Functions**: 35

- **Line 26**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 53**: `init()` (method)
  ```javascript
  init() {
  ```
- **Line 78**: `loadUserProgress()` (method)
  ```javascript
  loadUserProgress() {
  ```
- **Line 109**: `saveUserProgress()` (method)
  ```javascript
  saveUserProgress() {
  ```
- **Line 133**: `checkFirstVisit()` (method)
  ```javascript
  checkFirstVisit() {
  ```
- **Line 161**: `createHelpWidget()` (method)
  ```javascript
  createHelpWidget() {
  ```
- **Line 249**: `setupHelpWidgetEvents()` (method)
  ```javascript
  setupHelpWidgetEvents() {
  ```
- **Line 295**: `toggleHelpMenu()` (method)
  ```javascript
  toggleHelpMenu() {
  ```
- **Line 322**: `openHelpMenu()` (method)
  ```javascript
  openHelpMenu() {
  ```
- **Line 356**: `closeHelpMenu()` (method)
  ```javascript
  closeHelpMenu() {
  ```
- **Line 386**: `handleHelpAction()` (method)
  ```javascript
  handleHelpAction(action) {
  ```
- **Line 424**: `setupTours()` (method)
  ```javascript
  setupTours() {
  ```
- **Line 505**: `startTour()` (method)
  ```javascript
  startTour(tourId) {
  ```
- **Line 542**: `createTourOverlay()` (method)
  ```javascript
  createTourOverlay() {
  ```
- **Line 577**: `showTourStep()` (method)
  ```javascript
  showTourStep() {
  ```
- **Line 611**: `updateSpotlight()` (method)
  ```javascript
  updateSpotlight(target) {
  ```
- **Line 642**: `createStepPopup()` (method)
  ```javascript
  createStepPopup(step, target) {
  ```
- **Line 719**: `positionStepPopup()` (method)
  ```javascript
  positionStepPopup(popup, target, position) {
  ```
- **Line 765**: `setupStepEvents()` (method)
  ```javascript
  setupStepEvents(popup) {
  ```
- **Line 797**: `nextStep()` (method)
  ```javascript
  nextStep() {
  ```
- **Line 821**: `prevStep()` (method)
  ```javascript
  prevStep() {
  ```
- **Line 843**: `skipTour()` (method)
  ```javascript
  skipTour() {
  ```
- **Line 867**: `finishTour()` (method)
  ```javascript
  finishTour() {
  ```
- **Line 897**: `closeTour()` (method)
  ```javascript
  closeTour() {
  ```
- **Line 932**: `showWelcomeBanner()` (method)
  ```javascript
  showWelcomeBanner() {
  ```
- **Line 975**: `dismissWelcome()` (method)
  ```javascript
  dismissWelcome() {
  ```
- **Line 1004**: `createQuickTipsPanel()` (method)
  ```javascript
  createQuickTipsPanel() {
  ```
- **Line 1077**: `showQuickTips()` (method)
  ```javascript
  showQuickTips() {
  ```
- **Line 1107**: `hideQuickTips()` (method)
  ```javascript
  hideQuickTips() {
  ```
- **Line 1134**: `showDocumentation()` (method)
  ```javascript
  showDocumentation() {
  ```
- **Line 1159**: `showContactSupport()` (method)
  ```javascript
  showContactSupport() {
  ```
- **Line 1185**: `addHelpTooltip()` (method)
  ```javascript
  addHelpTooltip(element, text) {
  ```
- **Line 1218**: `highlightFeature()` (method)
  ```javascript
  highlightFeature(selector, duration = 5000) {
  ```
- **Line 1245**: `isTourCompleted()` (method)
  ```javascript
  isTourCompleted(tourId) {
  ```
- **Line 1264**: `resetProgress()` (method)
  ```javascript
  resetProgress() {
  ```

### frontend/js/modules/analytics-dashboard.js
**Undocumented Functions**: 33

- **Line 42**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 72**: `initialize()` (method)
  ```javascript
  async initialize(courseId = null) {
  ```
- **Line 110**: `setupEventListeners()` (method)
  ```javascript
  setupEventListeners() {
  ```
- **Line 185**: `loadCourseAnalytics()` (method)
  ```javascript
  async loadCourseAnalytics(courseId, daysBack = 30) {
  ```
- **Line 237**: `renderCourseAnalytics()` (method)
  ```javascript
  async renderCourseAnalytics(analytics) {
  ```
- **Line 277**: `updateOverviewCards()` (method)
  ```javascript
  updateOverviewCards(analytics) {
  ```
- **Line 329**: `renderEngagementChart()` (method)
  ```javascript
  async renderEngagementChart(analytics) {
  ```
- **Line 396**: `renderLabCompletionChart()` (method)
  ```javascript
  async renderLabCompletionChart(analytics) {
  ```
- **Line 461**: `renderQuizPerformanceChart()` (method)
  ```javascript
  async renderQuizPerformanceChart(analytics) {
  ```
- **Line 533**: `renderProgressDistributionChart()` (method)
  ```javascript
  async renderProgressDistributionChart(analytics) {
  ```
- **Line 601**: `loadStudentsList()` (method)
  ```javascript
  async loadStudentsList(courseId) {
  ```
- **Line 640**: `fetchStudentsList()` (method)
  ```javascript
  async fetchStudentsList(courseId) {
  ```
- **Line 692**: `renderStudentsList()` (method)
  ```javascript
  renderStudentsList(students, container) {
  ```
- **Line 758**: `viewStudentDetails()` (method)
  ```javascript
  async viewStudentDetails(studentId) {
  ```
- **Line 819**: `renderStudentDetailsModal()` (method)
  ```javascript
  renderStudentDetailsModal(analytics) {
  ```
- **Line 921**: `contactStudent()` (method)
  ```javascript
  async contactStudent(studentId) {
  ```
- **Line 945**: `searchStudents()` (method)
  ```javascript
  searchStudents(query) {
  ```
- **Line 980**: `updateTimeRange()` (method)
  ```javascript
  async updateTimeRange(daysBack) {
  ```
- **Line 1005**: `refreshAnalytics()` (method)
  ```javascript
  async refreshAnalytics() {
  ```
- **Line 1034**: `exportAnalytics()` (method)
  ```javascript
  async exportAnalytics() {
  ```
- **Line 1093**: `generateScoreDistribution()` (method)
  ```javascript
  generateScoreDistribution(avgScore, stdDev, totalAttempts) {
  ```
- **Line 1126**: `formatDate()` (method)
  ```javascript
  formatDate(dateString) {
  ```
- **Line 1147**: `showModal()` (method)
  ```javascript
  showModal(modal) {
  ```
- **Line 1168**: `hideModal()` (method)
  ```javascript
  hideModal(modal) {
  ```
- **Line 1190**: `showLoading()` (method)
  ```javascript
  showLoading(message = 'Loading...') {
  ```
- **Line 1212**: `hideLoading()` (method)
  ```javascript
  hideLoading() {
  ```
- **Line 1237**: `showError()` (method)
  ```javascript
  showError(message) {
  ```
- **Line 1266**: `showSuccess()` (method)
  ```javascript
  showSuccess(message) {
  ```
- **Line 1302**: `downloadPDFReport()` (method)
  ```javascript
  async downloadPDFReport() {
  ```
- **Line 1385**: `previewReportData()` (method)
  ```javascript
  async previewReportData() {
  ```
- **Line 1444**: `showReportPreview()` (method)
  ```javascript
  showReportPreview(previewData) {
  ```
- **Line 1478**: `getSelectedTimeRange()` (method)
  ```javascript
  getSelectedTimeRange() {
  ```
- **Line 1517**: `downloadStudentPDFReport()` (method)
  ```javascript
  async downloadStudentPDFReport(studentId) {
  ```

### frontend/js/modules/file-explorer.js
**Undocumented Functions**: 32

- **Line 42**: `constructor()` (method)
  ```javascript
  constructor(container, options = {}) {
  ```
- **Line 95**: `getCurrentUser()` (method)
  ```javascript
  getCurrentUser() {
  ```
- **Line 117**: `canDeleteFile()` (method)
  ```javascript
  canDeleteFile(file) {
  ```
- **Line 150**: `canUploadFiles()` (method)
  ```javascript
  canUploadFiles() {
  ```
- **Line 165**: `render()` (method)
  ```javascript
  render() {
  ```
- **Line 258**: `attachEventListeners()` (method)
  ```javascript
  attachEventListeners() {
  ```
- **Line 375**: `setupDragAndDrop()` (method)
  ```javascript
  async setupDragAndDrop() {
  ```
- **Line 419**: `loadFiles()` (method)
  ```javascript
  async loadFiles() {
  ```
- **Line 472**: `renderFiles()` (method)
  ```javascript
  renderFiles() {
  ```
- **Line 511**: `renderGridView()` (method)
  ```javascript
  renderGridView(files, container) {
  ```
- **Line 558**: `renderListView()` (method)
  ```javascript
  renderListView(files, container) {
  ```
- **Line 610**: `sortFiles()` (method)
  ```javascript
  sortFiles(files) {
  ```
- **Line 654**: `deleteFile()` (method)
  ```javascript
  async deleteFile(fileId) {
  ```
- **Line 716**: `deleteSelected()` (method)
  ```javascript
  async deleteSelected() {
  ```
- **Line 757**: `trackFileDeletion()` (method)
  ```javascript
  async trackFileDeletion(file) {
  ```
- **Line 793**: `downloadFile()` (method)
  ```javascript
  async downloadFile(fileId) {
  ```
- **Line 851**: `trackFileDownload()` (method)
  ```javascript
  async trackFileDownload(file) {
  ```
- **Line 884**: `previewFile()` (method)
  ```javascript
  async previewFile(fileId) {
  ```
- **Line 921**: `onUploadComplete()` (arrow_method)
  ```javascript
  onUploadComplete: async (response, file) => {
  ```
- **Line 949**: `uploadFiles()` (method)
  ```javascript
  async uploadFiles(files) {
  ```
- **Line 959**: `selectFile()` (method)
  ```javascript
  selectFile(fileId) {
  ```
- **Line 975**: `toggleFileSelection()` (method)
  ```javascript
  toggleFileSelection(fileId) {
  ```
- **Line 1043**: `setViewMode()` (method)
  ```javascript
  setViewMode(mode) {
  ```
- **Line 1099**: `getFileIcon()` (method)
  ```javascript
  getFileIcon(type) {
  ```
- **Line 1206**: `formatFileSize()` (method)
  ```javascript
  formatFileSize(bytes) {
  ```
- **Line 1227**: `formatDate()` (method)
  ```javascript
  formatDate(dateStr) {
  ```
- **Line 1251**: `truncateFilename()` (method)
  ```javascript
  truncateFilename(filename, maxLength) {
  ```
- **Line 1269**: `escapeHtml()` (method)
  ```javascript
  escapeHtml(str) {
  ```
- **Line 1280**: `showError()` (method)
  ```javascript
  showError(message) {
  ```
- **Line 1290**: `showSuccess()` (method)
  ```javascript
  showSuccess(message) {
  ```
- **Line 1300**: `showInfo()` (method)
  ```javascript
  showInfo(message) {
  ```
- **Line 1311**: `addStyles()` (method)
  ```javascript
  addStyles() {
  ```

### frontend/js/modules/instructor-dashboard.js
**Undocumented Functions**: 29

- **Line 67**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 117**: `init()` (method)
  ```javascript
  init() {
  ```
- **Line 157**: `showQuizManagement()` (method)
  ```javascript
  async showQuizManagement(courseId) {
  ```
- **Line 242**: `setupEventListeners()` (method)
  ```javascript
  setupEventListeners() {
  ```
- **Line 294**: `loadInitialData()` (method)
  ```javascript
  async loadInitialData() {
  ```
- **Line 328**: `loadCourses()` (method)
  ```javascript
  async loadCourses() {
  ```
- **Line 368**: `loadStudents()` (method)
  ```javascript
  async loadStudents() {
  ```
- **Line 401**: `renderDashboard()` (method)
  ```javascript
  renderDashboard() {
  ```
- **Line 460**: `renderTabContent()` (method)
  ```javascript
  renderTabContent() {
  ```
- **Line 500**: `renderCoursesTab()` (method)
  ```javascript
  renderCoursesTab() {
  ```
- **Line 552**: `renderCourseCard()` (method)
  ```javascript
  renderCourseCard(course) {
  ```
- **Line 614**: `renderStudentsTab()` (method)
  ```javascript
  renderStudentsTab() {
  ```
- **Line 682**: `renderStudentRow()` (method)
  ```javascript
  renderStudentRow(student) {
  ```
- **Line 740**: `renderAnalyticsTab()` (method)
  ```javascript
  renderAnalyticsTab() {
  ```
- **Line 837**: `renderContentTab()` (method)
  ```javascript
  renderContentTab() {
  ```
- **Line 940**: `renderFeedbackTab()` (method)
  ```javascript
  renderFeedbackTab() {
  ```
- **Line 1007**: `renderCourseFeedbackSection()` (method)
  ```javascript
  renderCourseFeedbackSection() {
  ```
- **Line 1069**: `renderStudentFeedbackSection()` (method)
  ```javascript
  renderStudentFeedbackSection() {
  ```
- **Line 1147**: `switchTab()` (method)
  ```javascript
  switchTab(tabName) {
  ```
- **Line 1183**: `showCreateCourseModal()` (method)
  ```javascript
  showCreateCourseModal() {
  ```
- **Line 1259**: `createCourse()` (method)
  ```javascript
  async createCourse(formData) {
  ```
- **Line 1313**: `editCourse()` (method)
  ```javascript
  editCourse(courseId) {
  ```
- **Line 1352**: `deleteCourse()` (method)
  ```javascript
  async deleteCourse(courseId) {
  ```
- **Line 1409**: `showAddStudentModal()` (method)
  ```javascript
  showAddStudentModal() {
  ```
- **Line 1482**: `addStudent()` (method)
  ```javascript
  async addStudent(formData) {
  ```
- **Line 1566**: `loadFeedbackData()` (method)
  ```javascript
  async loadFeedbackData() {
  ```
- **Line 1700**: `showStudentFeedbackModal()` (method)
  ```javascript
  showStudentFeedbackModal(studentId, courseId) {
  ```
- **Line 1986**: `showCreateInstanceModal()` (method)
  ```javascript
  async showCreateInstanceModal() {
  ```
- **Line 2251**: `completeCourseInstance()` (method)
  ```javascript
  async completeCourseInstance(instanceId, instanceName) {
  ```

### frontend/js/modules/config-manager.js
**Undocumented Functions**: 28

- **Line 42**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 92**: `_detectEnvironment()` (method)
  ```javascript
  _detectEnvironment() {
  ```
- **Line 123**: `_initializePerformanceOptimization()` (method)
  ```javascript
  _initializePerformanceOptimization() {
  ```
- **Line 154**: `getConfig()` (method)
  ```javascript
  async getConfig(key, options = {}) {
  ```
- **Line 209**: `_getCachedConfig()` (method)
  ```javascript
  _getCachedConfig(key, options = {}) {
  ```
- **Line 244**: `_fetchConfig()` (method)
  ```javascript
  async _fetchConfig(key, options = {}) {
  ```
- **Line 279**: `_fetchFromSource()` (method)
  ```javascript
  async _fetchFromSource(key, source, options = {}) {
  ```
- **Line 312**: `_fetchFromLocalStorage()` (method)
  ```javascript
  _fetchFromLocalStorage(key) {
  ```
- **Line 335**: `_fetchFromMemory()` (method)
  ```javascript
  _fetchFromMemory(key) {
  ```
- **Line 365**: `_fetchFromRemote()` (method)
  ```javascript
  async _fetchFromRemote(key, options = {}) {
  ```
- **Line 413**: `_getDefaultConfig()` (method)
  ```javascript
  _getDefaultConfig(key) {
  ```
- **Line 460**: `_getDefaultApiBaseUrl()` (method)
  ```javascript
  _getDefaultApiBaseUrl() {
  ```
- **Line 492**: `_setCachedConfig()` (method)
  ```javascript
  _setCachedConfig(key, value, options = {}) {
  ```
- **Line 522**: `setConfig()` (method)
  ```javascript
  async setConfig(key, value, options = {}) {
  ```
- **Line 550**: `onConfigChange()` (method)
  ```javascript
  onConfigChange(key, callback) {
  ```
- **Line 582**: `_notifyConfigChange()` (method)
  ```javascript
  _notifyConfigChange(key, newValue, oldValue) {
  ```
- **Line 607**: `_warmCriticalCache()` (method)
  ```javascript
  async _warmCriticalCache() {
  ```
- **Line 640**: `preloadAssets()` (method)
  ```javascript
  async preloadAssets(assets = []) {
  ```
- **Line 667**: `_preloadAsset()` (method)
  ```javascript
  async _preloadAsset(asset) {
  ```
- **Line 721**: `getAsset()` (method)
  ```javascript
  getAsset(url) {
  ```
- **Line 737**: `_setupPerformanceMetrics()` (method)
  ```javascript
  _setupPerformanceMetrics() {
  ```
- **Line 761**: `_recordCacheEffectiveness()` (method)
  ```javascript
  _recordCacheEffectiveness(key, accessTime, cacheHit) {
  ```
- **Line 787**: `_setupConfigurationMonitoring()` (method)
  ```javascript
  _setupConfigurationMonitoring() {
  ```
- **Line 822**: `_initializeAssetPreloading()` (method)
  ```javascript
  _initializeAssetPreloading() {
  ```
- **Line 845**: `invalidateConfig()` (method)
  ```javascript
  invalidateConfig(key) {
  ```
- **Line 870**: `getConfigs()` (method)
  ```javascript
  async getConfigs(keys, options = {}) {
  ```
- **Line 907**: `getCacheStats()` (method)
  ```javascript
  getCacheStats() {
  ```
- **Line 933**: `clearCache()` (method)
  ```javascript
  clearCache() {
  ```

### frontend/js/modules/projects/wizard/track-management/track-management-controller.js
**Undocumented Functions**: 28

- **Line 60**: `constructor()` (method)
  ```javascript
  constructor(trackState, dependencies) {
  ```
- **Line 79**: `initializeStateSubscriptions()` (method)
  ```javascript
  initializeStateSubscriptions() {
  ```
- **Line 105**: `openTrackManagementModal()` (method)
  ```javascript
  openTrackManagementModal(track, trackIndex = null) {
  ```
- **Line 133**: `closeTrackManagementModal()` (method)
  ```javascript
  closeTrackManagementModal(force = false) {
  ```
- **Line 159**: `renderModal()` (method)
  ```javascript
  renderModal() {
  ```
- **Line 223**: `renderActiveTab()` (method)
  ```javascript
  renderActiveTab() {
  ```
- **Line 258**: `updateTabIndicators()` (method)
  ```javascript
  updateTabIndicators() {
  ```
- **Line 282**: `switchTab()` (method)
  ```javascript
  switchTab(tabName) {
  ```
- **Line 302**: `attachEventHandlers()` (method)
  ```javascript
  attachEventHandlers() {
  ```
- **Line 307**: `tabHandler()` (arrow)
  ```javascript
  const tabHandler = (e) => {
  ```
- **Line 317**: `actionHandler()` (arrow)
  ```javascript
  const actionHandler = (e) => {
  ```
- **Line 332**: `detachEventHandlers()` (method)
  ```javascript
  detachEventHandlers() {
  ```
- **Line 346**: `handleAction()` (method)
  ```javascript
  async handleAction(action, target) {
  ```
- **Line 412**: `addInstructor()` (method)
  ```javascript
  async addInstructor() {
  ```
- **Line 433**: `removeInstructor()` (method)
  ```javascript
  removeInstructor(index) {
  ```
- **Line 456**: `createCourse()` (method)
  ```javascript
  async createCourse() {
  ```
- **Line 482**: `removeCourse()` (method)
  ```javascript
  removeCourse(index) {
  ```
- **Line 502**: `editCourse()` (method)
  ```javascript
  editCourse(index) {
  ```
- **Line 521**: `enrollStudent()` (method)
  ```javascript
  async enrollStudent() {
  ```
- **Line 541**: `bulkEnrollStudents()` (method)
  ```javascript
  async bulkEnrollStudents() {
  ```
- **Line 552**: `removeStudent()` (method)
  ```javascript
  removeStudent(index) {
  ```
- **Line 572**: `viewStudentProgress()` (method)
  ```javascript
  viewStudentProgress(index) {
  ```
- **Line 591**: `saveTrackChanges()` (method)
  ```javascript
  async saveTrackChanges() {
  ```
- **Line 645**: `emit()` (method)
  ```javascript
  emit(eventName, detail = {}) {
  ```
- **Line 661**: `on()` (method)
  ```javascript
  on(eventName, callback) {
  ```
- **Line 662**: `handler()` (arrow)
  ```javascript
  const handler = (e) => callback(e.detail);
  ```
- **Line 678**: `escapeHtml()` (method)
  ```javascript
  escapeHtml(str) {
  ```
- **Line 690**: `destroy()` (method)
  ```javascript
  destroy() {
  ```

### frontend/js/modules/auth.js
**Undocumented Functions**: 24

- **Line 49**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 128**: `getCurrentUser()` (method)
  ```javascript
  getCurrentUser() {
  ```
- **Line 165**: `isAuthenticated()` (method)
  ```javascript
  isAuthenticated() {
  ```
- **Line 179**: `getToken()` (method)
  ```javascript
  getToken() {
  ```
- **Line 196**: `initializeAuth()` (method)
  ```javascript
  initializeAuth() {
  ```
- **Line 250**: `login()` (method)
  ```javascript
  async login(credentials) {
  ```
- **Line 373**: `register()` (method)
  ```javascript
  async register(userData) {
  ```
- **Line 436**: `resetPassword()` (method)
  ```javascript
  async resetPassword(email, newPassword) {
  ```
- **Line 501**: `getUserProfile()` (method)
  ```javascript
  async getUserProfile() {
  ```
- **Line 561**: `logout()` (method)
  ```javascript
  async logout() {
  ```
- **Line 646**: `authenticatedFetch()` (method)
  ```javascript
  async authenticatedFetch(url, options = {}) {
  ```
- **Line 705**: `handleSessionExpired()` (method)
  ```javascript
  handleSessionExpired() {
  ```
- **Line 751**: `getUserRole()` (method)
  ```javascript
  getUserRole() {
  ```
- **Line 764**: `hasRole()` (method)
  ```javascript
  hasRole(role) {
  ```
- **Line 787**: `hasPageAccess()` (method)
  ```javascript
  hasPageAccess(page) {
  ```
- **Line 823**: `getRedirectUrl()` (method)
  ```javascript
  getRedirectUrl() {
  ```
- **Line 889**: `isSessionValid()` (method)
  ```javascript
  isSessionValid() {
  ```
- **Line 933**: `updateLastActivity()` (method)
  ```javascript
  updateLastActivity() {
  ```
- **Line 944**: `clearAllSessionData()` (method)
  ```javascript
  clearAllSessionData() {
  ```
- **Line 962**: `clearExpiredSession()` (method)
  ```javascript
  clearExpiredSession() {
  ```
- **Line 979**: `startSessionMonitoring()` (method)
  ```javascript
  startSessionMonitoring() {
  ```
- **Line 1005**: `stopSessionMonitoring()` (method)
  ```javascript
  stopSessionMonitoring() {
  ```
- **Line 1019**: `checkLogoutWarning()` (method)
  ```javascript
  checkLogoutWarning() {
  ```
- **Line 1053**: `showLogoutWarning()` (method)
  ```javascript
  showLogoutWarning(minutesRemaining) {
  ```

### frontend/js/modules/navigation-manager.js
**Undocumented Functions**: 24

- **Line 18**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 97**: `init()` (method)
  ```javascript
  init() {
  ```
- **Line 118**: `setupNavigationSearch()` (method)
  ```javascript
  setupNavigationSearch() {
  ```
- **Line 152**: `handleNavigationSearch()` (method)
  ```javascript
  handleNavigationSearch(query) {
  ```
- **Line 196**: `executeSearch()` (method)
  ```javascript
  executeSearch(query) {
  ```
- **Line 219**: `clearSearchHighlights()` (method)
  ```javascript
  clearSearchHighlights() {
  ```
- **Line 236**: `setupScrollIndicators()` (method)
  ```javascript
  setupScrollIndicators() {
  ```
- **Line 240**: `updateScrollIndicators()` (arrow)
  ```javascript
  const updateScrollIndicators = () => {
  ```
- **Line 267**: `setupKeyboardShortcuts()` (method)
  ```javascript
  setupKeyboardShortcuts() {
  ```
- **Line 312**: `focusSearch()` (method)
  ```javascript
  focusSearch() {
  ```
- **Line 331**: `setupTabEnhancements()` (method)
  ```javascript
  setupTabEnhancements() {
  ```
- **Line 370**: `navigateToTab()` (method)
  ```javascript
  navigateToTab(tabName) {
  ```
- **Line 414**: `scrollTabIntoView()` (method)
  ```javascript
  scrollTabIntoView(tab) {
  ```
- **Line 440**: `updateBreadcrumbs()` (method)
  ```javascript
  updateBreadcrumbs() {
  ```
- **Line 493**: `showTabContextMenu()` (method)
  ```javascript
  showTabContextMenu(event, tab) {
  ```
- **Line 551**: `closeMenu()` (arrow)
  ```javascript
  const closeMenu = (e) => {
  ```
- **Line 574**: `showKeyboardShortcuts()` (method)
  ```javascript
  showKeyboardShortcuts() {
  ```
- **Line 652**: `hideKeyboardShortcuts()` (method)
  ```javascript
  hideKeyboardShortcuts() {
  ```
- **Line 672**: `bookmarkTab()` (method)
  ```javascript
  bookmarkTab(tabName) {
  ```
- **Line 692**: `showTabInfo()` (method)
  ```javascript
  showTabInfo(tabName) {
  ```
- **Line 711**: `getNavigationHistory()` (method)
  ```javascript
  getNavigationHistory() {
  ```
- **Line 726**: `goBack()` (method)
  ```javascript
  goBack() {
  ```
- **Line 747**: `addNotificationBadge()` (method)
  ```javascript
  addNotificationBadge(tabName, count) {
  ```
- **Line 774**: `removeNotificationBadge()` (method)
  ```javascript
  removeNotificationBadge(tabName) {
  ```

### frontend/js/modules/projects/wizard/wizard-controller.js
**Undocumented Functions**: 23

- **Line 57**: `constructor()` (method)
  ```javascript
  constructor(wizardState, dependencies) {
  ```
- **Line 89**: `initializeStateSubscriptions()` (method)
  ```javascript
  initializeStateSubscriptions() {
  ```
- **Line 126**: `openWizard()` (method)
  ```javascript
  openWizard(organizationId) {
  ```
- **Line 154**: `closeWizard()` (method)
  ```javascript
  closeWizard() {
  ```
- **Line 180**: `destroy()` (method)
  ```javascript
  destroy() {
  ```
- **Line 200**: `nextStep()` (method)
  ```javascript
  async nextStep() {
  ```
- **Line 227**: `advanceFromStep1()` (method)
  ```javascript
  async advanceFromStep1() {
  ```
- **Line 261**: `advanceFromStep2()` (method)
  ```javascript
  async advanceFromStep2() {
  ```
- **Line 307**: `previousStep()` (method)
  ```javascript
  previousStep() {
  ```
- **Line 316**: `goToStep()` (method)
  ```javascript
  goToStep(stepNumber) {
  ```
- **Line 337**: `generateTrackProposals()` (method)
  ```javascript
  generateTrackProposals(audiences) {
  ```
- **Line 382**: `generateAISuggestions()` (method)
  ```javascript
  async generateAISuggestions() {
  ```
- **Line 430**: `buildAIPrompt()` (method)
  ```javascript
  buildAIPrompt(state) {
  ```
- **Line 454**: `parseAIResponse()` (method)
  ```javascript
  parseAIResponse(response) {
  ```
- **Line 497**: `submitProject()` (method)
  ```javascript
  async submitProject() {
  ```
- **Line 561**: `createTracks()` (method)
  ```javascript
  async createTracks(projectId, tracks) {
  ```
- **Line 595**: `renderStep()` (method)
  ```javascript
  renderStep(stepNumber) {
  ```
- **Line 622**: `updateNavigationButtons()` (method)
  ```javascript
  updateNavigationButtons(currentStep) {
  ```
- **Line 646**: `updateLoadingState()` (method)
  ```javascript
  updateLoadingState(loading) {
  ```
- **Line 664**: `emit()` (method)
  ```javascript
  emit(event, data) {
  ```
- **Line 676**: `defaultOpenModal()` (method)
  ```javascript
  defaultOpenModal(modalId) {
  ```
- **Line 683**: `defaultCloseModal()` (method)
  ```javascript
  defaultCloseModal(modalId) {
  ```
- **Line 690**: `defaultShowNotification()` (method)
  ```javascript
  defaultShowNotification(message, type = 'info') {
  ```

### frontend/js/modules/projects/wizard/track-management/track-management-state.js
**Undocumented Functions**: 23

- **Line 75**: `getState()` (method)
  ```javascript
  getState() {
  ```
- **Line 85**: `setState()` (method)
  ```javascript
  setState(updates) {
  ```
- **Line 100**: `subscribe()` (method)
  ```javascript
  subscribe(callback) {
  ```
- **Line 123**: `notify()` (method)
  ```javascript
  notify(oldState, newState) {
  ```
- **Line 143**: `setTrack()` (method)
  ```javascript
  setTrack(track, trackIndex = null) {
  ```
- **Line 181**: `getTrack()` (method)
  ```javascript
  getTrack() {
  ```
- **Line 203**: `setActiveTab()` (method)
  ```javascript
  setActiveTab(tabName) {
  ```
- **Line 218**: `getActiveTab()` (method)
  ```javascript
  getActiveTab() {
  ```
- **Line 231**: `addInstructor()` (method)
  ```javascript
  addInstructor(instructor) {
  ```
- **Line 245**: `removeInstructor()` (method)
  ```javascript
  removeInstructor(index) {
  ```
- **Line 261**: `updateInstructor()` (method)
  ```javascript
  updateInstructor(index, updates) {
  ```
- **Line 277**: `getInstructors()` (method)
  ```javascript
  getInstructors() {
  ```
- **Line 290**: `addCourse()` (method)
  ```javascript
  addCourse(course) {
  ```
- **Line 304**: `removeCourse()` (method)
  ```javascript
  removeCourse(index) {
  ```
- **Line 320**: `updateCourse()` (method)
  ```javascript
  updateCourse(index, updates) {
  ```
- **Line 336**: `getCourses()` (method)
  ```javascript
  getCourses() {
  ```
- **Line 349**: `addStudent()` (method)
  ```javascript
  addStudent(student) {
  ```
- **Line 363**: `removeStudent()` (method)
  ```javascript
  removeStudent(index) {
  ```
- **Line 379**: `updateStudent()` (method)
  ```javascript
  updateStudent(index, updates) {
  ```
- **Line 395**: `getStudents()` (method)
  ```javascript
  getStudents() {
  ```
- **Line 408**: `isDirty()` (method)
  ```javascript
  isDirty() {
  ```
- **Line 424**: `setLoading()` (method)
  ```javascript
  setLoading(loading) {
  ```
- **Line 433**: `setError()` (method)
  ```javascript
  setError(error) {
  ```

### frontend/js/modules/instructor-tab-handlers.js
**Undocumented Functions**: 22

- **Line 263**: `openAddStudentModal()` (function)
  ```javascript
  function openAddStudentModal() {
  ```
- **Line 292**: `closeAddStudentModal()` (function)
  ```javascript
  function closeAddStudentModal() {
  ```
- **Line 794**: `renderAnalyticsCharts()` (function)
  ```javascript
  function renderAnalyticsCharts(data) {
  ```
- **Line 848**: `destroyExistingCharts()` (function)
  ```javascript
  function destroyExistingCharts() {
  ```
- **Line 881**: `renderEngagementChart()` (function)
  ```javascript
  function renderEngagementChart(data) {
  ```
- **Line 980**: `renderLabCompletionChart()` (function)
  ```javascript
  function renderLabCompletionChart(data) {
  ```
- **Line 1057**: `renderQuizPerformanceChart()` (function)
  ```javascript
  function renderQuizPerformanceChart(data) {
  ```
- **Line 1152**: `renderProgressDistributionChart()` (function)
  ```javascript
  function renderProgressDistributionChart(data) {
  ```
- **Line 1233**: `exportAnalyticsData()` (function)
  ```javascript
  function exportAnalyticsData() {
  ```
- **Line 1256**: `downloadPDFReport()` (function)
  ```javascript
  function downloadPDFReport() {
  ```
- **Line 1627**: `filterPublishedCourses()` (function)
  ```javascript
  function filterPublishedCourses() {
  ```
- **Line 1658**: `createCourseInstance()` (function)
  ```javascript
  function createCourseInstance(courseId) {
  ```
- **Line 1960**: `formatDate()` (function)
  ```javascript
  function formatDate(dateString) {
  ```
- **Line 1985**: `filterInstances()` (function)
  ```javascript
  function filterInstances() {
  ```
- **Line 2019**: `searchInstances()` (function)
  ```javascript
  function searchInstances() {
  ```
- **Line 2054**: `showCreateInstanceModal()` (function)
  ```javascript
  function showCreateInstanceModal() {
  ```
- **Line 2166**: `closeCreateInstanceModal()` (function)
  ```javascript
  function closeCreateInstanceModal() {
  ```
- **Line 2192**: `closeModalOnOutsideClick()` (function)
  ```javascript
  function closeModalOnOutsideClick(event) {
  ```
- **Line 2756**: `regenerateContent()` (function)
  ```javascript
  function regenerateContent() {
  ```
- **Line 2817**: `filterFeedback()` (function)
  ```javascript
  function filterFeedback() {
  ```
- **Line 2857**: `respondToFeedback()` (function)
  ```javascript
  function respondToFeedback(feedbackId) {
  ```
- **Line 2897**: `closeFeedbackResponseModal()` (function)
  ```javascript
  function closeFeedbackResponseModal() {
  ```

### frontend/js/modules/lab-lifecycle.js
**Undocumented Functions**: 22

- **Line 21**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 45**: `initialize()` (method)
  ```javascript
  async initialize(user) {
  ```
- **Line 84**: `loadEnrolledCourses()` (method)
  ```javascript
  async loadEnrolledCourses() {
  ```
- **Line 119**: `initializeUserLabs()` (method)
  ```javascript
  async initializeUserLabs() {
  ```
- **Line 146**: `getOrCreateStudentLab()` (method)
  ```javascript
  async getOrCreateStudentLab(courseId) {
  ```
- **Line 201**: `pollLabStatus()` (method)
  ```javascript
  async pollLabStatus(labId, courseId) {
  ```
- **Line 205**: `checkStatus()` (arrow)
  ```javascript
  const checkStatus = async () => {
  ```
- **Line 252**: `pauseAllLabs()` (method)
  ```javascript
  async pauseAllLabs() {
  ```
- **Line 289**: `resumeAllLabs()` (method)
  ```javascript
  async resumeAllLabs() {
  ```
- **Line 327**: `getLabAccessUrl()` (method)
  ```javascript
  getLabAccessUrl(courseId) {
  ```
- **Line 347**: `isLabReady()` (method)
  ```javascript
  isLabReady(courseId) {
  ```
- **Line 364**: `getLabStatus()` (method)
  ```javascript
  getLabStatus(courseId) {
  ```
- **Line 380**: `startLabHealthChecks()` (method)
  ```javascript
  startLabHealthChecks() {
  ```
- **Line 399**: `stopLabHealthChecks()` (method)
  ```javascript
  stopLabHealthChecks() {
  ```
- **Line 417**: `performLabHealthCheck()` (method)
  ```javascript
  async performLabHealthCheck() {
  ```
- **Line 450**: `setupWindowUnloadHandler()` (method)
  ```javascript
  setupWindowUnloadHandler() {
  ```
- **Line 484**: `quickPauseAllLabs()` (method)
  ```javascript
  async quickPauseAllLabs() {
  ```
- **Line 515**: `cleanup()` (method)
  ```javascript
  async cleanup() {
  ```
- **Line 540**: `updateEnrolledCourses()` (method)
  ```javascript
  async updateEnrolledCourses(courses) {
  ```
- **Line 564**: `accessLab()` (method)
  ```javascript
  async accessLab(courseId) {
  ```
- **Line 599**: `resumeSpecificLab()` (method)
  ```javascript
  async resumeSpecificLab(courseId) {
  ```
- **Line 635**: `updateLabAccess()` (method)
  ```javascript
  async updateLabAccess(labId) {
  ```

### frontend/js/config-global.js
**Undocumented Functions**: 22

- **Line 27**: `detectHost()` (function)
  ```javascript
  function detectHost() {
  ```
- **Line 144**: `USER_BY_EMAIL()` (arrow_method)
  ```javascript
  USER_BY_EMAIL: (email) => `${urls.USER_MANAGEMENT}/users/by-email/${email}`,
  ```
- **Line 152**: `COURSE_BY_ID()` (arrow_method)
  ```javascript
  COURSE_BY_ID: (id) => `${urls.COURSE_MANAGEMENT}/courses/${id}`,
  ```
- **Line 155**: `COURSE_STUDENTS()` (arrow_method)
  ```javascript
  COURSE_STUDENTS: (courseId) => `${urls.COURSE_MANAGEMENT}/instructor/course/${courseId}/students`,
  ```
- **Line 156**: `REMOVE_ENROLLMENT()` (arrow_method)
  ```javascript
  REMOVE_ENROLLMENT: (enrollmentId) => `${urls.COURSE_MANAGEMENT}/instructor/enrollment/${enrollmentId}`,
  ```
- **Line 166**: `SYLLABUS()` (arrow_method)
  ```javascript
  SYLLABUS: (courseId) => `${urls.COURSE_GENERATOR}/syllabus/${courseId}`,
  ```
- **Line 174**: `SLIDES()` (arrow_method)
  ```javascript
  SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/${courseId}`,
  ```
- **Line 175**: `UPDATE_SLIDES()` (arrow_method)
  ```javascript
  UPDATE_SLIDES: (courseId) => `${urls.COURSE_GENERATOR}/slides/update/${courseId}`,
  ```
- **Line 179**: `QUIZZES()` (arrow_method)
  ```javascript
  QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quizzes/${courseId}`,
  ```
- **Line 182**: `QUIZ_GET_COURSE_QUIZZES()` (arrow_method)
  ```javascript
  QUIZ_GET_COURSE_QUIZZES: (courseId) => `${urls.COURSE_GENERATOR}/quiz/course/${courseId}`,
  ```
- **Line 183**: `QUIZ_GET_BY_ID()` (arrow_method)
  ```javascript
  QUIZ_GET_BY_ID: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}`,
  ```
- **Line 184**: `QUIZ_SUBMIT()` (arrow_method)
  ```javascript
  QUIZ_SUBMIT: (quizId) => `${urls.COURSE_GENERATOR}/quiz/${quizId}/submit`,
  ```
- **Line 185**: `QUIZ_ANALYTICS()` (arrow_method)
  ```javascript
  QUIZ_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/quiz/analytics/${courseId}`,
  ```
- **Line 188**: `LAB_BY_COURSE()` (arrow_method)
  ```javascript
  LAB_BY_COURSE: (courseId) => `${urls.COURSE_GENERATOR}/lab/${courseId}`,
  ```
- **Line 190**: `LAB_STOP()` (arrow_method)
  ```javascript
  LAB_STOP: (courseId) => `${urls.COURSE_GENERATOR}/lab/stop/${courseId}`,
  ```
- **Line 191**: `LAB_ACCESS()` (arrow_method)
  ```javascript
  LAB_ACCESS: (courseId) => `${urls.COURSE_GENERATOR}/lab/access/${courseId}`,
  ```
- **Line 194**: `LAB_ANALYTICS()` (arrow_method)
  ```javascript
  LAB_ANALYTICS: (courseId) => `${urls.COURSE_GENERATOR}/lab/analytics/${courseId}`,
  ```
- **Line 197**: `EXERCISES()` (arrow_method)
  ```javascript
  EXERCISES: (courseId) => `${urls.COURSE_GENERATOR}/exercises/${courseId}`,
  ```
- **Line 202**: `LAB_SESSION_LOAD()` (arrow_method)
  ```javascript
  LAB_SESSION_LOAD: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,
  ```
- **Line 203**: `LAB_SESSION_CLEAR()` (arrow_method)
  ```javascript
  LAB_SESSION_CLEAR: (courseId, studentId) => `${urls.COURSE_GENERATOR}/lab/session/${courseId}/${studentId}`,
  ```
- **Line 211**: `COURSES_BY_STATUS()` (arrow_method)
  ```javascript
  COURSES_BY_STATUS: (status) => `https://localhost:8004/courses?status=${status}`,
  ```
- **Line 212**: `INSTRUCTOR_INSTANCES()` (arrow_method)
  ```javascript
  INSTRUCTOR_INSTANCES: (instructorId) => `https://localhost:8004/course-instances?instructor_id=${instructorId}`,
  ```

### frontend/js/modules/asset-cache.js
**Undocumented Functions**: 21

- **Line 34**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 89**: `_initializeAssetCaching()` (method)
  ```javascript
  async _initializeAssetCaching() {
  ```
- **Line 133**: `_registerServiceWorker()` (method)
  ```javascript
  async _registerServiceWorker() {
  ```
- **Line 201**: `_defineCriticalAssets()` (method)
  ```javascript
  _defineCriticalAssets() {
  ```
- **Line 247**: `_setupAssetVersioning()` (method)
  ```javascript
  async _setupAssetVersioning() {
  ```
- **Line 288**: `_initializePreloading()` (method)
  ```javascript
  _initializePreloading() {
  ```
- **Line 315**: `_preloadCriticalAssets()` (method)
  ```javascript
  async _preloadCriticalAssets() {
  ```
- **Line 349**: `_preloadAsset()` (method)
  ```javascript
  async _preloadAsset(url, options = {}) {
  ```
- **Line 398**: `_performAssetPreload()` (method)
  ```javascript
  async _performAssetPreload(url, options = {}) {
  ```
- **Line 453**: `_fetchWithRetry()` (method)
  ```javascript
  async _fetchWithRetry(url, options = {}, retries = 3) {
  ```
- **Line 487**: `_getFromCache()` (method)
  ```javascript
  async _getFromCache(url) {
  ```
- **Line 534**: `_cacheResponse()` (method)
  ```javascript
  async _cacheResponse(url, response) {
  ```
- **Line 575**: `_setupIntelligentPreloading()` (method)
  ```javascript
  _setupIntelligentPreloading() {
  ```
- **Line 602**: `_setupNavigationBasedPreloading()` (method)
  ```javascript
  _setupNavigationBasedPreloading() {
  ```
- **Line 633**: `_setupRoleBasedPreloading()` (method)
  ```javascript
  async _setupRoleBasedPreloading() {
  ```
- **Line 677**: `_setupPatternBasedPreloading()` (method)
  ```javascript
  _setupPatternBasedPreloading() {
  ```
- **Line 725**: `_setupLazyLoading()` (method)
  ```javascript
  _setupLazyLoading() {
  ```
- **Line 786**: `_loadLazyImage()` (method)
  ```javascript
  async _loadLazyImage(img, src) {
  ```
- **Line 843**: `_setupHoverPrefetch()` (method)
  ```javascript
  _setupHoverPrefetch() {
  ```
- **Line 913**: `handler()` (arrow_method)
  ```javascript
  handler: () => window.location.reload()
  ```
- **Line 917**: `handler()` (arrow_method)
  ```javascript
  handler: () => {} // Dismiss notification
  ```

### frontend/js/modules/projects/project-controller.js
**Undocumented Functions**: 18

- **Line 46**: `constructor()` (method)
  ```javascript
  constructor(projectStore, projectUI, projectAPI, notificationService) {
  ```
- **Line 93**: `initialize()` (method)
  ```javascript
  async initialize(organizationId) {
  ```
- **Line 110**: `initializeStateSubscriptions()` (method)
  ```javascript
  initializeStateSubscriptions() {
  ```
- **Line 156**: `initializeUIEventListeners()` (method)
  ```javascript
  initializeUIEventListeners() {
  ```
- **Line 180**: `loadProjects()` (method)
  ```javascript
  async loadProjects(filters = {}) {
  ```
- **Line 220**: `filterByStatus()` (method)
  ```javascript
  async filterByStatus(status, refetch = false) {
  ```
- **Line 234**: `search()` (method)
  ```javascript
  async search(searchTerm, refetch = false) {
  ```
- **Line 254**: `viewProject()` (method)
  ```javascript
  async viewProject(projectId) {
  ```
- **Line 286**: `showCreateProjectModal()` (method)
  ```javascript
  showCreateProjectModal() {
  ```
- **Line 301**: `createProject()` (method)
  ```javascript
  async createProject(projectData) {
  ```
- **Line 347**: `editProject()` (method)
  ```javascript
  async editProject(projectId) {
  ```
- **Line 375**: `updateProject()` (method)
  ```javascript
  async updateProject(projectId, updates) {
  ```
- **Line 422**: `deleteProjectPrompt()` (method)
  ```javascript
  deleteProjectPrompt(projectId) {
  ```
- **Line 442**: `deleteProject()` (method)
  ```javascript
  async deleteProject(projectId) {
  ```
- **Line 487**: `manageMembers()` (method)
  ```javascript
  async manageMembers(projectId) {
  ```
- **Line 535**: `on()` (method)
  ```javascript
  on(event, callback) {
  ```
- **Line 555**: `emit()` (method)
  ```javascript
  emit(event, ...args) {
  ```
- **Line 577**: `destroy()` (method)
  ```javascript
  destroy() {
  ```

### frontend/js/project-dashboard.js
**Undocumented Functions**: 18

- **Line 195**: `updateProjectDisplay()` (function)
  ```javascript
  function updateProjectDisplay() {
  ```
- **Line 221**: `calculateProjectProgress()` (function)
  ```javascript
  function calculateProjectProgress() {
  ```
- **Line 258**: `setupTabNavigation()` (function)
  ```javascript
  function setupTabNavigation() {
  ```
- **Line 330**: `displayTracksOverview()` (function)
  ```javascript
  function displayTracksOverview(tracks) {
  ```
- **Line 421**: `displayModulesList()` (function)
  ```javascript
  function displayModulesList(modules) {
  ```
- **Line 523**: `setupEventListeners()` (function)
  ```javascript
  function setupEventListeners() {
  ```
- **Line 530**: `showCreateTrackModal()` (function)
  ```javascript
  function showCreateTrackModal() {
  ```
- **Line 577**: `showCreateModuleModal()` (function)
  ```javascript
  function showCreateModuleModal(trackId = null) {
  ```
- **Line 661**: `closeModal()` (function)
  ```javascript
  function closeModal(modalId) {
  ```
- **Line 708**: `viewModule()` (function)
  ```javascript
  function viewModule(moduleId) {
  ```
- **Line 712**: `editModule()` (function)
  ```javascript
  function editModule(moduleId) {
  ```
- **Line 716**: `editTrack()` (function)
  ```javascript
  function editTrack(trackId) {
  ```
- **Line 720**: `manageTrackContent()` (function)
  ```javascript
  function manageTrackContent(trackId) {
  ```
- **Line 724**: `editProject()` (function)
  ```javascript
  function editProject() {
  ```
- **Line 756**: `manageParticipants()` (function)
  ```javascript
  function manageParticipants() {
  ```
- **Line 761**: `showLoadingSpinner()` (function)
  ```javascript
  function showLoadingSpinner() {
  ```
- **Line 765**: `hideLoadingSpinner()` (function)
  ```javascript
  function hideLoadingSpinner() {
  ```
- **Line 770**: `getMockProjectTracks()` (function)
  ```javascript
  function getMockProjectTracks() {
  ```

### frontend/js/password-change.js
**Undocumented Functions**: 17

- **Line 40**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 48**: `init()` (method)
  ```javascript
  init() {
  ```
- **Line 57**: `initializeEventListeners()` (method)
  ```javascript
  initializeEventListeners() {
  ```
- **Line 71**: `initializePasswordFields()` (method)
  ```javascript
  initializePasswordFields() {
  ```
- **Line 92**: `initializeValidation()` (method)
  ```javascript
  initializeValidation() {
  ```
- **Line 99**: `checkPasswordStrength()` (method)
  ```javascript
  checkPasswordStrength(password) {
  ```
- **Line 149**: `calculatePasswordStrength()` (method)
  ```javascript
  calculatePasswordStrength(password) {
  ```
- **Line 183**: `validatePasswordMatch()` (method)
  ```javascript
  validatePasswordMatch() {
  ```
- **Line 210**: `validateField()` (method)
  ```javascript
  validateField(field) {
  ```
- **Line 267**: `validateForm()` (method)
  ```javascript
  validateForm() {
  ```
- **Line 290**: `handleSubmit()` (method)
  ```javascript
  async handleSubmit(event) {
  ```
- **Line 350**: `getAuthToken()` (method)
  ```javascript
  getAuthToken() {
  ```
- **Line 359**: `showSuccess()` (method)
  ```javascript
  showSuccess(data) {
  ```
- **Line 377**: `showFieldError()` (method)
  ```javascript
  showFieldError(fieldId, message) {
  ```
- **Line 388**: `clearFieldError()` (method)
  ```javascript
  clearFieldError(fieldId) {
  ```
- **Line 399**: `showGeneralError()` (method)
  ```javascript
  showGeneralError(message) {
  ```
- **Line 429**: `setSubmitLoading()` (method)
  ```javascript
  setSubmitLoading(loading) {
  ```

### frontend/js/modules/projects/services/project-api-service.js
**Undocumented Functions**: 16

- **Line 58**: `constructor()` (method)
  ```javascript
  constructor(organizationId) {
  ```
- **Line 81**: `setOrganizationId()` (method)
  ```javascript
  setOrganizationId(organizationId) {
  ```
- **Line 106**: `fetchProjects()` (method)
  ```javascript
  async fetchProjects(filters = {}) {
  ```
- **Line 142**: `createProject()` (method)
  ```javascript
  async createProject(projectData) {
  ```
- **Line 177**: `updateProject()` (method)
  ```javascript
  async updateProject(projectId, updates) {
  ```
- **Line 208**: `deleteProject()` (method)
  ```javascript
  async deleteProject(projectId) {
  ```
- **Line 240**: `fetchProjectMembers()` (method)
  ```javascript
  async fetchProjectMembers(projectId) {
  ```
- **Line 274**: `addInstructor()` (method)
  ```javascript
  async addInstructor(instructorData) {
  ```
- **Line 303**: `addStudent()` (method)
  ```javascript
  async addStudent(studentData) {
  ```
- **Line 332**: `removeMember()` (method)
  ```javascript
  async removeMember(userId) {
  ```
- **Line 369**: `createTrack()` (method)
  ```javascript
  async createTrack(trackData) {
  ```
- **Line 403**: `batchCreateTracks()` (method)
  ```javascript
  async batchCreateTracks(projectId, tracksData) {
  ```
- **Line 454**: `initializeAIForProject()` (method)
  ```javascript
  initializeAIForProject(projectContext) {
  ```
- **Line 483**: `getAISuggestions()` (method)
  ```javascript
  async getAISuggestions(prompt, options = {}) {
  ```
- **Line 507**: `getOrganizationId()` (method)
  ```javascript
  getOrganizationId() {
  ```
- **Line 522**: `validateProjectData()` (method)
  ```javascript
  validateProjectData(projectData) {
  ```

### frontend/js/modules/slideshow.js
**Undocumented Functions**: 15

- **Line 15**: `constructor()` (method)
  ```javascript
  constructor(containerSelector) {
  ```
- **Line 48**: `init()` (method)
  ```javascript
  init() {
  ```
- **Line 69**: `setupEventListeners()` (method)
  ```javascript
  setupEventListeners() {
  ```
- **Line 100**: `setupIntersectionObserver()` (method)
  ```javascript
  setupIntersectionObserver() {
  ```
- **Line 133**: `prevSlide()` (method)
  ```javascript
  prevSlide() {
  ```
- **Line 138**: `goToSlide()` (method)
  ```javascript
  goToSlide(index) {
  ```
- **Line 149**: `updateSlideshow()` (method)
  ```javascript
  updateSlideshow() {
  ```
- **Line 172**: `pauseAutoplay()` (method)
  ```javascript
  pauseAutoplay() {
  ```
- **Line 180**: `resumeAutoplay()` (method)
  ```javascript
  resumeAutoplay() {
  ```
- **Line 186**: `toggleAutoplay()` (method)
  ```javascript
  toggleAutoplay() {
  ```
- **Line 202**: `handleTouchEnd()` (method)
  ```javascript
  handleTouchEnd(e) {
  ```
- **Line 207**: `handleSwipeGesture()` (method)
  ```javascript
  handleSwipeGesture() {
  ```
- **Line 260**: `getTotalSlides()` (method)
  ```javascript
  getTotalSlides() {
  ```
- **Line 264**: `isAutoplayActive()` (method)
  ```javascript
  isAutoplayActive() {
  ```
- **Line 268**: `setAutoplayDelay()` (method)
  ```javascript
  setAutoplayDelay(delay) {
  ```

### frontend/js/modules/app.js
**Undocumented Functions**: 15

- **Line 40**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 67**: `getCurrentPage()` (method)
  ```javascript
  getCurrentPage() {
  ```
- **Line 89**: `init()` (method)
  ```javascript
  async init() {
  ```
- **Line 163**: `setupGlobalHandlers()` (method)
  ```javascript
  setupGlobalHandlers() {
  ```
- **Line 206**: `handleGlobalError()` (method)
  ```javascript
  handleGlobalError(event) {
  ```
- **Line 253**: `handleUnhandledRejection()` (method)
  ```javascript
  handleUnhandledRejection(event) {
  ```
- **Line 288**: `logError()` (method)
  ```javascript
  logError(type, details) {
  ```
- **Line 323**: `setupAuthEventListeners()` (method)
  ```javascript
  setupAuthEventListeners() {
  ```
- **Line 325**: `attachListeners()` (arrow)
  ```javascript
  const attachListeners = () => {
  ```
- **Line 453**: `setupGlobalExports()` (method)
  ```javascript
  setupGlobalExports() {
  ```
- **Line 679**: `initializePage()` (method)
  ```javascript
  initializePage() {
  ```
- **Line 719**: `requiresAuth()` (method)
  ```javascript
  requiresAuth() {
  ```
- **Line 743**: `getState()` (method)
  ```javascript
  getState() {
  ```
- **Line 762**: `_initializePerformanceOptimizations()` (method)
  ```javascript
  async _initializePerformanceOptimizations() {
  ```
- **Line 792**: `_preloadPageAssets()` (method)
  ```javascript
  async _preloadPageAssets() {
  ```

### frontend/js/modules/projects/ui/project-list-renderer.js
**Undocumented Functions**: 15

- **Line 46**: `constructor()` (method)
  ```javascript
  constructor(container) {
  ```
- **Line 75**: `initializeEventDelegation()` (method)
  ```javascript
  initializeEventDelegation() {
  ```
- **Line 104**: `render()` (method)
  ```javascript
  render(projects) {
  ```
- **Line 132**: `renderTableHeader()` (method)
  ```javascript
  renderTableHeader() {
  ```
- **Line 153**: `renderTableBody()` (method)
  ```javascript
  renderTableBody(projects) {
  ```
- **Line 177**: `renderProjectRow()` (method)
  ```javascript
  renderProjectRow(project) {
  ```
- **Line 225**: `renderStatusBadge()` (method)
  ```javascript
  renderStatusBadge(status) {
  ```
- **Line 250**: `renderActionButtons()` (method)
  ```javascript
  renderActionButtons(projectId) {
  ```
- **Line 297**: `renderEmpty()` (method)
  ```javascript
  renderEmpty() {
  ```
- **Line 319**: `renderLoading()` (method)
  ```javascript
  renderLoading() {
  ```
- **Line 336**: `renderError()` (method)
  ```javascript
  renderError(errorMessage) {
  ```
- **Line 373**: `on()` (method)
  ```javascript
  on(event, callback) {
  ```
- **Line 397**: `emit()` (method)
  ```javascript
  emit(event, ...args) {
  ```
- **Line 420**: `truncate()` (method)
  ```javascript
  truncate(text, maxLength) {
  ```
- **Line 433**: `clear()` (method)
  ```javascript
  clear() {
  ```

### frontend/js/modules/projects/state/project-store.js
**Undocumented Functions**: 15

- **Line 98**: `setState()` (method)
  ```javascript
  setState(updates) {
  ```
- **Line 119**: `getState()` (method)
  ```javascript
  getState() {
  ```
- **Line 141**: `subscribe()` (method)
  ```javascript
  subscribe(callback) {
  ```
- **Line 160**: `notify()` (method)
  ```javascript
  notify(oldState, newState) {
  ```
- **Line 183**: `setProjects()` (method)
  ```javascript
  setProjects(projects) {
  ```
- **Line 197**: `setCurrentProject()` (method)
  ```javascript
  setCurrentProject(project) {
  ```
- **Line 209**: `setCurrentProjectId()` (method)
  ```javascript
  setCurrentProjectId(projectId) {
  ```
- **Line 220**: `setMembers()` (method)
  ```javascript
  setMembers(members) {
  ```
- **Line 229**: `setFilters()` (method)
  ```javascript
  setFilters(filters) {
  ```
- **Line 243**: `setLoading()` (method)
  ```javascript
  setLoading(loading) {
  ```
- **Line 256**: `setError()` (method)
  ```javascript
  setError(error) {
  ```
- **Line 276**: `reset()` (method)
  ```javascript
  reset() {
  ```
- **Line 308**: `calculateStats()` (method)
  ```javascript
  calculateStats(projects) {
  ```
- **Line 327**: `getFilteredProjects()` (method)
  ```javascript
  getFilteredProjects() {
  ```
- **Line 353**: `getProjectById()` (method)
  ```javascript
  getProjectById(projectId) {
  ```

### frontend/js/accessibility-manager.js
**Undocumented Functions**: 15

- **Line 15**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 40**: `detectInputMethod()` (method)
  ```javascript
  detectInputMethod() {
  ```
- **Line 121**: `announce()` (method)
  ```javascript
  announce(message, priority = 'polite') {
  ```
- **Line 161**: `trapFocusInModal()` (method)
  ```javascript
  trapFocusInModal(modal) {
  ```
- **Line 181**: `trapFocus()` (arrow)
  ```javascript
  const trapFocus = (e) => {
  ```
- **Line 198**: `handleEscape()` (arrow)
  ```javascript
  const handleEscape = (e) => {
  ```
- **Line 216**: `closeModal()` (method)
  ```javascript
  closeModal(modal) {
  ```
- **Line 300**: `selectTab()` (method)
  ```javascript
  selectTab(selectedTab) {
  ```
- **Line 351**: `validateField()` (method)
  ```javascript
  validateField(field) {
  ```
- **Line 383**: `showFieldError()` (method)
  ```javascript
  showFieldError(field, message) {
  ```
- **Line 409**: `clearFieldError()` (method)
  ```javascript
  clearFieldError(field) {
  ```
- **Line 427**: `getFieldLabel()` (method)
  ```javascript
  getFieldLabel(field) {
  ```
- **Line 437**: `isValidEmail()` (method)
  ```javascript
  isValidEmail(email) {
  ```
- **Line 468**: `showButtonLoading()` (method)
  ```javascript
  showButtonLoading(button, message = 'Loading...') {
  ```
- **Line 482**: `hideButtonLoading()` (method)
  ```javascript
  hideButtonLoading(button) {
  ```

### frontend/js/admin.js
**Undocumented Functions**: 14

- **Line 81**: `handleAuthError()` (function)
  ```javascript
  function handleAuthError(response) {
  ```
- **Line 123**: `getCurrentUser()` (function)
  ```javascript
  function getCurrentUser() {
  ```
- **Line 163**: `validateAdminSession()` (function)
  ```javascript
  function validateAdminSession() {
  ```
- **Line 249**: `showSection()` (function)
  ```javascript
  function showSection(sectionId) {
  ```
- **Line 294**: `showAlert()` (function)
  ```javascript
  function showAlert(message, type = 'success') {
  ```
- **Line 418**: `displayUsers()` (function)
  ```javascript
  function displayUsers(users) {
  ```
- **Line 444**: `refreshUsers()` (function)
  ```javascript
  function refreshUsers() {
  ```
- **Line 485**: `closeModal()` (function)
  ```javascript
  function closeModal() {
  ```
- **Line 620**: `logout()` (function)
  ```javascript
  function logout() {
  ```
- **Line 627**: `toggleSelectAll()` (function)
  ```javascript
  function toggleSelectAll() {
  ```
- **Line 638**: `updateBulkActions()` (function)
  ```javascript
  function updateBulkActions() {
  ```
- **Line 738**: `filterUsers()` (function)
  ```javascript
  function filterUsers() {
  ```
- **Line 803**: `updateFilterResults()` (function)
  ```javascript
  function updateFilterResults(filteredCount, totalCount) {
  ```
- **Line 813**: `clearFilters()` (function)
  ```javascript
  function clearFilters() {
  ```

### frontend/js/knowledge-graph-client.js
**Undocumented Functions**: 13

- **Line 15**: `constructor()` (method)
  ```javascript
  constructor(baseUrl = 'https://localhost:8012/api/v1/graph') {
  ```
- **Line 29**: `getGraphVisualization()` (method)
  ```javascript
  async getGraphVisualization(filters = {}) {
  ```
- **Line 66**: `findLearningPath()` (method)
  ```javascript
  async findLearningPath(startCourseId, endCourseId, studentId = null, optimization = 'shortest') {
  ```
- **Line 107**: `checkPrerequisites()` (method)
  ```javascript
  async checkPrerequisites(courseId, studentId) {
  ```
- **Line 149**: `getNeighbors()` (method)
  ```javascript
  async getNeighbors(nodeId, edgeTypes = null, depth = 1, direction = 'both') {
  ```
- **Line 183**: `getConceptMap()` (method)
  ```javascript
  async getConceptMap(topicId = null, depth = 3) {
  ```
- **Line 220**: `getSkillProgression()` (method)
  ```javascript
  async getSkillProgression(studentId, targetSkills = null) {
  ```
- **Line 256**: `getRelatedCourses()` (method)
  ```javascript
  async getRelatedCourses(courseId, relationshipTypes = ['similar_to', 'alternative_to'], limit = 5) {
  ```
- **Line 290**: `searchNodes()` (method)
  ```javascript
  async searchNodes(query, nodeTypes = null, limit = 20) {
  ```
- **Line 320**: `getGraphStatistics()` (method)
  ```javascript
  async getGraphStatistics() {
  ```
- **Line 427**: `_getFromCache()` (method)
  ```javascript
  _getFromCache(key) {
  ```
- **Line 440**: `_setCache()` (method)
  ```javascript
  _setCache(key, data) {
  ```
- **Line 447**: `clearCache()` (method)
  ```javascript
  clearCache() {
  ```

### frontend/js/modules/course-video-manager.js
**Undocumented Functions**: 12

- **Line 25**: `initializeVideoManager()` (function)
  ```javascript
  function initializeVideoManager() {
  ```
- **Line 51**: `openVideoModal()` (function)
  ```javascript
  function openVideoModal(modalId) {
  ```
- **Line 68**: `closeVideoModal()` (function)
  ```javascript
  function closeVideoModal(modalId) {
  ```
- **Line 165**: `handleVideoLink()` (function)
  ```javascript
  function handleVideoLink() {
  ```
- **Line 224**: `renderVideosList()` (function)
  ```javascript
  function renderVideosList() {
  ```
- **Line 268**: `getVideoIcon()` (function)
  ```javascript
  function getVideoIcon(videoType) {
  ```
- **Line 289**: `getVideoMeta()` (function)
  ```javascript
  function getVideoMeta(video) {
  ```
- **Line 303**: `removeVideo()` (function)
  ```javascript
  function removeVideo(videoId) {
  ```
- **Line 324**: `generateTempId()` (function)
  ```javascript
  function generateTempId() {
  ```
- **Line 334**: `escapeHtml()` (function)
  ```javascript
  function escapeHtml(text) {
  ```
- **Line 471**: `clearCourseVideos()` (function)
  ```javascript
  function clearCourseVideos() {
  ```
- **Line 482**: `getCourseVideos()` (arrow_method)
  ```javascript
  getCourseVideos: () => courseVideos
  ```

### frontend/js/metadata-client.js
**Undocumented Functions**: 12

- **Line 15**: `constructor()` (method)
  ```javascript
  constructor(baseUrl = 'https://localhost:8011/api/v1/metadata') {
  ```
- **Line 30**: `search()` (method)
  ```javascript
  async search(query, options = {}) {
  ```
- **Line 87**: `searchFuzzy()` (method)
  ```javascript
  async searchFuzzy(query, options = {}) {
  ```
- **Line 135**: `getRecommendations()` (method)
  ```javascript
  async getRecommendations(completedCourseIds, options = {}) {
  ```
- **Line 181**: `getRelatedContent()` (method)
  ```javascript
  async getRelatedContent(entityId, entityType, options = {}) {
  ```
- **Line 217**: `getByTags()` (method)
  ```javascript
  async getByTags(tags, options = {}) {
  ```
- **Line 354**: `getPopularTags()` (method)
  ```javascript
  async getPopularTags(entityType = 'course', limit = 20) {
  ```
- **Line 389**: `buildLearningPath()` (method)
  ```javascript
  async buildLearningPath(topic, options = {}) {
  ```
- **Line 429**: `_getFromCache()` (method)
  ```javascript
  _getFromCache(key) {
  ```
- **Line 442**: `_setCache()` (method)
  ```javascript
  _setCache(key, data) {
  ```
- **Line 449**: `_invalidateEntityCache()` (method)
  ```javascript
  _invalidateEntityCache(entityId, entityType) {
  ```
- **Line 454**: `clearCache()` (method)
  ```javascript
  clearCache() {
  ```

### frontend/js/modules/navigation.js
**Undocumented Functions**: 11

- **Line 35**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 49**: `getCurrentPage()` (method)
  ```javascript
  getCurrentPage() {
  ```
- **Line 71**: `setupEventListeners()` (method)
  ```javascript
  setupEventListeners() {
  ```
- **Line 93**: `handleHashNavigation()` (method)
  ```javascript
  handleHashNavigation() {
  ```
- **Line 112**: `routeToSection()` (method)
  ```javascript
  routeToSection(hash) {
  ```
- **Line 430**: `showRegister()` (method)
  ```javascript
  showRegister() {
  ```
- **Line 645**: `showInstructorRegistration()` (method)
  ```javascript
  showInstructorRegistration() {
  ```
- **Line 836**: `checkPasswordMatch()` (arrow)
  ```javascript
  const checkPasswordMatch = () => {
  ```
- **Line 898**: `setupInstructorRegistrationForm()` (method)
  ```javascript
  setupInstructorRegistrationForm() {
  ```
- **Line 941**: `checkPasswordMatch()` (arrow)
  ```javascript
  const checkPasswordMatch = () => {
  ```
- **Line 1012**: `loadAvailableOrganizations()` (method)
  ```javascript
  async loadAvailableOrganizations() {
  ```

### frontend/js/modules/session-manager.js
**Undocumented Functions**: 11

- **Line 69**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 96**: `init()` (method)
  ```javascript
  init() {
  ```
- **Line 134**: `setupActivityListeners()` (method)
  ```javascript
  setupActivityListeners() {
  ```
- **Line 160**: `onUserActivity()` (method)
  ```javascript
  onUserActivity() {
  ```
- **Line 188**: `updateActivity()` (method)
  ```javascript
  updateActivity() {
  ```
- **Line 213**: `resetTimeout()` (method)
  ```javascript
  resetTimeout() {
  ```
- **Line 254**: `showWarning()` (method)
  ```javascript
  showWarning() {
  ```
- **Line 341**: `hideWarning()` (method)
  ```javascript
  hideWarning() {
  ```
- **Line 369**: `checkExistingSession()` (method)
  ```javascript
  checkExistingSession() {
  ```
- **Line 405**: `logout()` (method)
  ```javascript
  logout() {
  ```
- **Line 444**: `endSession()` (method)
  ```javascript
  endSession() {
  ```

### frontend/js/modules/org-admin-settings.js
**Undocumented Functions**: 11

- **Line 57**: `setupFormHandlers()` (function)
  ```javascript
  function setupFormHandlers() {
  ```
- **Line 127**: `populateOrganizationProfileForm()` (function)
  ```javascript
  function populateOrganizationProfileForm(org) {
  ```
- **Line 190**: `populateContactInformationForm()` (function)
  ```javascript
  function populateContactInformationForm(org) {
  ```
- **Line 260**: `populateBrandingSettings()` (function)
  ```javascript
  function populateBrandingSettings(org) {
  ```
- **Line 297**: `populatePreferences()` (function)
  ```javascript
  function populatePreferences(org) {
  ```
- **Line 501**: `onUploadStart()` (arrow_method)
  ```javascript
  onUploadStart: () => {
  ```
- **Line 505**: `onUploadProgress()` (arrow_method)
  ```javascript
  onUploadProgress: (percent, file) => {
  ```
- **Line 509**: `onUploadComplete()` (arrow_method)
  ```javascript
  onUploadComplete: async (response, file) => {
  ```
- **Line 523**: `onUploadError()` (arrow_method)
  ```javascript
  onUploadError: (error) => {
  ```
- **Line 543**: `setupFallbackLogoUpload()` (function)
  ```javascript
  function setupFallbackLogoUpload() {
  ```
- **Line 603**: `displayLogoPreview()` (function)
  ```javascript
  function displayLogoPreview(logoUrl) {
  ```

### frontend/js/modules/projects/index.js
**Undocumented Functions**: 11

- **Line 80**: `initialize()` (arrow_method)
  ```javascript
  initialize: (organizationId) => projectController.initialize(organizationId),
  ```
- **Line 88**: `loadProjects()` (arrow_method)
  ```javascript
  loadProjects: (filters) => projectController.loadProjects(filters),
  ```
- **Line 97**: `filterByStatus()` (arrow_method)
  ```javascript
  filterByStatus: (status, refetch) => projectController.filterByStatus(status, refetch),
  ```
- **Line 106**: `search()` (arrow_method)
  ```javascript
  search: (searchTerm, refetch) => projectController.search(searchTerm, refetch),
  ```
- **Line 114**: `createProject()` (arrow_method)
  ```javascript
  createProject: (projectData) => projectController.createProject(projectData),
  ```
- **Line 123**: `updateProject()` (arrow_method)
  ```javascript
  updateProject: (projectId, updates) => projectController.updateProject(projectId, updates),
  ```
- **Line 131**: `deleteProject()` (arrow_method)
  ```javascript
  deleteProject: (projectId) => projectController.deleteProject(projectId),
  ```
- **Line 140**: `on()` (arrow_method)
  ```javascript
  on: (event, callback) => projectController.on(event, callback),
  ```
- **Line 147**: `getState()` (arrow_method)
  ```javascript
  getState: () => projectStore.getState(),
  ```
- **Line 154**: `destroy()` (arrow_method)
  ```javascript
  destroy: () => projectController.destroy()
  ```
- **Line 175**: `constructor()` (method)
  ```javascript
  constructor(config) {
  ```

### frontend/js/modules/activity-tracker.js
**Undocumented Functions**: 10

- **Line 41**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 92**: `trackActivity()` (method)
  ```javascript
  trackActivity() {
  ```
- **Line 126**: `start()` (method)
  ```javascript
  start() {
  ```
- **Line 176**: `stop()` (method)
  ```javascript
  stop() {
  ```
- **Line 231**: `checkActivity()` (method)
  ```javascript
  checkActivity() {
  ```
- **Line 282**: `showSessionWarning()` (method)
  ```javascript
  showSessionWarning() {
  ```
- **Line 410**: `handleTimeout()` (method)
  ```javascript
  handleTimeout() {
  ```
- **Line 452**: `getTimeUntilTimeout()` (method)
  ```javascript
  getTimeUntilTimeout() {
  ```
- **Line 478**: `shouldShowWarning()` (method)
  ```javascript
  shouldShowWarning() {
  ```
- **Line 499**: `resetTimer()` (method)
  ```javascript
  resetTimer() {
  ```

### frontend/js/modules/projects/wizard/index.js
**Undocumented Functions**: 10

- **Line 73**: `open()` (arrow_method)
  ```javascript
  open: (organizationId) => wizardController.openWizard(organizationId),
  ```
- **Line 80**: `close()` (arrow_method)
  ```javascript
  close: () => wizardController.closeWizard(),
  ```
- **Line 87**: `nextStep()` (arrow_method)
  ```javascript
  nextStep: () => wizardController.nextStep(),
  ```
- **Line 94**: `previousStep()` (arrow_method)
  ```javascript
  previousStep: () => wizardController.previousStep(),
  ```
- **Line 102**: `goToStep()` (arrow_method)
  ```javascript
  goToStep: (stepNumber) => wizardController.goToStep(stepNumber),
  ```
- **Line 109**: `submit()` (arrow_method)
  ```javascript
  submit: () => wizardController.submitProject(),
  ```
- **Line 116**: `getState()` (arrow_method)
  ```javascript
  getState: () => wizardState.getState(),
  ```
- **Line 133**: `on()` (arrow_method)
  ```javascript
  on: (event, callback) => {
  ```
- **Line 143**: `destroy()` (arrow_method)
  ```javascript
  destroy: () => wizardController.destroy()
  ```
- **Line 165**: `constructor()` (method)
  ```javascript
  constructor(dependencies) {
  ```

### frontend/js/lab-refactored.js
**Undocumented Functions**: 9

- **Line 49**: `setupLabEventHandlers()` (function)
  ```javascript
  function setupLabEventHandlers() {
  ```
- **Line 82**: `updateExercisesList()` (function)
  ```javascript
  function updateExercisesList(exercises) {
  ```
- **Line 94**: `createExerciseElement()` (function)
  ```javascript
  function createExerciseElement(exercise) {
  ```
- **Line 121**: `displayExercise()` (function)
  ```javascript
  function displayExercise(exercise) {
  ```
- **Line 152**: `displayTerminalOutput()` (function)
  ```javascript
  function displayTerminalOutput(output, command) {
  ```
- **Line 178**: `updatePanelButton()` (function)
  ```javascript
  function updatePanelButton(panelName, visible) {
  ```
- **Line 186**: `updateProgressDisplay()` (function)
  ```javascript
  function updateProgressDisplay() {
  ```
- **Line 269**: `formatTime()` (function)
  ```javascript
  function formatTime(milliseconds) {
  ```
- **Line 283**: `handleExerciseSubmission()` (function)
  ```javascript
  function handleExerciseSubmission(data) {
  ```

### frontend/js/modules/projects/wizard/track-management/index.js
**Undocumented Functions**: 8

- **Line 82**: `openTrackModal()` (arrow_method)
  ```javascript
  openTrackModal: (track, trackIndex) =>
  ```
- **Line 91**: `closeTrackModal()` (arrow_method)
  ```javascript
  closeTrackModal: (force) =>
  ```
- **Line 99**: `getTrack()` (arrow_method)
  ```javascript
  getTrack: () => trackState.getTrack(),
  ```
- **Line 106**: `getState()` (arrow_method)
  ```javascript
  getState: () => trackState.getState(),
  ```
- **Line 113**: `isDirty()` (arrow_method)
  ```javascript
  isDirty: () => trackState.isDirty(),
  ```
- **Line 136**: `on()` (arrow_method)
  ```javascript
  on: (eventName, callback) => trackController.on(eventName, callback),
  ```
- **Line 143**: `destroy()` (arrow_method)
  ```javascript
  destroy: () => trackController.destroy()
  ```
- **Line 165**: `constructor()` (method)
  ```javascript
  constructor(dependencies) {
  ```

### frontend/js/modules/drag-drop-upload.js
**Undocumented Functions**: 7

- **Line 22**: `constructor()` (method)
  ```javascript
  constructor(dropZone, options = {}) {
  ```
- **Line 136**: `handleDrop()` (method)
  ```javascript
  handleDrop(e) {
  ```
- **Line 147**: `handleFiles()` (method)
  ```javascript
  async handleFiles(files) {
  ```
- **Line 170**: `validateFile()` (method)
  ```javascript
  validateFile(file) {
  ```
- **Line 203**: `uploadFile()` (method)
  ```javascript
  async uploadFile(file) {
  ```
- **Line 267**: `updateProgress()` (method)
  ```javascript
  updateProgress(percent, filename) {
  ```
- **Line 295**: `formatAcceptedTypes()` (method)
  ```javascript
  formatAcceptedTypes() {
  ```

### frontend/js/modules/org-admin-projects.js
**Undocumented Functions**: 7

- **Line 109**: `renderProjectsTable()` (function)
  ```javascript
  function renderProjectsTable(projects) {
  ```
- **Line 158**: `updateProjectsStats()` (function)
  ```javascript
  function updateProjectsStats(projects) {
  ```
- **Line 310**: `showProjectStep()` (function)
  ```javascript
  function showProjectStep(stepNumber) {
  ```
- **Line 482**: `collectWizardData()` (function)
  ```javascript
  function collectWizardData() {
  ```
- **Line 704**: `populateSelectedRolesSummary()` (function)
  ```javascript
  function populateSelectedRolesSummary() {
  ```
- **Line 856**: `renderProjectMembers()` (function)
  ```javascript
  function renderProjectMembers(members) {
  ```
- **Line 1202**: `generateMockSuggestions()` (function)
  ```javascript
  function generateMockSuggestions(projectName, description, targetRoles) {
  ```

### frontend/js/config.js
**Undocumented Functions**: 7

- **Line 25**: `SYLLABUS()` (arrow_method)
  ```javascript
  SYLLABUS: (courseId) => `https://localhost:8002/courses/${courseId}/syllabus`,
  ```
- **Line 26**: `SLIDES()` (arrow_method)
  ```javascript
  SLIDES: (courseId) => `https://localhost:8002/courses/${courseId}/slides`,
  ```
- **Line 27**: `LAB_BY_COURSE()` (arrow_method)
  ```javascript
  LAB_BY_COURSE: (courseId) => `https://localhost:8001/labs/course/${courseId}`,
  ```
- **Line 28**: `QUIZZES()` (arrow_method)
  ```javascript
  QUIZZES: (courseId) => `https://localhost:8000/quizzes/course/${courseId}`,
  ```
- **Line 29**: `QUIZ_GET_COURSE_QUIZZES()` (arrow_method)
  ```javascript
  QUIZ_GET_COURSE_QUIZZES: (courseId) => `https://localhost:8000/quizzes/course/${courseId}`,
  ```
- **Line 35**: `COURSES_BY_STATUS()` (arrow_method)
  ```javascript
  COURSES_BY_STATUS: (status) => `https://localhost:8004/courses?status=${status}`,
  ```
- **Line 36**: `INSTRUCTOR_INSTANCES()` (arrow_method)
  ```javascript
  INSTRUCTOR_INSTANCES: (instructorId) => `https://localhost:8004/course-instances?instructor_id=${instructorId}`
  ```

### frontend/js/modules/org-admin-file-manager.js
**Undocumented Functions**: 6

- **Line 78**: `onFileSelect()` (arrow_method)
  ```javascript
  onFileSelect: (file) => {
  ```
- **Line 82**: `onFileDelete()` (arrow_method)
  ```javascript
  onFileDelete: (file) => {
  ```
- **Line 90**: `onFileUpload()` (arrow_method)
  ```javascript
  onFileUpload: (response, file) => {
  ```
- **Line 98**: `onError()` (arrow_method)
  ```javascript
  onError: (error) => {
  ```
- **Line 112**: `getCurrentUser()` (function)
  ```javascript
  function getCurrentUser() {
  ```
- **Line 128**: `showNotification()` (function)
  ```javascript
  function showNotification(message, type = 'info') {
  ```

### frontend/js/modules/student-file-manager.js
**Undocumented Functions**: 6

- **Line 9**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 368**: `downloadCourseSyllabus()` (method)
  ```javascript
  async downloadCourseSyllabus(courseId, format = 'pdf') {
  ```
- **Line 410**: `downloadCourseSlides()` (method)
  ```javascript
  async downloadCourseSlides(courseId, moduleId = null) {
  ```
- **Line 453**: `downloadAllCourseMaterials()` (method)
  ```javascript
  async downloadAllCourseMaterials(courseId) {
  ```
- **Line 496**: `trackFileDownload()` (method)
  ```javascript
  async trackFileDownload(courseId, fileType, filename, fileSize) {
  ```
- **Line 539**: `triggerDownload()` (method)
  ```javascript
  triggerDownload(blob, filename) {
  ```

### frontend/js/modules/instructor-file-manager.js
**Undocumented Functions**: 6

- **Line 78**: `onFileSelect()` (arrow_method)
  ```javascript
  onFileSelect: (file) => {
  ```
- **Line 82**: `onFileDelete()` (arrow_method)
  ```javascript
  onFileDelete: (file) => {
  ```
- **Line 90**: `onFileUpload()` (arrow_method)
  ```javascript
  onFileUpload: (response, file) => {
  ```
- **Line 98**: `onError()` (arrow_method)
  ```javascript
  onError: (error) => {
  ```
- **Line 112**: `getCurrentUser()` (function)
  ```javascript
  function getCurrentUser() {
  ```
- **Line 128**: `showNotification()` (function)
  ```javascript
  function showNotification(message, type = 'info') {
  ```

### frontend/js/modules/projects/wizard/track-management/tabs/students-tab.js
**Undocumented Functions**: 6

- **Line 95**: `renderStudentCard()` (function)
  ```javascript
  function renderStudentCard(student, index) {
  ```
- **Line 150**: `renderProgressBar()` (function)
  ```javascript
  function renderProgressBar(progress, color) {
  ```
- **Line 173**: `getInitials()` (function)
  ```javascript
  function getInitials(name) {
  ```
- **Line 189**: `getProgressColor()` (function)
  ```javascript
  function getProgressColor(progress) {
  ```
- **Line 203**: `getStatusBadge()` (function)
  ```javascript
  function getStatusBadge(status) {
  ```
- **Line 228**: `renderStudentsStats()` (function)
  ```javascript
  function renderStudentsStats(students) {
  ```

### frontend/js/modules/org-admin-core.js
**Undocumented Functions**: 5

- **Line 138**: `updateOrganizationHeader()` (function)
  ```javascript
  function updateOrganizationHeader(organization) {
  ```
- **Line 191**: `setupNavigationListeners()` (function)
  ```javascript
  function setupNavigationListeners() {
  ```
- **Line 357**: `formatTimeAgo()` (function)
  ```javascript
  function formatTimeAgo(timestamp) {
  ```
- **Line 469**: `escapeHtml()` (function)
  ```javascript
  function escapeHtml(text) {
  ```
- **Line 481**: `setupLogoutHandler()` (function)
  ```javascript
  function setupLogoutHandler() {
  ```

### frontend/js/modules/org-admin/modals.js
**Undocumented Functions**: 5

- **Line 570**: `loadAnalyticsTabContent()` (function)
  ```javascript
  function loadAnalyticsTabContent(tabName) {
  ```
- **Line 694**: `displayRAGSuggestions()` (function)
  ```javascript
  function displayRAGSuggestions(ragResult, projectDescription, targetRoles) {
  ```
- **Line 761**: `generateMockRAGSuggestions()` (function)
  ```javascript
  function generateMockRAGSuggestions(description, targetRoles) {
  ```
- **Line 823**: `displayTrackTemplates()` (function)
  ```javascript
  function displayTrackTemplates(templates) {
  ```
- **Line 894**: `getMockTrackTemplates()` (function)
  ```javascript
  function getMockTrackTemplates() {
  ```

### frontend/js/modules/accessibility-manager.js
**Undocumented Functions**: 4

- **Line 47**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 82**: `init()` (method)
  ```javascript
  init() {
  ```
- **Line 107**: `createLiveRegion()` (method)
  ```javascript
  createLiveRegion(politeness) {
  ```
- **Line 167**: `announceLoadingComplete()` (method)
  ```javascript
  announceLoadingComplete(result) {
  ```

### frontend/js/modules/org-admin-analytics.js
**Undocumented Functions**: 4

- **Line 132**: `displayContentAnalytics()` (function)
  ```javascript
  function displayContentAnalytics(analytics) {
  ```
- **Line 244**: `displayTagFilterResults()` (function)
  ```javascript
  function displayTagFilterResults(tag, results) {
  ```
- **Line 314**: `analyzeDifficultyGaps()` (function)
  ```javascript
  function analyzeDifficultyGaps(courses) {
  ```
- **Line 352**: `displayContentGaps()` (function)
  ```javascript
  function displayContentGaps({ topicGaps, difficultyGaps }) {
  ```

### frontend/js/modules/org-admin-courses.js
**Undocumented Functions**: 4

- **Line 251**: `validateCourseForm()` (function)
  ```javascript
  function validateCourseForm() {
  ```
- **Line 298**: `showFieldError()` (function)
  ```javascript
  function showFieldError(fieldId, message) {
  ```
- **Line 394**: `parseTags()` (function)
  ```javascript
  function parseTags(tagsString) {
  ```
- **Line 411**: `escapeHtml()` (function)
  ```javascript
  function escapeHtml(text) {
  ```

### frontend/js/modules/projects/wizard/track-confirmation-dialog.js
**Undocumented Functions**: 4

- **Line 193**: `defaultEscapeHtml()` (function)
  ```javascript
  function defaultEscapeHtml(unsafe) {
  ```
- **Line 213**: `defaultOpenModal()` (function)
  ```javascript
  function defaultOpenModal(modalId) {
  ```
- **Line 226**: `defaultCloseModal()` (function)
  ```javascript
  function defaultCloseModal(modalId) {
  ```
- **Line 355**: `truncateText()` (function)
  ```javascript
  function truncateText(text, maxLength) {
  ```

### frontend/js/modules/projects/wizard/track-management/tabs/courses-tab.js
**Undocumented Functions**: 4

- **Line 85**: `renderCourseCard()` (function)
  ```javascript
  function renderCourseCard(course, index) {
  ```
- **Line 144**: `getStatusBadge()` (function)
  ```javascript
  function getStatusBadge(status) {
  ```
- **Line 162**: `capitalize()` (function)
  ```javascript
  function capitalize(str) {
  ```
- **Line 180**: `renderCoursesStats()` (function)
  ```javascript
  function renderCoursesStats(courses) {
  ```

### frontend/js/inline-validation.js
**Undocumented Functions**: 4

- **Line 37**: `constructor()` (method)
  ```javascript
  constructor(formSelector) {
  ```
- **Line 99**: `validateField()` (method)
  ```javascript
  validateField(input) {
  ```
- **Line 188**: `getFieldLabel()` (method)
  ```javascript
  getFieldLabel(input) {
  ```
- **Line 207**: `validateForm()` (method)
  ```javascript
  validateForm() {
  ```

### frontend/js/modules/notifications.js
**Undocumented Functions**: 3

- **Line 36**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 59**: `createContainer()` (method)
  ```javascript
  createContainer() {
  ```
- **Line 213**: `show()` (method)
  ```javascript
  show(message, type = 'info', options = {}) {
  ```

### frontend/js/modules/data-visualization.js
**Undocumented Functions**: 3

- **Line 7**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
- **Line 393**: `animate()` (arrow)
  ```javascript
  const animate = (currentTime) => {
  ```
- **Line 440**: `handleSort()` (arrow)
  ```javascript
  const handleSort = () => {
  ```

### frontend/js/modules/org-admin-utils.js
**Undocumented Functions**: 3

- **Line 196**: `getNotificationColor()` (function)
  ```javascript
  function getNotificationColor(type) {
  ```
- **Line 210**: `getNotificationIcon()` (function)
  ```javascript
  function getNotificationIcon(type) {
  ```
- **Line 369**: `later()` (arrow)
  ```javascript
  const later = () => {
  ```

### frontend/js/modules/ai-assistant.js
**Undocumented Functions**: 3

- **Line 79**: `getContextSystemPrompt()` (function)
  ```javascript
  function getContextSystemPrompt(contextType) {
  ```
- **Line 275**: `detectWebSearchIntent()` (function)
  ```javascript
  function detectWebSearchIntent(message) {
  ```
- **Line 741**: `buildContextAwarePrompt()` (function)
  ```javascript
  function buildContextAwarePrompt(userMessage, context, ragContext, metadataContext, knowledgeGraphContext, webResults) {
  ```

### frontend/js/main.js
**Undocumented Functions**: 3

- **Line 45**: `initializeSlideshow()` (function)
  ```javascript
  function initializeSlideshow() {
  ```
- **Line 50**: `checkCSSLoaded()` (arrow)
  ```javascript
  const checkCSSLoaded = () => {
  ```
- **Line 70**: `waitForFullLoad()` (function)
  ```javascript
  function waitForFullLoad() {
  ```

### frontend/js/modules/org-admin-students.js
**Undocumented Functions**: 2

- **Line 90**: `renderStudentsTable()` (function)
  ```javascript
  function renderStudentsTable(students) {
  ```
- **Line 137**: `updateStudentsStats()` (function)
  ```javascript
  function updateStudentsStats(students) {
  ```

### frontend/js/modules/org-admin-instructors.js
**Undocumented Functions**: 2

- **Line 89**: `renderInstructorsTable()` (function)
  ```javascript
  function renderInstructorsTable(instructors) {
  ```
- **Line 132**: `updateInstructorsStats()` (function)
  ```javascript
  function updateInstructorsStats(instructors) {
  ```

### frontend/js/modules/org-admin-tracks.js
**Undocumented Functions**: 2

- **Line 107**: `renderTracksTable()` (function)
  ```javascript
  function renderTracksTable(tracks) {
  ```
- **Line 165**: `updateTracksStats()` (function)
  ```javascript
  function updateTracksStats(tracks) {
  ```

### frontend/js/modules/projects/wizard/track-management/tabs/info-tab.js
**Undocumented Functions**: 2

- **Line 91**: `renderSkillsSection()` (function)
  ```javascript
  function renderSkillsSection(skills) {
  ```
- **Line 126**: `formatAudience()` (function)
  ```javascript
  function formatAudience(audience) {
  ```

### frontend/js/focus-manager.js
**Undocumented Functions**: 2

- **Line 33**: `handleMouseDown()` (function)
  ```javascript
  function handleMouseDown() {
  ```
- **Line 45**: `handleKeyDown()` (function)
  ```javascript
  function handleKeyDown(e) {
  ```

### frontend/js/bulk-enrollment.js
**Undocumented Functions**: 2

- **Line 616**: `getAuthToken()` (function)
  ```javascript
  function getAuthToken() {
  ```
- **Line 625**: `getCurrentUserId()` (function)
  ```javascript
  function getCurrentUserId() {
  ```

### frontend/js/modules/feedback-manager.js
**Undocumented Functions**: 1

- **Line 9**: `constructor()` (method)
  ```javascript
  constructor() {
  ```

### frontend/js/modules/ui-components.js
**Undocumented Functions**: 1

- **Line 620**: `later()` (arrow)
  ```javascript
  const later = () => {
  ```

### frontend/js/modules/projects/wizard/track-generator.js
**Undocumented Functions**: 1

- **Line 187**: `capitalizeWord()` (function)
  ```javascript
  function capitalizeWord(word) {
  ```

### frontend/js/lab-integration.js
**Undocumented Functions**: 1

- **Line 11**: `constructor()` (method)
  ```javascript
  constructor() {
  ```
