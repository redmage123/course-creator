import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports } from "./react-vendor-cEae-lCc.js";
import { c as apiClient } from "./index-C0G9mbri.js";
import "./state-vendor-B_izx0oA.js";
class IntegrationsService {
  baseUrl = "/integrations";
  // ========================================================================
  // LTI PLATFORM METHODS
  // ========================================================================
  /**
   * Register new LTI 1.3 platform
   *
   * What: Creates LTI platform registration for external LMS
   * Where: Called when organization admin sets up LTI integration
   * Why: Enables external LMS to launch into platform as LTI tool
   */
  async registerLTIPlatform(organizationId, data) {
    return await apiClient.post(
      `${this.baseUrl}/lti/platforms`,
      { ...data, organization_id: organizationId }
    );
  }
  /**
   * Get all LTI platforms for organization
   */
  async getOrganizationLTIPlatforms(organizationId) {
    return await apiClient.get(
      `${this.baseUrl}/lti/platforms`,
      { params: { organization_id: organizationId } }
    );
  }
  /**
   * Get LTI platform by ID
   */
  async getLTIPlatformById(platformId) {
    return await apiClient.get(
      `${this.baseUrl}/lti/platforms/${platformId}`
    );
  }
  /**
   * Verify LTI platform after successful handshake
   */
  async verifyLTIPlatform(platformId) {
    return await apiClient.post(
      `${this.baseUrl}/lti/platforms/${platformId}/verify`
    );
  }
  /**
   * Deactivate LTI platform
   */
  async deactivateLTIPlatform(platformId) {
    return await apiClient.post(
      `${this.baseUrl}/lti/platforms/${platformId}/deactivate`
    );
  }
  /**
   * Get LTI contexts for platform
   */
  async getLTIContexts(platformId) {
    return await apiClient.get(
      `${this.baseUrl}/lti/platforms/${platformId}/contexts`
    );
  }
  /**
   * Link LTI context to course
   */
  async linkLTIContextToCourse(contextId, courseId) {
    return await apiClient.post(
      `${this.baseUrl}/lti/contexts/${contextId}/link`,
      { course_id: courseId }
    );
  }
  /**
   * Get pending grade syncs for monitoring
   */
  async getPendingGradeSyncs(limit = 100) {
    return await apiClient.get(
      `${this.baseUrl}/lti/grade-syncs/pending`,
      { params: { limit } }
    );
  }
  // ========================================================================
  // CALENDAR METHODS
  // ========================================================================
  /**
   * Connect calendar provider
   *
   * What: Connects user calendar for synchronization
   * Where: Called after OAuth authorization completes
   * Why: Enables automatic calendar sync for deadlines and events
   */
  async connectCalendar(data) {
    return await apiClient.post(
      `${this.baseUrl}/calendars/connect`,
      data
    );
  }
  /**
   * Get user's connected calendars
   */
  async getUserCalendars(userId) {
    return await apiClient.get(
      `${this.baseUrl}/calendars`,
      { params: { user_id: userId } }
    );
  }
  /**
   * Update calendar settings
   */
  async updateCalendarSettings(providerId, data) {
    return await apiClient.put(
      `${this.baseUrl}/calendars/${providerId}`,
      data
    );
  }
  /**
   * Disconnect calendar
   */
  async disconnectCalendar(providerId) {
    await apiClient.delete(`${this.baseUrl}/calendars/${providerId}`);
  }
  /**
   * Get calendar events for user
   */
  async getCalendarEvents(userId, startDate, endDate) {
    return await apiClient.get(
      `${this.baseUrl}/calendars/events`,
      { params: { user_id: userId, start_date: startDate, end_date: endDate } }
    );
  }
  /**
   * Trigger manual calendar sync
   */
  async triggerCalendarSync(providerId) {
    return await apiClient.post(
      `${this.baseUrl}/calendars/${providerId}/sync`
    );
  }
  // ========================================================================
  // SLACK METHODS
  // ========================================================================
  /**
   * Connect Slack workspace
   *
   * What: Connects organization Slack workspace
   * Where: Called after Slack OAuth flow completes
   * Why: Enables Slack notifications, commands, and AI assistant
   */
  async connectSlackWorkspace(organizationId, data) {
    return await apiClient.post(
      `${this.baseUrl}/slack/workspaces`,
      { ...data, organization_id: organizationId }
    );
  }
  /**
   * Get organization Slack workspace
   */
  async getOrganizationSlackWorkspace(organizationId) {
    return await apiClient.get(
      `${this.baseUrl}/slack/workspaces`,
      { params: { organization_id: organizationId } }
    );
  }
  /**
   * Update Slack workspace settings
   */
  async updateSlackSettings(workspaceId, data) {
    return await apiClient.put(
      `${this.baseUrl}/slack/workspaces/${workspaceId}`,
      data
    );
  }
  /**
   * Disconnect Slack workspace
   */
  async disconnectSlackWorkspace(workspaceId) {
    await apiClient.delete(`${this.baseUrl}/slack/workspaces/${workspaceId}`);
  }
  /**
   * Get Slack channel mappings for entity
   */
  async getEntitySlackChannels(entityType, entityId) {
    return await apiClient.get(
      `${this.baseUrl}/slack/channels`,
      { params: { entity_type: entityType, entity_id: entityId } }
    );
  }
  /**
   * Map Slack channel to entity
   */
  async mapSlackChannel(workspaceId, channelId, entityType, entityId, channelName) {
    return await apiClient.post(
      `${this.baseUrl}/slack/channels`,
      {
        workspace_id: workspaceId,
        channel_id: channelId,
        channel_name: channelName,
        entity_type: entityType,
        entity_id: entityId
      }
    );
  }
  /**
   * Test Slack connection
   */
  async testSlackConnection(workspaceId) {
    return await apiClient.post(
      `${this.baseUrl}/slack/workspaces/${workspaceId}/test`
    );
  }
  // ========================================================================
  // WEBHOOK METHODS
  // ========================================================================
  /**
   * Create outbound webhook
   *
   * What: Creates webhook for sending events to external services
   * Where: Called when setting up webhook integration
   * Why: Enables event notifications to Zapier, custom apps, etc.
   */
  async createOutboundWebhook(organizationId, data) {
    return await apiClient.post(
      `${this.baseUrl}/webhooks/outbound`,
      { ...data, organization_id: organizationId }
    );
  }
  /**
   * Get organization outbound webhooks
   */
  async getOrganizationWebhooks(organizationId) {
    return await apiClient.get(
      `${this.baseUrl}/webhooks/outbound`,
      { params: { organization_id: organizationId } }
    );
  }
  /**
   * Update outbound webhook
   */
  async updateOutboundWebhook(webhookId, data) {
    return await apiClient.put(
      `${this.baseUrl}/webhooks/outbound/${webhookId}`,
      data
    );
  }
  /**
   * Delete outbound webhook
   */
  async deleteOutboundWebhook(webhookId) {
    await apiClient.delete(`${this.baseUrl}/webhooks/outbound/${webhookId}`);
  }
  /**
   * Test outbound webhook
   */
  async testOutboundWebhook(webhookId) {
    return await apiClient.post(
      `${this.baseUrl}/webhooks/outbound/${webhookId}/test`
    );
  }
  /**
   * Get webhook delivery logs
   */
  async getWebhookDeliveryLogs(webhookId, limit = 50) {
    return await apiClient.get(
      `${this.baseUrl}/webhooks/outbound/${webhookId}/logs`,
      { params: { limit } }
    );
  }
  /**
   * Get inbound webhooks for organization
   */
  async getInboundWebhooks(organizationId) {
    return await apiClient.get(
      `${this.baseUrl}/webhooks/inbound`,
      { params: { organization_id: organizationId } }
    );
  }
  /**
   * Create inbound webhook
   */
  async createInboundWebhook(organizationId, name, handlerType, description2) {
    return await apiClient.post(
      `${this.baseUrl}/webhooks/inbound`,
      {
        organization_id: organizationId,
        name,
        handler_type: handlerType,
        description: description2
      }
    );
  }
  /**
   * Delete inbound webhook
   */
  async deleteInboundWebhook(webhookId) {
    await apiClient.delete(`${this.baseUrl}/webhooks/inbound/${webhookId}`);
  }
  // ========================================================================
  // OAUTH TOKEN METHODS
  // ========================================================================
  /**
   * Store OAuth token
   *
   * What: Stores OAuth token for external service access
   * Where: Called after OAuth authorization
   * Why: Enables API access to Google, Microsoft, Slack, GitHub, Zoom
   */
  async storeOAuthToken(data) {
    return await apiClient.post(
      `${this.baseUrl}/oauth/tokens`,
      data
    );
  }
  /**
   * Get OAuth token for provider
   */
  async getOAuthToken(provider, userId, organizationId) {
    return await apiClient.get(
      `${this.baseUrl}/oauth/tokens/${provider}`,
      { params: { user_id: userId, organization_id: organizationId } }
    );
  }
  /**
   * Refresh OAuth token
   */
  async refreshOAuthToken(tokenId) {
    return await apiClient.post(
      `${this.baseUrl}/oauth/tokens/${tokenId}/refresh`
    );
  }
  /**
   * Revoke OAuth token
   */
  async revokeOAuthToken(tokenId) {
    await apiClient.delete(`${this.baseUrl}/oauth/tokens/${tokenId}`);
  }
  /**
   * Get user's OAuth connections
   */
  async getUserOAuthConnections(userId) {
    return await apiClient.get(
      `${this.baseUrl}/oauth/tokens`,
      { params: { user_id: userId } }
    );
  }
  /**
   * Get organization's OAuth connections
   */
  async getOrganizationOAuthConnections(organizationId) {
    return await apiClient.get(
      `${this.baseUrl}/oauth/tokens`,
      { params: { organization_id: organizationId } }
    );
  }
  // ========================================================================
  // OAUTH FLOW HELPERS
  // ========================================================================
  /**
   * Initiate OAuth flow
   *
   * What: Redirects to OAuth provider authorization page
   * Where: Called when user clicks "Connect" button
   * Why: Starts OAuth authorization flow for external service
   */
  initiateOAuthFlow(provider, scopes, redirectUri) {
    const params = new URLSearchParams({
      provider,
      scopes: scopes.join(","),
      redirect_uri: redirectUri
    });
    window.location.href = `${this.baseUrl}/oauth/authorize?${params.toString()}`;
  }
  /**
   * Handle OAuth callback
   *
   * What: Processes OAuth callback with authorization code
   * Where: Called on OAuth redirect URL
   * Why: Exchanges authorization code for access token
   */
  async handleOAuthCallback(provider, code, state) {
    return await apiClient.post(
      `${this.baseUrl}/oauth/callback`,
      { provider, code, state }
    );
  }
}
const integrationsService = new IntegrationsService();
const useIntegrations = (organizationId, userId) => {
  const [state, setState] = reactExports.useState({
    ltiPlatforms: [],
    ltiLoading: false,
    ltiError: null,
    calendars: [],
    calendarsLoading: false,
    calendarsError: null,
    slackWorkspace: null,
    slackLoading: false,
    slackError: null,
    outboundWebhooks: [],
    inboundWebhooks: [],
    webhooksLoading: false,
    webhooksError: null,
    oauthTokens: [],
    oauthLoading: false,
    oauthError: null
  });
  const fetchLTIPlatforms = reactExports.useCallback(async () => {
    setState((prev) => ({ ...prev, ltiLoading: true, ltiError: null }));
    try {
      const platforms = await integrationsService.getOrganizationLTIPlatforms(organizationId);
      setState((prev) => ({
        ...prev,
        ltiPlatforms: Array.isArray(platforms) ? platforms : [],
        ltiLoading: false
      }));
    } catch (error2) {
      setState((prev) => ({
        ...prev,
        ltiError: error2.response?.data?.message || "Failed to load LTI platforms",
        ltiLoading: false
      }));
    }
  }, [organizationId]);
  const fetchCalendars = reactExports.useCallback(async () => {
    if (!userId) return;
    setState((prev) => ({ ...prev, calendarsLoading: true, calendarsError: null }));
    try {
      const calendars = await integrationsService.getUserCalendars(userId);
      setState((prev) => ({
        ...prev,
        calendars,
        calendarsLoading: false
      }));
    } catch (error2) {
      setState((prev) => ({
        ...prev,
        calendarsError: error2.response?.data?.message || "Failed to load calendars",
        calendarsLoading: false
      }));
    }
  }, [userId]);
  const fetchSlackWorkspace = reactExports.useCallback(async () => {
    setState((prev) => ({ ...prev, slackLoading: true, slackError: null }));
    try {
      const workspace = await integrationsService.getOrganizationSlackWorkspace(organizationId);
      setState((prev) => ({
        ...prev,
        slackWorkspace: workspace,
        slackLoading: false
      }));
    } catch (error2) {
      setState((prev) => ({
        ...prev,
        slackError: error2.response?.data?.message || "Failed to load Slack workspace",
        slackLoading: false
      }));
    }
  }, [organizationId]);
  const fetchWebhooks = reactExports.useCallback(async () => {
    setState((prev) => ({ ...prev, webhooksLoading: true, webhooksError: null }));
    try {
      const [outbound, inbound] = await Promise.all([
        integrationsService.getOrganizationWebhooks(organizationId),
        integrationsService.getInboundWebhooks(organizationId)
      ]);
      setState((prev) => ({
        ...prev,
        outboundWebhooks: Array.isArray(outbound) ? outbound : [],
        inboundWebhooks: Array.isArray(inbound) ? inbound : [],
        webhooksLoading: false
      }));
    } catch (error2) {
      setState((prev) => ({
        ...prev,
        webhooksError: error2.response?.data?.message || "Failed to load webhooks",
        webhooksLoading: false
      }));
    }
  }, [organizationId]);
  const fetchOAuthTokens = reactExports.useCallback(async () => {
    setState((prev) => ({ ...prev, oauthLoading: true, oauthError: null }));
    try {
      let tokens = [];
      if (userId) {
        const result = await integrationsService.getUserOAuthConnections(userId);
        tokens = Array.isArray(result) ? result : [];
      } else {
        const result = await integrationsService.getOrganizationOAuthConnections(organizationId);
        tokens = Array.isArray(result) ? result : [];
      }
      setState((prev) => ({
        ...prev,
        oauthTokens: tokens,
        oauthLoading: false
      }));
    } catch (error2) {
      setState((prev) => ({
        ...prev,
        oauthError: error2.response?.data?.message || "Failed to load OAuth connections",
        oauthLoading: false
      }));
    }
  }, [userId, organizationId]);
  const refreshAll = reactExports.useCallback(async () => {
    await Promise.all([
      fetchLTIPlatforms(),
      fetchCalendars(),
      fetchSlackWorkspace(),
      fetchWebhooks(),
      fetchOAuthTokens()
    ]);
  }, [
    fetchLTIPlatforms,
    fetchCalendars,
    fetchSlackWorkspace,
    fetchWebhooks,
    fetchOAuthTokens
  ]);
  reactExports.useEffect(() => {
    fetchLTIPlatforms();
    fetchSlackWorkspace();
    fetchWebhooks();
    fetchOAuthTokens();
  }, [fetchLTIPlatforms, fetchSlackWorkspace, fetchWebhooks, fetchOAuthTokens]);
  reactExports.useEffect(() => {
    if (userId) {
      fetchCalendars();
    }
  }, [userId, fetchCalendars]);
  const isLoading = state.ltiLoading || state.calendarsLoading || state.slackLoading || state.webhooksLoading || state.oauthLoading;
  const hasError = !!state.ltiError || !!state.calendarsError || !!state.slackError || !!state.webhooksError || !!state.oauthError;
  return {
    // State
    ...state,
    isLoading,
    hasError,
    // Refresh methods
    refreshAll,
    refreshLTI: fetchLTIPlatforms,
    refreshCalendars: fetchCalendars,
    refreshSlack: fetchSlackWorkspace,
    refreshWebhooks: fetchWebhooks,
    refreshOAuth: fetchOAuthTokens
  };
};
const badge = "_badge_1szu9_9";
const indicator = "_indicator_1szu9_40";
const statusConnected = "_statusConnected_1szu9_58";
const statusDisconnected = "_statusDisconnected_1szu9_69";
const statusError = "_statusError_1szu9_80";
const statusPending = "_statusPending_1szu9_91";
const statusSyncing = "_statusSyncing_1szu9_102";
const pulse = "_pulse_1szu9_113";
const text = "_text_1szu9_127";
const lastSync = "_lastSync_1szu9_133";
const errorTooltip = "_errorTooltip_1szu9_141";
const styles$6 = {
  badge,
  "size-small": "_size-small_1szu9_21",
  "size-medium": "_size-medium_1szu9_27",
  "size-large": "_size-large_1szu9_33",
  indicator,
  statusConnected,
  statusDisconnected,
  statusError,
  statusPending,
  statusSyncing,
  pulse,
  text,
  lastSync,
  errorTooltip
};
const IntegrationStatusBadge = ({
  status,
  lastSync: lastSync2,
  errorMessage,
  size = "medium"
}) => {
  const getStatusText = () => {
    switch (status) {
      case "connected":
        return "Connected";
      case "disconnected":
        return "Disconnected";
      case "error":
        return "Error";
      case "pending":
        return "Pending";
      case "syncing":
        return "Syncing...";
      default:
        return "Unknown";
    }
  };
  const getStatusClass = () => {
    switch (status) {
      case "connected":
        return styles$6.statusConnected;
      case "disconnected":
        return styles$6.statusDisconnected;
      case "error":
        return styles$6.statusError;
      case "pending":
        return styles$6.statusPending;
      case "syncing":
        return styles$6.statusSyncing;
      default:
        return styles$6.statusDisconnected;
    }
  };
  const formatLastSync = () => {
    if (!lastSync2) return null;
    try {
      const date = new Date(lastSync2);
      const now = /* @__PURE__ */ new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 6e4);
      const diffHours = Math.floor(diffMs / 36e5);
      const diffDays = Math.floor(diffMs / 864e5);
      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? "s" : ""} ago`;
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
      return date.toLocaleDateString();
    } catch (error2) {
      return null;
    }
  };
  const statusText = getStatusText();
  const statusClass = getStatusClass();
  const lastSyncText = formatLastSync();
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      className: `${styles$6.badge} ${statusClass} ${styles$6[`size-${size}`]}`,
      role: "status",
      "aria-label": `Integration status: ${statusText}${errorMessage ? ` - ${errorMessage}` : ""}`,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "span",
          {
            className: `${styles$6.indicator} ${status === "syncing" ? styles$6.pulse : ""}`,
            "aria-hidden": "true"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.text, children: statusText }),
        size !== "small" && lastSyncText && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.lastSync, title: `Last synced: ${lastSync2}`, children: lastSyncText }),
        errorMessage && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.errorTooltip, title: errorMessage, children: "ⓘ" })
      ]
    }
  );
};
const panel$4 = "_panel_2z0ss_6";
const header$4 = "_header_2z0ss_13";
const title$4 = "_title_2z0ss_22";
const description$4 = "_description_2z0ss_29";
const addButton$1 = "_addButton_2z0ss_35";
const successMessage = "_successMessage_2z0ss_57";
const form$1 = "_form_2z0ss_68";
const formTitle = "_formTitle_2z0ss_76";
const formGroup$1 = "_formGroup_2z0ss_83";
const label = "_label_2z0ss_87";
const helpText = "_helpText_2z0ss_95";
const input$1 = "_input_2z0ss_103";
const error = "_error_2z0ss_118";
const submitError = "_submitError_2z0ss_125";
const formActions$1 = "_formActions_2z0ss_135";
const cancelButton$1 = "_cancelButton_2z0ss_144";
const submitButton$1 = "_submitButton_2z0ss_160";
const platformList = "_platformList_2z0ss_183";
const platformCard = "_platformCard_2z0ss_189";
const platformHeader = "_platformHeader_2z0ss_201";
const platformName = "_platformName_2z0ss_208";
const platformIssuer = "_platformIssuer_2z0ss_215";
const platformDetails = "_platformDetails_2z0ss_222";
const detailRow = "_detailRow_2z0ss_229";
const detailLabel = "_detailLabel_2z0ss_241";
const detailValue = "_detailValue_2z0ss_247";
const verified = "_verified_2z0ss_256";
const unverified = "_unverified_2z0ss_261";
const platformActions = "_platformActions_2z0ss_266";
const verifyButton = "_verifyButton_2z0ss_271";
const deactivateButton = "_deactivateButton_2z0ss_287";
const emptyState$2 = "_emptyState_2z0ss_304";
const emptyStateHint$1 = "_emptyStateHint_2z0ss_313";
const instructions$1 = "_instructions_2z0ss_320";
const instructionsTitle$1 = "_instructionsTitle_2z0ss_328";
const instructionsList = "_instructionsList_2z0ss_335";
const configValues = "_configValues_2z0ss_346";
const styles$5 = {
  panel: panel$4,
  header: header$4,
  title: title$4,
  description: description$4,
  addButton: addButton$1,
  successMessage,
  form: form$1,
  formTitle,
  formGroup: formGroup$1,
  label,
  helpText,
  input: input$1,
  error,
  submitError,
  formActions: formActions$1,
  cancelButton: cancelButton$1,
  submitButton: submitButton$1,
  platformList,
  platformCard,
  platformHeader,
  platformName,
  platformIssuer,
  platformDetails,
  detailRow,
  detailLabel,
  detailValue,
  verified,
  unverified,
  platformActions,
  verifyButton,
  deactivateButton,
  emptyState: emptyState$2,
  emptyStateHint: emptyStateHint$1,
  instructions: instructions$1,
  instructionsTitle: instructionsTitle$1,
  instructionsList,
  configValues
};
const LTIIntegrationPanel = ({
  organizationId,
  platforms,
  onRefresh
}) => {
  const [showAddForm, setShowAddForm] = reactExports.useState(false);
  const [formData, setFormData] = reactExports.useState({
    platform_name: "",
    issuer: "",
    client_id: "",
    auth_login_url: "",
    auth_token_url: "",
    jwks_url: "",
    deployment_id: "",
    scopes: []
  });
  const [formErrors, setFormErrors] = reactExports.useState({});
  const [submitting, setSubmitting] = reactExports.useState(false);
  const [successMessage2, setSuccessMessage] = reactExports.useState("");
  const validateForm = () => {
    const errors = {};
    if (!formData.platform_name.trim()) {
      errors.platform_name = "Platform name is required";
    }
    if (!formData.issuer.trim()) {
      errors.issuer = "Issuer URL is required";
    } else if (!formData.issuer.startsWith("http")) {
      errors.issuer = "Issuer must be a valid URL";
    }
    if (!formData.client_id.trim()) {
      errors.client_id = "Client ID is required";
    }
    if (!formData.auth_login_url.trim()) {
      errors.auth_login_url = "Auth login URL is required";
    } else if (!formData.auth_login_url.startsWith("http")) {
      errors.auth_login_url = "Auth login URL must be a valid URL";
    }
    if (!formData.auth_token_url.trim()) {
      errors.auth_token_url = "Auth token URL is required";
    } else if (!formData.auth_token_url.startsWith("http")) {
      errors.auth_token_url = "Auth token URL must be a valid URL";
    }
    if (!formData.jwks_url.trim()) {
      errors.jwks_url = "JWKS URL is required";
    } else if (!formData.jwks_url.startsWith("http")) {
      errors.jwks_url = "JWKS URL must be a valid URL";
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;
    setSubmitting(true);
    setSuccessMessage("");
    try {
      await integrationsService.registerLTIPlatform(organizationId, formData);
      setSuccessMessage("LTI platform registered successfully!");
      setShowAddForm(false);
      setFormData({
        platform_name: "",
        issuer: "",
        client_id: "",
        auth_login_url: "",
        auth_token_url: "",
        jwks_url: "",
        deployment_id: "",
        scopes: []
      });
      setFormErrors({});
      onRefresh();
    } catch (error2) {
      setFormErrors({
        submit: error2.response?.data?.message || "Failed to register LTI platform"
      });
    } finally {
      setSubmitting(false);
    }
  };
  const handleDeactivate = async (platformId) => {
    if (!window.confirm("Are you sure you want to deactivate this LTI platform?")) {
      return;
    }
    try {
      await integrationsService.deactivateLTIPlatform(platformId);
      setSuccessMessage("LTI platform deactivated successfully!");
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to deactivate LTI platform");
    }
  };
  const handleVerify = async (platformId) => {
    try {
      await integrationsService.verifyLTIPlatform(platformId);
      setSuccessMessage("LTI platform verified successfully!");
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to verify LTI platform");
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.panel, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$5.title, children: "LTI 1.3 Integration" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$5.description, children: "Connect external LMS platforms (Canvas, Moodle, Blackboard) for seamless integration" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: styles$5.addButton,
          onClick: () => setShowAddForm(!showAddForm),
          disabled: submitting,
          children: showAddForm ? "Cancel" : "+ Add LTI Platform"
        }
      )
    ] }),
    successMessage2 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.successMessage, children: [
      "✓ ",
      successMessage2
    ] }),
    showAddForm && /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, className: styles$5.form, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$5.formTitle, children: "Register LTI 1.3 Platform" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "platform_name", className: styles$5.label, children: "Platform Name *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "text",
            id: "platform_name",
            className: styles$5.input,
            placeholder: "e.g., Canvas LMS",
            value: formData.platform_name,
            onChange: (e) => setFormData({ ...formData, platform_name: e.target.value })
          }
        ),
        formErrors.platform_name && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.error, children: formErrors.platform_name })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "issuer", className: styles$5.label, children: [
          "Issuer URL *",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.helpText, children: "The platform's issuer identifier (e.g., https://canvas.instructure.com)" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "url",
            id: "issuer",
            className: styles$5.input,
            placeholder: "https://example.com",
            value: formData.issuer,
            onChange: (e) => setFormData({ ...formData, issuer: e.target.value })
          }
        ),
        formErrors.issuer && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.error, children: formErrors.issuer })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "client_id", className: styles$5.label, children: [
          "Client ID *",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.helpText, children: "The OAuth 2.0 client identifier provided by the LMS" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "text",
            id: "client_id",
            className: styles$5.input,
            placeholder: "Client ID from LMS",
            value: formData.client_id,
            onChange: (e) => setFormData({ ...formData, client_id: e.target.value })
          }
        ),
        formErrors.client_id && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.error, children: formErrors.client_id })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "auth_login_url", className: styles$5.label, children: [
          "Auth Login URL *",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.helpText, children: "OIDC login initiation endpoint" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "url",
            id: "auth_login_url",
            className: styles$5.input,
            placeholder: "https://example.com/api/lti/authorize_redirect",
            value: formData.auth_login_url,
            onChange: (e) => setFormData({ ...formData, auth_login_url: e.target.value })
          }
        ),
        formErrors.auth_login_url && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.error, children: formErrors.auth_login_url })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "auth_token_url", className: styles$5.label, children: [
          "Auth Token URL *",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.helpText, children: "OAuth 2.0 token endpoint" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "url",
            id: "auth_token_url",
            className: styles$5.input,
            placeholder: "https://example.com/login/oauth2/token",
            value: formData.auth_token_url,
            onChange: (e) => setFormData({ ...formData, auth_token_url: e.target.value })
          }
        ),
        formErrors.auth_token_url && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.error, children: formErrors.auth_token_url })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "jwks_url", className: styles$5.label, children: [
          "JWKS URL *",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.helpText, children: "JSON Web Key Set endpoint for token verification" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "url",
            id: "jwks_url",
            className: styles$5.input,
            placeholder: "https://example.com/api/lti/security/jwks",
            value: formData.jwks_url,
            onChange: (e) => setFormData({ ...formData, jwks_url: e.target.value })
          }
        ),
        formErrors.jwks_url && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.error, children: formErrors.jwks_url })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "deployment_id", className: styles$5.label, children: [
          "Deployment ID (Optional)",
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.helpText, children: "Platform deployment identifier (if required by LMS)" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "text",
            id: "deployment_id",
            className: styles$5.input,
            placeholder: "Deployment ID (optional)",
            value: formData.deployment_id,
            onChange: (e) => setFormData({ ...formData, deployment_id: e.target.value })
          }
        )
      ] }),
      formErrors.submit && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$5.submitError, children: formErrors.submit }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.formActions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "button",
            className: styles$5.cancelButton,
            onClick: () => setShowAddForm(false),
            disabled: submitting,
            children: "Cancel"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "submit",
            className: styles$5.submitButton,
            disabled: submitting,
            children: submitting ? "Registering..." : "Register Platform"
          }
        )
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$5.platformList, children: platforms.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.emptyState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No LTI platforms configured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$5.emptyStateHint, children: 'Click "Add LTI Platform" to connect your first LMS' })
    ] }) : platforms.map((platform) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.platformCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.platformHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$5.platformName, children: platform.platform_name }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$5.platformIssuer, children: platform.issuer })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          IntegrationStatusBadge,
          {
            status: platform.is_active ? "connected" : "disconnected",
            lastSync: platform.last_connection_at
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.platformDetails, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.detailRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.detailLabel, children: "Client ID:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: styles$5.detailValue, children: platform.client_id })
        ] }),
        platform.deployment_id && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.detailRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.detailLabel, children: "Deployment ID:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: styles$5.detailValue, children: platform.deployment_id })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.detailRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.detailLabel, children: "Verified:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.detailValue, children: platform.verified_at ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.verified, children: "✓ Verified" }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.unverified, children: "Not verified" }) })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.platformActions, children: [
        !platform.verified_at && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$5.verifyButton,
            onClick: () => handleVerify(platform.id),
            children: "Verify Platform"
          }
        ),
        platform.is_active && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$5.deactivateButton,
            onClick: () => handleDeactivate(platform.id),
            children: "Deactivate"
          }
        )
      ] })
    ] }, platform.id)) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$5.instructions, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$5.instructionsTitle, children: "LTI 1.3 Setup Instructions" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ol", { className: styles$5.instructionsList, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "In your LMS admin panel, navigate to LTI Developer Keys or External Apps" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Create a new LTI 1.3 configuration" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Use the following configuration values:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: styles$5.configValues, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Tool URL:" }),
            " ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("code", { children: "https://your-domain.com/lti/launch" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Redirect URIs:" }),
            " ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("code", { children: "https://your-domain.com/lti/callback" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Public JWK URL:" }),
            " ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("code", { children: "https://your-domain.com/lti/jwks" })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Copy the Issuer, Client ID, and platform URLs from your LMS" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: 'Click "Add LTI Platform" above and paste the values' }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Test the connection by launching from your LMS" })
      ] })
    ] })
  ] });
};
const panel$3 = "_panel_2nnhu_1";
const header$3 = "_header_2nnhu_1";
const title$3 = "_title_2nnhu_1";
const description$3 = "_description_2nnhu_1";
const emptyState$1 = "_emptyState_2nnhu_1";
const emptyStateHint = "_emptyStateHint_2nnhu_1";
const connectButtons = "_connectButtons_2nnhu_4";
const connectButton$2 = "_connectButton_2nnhu_4";
const google = "_google_2nnhu_26";
const outlook = "_outlook_2nnhu_31";
const icon = "_icon_2nnhu_46";
const calendarList = "_calendarList_2nnhu_50";
const calendarCard = "_calendarCard_2nnhu_56";
const calendarHeader = "_calendarHeader_2nnhu_63";
const calendarName = "_calendarName_2nnhu_70";
const calendarSubtitle = "_calendarSubtitle_2nnhu_77";
const settings$1 = "_settings_2nnhu_83";
const settingRow$1 = "_settingRow_2nnhu_90";
const calendarActions = "_calendarActions_2nnhu_104";
const syncButton = "_syncButton_2nnhu_109";
const disconnectButton$1 = "_disconnectButton_2nnhu_124";
const styles$4 = {
  panel: panel$3,
  header: header$3,
  title: title$3,
  description: description$3,
  emptyState: emptyState$1,
  emptyStateHint,
  connectButtons,
  connectButton: connectButton$2,
  google,
  outlook,
  icon,
  calendarList,
  calendarCard,
  calendarHeader,
  calendarName,
  calendarSubtitle,
  settings: settings$1,
  settingRow: settingRow$1,
  calendarActions,
  syncButton,
  disconnectButton: disconnectButton$1
};
const CalendarSyncPanel = ({
  userId,
  calendars,
  onRefresh
}) => {
  const [selectedProvider, setSelectedProvider] = reactExports.useState(null);
  const [syncSettings, setSyncSettings] = reactExports.useState({});
  const [syncing, setSyncing] = reactExports.useState(false);
  const handleConnect = (providerType) => {
    const redirectUri = `${window.location.origin}/integrations/calendar/callback`;
    const scopes = providerType === "google" ? ["https://www.googleapis.com/auth/calendar"] : ["Calendars.ReadWrite"];
    integrationsService.initiateOAuthFlow(
      providerType === "google" ? "google" : "microsoft",
      scopes,
      redirectUri
    );
  };
  const handleDisconnect = async (providerId) => {
    if (!window.confirm("Disconnect this calendar?")) return;
    try {
      await integrationsService.disconnectCalendar(providerId);
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to disconnect calendar");
    }
  };
  const handleSyncNow = async (providerId) => {
    setSyncing(true);
    try {
      const result = await integrationsService.triggerCalendarSync(providerId);
      alert(`Successfully synced ${result.synced_count} events`);
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to sync calendar");
    } finally {
      setSyncing(false);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.panel, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.header, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$4.title, children: "Calendar Sync" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$4.description, children: "Automatically sync course deadlines and events to your calendar" })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.connectButtons, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          className: `${styles$4.connectButton} ${styles$4.google}`,
          onClick: () => handleConnect("google"),
          disabled: calendars.some((c) => c.provider_type === "google"),
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.icon, children: "📅" }),
            calendars.some((c) => c.provider_type === "google") ? "Google Connected" : "Connect Google Calendar"
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          className: `${styles$4.connectButton} ${styles$4.outlook}`,
          onClick: () => handleConnect("outlook"),
          disabled: calendars.some((c) => c.provider_type === "outlook"),
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4.icon, children: "📆" }),
            calendars.some((c) => c.provider_type === "outlook") ? "Outlook Connected" : "Connect Outlook Calendar"
          ]
        }
      )
    ] }),
    calendars.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.calendarList, children: calendars.map((calendar) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.calendarCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.calendarHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$4.calendarName, children: calendar.provider_type === "google" ? "📅 Google Calendar" : "📆 Outlook Calendar" }),
          calendar.calendar_name && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$4.calendarSubtitle, children: calendar.calendar_name })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          IntegrationStatusBadge,
          {
            status: calendar.is_connected ? "connected" : "disconnected",
            lastSync: calendar.last_sync_at,
            errorMessage: calendar.last_sync_error || void 0
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.settings, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$4.settingRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: calendar.sync_enabled,
              onChange: (e) => {
                integrationsService.updateCalendarSettings(calendar.id, {
                  sync_enabled: e.target.checked
                }).then(onRefresh);
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Enable automatic sync" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$4.settingRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: calendar.sync_deadline_reminders,
              disabled: !calendar.sync_enabled,
              onChange: (e) => {
                integrationsService.updateCalendarSettings(calendar.id, {
                  sync_deadline_reminders: e.target.checked
                }).then(onRefresh);
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Sync assignment deadlines" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$4.settingRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: calendar.sync_quiz_dates,
              disabled: !calendar.sync_enabled,
              onChange: (e) => {
                integrationsService.updateCalendarSettings(calendar.id, {
                  sync_quiz_dates: e.target.checked
                }).then(onRefresh);
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Sync quiz dates" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$4.settingRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: calendar.sync_class_schedules,
              disabled: !calendar.sync_enabled,
              onChange: (e) => {
                integrationsService.updateCalendarSettings(calendar.id, {
                  sync_class_schedules: e.target.checked
                }).then(onRefresh);
              }
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Sync class schedules" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.calendarActions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$4.syncButton,
            onClick: () => handleSyncNow(calendar.id),
            disabled: syncing,
            children: syncing ? "Syncing..." : "Sync Now"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$4.disconnectButton,
            onClick: () => handleDisconnect(calendar.id),
            children: "Disconnect"
          }
        )
      ] })
    ] }, calendar.id)) }),
    calendars.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.emptyState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No calendars connected" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$4.emptyStateHint, children: "Connect Google Calendar or Outlook to automatically sync course events" })
    ] })
  ] });
};
const panel$2 = "_panel_w3n2e_1";
const header$2 = "_header_w3n2e_1";
const title$2 = "_title_w3n2e_1";
const description$2 = "_description_w3n2e_1";
const instructions = "_instructions_w3n2e_145";
const instructionsTitle = "_instructionsTitle_w3n2e_153";
const connectSection = "_connectSection_w3n2e_4";
const connectButton$1 = "_connectButton_w3n2e_11";
const slackIcon = "_slackIcon_w3n2e_30";
const connectHint = "_connectHint_w3n2e_34";
const workspaceCard = "_workspaceCard_w3n2e_40";
const workspaceHeader = "_workspaceHeader_w3n2e_46";
const workspaceName = "_workspaceName_w3n2e_53";
const workspaceDomain = "_workspaceDomain_w3n2e_59";
const settings = "_settings_w3n2e_65";
const settingsTitle = "_settingsTitle_w3n2e_72";
const settingRow = "_settingRow_w3n2e_78";
const channels = "_channels_w3n2e_85";
const channelRow = "_channelRow_w3n2e_92";
const channelInput = "_channelInput_w3n2e_105";
const actions = "_actions_w3n2e_112";
const testButton$1 = "_testButton_w3n2e_117";
const disconnectButton = "_disconnectButton_w3n2e_131";
const styles$3 = {
  panel: panel$2,
  header: header$2,
  title: title$2,
  description: description$2,
  instructions,
  instructionsTitle,
  connectSection,
  connectButton: connectButton$1,
  slackIcon,
  connectHint,
  workspaceCard,
  workspaceHeader,
  workspaceName,
  workspaceDomain,
  settings,
  settingsTitle,
  settingRow,
  channels,
  channelRow,
  channelInput,
  actions,
  testButton: testButton$1,
  disconnectButton
};
const SlackIntegrationPanel = ({
  organizationId,
  workspace,
  onRefresh
}) => {
  const [testing, setTesting] = reactExports.useState(false);
  const handleConnect = () => {
    const redirectUri = `${window.location.origin}/integrations/slack/callback`;
    const scopes = [
      "chat:write",
      "channels:read",
      "groups:read",
      "users:read",
      "incoming-webhook"
    ];
    integrationsService.initiateOAuthFlow("slack", scopes, redirectUri);
  };
  const handleDisconnect = async () => {
    if (!workspace || !window.confirm("Disconnect Slack workspace?")) return;
    try {
      await integrationsService.disconnectSlackWorkspace(workspace.id);
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to disconnect Slack");
    }
  };
  const handleTestConnection = async () => {
    if (!workspace) return;
    setTesting(true);
    try {
      const result = await integrationsService.testSlackConnection(workspace.id);
      alert(result.message);
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to test Slack connection");
    } finally {
      setTesting(false);
    }
  };
  const handleUpdateSettings = async (settings2) => {
    if (!workspace) return;
    try {
      await integrationsService.updateSlackSettings(workspace.id, settings2);
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to update settings");
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.panel, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.header, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$3.title, children: "💬 Slack Integration" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$3.description, children: "Send automated notifications to Slack channels for course updates" })
    ] }) }),
    !workspace ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.connectSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { className: styles$3.connectButton, onClick: handleConnect, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.slackIcon, children: "💬" }),
        "Add to Slack"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$3.connectHint, children: "Connect your Slack workspace to receive course notifications" })
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.workspaceCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.workspaceHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$3.workspaceName, children: workspace.workspace_name || "Slack Workspace" }),
          workspace.workspace_domain && /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles$3.workspaceDomain, children: [
            workspace.workspace_domain,
            ".slack.com"
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          IntegrationStatusBadge,
          {
            status: workspace.is_active ? "connected" : "disconnected",
            lastSync: workspace.last_activity_at
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.settings, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: styles$3.settingsTitle, children: "Notification Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$3.settingRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: workspace.enable_notifications,
              onChange: (e) => handleUpdateSettings({ enable_notifications: e.target.checked })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Enable notifications" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$3.settingRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: workspace.enable_commands,
              onChange: (e) => handleUpdateSettings({ enable_commands: e.target.checked })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Enable slash commands" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$3.settingRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: workspace.enable_ai_assistant,
              onChange: (e) => handleUpdateSettings({ enable_ai_assistant: e.target.checked })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Enable AI assistant" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.channels, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: styles$3.settingsTitle, children: "Default Channels" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.channelRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { children: "Announcements Channel:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "text",
              className: styles$3.channelInput,
              placeholder: "#announcements",
              value: workspace.default_announcements_channel || "",
              onChange: (e) => handleUpdateSettings({ default_announcements_channel: e.target.value })
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.channelRow, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { children: "Alerts Channel:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "text",
              className: styles$3.channelInput,
              placeholder: "#alerts",
              value: workspace.default_alerts_channel || "",
              onChange: (e) => handleUpdateSettings({ default_alerts_channel: e.target.value })
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.actions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$3.testButton,
            onClick: handleTestConnection,
            disabled: testing,
            children: testing ? "Testing..." : "Test Connection"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { className: styles$3.disconnectButton, onClick: handleDisconnect, children: "Disconnect" })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.instructions, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: styles$3.instructionsTitle, children: "Slack Integration Features" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "📢 Automatic notifications for course announcements" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "⏰ Deadline reminders sent to designated channels" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "📊 Grade release notifications (optional)" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "🆕 New content availability alerts" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "💬 Discussion reply notifications" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "🤖 AI assistant for course questions (beta)" })
      ] })
    ] })
  ] });
};
const panel$1 = "_panel_o5mk4_1";
const header$1 = "_header_o5mk4_1";
const title$1 = "_title_o5mk4_1";
const description$1 = "_description_o5mk4_1";
const addButton = "_addButton_o5mk4_1";
const form = "_form_o5mk4_1";
const formGroup = "_formGroup_o5mk4_1";
const input = "_input_o5mk4_1";
const formActions = "_formActions_o5mk4_1";
const cancelButton = "_cancelButton_o5mk4_1";
const submitButton = "_submitButton_o5mk4_1";
const emptyState = "_emptyState_o5mk4_1";
const tabs$1 = "_tabs_o5mk4_4";
const tab$1 = "_tab_o5mk4_4";
const active = "_active_o5mk4_27";
const webhookList = "_webhookList_o5mk4_32";
const webhookCard = "_webhookCard_o5mk4_38";
const webhookHeader = "_webhookHeader_o5mk4_44";
const webhookName = "_webhookName_o5mk4_51";
const webhookUrl = "_webhookUrl_o5mk4_57";
const webhookToken = "_webhookToken_o5mk4_64";
const webhookStats = "_webhookStats_o5mk4_76";
const webhookActions = "_webhookActions_o5mk4_84";
const testButton = "_testButton_o5mk4_89";
const deleteButton = "_deleteButton_o5mk4_103";
const select = "_select_o5mk4_117";
const styles$2 = {
  panel: panel$1,
  header: header$1,
  title: title$1,
  description: description$1,
  addButton,
  form,
  formGroup,
  input,
  formActions,
  cancelButton,
  submitButton,
  emptyState,
  tabs: tabs$1,
  tab: tab$1,
  active,
  webhookList,
  webhookCard,
  webhookHeader,
  webhookName,
  webhookUrl,
  webhookToken,
  webhookStats,
  webhookActions,
  testButton,
  deleteButton,
  select
};
const WebhookManager = ({
  organizationId,
  outboundWebhooks,
  inboundWebhooks,
  onRefresh
}) => {
  const [activeTab2, setActiveTab] = reactExports.useState("outbound");
  const [showAddForm, setShowAddForm] = reactExports.useState(false);
  const [formData, setFormData] = reactExports.useState({
    name: "",
    target_url: "",
    auth_type: "none",
    event_types: []
  });
  const handleCreateOutbound = async (e) => {
    e.preventDefault();
    try {
      await integrationsService.createOutboundWebhook(organizationId, formData);
      setShowAddForm(false);
      setFormData({ name: "", target_url: "", auth_type: "none", event_types: [] });
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to create webhook");
    }
  };
  const handleTestWebhook = async (webhookId) => {
    try {
      const result = await integrationsService.testOutboundWebhook(webhookId);
      alert(result.success ? `Success! Status: ${result.status_code}` : `Failed: ${result.message}`);
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to test webhook");
    }
  };
  const handleDeleteWebhook = async (webhookId) => {
    if (!window.confirm("Delete this webhook?")) return;
    try {
      await integrationsService.deleteOutboundWebhook(webhookId);
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to delete webhook");
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.panel, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$2.title, children: "🔗 Webhooks" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2.description, children: "Send and receive events to/from external services" })
      ] }),
      activeTab2 === "outbound" && /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: styles$2.addButton,
          onClick: () => setShowAddForm(!showAddForm),
          children: showAddForm ? "Cancel" : "+ Add Webhook"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.tabs, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          className: `${styles$2.tab} ${activeTab2 === "outbound" ? styles$2.active : ""}`,
          onClick: () => setActiveTab("outbound"),
          children: [
            "Outbound (",
            outboundWebhooks.length,
            ")"
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          className: `${styles$2.tab} ${activeTab2 === "inbound" ? styles$2.active : ""}`,
          onClick: () => setActiveTab("inbound"),
          children: [
            "Inbound (",
            inboundWebhooks.length,
            ")"
          ]
        }
      )
    ] }),
    showAddForm && activeTab2 === "outbound" && /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleCreateOutbound, className: styles$2.form, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { children: "Webhook Name *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "text",
            className: styles$2.input,
            placeholder: "e.g., Zapier Enrollment Sync",
            value: formData.name,
            onChange: (e) => setFormData({ ...formData, name: e.target.value }),
            required: true
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { children: "Target URL *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "url",
            className: styles$2.input,
            placeholder: "https://hooks.zapier.com/...",
            value: formData.target_url,
            onChange: (e) => setFormData({ ...formData, target_url: e.target.value }),
            required: true
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formGroup, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { children: "Authentication Type" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "select",
          {
            className: styles$2.select,
            value: formData.auth_type,
            onChange: (e) => setFormData({ ...formData, auth_type: e.target.value }),
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "none", children: "None" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "bearer", children: "Bearer Token" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "basic", children: "Basic Auth" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "hmac", children: "HMAC Signature" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "api_key", children: "API Key" })
            ]
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.formActions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { type: "button", className: styles$2.cancelButton, onClick: () => setShowAddForm(false), children: "Cancel" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { type: "submit", className: styles$2.submitButton, children: "Create Webhook" })
      ] })
    ] }),
    activeTab2 === "outbound" && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.webhookList, children: outboundWebhooks.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No outbound webhooks configured" }) }) : outboundWebhooks.map((webhook) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.webhookCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.webhookHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$2.webhookName, children: webhook.name }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2.webhookUrl, children: webhook.target_url })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          IntegrationStatusBadge,
          {
            status: webhook.is_active ? "connected" : "disconnected",
            lastSync: webhook.last_triggered_at
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.webhookStats, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Success: ",
          webhook.success_count
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Failed: ",
          webhook.failure_count
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Auth: ",
          webhook.auth_type
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.webhookActions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$2.testButton,
            onClick: () => handleTestWebhook(webhook.id),
            children: "Test"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$2.deleteButton,
            onClick: () => handleDeleteWebhook(webhook.id),
            children: "Delete"
          }
        )
      ] })
    ] }, webhook.id)) }),
    activeTab2 === "inbound" && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.webhookList, children: inboundWebhooks.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.emptyState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "No inbound webhooks configured" }) }) : inboundWebhooks.map((webhook) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.webhookCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.webhookHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$2.webhookName, children: webhook.name }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("code", { className: styles$2.webhookToken, children: [
            window.location.origin,
            "/webhooks/",
            webhook.webhook_token
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          IntegrationStatusBadge,
          {
            status: webhook.is_active ? "connected" : "disconnected",
            lastSync: webhook.last_received_at
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2.webhookStats, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Received: ",
          webhook.total_received
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Processed: ",
          webhook.total_processed
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Failed: ",
          webhook.total_failed
        ] })
      ] })
    ] }, webhook.id)) })
  ] });
};
const panel = "_panel_1omu5_1";
const header = "_header_1omu5_1";
const title = "_title_1omu5_1";
const description = "_description_1omu5_1";
const providerList = "_providerList_1omu5_4";
const providerCard = "_providerCard_1omu5_11";
const providerHeader = "_providerHeader_1omu5_18";
const providerInfo = "_providerInfo_1omu5_25";
const providerIcon = "_providerIcon_1omu5_31";
const providerName = "_providerName_1omu5_35";
const providerDetails = "_providerDetails_1omu5_41";
const tokenInfo = "_tokenInfo_1omu5_47";
const tokenStats = "_tokenStats_1omu5_54";
const errorBadge = "_errorBadge_1omu5_62";
const tokenError = "_tokenError_1omu5_70";
const providerActions = "_providerActions_1omu5_79";
const connectButton = "_connectButton_1omu5_84";
const refreshButton$1 = "_refreshButton_1omu5_99";
const revokeButton = "_revokeButton_1omu5_114";
const infoBox = "_infoBox_1omu5_129";
const infoTitle = "_infoTitle_1omu5_136";
const infoList = "_infoList_1omu5_149";
const styles$1 = {
  panel,
  header,
  title,
  description,
  providerList,
  providerCard,
  providerHeader,
  providerInfo,
  providerIcon,
  providerName,
  providerDetails,
  tokenInfo,
  tokenStats,
  errorBadge,
  tokenError,
  providerActions,
  connectButton,
  refreshButton: refreshButton$1,
  revokeButton,
  infoBox,
  infoTitle,
  infoList
};
const PROVIDERS = [
  { id: "google", name: "Google", icon: "🔵", color: "#4285F4" },
  { id: "microsoft", name: "Microsoft", icon: "🟦", color: "#00A4EF" },
  { id: "slack", name: "Slack", icon: "💬", color: "#4A154B" },
  { id: "github", name: "GitHub", icon: "🐙", color: "#181717" },
  { id: "zoom", name: "Zoom", icon: "🎥", color: "#2D8CFF" }
];
const OAuthConnectionsPanel = ({
  userId,
  organizationId,
  tokens,
  onRefresh
}) => {
  const handleConnect = (provider) => {
    const redirectUri = `${window.location.origin}/integrations/oauth/callback`;
    const scopesMap = {
      google: ["profile", "email", "openid"],
      microsoft: ["User.Read", "Calendars.ReadWrite"],
      slack: ["identity.basic"],
      github: ["read:user"],
      zoom: ["user:read"]
    };
    integrationsService.initiateOAuthFlow(
      provider,
      scopesMap[provider],
      redirectUri
    );
  };
  const handleRevoke = async (tokenId, providerName2) => {
    if (!window.confirm(`Revoke ${providerName2} connection?`)) return;
    try {
      await integrationsService.revokeOAuthToken(tokenId);
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to revoke connection");
    }
  };
  const handleRefresh = async (tokenId) => {
    try {
      await integrationsService.refreshOAuthToken(tokenId);
      alert("Token refreshed successfully");
      onRefresh();
    } catch (error2) {
      alert(error2.response?.data?.message || "Failed to refresh token");
    }
  };
  const getTokenForProvider = (providerId) => {
    return tokens.find((t) => t.provider === providerId);
  };
  const isTokenExpired = (token) => {
    if (!token.expires_at) return false;
    return new Date(token.expires_at) < /* @__PURE__ */ new Date();
  };
  const formatExpiration = (expiresAt) => {
    if (!expiresAt) return "Never expires";
    const date = new Date(expiresAt);
    const now = /* @__PURE__ */ new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.floor(diffMs / 864e5);
    if (diffMs < 0) return "Expired";
    if (diffDays === 0) return "Expires today";
    if (diffDays === 1) return "Expires tomorrow";
    if (diffDays < 7) return `Expires in ${diffDays} days`;
    return `Expires ${date.toLocaleDateString()}`;
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.panel, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.header, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: styles$1.title, children: "🔐 OAuth Connections" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.description, children: "Manage connected third-party services and access tokens" })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.providerList, children: PROVIDERS.map((provider) => {
      const token = getTokenForProvider(provider.id);
      const isExpired = token ? isTokenExpired(token) : false;
      return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.providerCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.providerHeader, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.providerInfo, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.providerIcon, children: provider.icon }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$1.providerName, children: provider.name }),
              token && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.providerDetails, children: formatExpiration(token.expires_at) })
            ] })
          ] }),
          token ? /* @__PURE__ */ jsxRuntimeExports.jsx(
            IntegrationStatusBadge,
            {
              status: !token.is_valid ? "error" : isExpired ? "error" : "connected",
              lastSync: token.last_used_at,
              errorMessage: token.last_error || void 0
            }
          ) : /* @__PURE__ */ jsxRuntimeExports.jsx(IntegrationStatusBadge, { status: "disconnected" })
        ] }),
        token && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.tokenInfo, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.tokenStats, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
              "Scopes: ",
              token.scopes.length > 0 ? token.scopes.join(", ") : "None"
            ] }),
            token.consecutive_failures > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.errorBadge, children: [
              token.consecutive_failures,
              " failed attempt(s)"
            ] })
          ] }),
          token.last_error && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.tokenError, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Last Error:" }),
            " ",
            token.last_error
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.providerActions, children: !token ? /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$1.connectButton,
            onClick: () => handleConnect(provider.id),
            children: "Connect"
          }
        ) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          isExpired && /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              className: styles$1.refreshButton,
              onClick: () => handleRefresh(token.id),
              children: "Refresh Token"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              className: styles$1.revokeButton,
              onClick: () => handleRevoke(token.id, provider.name),
              children: "Revoke Access"
            }
          )
        ] }) })
      ] }, provider.id);
    }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.infoBox, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { className: styles$1.infoTitle, children: "About OAuth Connections" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "OAuth connections allow this platform to access external services on your behalf. Tokens are encrypted and stored securely. You can revoke access at any time." }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: styles$1.infoList, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Google:" }),
          " Used for Calendar sync and Google Drive integration"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Microsoft:" }),
          " Used for Outlook Calendar and OneDrive integration"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Slack:" }),
          " Used for workspace notifications and commands"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "GitHub:" }),
          " Used for code repository integration and version control"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Zoom:" }),
          " Used for virtual classroom and meeting scheduling"
        ] })
      ] })
    ] })
  ] });
};
const container = "_container_12md8_9";
const pageHeader = "_pageHeader_12md8_16";
const pageTitle = "_pageTitle_12md8_25";
const pageDescription = "_pageDescription_12md8_32";
const refreshButton = "_refreshButton_12md8_38";
const errorBanner = "_errorBanner_12md8_61";
const tabs = "_tabs_12md8_81";
const tab = "_tab_12md8_81";
const activeTab = "_activeTab_12md8_111";
const errorTab = "_errorTab_12md8_117";
const tabIcon = "_tabIcon_12md8_121";
const tabLabel = "_tabLabel_12md8_125";
const tabBadge = "_tabBadge_12md8_129";
const tabErrorIndicator = "_tabErrorIndicator_12md8_147";
const tabContent = "_tabContent_12md8_161";
const errorState = "_errorState_12md8_177";
const styles = {
  container,
  pageHeader,
  pageTitle,
  pageDescription,
  refreshButton,
  errorBanner,
  tabs,
  tab,
  activeTab,
  errorTab,
  tabIcon,
  tabLabel,
  tabBadge,
  tabErrorIndicator,
  tabContent,
  errorState
};
const IntegrationsSettings = ({
  organizationId,
  userId
}) => {
  const [activeTab2, setActiveTab] = reactExports.useState("lti");
  const {
    ltiPlatforms,
    ltiError,
    calendars,
    calendarsError,
    slackWorkspace,
    slackError,
    outboundWebhooks,
    inboundWebhooks,
    webhooksError,
    oauthTokens,
    oauthError,
    isLoading,
    hasError,
    refreshAll,
    refreshLTI,
    refreshCalendars,
    refreshSlack,
    refreshWebhooks,
    refreshOAuth
  } = useIntegrations(organizationId, userId);
  const tabs2 = [
    {
      id: "lti",
      label: "LTI Platforms",
      icon: "🔗",
      count: ltiPlatforms.length,
      error: ltiError
    },
    {
      id: "calendar",
      label: "Calendar Sync",
      icon: "📅",
      count: calendars.length,
      error: calendarsError
    },
    {
      id: "slack",
      label: "Slack",
      icon: "💬",
      count: slackWorkspace ? 1 : 0,
      error: slackError
    },
    {
      id: "webhooks",
      label: "Webhooks",
      icon: "🔗",
      count: outboundWebhooks.length + inboundWebhooks.length,
      error: webhooksError
    },
    {
      id: "oauth",
      label: "OAuth Connections",
      icon: "🔐",
      count: oauthTokens.length,
      error: oauthError
    }
  ];
  const renderTabContent = () => {
    switch (activeTab2) {
      case "lti":
        return /* @__PURE__ */ jsxRuntimeExports.jsx(
          LTIIntegrationPanel,
          {
            organizationId,
            platforms: ltiPlatforms,
            onRefresh: refreshLTI
          }
        );
      case "calendar":
        if (!userId) {
          return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.errorState, children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Calendar sync requires user authentication" }) });
        }
        return /* @__PURE__ */ jsxRuntimeExports.jsx(
          CalendarSyncPanel,
          {
            userId,
            calendars,
            onRefresh: refreshCalendars
          }
        );
      case "slack":
        return /* @__PURE__ */ jsxRuntimeExports.jsx(
          SlackIntegrationPanel,
          {
            organizationId,
            workspace: slackWorkspace,
            onRefresh: refreshSlack
          }
        );
      case "webhooks":
        return /* @__PURE__ */ jsxRuntimeExports.jsx(
          WebhookManager,
          {
            organizationId,
            outboundWebhooks,
            inboundWebhooks,
            onRefresh: refreshWebhooks
          }
        );
      case "oauth":
        return /* @__PURE__ */ jsxRuntimeExports.jsx(
          OAuthConnectionsPanel,
          {
            userId,
            organizationId,
            tokens: oauthTokens,
            onRefresh: refreshOAuth
          }
        );
      default:
        return null;
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.container, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.pageHeader, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles.pageTitle, children: "Integrations" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.pageDescription, children: "Connect external services and manage integration settings" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: styles.refreshButton,
          onClick: refreshAll,
          disabled: isLoading,
          title: "Refresh all integrations",
          children: isLoading ? "⟳ Refreshing..." : "⟳ Refresh"
        }
      )
    ] }),
    hasError && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.errorBanner, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "⚠️ Some integrations failed to load." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Check individual tabs for details." })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.tabs, children: tabs2.map((tab2) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "button",
      {
        className: `${styles.tab} ${activeTab2 === tab2.id ? styles.activeTab : ""} ${tab2.error ? styles.errorTab : ""}`,
        onClick: () => setActiveTab(tab2.id),
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.tabIcon, children: tab2.icon }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.tabLabel, children: tab2.label }),
          tab2.count !== void 0 && tab2.count > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.tabBadge, children: tab2.count }),
          tab2.error && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.tabErrorIndicator, title: tab2.error, children: "!" })
        ]
      },
      tab2.id
    )) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.tabContent, children: renderTabContent() })
  ] });
};
export {
  IntegrationsSettings,
  IntegrationsSettings as default
};
//# sourceMappingURL=IntegrationsSettings-BREqIaEX.js.map
