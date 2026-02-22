import { a as axios, j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { t as tokenManager, H as Heading, B as Button, C as Card } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { u as useAppSelector } from "./hooks-Dtz71KqZ.js";
import "./state-vendor-B_izx0oA.js";
const AVAILABLE_PROVIDERS = [
  { name: "openai", displayName: "OpenAI", models: ["gpt-4-vision-preview", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"], supportsVision: true },
  { name: "anthropic", displayName: "Anthropic", models: ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-3.5-sonnet"], supportsVision: true },
  { name: "deepseek", displayName: "Deepseek", models: ["deepseek-vl", "deepseek-chat"], supportsVision: true },
  { name: "qwen", displayName: "Qwen (Alibaba)", models: ["qwen-vl-plus", "qwen-vl-max"], supportsVision: true },
  { name: "ollama", displayName: "Ollama (Local)", models: ["llava", "bakllava", "llava-llama3"], supportsVision: true },
  { name: "llama", displayName: "Meta Llama", models: ["llama-3.2-vision-90b", "llama-3.2-vision-11b"], supportsVision: true },
  { name: "gemini", displayName: "Google Gemini", models: ["gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash"], supportsVision: true },
  { name: "mistral", displayName: "Mistral", models: ["pixtral-12b", "mistral-large"], supportsVision: true }
];
const mockSettings = {
  organizationName: "Acme Corporation",
  contactEmail: "admin@acme.com",
  contactPhone: "+1 (555) 123-4567",
  website: "https://acme.com",
  address: "123 Business St, City, State 12345",
  logoUrl: "",
  primaryColor: "#3b82f6",
  secondaryColor: "#10b981",
  customDomain: "training.acme.com",
  requireCourseApproval: true,
  allowSelfEnrollment: false,
  certificateEnabled: true,
  minPassingScore: 70,
  ssoEnabled: false,
  ssoProvider: "None",
  slackWebhookUrl: "",
  emailNotifications: true,
  subscriptionPlan: "Enterprise",
  maxTrainers: 50,
  maxStudents: 1e3,
  storageLimit: 100
};
const OrganizationSettings = () => {
  const user = useAppSelector((state) => state.user.profile);
  const [settings, setSettings] = reactExports.useState(mockSettings);
  const [activeTab, setActiveTab] = reactExports.useState("profile");
  const [isSaving, setIsSaving] = reactExports.useState(false);
  const [llmProviders, setLlmProviders] = reactExports.useState([]);
  const [loadingProviders, setLoadingProviders] = reactExports.useState(false);
  const [providerError, setProviderError] = reactExports.useState(null);
  const [showAddProvider, setShowAddProvider] = reactExports.useState(false);
  const [newProviderName, setNewProviderName] = reactExports.useState("");
  const [newProviderModel, setNewProviderModel] = reactExports.useState("");
  const [newProviderApiKey, setNewProviderApiKey] = reactExports.useState("");
  const [testingConnection, setTestingConnection] = reactExports.useState(false);
  const [connectionTestResult, setConnectionTestResult] = reactExports.useState(null);
  const loadLLMProviders = reactExports.useCallback(async () => {
    const orgId = user?.organizationId;
    if (!orgId) return;
    setLoadingProviders(true);
    setProviderError(null);
    try {
      const response = await axios.get(
        `/api/v1/organizations/${orgId}/llm-config`,
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`
          }
        }
      );
      setLlmProviders(response.data.configs || []);
    } catch (err) {
      console.error("Failed to load LLM providers:", err);
      setProviderError("Failed to load AI provider configurations");
    } finally {
      setLoadingProviders(false);
    }
  }, [user?.organizationId]);
  reactExports.useEffect(() => {
    if (activeTab === "ai-providers") {
      loadLLMProviders();
    }
  }, [activeTab, loadLLMProviders]);
  const handleUpdateSettings = async (section) => {
    setIsSaving(true);
    try {
      console.log("Updating settings:", { section, settings });
      await new Promise((resolve) => setTimeout(resolve, 1e3));
      alert(`${section} settings updated successfully!`);
    } catch (err) {
      console.error("Failed to update settings:", err);
      alert("Failed to update settings. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };
  const handleInputChange = (field, value) => {
    setSettings((prev) => ({ ...prev, [field]: value }));
  };
  const renderTabs = () => {
    const tabs = [
      { id: "profile", label: "Organization Profile", icon: "🏢" },
      { id: "branding", label: "Branding", icon: "🎨" },
      { id: "training", label: "Training Policies", icon: "📚" },
      { id: "integrations", label: "Integrations", icon: "🔌" },
      { id: "ai-providers", label: "AI Providers", icon: "🤖" },
      { id: "subscription", label: "Subscription", icon: "💳" }
    ];
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
      display: "flex",
      gap: "0.5rem",
      marginBottom: "1.5rem",
      borderBottom: "2px solid #e5e7eb",
      overflowX: "auto",
      flexWrap: "wrap"
    }, children: tabs.map((tab) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "button",
      {
        onClick: () => setActiveTab(tab.id),
        style: {
          padding: "0.75rem 1.25rem",
          fontSize: "0.875rem",
          fontWeight: 500,
          border: "none",
          borderBottom: activeTab === tab.id ? "3px solid #3b82f6" : "3px solid transparent",
          backgroundColor: "transparent",
          color: activeTab === tab.id ? "#3b82f6" : "#6b7280",
          cursor: "pointer",
          transition: "all 0.2s",
          whiteSpace: "nowrap"
        },
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: { marginRight: "0.5rem" }, children: tab.icon }),
          tab.label
        ]
      },
      tab.id
    )) });
  };
  const renderProfileTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Organization Profile" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "orgName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Organization Name *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "orgName",
            name: "orgName",
            type: "text",
            value: settings.organizationName,
            onChange: (e) => handleInputChange("organizationName", e.target.value),
            required: true
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "contactEmail", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Contact Email *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "contactEmail",
              name: "contactEmail",
              type: "email",
              value: settings.contactEmail,
              onChange: (e) => handleInputChange("contactEmail", e.target.value),
              required: true
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "contactPhone", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Contact Phone" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "contactPhone",
              name: "contactPhone",
              type: "tel",
              value: settings.contactPhone,
              onChange: (e) => handleInputChange("contactPhone", e.target.value)
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "website", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Website" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "website",
            name: "website",
            type: "url",
            value: settings.website,
            onChange: (e) => handleInputChange("website", e.target.value)
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "address", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Address" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "textarea",
          {
            id: "address",
            name: "address",
            value: settings.address,
            onChange: (e) => handleInputChange("address", e.target.value),
            rows: 3,
            style: {
              width: "100%",
              padding: "0.75rem",
              fontSize: "0.875rem",
              border: "1px solid #d1d5db",
              borderRadius: "0.375rem",
              fontFamily: "inherit"
            }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Profile"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Profile Settings"
        }
      ) })
    ] })
  ] });
  const renderBrandingTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Branding & Appearance" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "logoUrl", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Organization Logo URL" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "logoUrl",
            name: "logoUrl",
            type: "url",
            placeholder: "https://example.com/logo.png",
            value: settings.logoUrl,
            onChange: (e) => handleInputChange("logoUrl", e.target.value)
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "Upload your logo and paste the URL here. Recommended size: 200x50px" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "primaryColor", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Primary Color" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem", alignItems: "center" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "primaryColor",
                name: "primaryColor",
                type: "color",
                value: settings.primaryColor,
                onChange: (e) => handleInputChange("primaryColor", e.target.value),
                style: { width: "60px", height: "40px", cursor: "pointer", border: "1px solid #d1d5db", borderRadius: "0.375rem" }
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "text",
                value: settings.primaryColor,
                onChange: (e) => handleInputChange("primaryColor", e.target.value),
                style: { flex: 1 }
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "secondaryColor", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Secondary Color" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem", alignItems: "center" }, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "secondaryColor",
                name: "secondaryColor",
                type: "color",
                value: settings.secondaryColor,
                onChange: (e) => handleInputChange("secondaryColor", e.target.value),
                style: { width: "60px", height: "40px", cursor: "pointer", border: "1px solid #d1d5db", borderRadius: "0.375rem" }
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "text",
                value: settings.secondaryColor,
                onChange: (e) => handleInputChange("secondaryColor", e.target.value),
                style: { flex: 1 }
              }
            )
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "customDomain", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Custom Domain" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "customDomain",
            name: "customDomain",
            type: "text",
            placeholder: "training.yourcompany.com",
            value: settings.customDomain,
            onChange: (e) => handleInputChange("customDomain", e.target.value)
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "Contact support to configure DNS settings for your custom domain" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Branding"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Branding Settings"
        }
      ) })
    ] })
  ] });
  const renderTrainingTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Training Policies" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Require Course Approval" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Trainers must get approval before publishing courses" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.requireCourseApproval,
            onChange: (e) => handleInputChange("requireCourseApproval", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Allow Self-Enrollment" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Students can enroll in courses without trainer approval" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.allowSelfEnrollment,
            onChange: (e) => handleInputChange("allowSelfEnrollment", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Enable Certificates" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Students receive certificates upon course completion" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.certificateEnabled,
            onChange: (e) => handleInputChange("certificateEnabled", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "minPassingScore", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Minimum Passing Score (%)" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "minPassingScore",
            name: "minPassingScore",
            type: "number",
            min: "0",
            max: "100",
            value: settings.minPassingScore,
            onChange: (e) => handleInputChange("minPassingScore", parseInt(e.target.value))
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "Default minimum score required to pass quizzes and assessments" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Training Policies"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Training Policies"
        }
      ) })
    ] })
  ] });
  const renderIntegrationsTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Integrations & Notifications" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Single Sign-On (SSO)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Enable SSO authentication for your organization" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.ssoEnabled,
            onChange: (e) => handleInputChange("ssoEnabled", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      settings.ssoEnabled && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "ssoProvider", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "SSO Provider" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "select",
          {
            id: "ssoProvider",
            name: "ssoProvider",
            value: settings.ssoProvider,
            onChange: (e) => handleInputChange("ssoProvider", e.target.value),
            style: {
              width: "100%",
              padding: "0.75rem",
              fontSize: "0.875rem",
              border: "1px solid #d1d5db",
              borderRadius: "0.375rem",
              backgroundColor: "white"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "None", children: "Select Provider" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "Google", children: "Google Workspace" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "Microsoft", children: "Microsoft Azure AD" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "Okta", children: "Okta" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "SAML", children: "Generic SAML 2.0" })
            ]
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "slackWebhook", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Slack Webhook URL" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "slackWebhook",
            name: "slackWebhook",
            type: "url",
            placeholder: "https://hooks.slack.com/services/...",
            value: settings.slackWebhookUrl,
            onChange: (e) => handleInputChange("slackWebhookUrl", e.target.value)
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "Receive notifications about course completions and enrollments" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Email Notifications" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Send email notifications for important events" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.emailNotifications,
            onChange: (e) => handleInputChange("emailNotifications", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Integrations"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Integration Settings"
        }
      ) })
    ] })
  ] });
  const handleAddProvider = async () => {
    const orgId = user?.organizationId;
    if (!orgId || !newProviderName || !newProviderModel) {
      setProviderError("Please select a provider and model");
      return;
    }
    setIsSaving(true);
    setProviderError(null);
    try {
      await axios.post(
        `/api/v1/organizations/${orgId}/llm-config`,
        {
          provider_name: newProviderName,
          model_name: newProviderModel,
          api_key: newProviderApiKey,
          is_active: true,
          is_default: llmProviders.length === 0
          // First provider is default
        },
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`
          }
        }
      );
      setShowAddProvider(false);
      setNewProviderName("");
      setNewProviderModel("");
      setNewProviderApiKey("");
      setConnectionTestResult(null);
      await loadLLMProviders();
    } catch (err) {
      console.error("Failed to add provider:", err);
      setProviderError(err.response?.data?.detail || "Failed to add AI provider");
    } finally {
      setIsSaving(false);
    }
  };
  const handleDeleteProvider = async (configId) => {
    const orgId = user?.organizationId;
    if (!orgId) return;
    if (!confirm("Are you sure you want to remove this AI provider configuration?")) {
      return;
    }
    setIsSaving(true);
    try {
      await axios.delete(
        `/api/v1/organizations/${orgId}/llm-config/${configId}`,
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`
          }
        }
      );
      await loadLLMProviders();
    } catch (err) {
      console.error("Failed to delete provider:", err);
      setProviderError(err.response?.data?.detail || "Failed to delete provider");
    } finally {
      setIsSaving(false);
    }
  };
  const handleSetDefaultProvider = async (configId) => {
    const orgId = user?.organizationId;
    if (!orgId) return;
    setIsSaving(true);
    try {
      await axios.put(
        `/api/v1/organizations/${orgId}/llm-config/${configId}`,
        { is_default: true },
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`
          }
        }
      );
      await loadLLMProviders();
    } catch (err) {
      console.error("Failed to set default provider:", err);
      setProviderError(err.response?.data?.detail || "Failed to set default provider");
    } finally {
      setIsSaving(false);
    }
  };
  const handleTestConnection = async () => {
    const orgId = user?.organizationId;
    if (!orgId || !newProviderName || !newProviderApiKey) {
      setConnectionTestResult({ success: false, message: "Provider and API key are required" });
      return;
    }
    setTestingConnection(true);
    setConnectionTestResult(null);
    try {
      const response = await axios.post(
        `/api/v1/organizations/${orgId}/llm-config/test`,
        {
          provider_name: newProviderName,
          model_name: newProviderModel || "default",
          api_key: newProviderApiKey
        },
        {
          headers: {
            Authorization: `Bearer ${tokenManager.getToken()}`
          }
        }
      );
      setConnectionTestResult({
        success: response.data.success,
        message: response.data.message || "Connection successful!"
      });
    } catch (err) {
      setConnectionTestResult({
        success: false,
        message: err.response?.data?.detail || "Connection test failed"
      });
    } finally {
      setTestingConnection(false);
    }
  };
  const getModelsForProvider = (providerName) => {
    const provider = AVAILABLE_PROVIDERS.find((p) => p.name === providerName);
    return provider?.models || [];
  };
  const renderAIProvidersTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "AI Provider Configuration" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", marginBottom: "1.5rem", fontSize: "0.9rem" }, children: "Configure AI providers for screenshot analysis and course generation. These providers enable AI-powered features like extracting content from screenshots and generating course structures." }),
    providerError && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: {
      padding: "0.75rem 1rem",
      backgroundColor: "#fef2f2",
      border: "1px solid #fecaca",
      borderRadius: "0.375rem",
      color: "#dc2626",
      marginBottom: "1rem",
      display: "flex",
      alignItems: "center",
      gap: "0.5rem"
    }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "⚠️" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: providerError }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          onClick: () => setProviderError(null),
          style: {
            marginLeft: "auto",
            background: "none",
            border: "none",
            cursor: "pointer",
            fontSize: "1.25rem",
            color: "#dc2626"
          },
          children: "×"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { style: { margin: 0, fontSize: "1rem", fontWeight: 600 }, children: "Configured Providers" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "primary",
            onClick: () => setShowAddProvider(true),
            disabled: showAddProvider,
            children: "+ Add Provider"
          }
        )
      ] }),
      loadingProviders ? /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { textAlign: "center", padding: "2rem", color: "#666" }, children: "Loading providers..." }) : llmProviders.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: {
        padding: "2rem",
        backgroundColor: "#f9fafb",
        borderRadius: "0.5rem",
        textAlign: "center",
        color: "#666"
      }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0 0 0.5rem 0", fontSize: "1.1rem" }, children: "No AI providers configured" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.9rem" }, children: "Add an AI provider to enable screenshot-based course creation" })
      ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "grid", gap: "0.75rem" }, children: llmProviders.map((config) => {
        const providerInfo = AVAILABLE_PROVIDERS.find((p) => p.name === config.provider_name);
        return /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "div",
          {
            style: {
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "1rem",
              backgroundColor: config.is_default ? "#f0f9ff" : "#f9fafb",
              border: `1px solid ${config.is_default ? "#bae6fd" : "#e5e7eb"}`,
              borderRadius: "0.5rem"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", gap: "1rem" }, children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "div",
                  {
                    style: {
                      width: "40px",
                      height: "40px",
                      borderRadius: "50%",
                      backgroundColor: config.is_active ? "#10b981" : "#9ca3af",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "white",
                      fontSize: "1.25rem"
                    },
                    children: "🤖"
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: 0, fontWeight: 600 }, children: [
                    providerInfo?.displayName || config.provider_name,
                    config.is_default && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { style: {
                      marginLeft: "0.5rem",
                      padding: "0.125rem 0.5rem",
                      backgroundColor: "#3b82f6",
                      color: "white",
                      borderRadius: "1rem",
                      fontSize: "0.7rem",
                      fontWeight: 500
                    }, children: "DEFAULT" })
                  ] }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: "0.25rem 0 0", fontSize: "0.85rem", color: "#666" }, children: [
                    "Model: ",
                    config.model_name
                  ] })
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.5rem" }, children: [
                !config.is_default && /* @__PURE__ */ jsxRuntimeExports.jsx(
                  Button,
                  {
                    variant: "secondary",
                    onClick: () => handleSetDefaultProvider(config.id),
                    disabled: isSaving,
                    children: "Set Default"
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  Button,
                  {
                    variant: "danger",
                    onClick: () => handleDeleteProvider(config.id),
                    disabled: isSaving,
                    children: "Remove"
                  }
                )
              ] })
            ]
          },
          config.id
        );
      }) })
    ] }),
    showAddProvider && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: {
      padding: "1.5rem",
      backgroundColor: "#f9fafb",
      border: "1px solid #e5e7eb",
      borderRadius: "0.5rem"
    }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { style: { margin: 0, fontWeight: 600 }, children: "Add New AI Provider" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            onClick: () => {
              setShowAddProvider(false);
              setNewProviderName("");
              setNewProviderModel("");
              setNewProviderApiKey("");
              setConnectionTestResult(null);
            },
            style: {
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: "1.25rem",
              color: "#666"
            },
            children: "×"
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "providerName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Provider *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              id: "providerName",
              value: newProviderName,
              onChange: (e) => {
                setNewProviderName(e.target.value);
                setNewProviderModel("");
              },
              style: {
                width: "100%",
                padding: "0.75rem",
                fontSize: "0.875rem",
                border: "1px solid #d1d5db",
                borderRadius: "0.375rem",
                backgroundColor: "white"
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "Select Provider" }),
                AVAILABLE_PROVIDERS.map((provider) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: provider.name, children: [
                  provider.displayName,
                  " ",
                  provider.supportsVision ? "(Vision)" : ""
                ] }, provider.name))
              ]
            }
          )
        ] }),
        newProviderName && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "providerModel", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Model *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              id: "providerModel",
              value: newProviderModel,
              onChange: (e) => setNewProviderModel(e.target.value),
              style: {
                width: "100%",
                padding: "0.75rem",
                fontSize: "0.875rem",
                border: "1px solid #d1d5db",
                borderRadius: "0.375rem",
                backgroundColor: "white"
              },
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "Select Model" }),
                getModelsForProvider(newProviderName).map((model) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: model, children: model }, model))
              ]
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "providerApiKey", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: [
            "API Key ",
            newProviderName !== "ollama" ? "*" : "(Optional for local)"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "providerApiKey",
              name: "providerApiKey",
              type: "password",
              placeholder: "Enter your API key",
              value: newProviderApiKey,
              onChange: (e) => setNewProviderApiKey(e.target.value)
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.8rem", color: "#666", marginTop: "0.25rem" }, children: "Your API key is encrypted and stored securely" })
        ] }),
        connectionTestResult && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: {
          padding: "0.75rem 1rem",
          backgroundColor: connectionTestResult.success ? "#f0fdf4" : "#fef2f2",
          border: `1px solid ${connectionTestResult.success ? "#86efac" : "#fecaca"}`,
          borderRadius: "0.375rem",
          color: connectionTestResult.success ? "#166534" : "#dc2626"
        }, children: [
          connectionTestResult.success ? "✓" : "✗",
          " ",
          connectionTestResult.message
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem", paddingTop: "0.5rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "secondary",
              onClick: handleTestConnection,
              disabled: testingConnection || !newProviderName,
              children: testingConnection ? "Testing..." : "Test Connection"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              variant: "primary",
              onClick: handleAddProvider,
              disabled: isSaving || !newProviderName || !newProviderModel || newProviderName !== "ollama" && !newProviderApiKey,
              children: isSaving ? "Adding..." : "Add Provider"
            }
          )
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: {
      marginTop: "1.5rem",
      padding: "1rem",
      backgroundColor: "#fffbeb",
      border: "1px solid #fcd34d",
      borderRadius: "0.5rem"
    }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h4", { style: { margin: "0 0 0.5rem 0", color: "#92400e", fontSize: "0.95rem" }, children: "📋 Supported Providers" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "0.5rem" }, children: AVAILABLE_PROVIDERS.map((provider) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { fontSize: "0.85rem", color: "#78350f" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: provider.displayName }),
        provider.supportsVision && " 📷"
      ] }, provider.name)) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.8rem", color: "#92400e", marginTop: "0.75rem", marginBottom: 0 }, children: "📷 = Supports vision/image analysis for screenshot-based course creation" })
    ] })
  ] });
  const renderSubscriptionTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Subscription & Limits" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "1rem", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontWeight: 600, margin: 0, marginBottom: "0.5rem", color: "#0c4a6e" }, children: [
          "Current Plan: ",
          settings.subscriptionPlan
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "0.875rem", color: "#0c4a6e", margin: 0 }, children: [
          "Your organization is on the ",
          settings.subscriptionPlan,
          " plan with the following limits"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Max Trainers" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#3b82f6" }, children: settings.maxTrainers })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Max Students" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#10b981" }, children: settings.maxStudents })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "medium", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { margin: 0, fontSize: "0.85rem", color: "#666" }, children: "Storage Limit" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { margin: "0.5rem 0 0", fontSize: "2rem", fontWeight: "bold", color: "#f59e0b" }, children: [
            settings.storageLimit,
            " GB"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "1.5rem", backgroundColor: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", style: { fontSize: "1.1rem", marginBottom: "1rem" }, children: "Upgrade Your Plan" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginBottom: "1rem" }, children: "Need more trainers, students, or storage? Upgrade to a higher tier plan or contact our sales team for custom enterprise pricing." }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Contact Sales" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "1rem", backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 600, margin: 0, marginBottom: "0.5rem", color: "#991b1b" }, children: "⚠️ Danger Zone" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#991b1b", marginBottom: "1rem" }, children: "Permanently delete your organization and all associated data. This action cannot be undone." }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "danger", children: "Delete Organization" })
      ] })
    ] })
  ] });
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1200px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Organization Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Configure your organization's profile, branding, and policies" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/org-admin", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Back to Dashboard" }) })
    ] }),
    renderTabs(),
    activeTab === "profile" && renderProfileTab(),
    activeTab === "branding" && renderBrandingTab(),
    activeTab === "training" && renderTrainingTab(),
    activeTab === "integrations" && renderIntegrationsTab(),
    activeTab === "ai-providers" && renderAIProvidersTab(),
    activeTab === "subscription" && renderSubscriptionTab()
  ] }) });
};
export {
  OrganizationSettings
};
//# sourceMappingURL=OrganizationSettings-DR80S0Ae.js.map
