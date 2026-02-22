import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { H as Heading, B as Button, C as Card } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const mockSettings = {
  platformName: "Course Creator Platform",
  supportEmail: "support@example.com",
  supportUrl: "https://support.example.com",
  defaultLanguage: "en",
  smtpHost: "smtp.example.com",
  smtpPort: 587,
  smtpUsername: "noreply@example.com",
  smtpPassword: "••••••••",
  fromEmail: "noreply@example.com",
  fromName: "Course Creator",
  storageProvider: "s3",
  s3Bucket: "course-creator-storage",
  s3Region: "us-east-1",
  s3AccessKey: "••••••••",
  maxFileSize: 100,
  sessionTimeout: 60,
  passwordMinLength: 8,
  requireMFA: false,
  allowPasswordReset: true,
  maxLoginAttempts: 5,
  enableCourseGeneration: true,
  enableLabEnvironments: true,
  enableCertificates: true,
  enableAnalytics: true,
  maintenanceMode: false,
  maintenanceMessage: "The platform is currently undergoing maintenance. Please check back soon."
};
const SystemSettings = () => {
  const [settings, setSettings] = reactExports.useState(mockSettings);
  const [activeTab, setActiveTab] = reactExports.useState("general");
  const [isSaving, setIsSaving] = reactExports.useState(false);
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
      { id: "general", label: "General", icon: "⚙️" },
      { id: "email", label: "Email", icon: "📧" },
      { id: "storage", label: "Storage", icon: "💾" },
      { id: "security", label: "Security", icon: "🔒" },
      { id: "features", label: "Features", icon: "✨" },
      { id: "maintenance", label: "Maintenance", icon: "🔧" }
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
  const renderGeneralTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "General Settings" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "platformName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Platform Name *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "platformName",
            name: "platformName",
            type: "text",
            value: settings.platformName,
            onChange: (e) => handleInputChange("platformName", e.target.value),
            required: true
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "supportEmail", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Support Email *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "supportEmail",
              name: "supportEmail",
              type: "email",
              value: settings.supportEmail,
              onChange: (e) => handleInputChange("supportEmail", e.target.value),
              required: true
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "supportUrl", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Support URL" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "supportUrl",
              name: "supportUrl",
              type: "url",
              value: settings.supportUrl,
              onChange: (e) => handleInputChange("supportUrl", e.target.value)
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "defaultLanguage", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Default Language" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "select",
          {
            id: "defaultLanguage",
            name: "defaultLanguage",
            value: settings.defaultLanguage,
            onChange: (e) => handleInputChange("defaultLanguage", e.target.value),
            style: {
              width: "100%",
              padding: "0.75rem",
              fontSize: "0.875rem",
              border: "1px solid #d1d5db",
              borderRadius: "0.375rem",
              backgroundColor: "white"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "en", children: "English" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "es", children: "Spanish" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "fr", children: "French" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "de", children: "German" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "zh", children: "Chinese" })
            ]
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("General"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save General Settings"
        }
      ) })
    ] })
  ] });
  const renderEmailTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Email Configuration" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "smtpHost", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "SMTP Host *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "smtpHost",
              name: "smtpHost",
              type: "text",
              placeholder: "smtp.example.com",
              value: settings.smtpHost,
              onChange: (e) => handleInputChange("smtpHost", e.target.value),
              required: true
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "smtpPort", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "SMTP Port *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "smtpPort",
              name: "smtpPort",
              type: "number",
              value: settings.smtpPort,
              onChange: (e) => handleInputChange("smtpPort", parseInt(e.target.value)),
              required: true
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "smtpUsername", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "SMTP Username" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "smtpUsername",
              name: "smtpUsername",
              type: "text",
              value: settings.smtpUsername,
              onChange: (e) => handleInputChange("smtpUsername", e.target.value)
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "smtpPassword", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "SMTP Password" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "smtpPassword",
              name: "smtpPassword",
              type: "password",
              value: settings.smtpPassword,
              onChange: (e) => handleInputChange("smtpPassword", e.target.value)
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "fromEmail", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "From Email *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "fromEmail",
              name: "fromEmail",
              type: "email",
              placeholder: "noreply@example.com",
              value: settings.fromEmail,
              onChange: (e) => handleInputChange("fromEmail", e.target.value),
              required: true
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "fromName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "From Name *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "fromName",
              name: "fromName",
              type: "text",
              placeholder: "Course Creator",
              value: settings.fromName,
              onChange: (e) => handleInputChange("fromName", e.target.value),
              required: true
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Email"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Email Settings"
        }
      ) })
    ] })
  ] });
  const renderStorageTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Storage Configuration" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "storageProvider", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Storage Provider *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "select",
          {
            id: "storageProvider",
            name: "storageProvider",
            value: settings.storageProvider,
            onChange: (e) => handleInputChange("storageProvider", e.target.value),
            style: {
              width: "100%",
              padding: "0.75rem",
              fontSize: "0.875rem",
              border: "1px solid #d1d5db",
              borderRadius: "0.375rem",
              backgroundColor: "white"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "local", children: "Local Storage" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "s3", children: "Amazon S3" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "azure", children: "Azure Blob Storage" })
            ]
          }
        )
      ] }),
      settings.storageProvider === "s3" && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "s3Bucket", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "S3 Bucket Name" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "s3Bucket",
                name: "s3Bucket",
                type: "text",
                value: settings.s3Bucket,
                onChange: (e) => handleInputChange("s3Bucket", e.target.value)
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "s3Region", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "S3 Region" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "s3Region",
                name: "s3Region",
                type: "text",
                value: settings.s3Region,
                onChange: (e) => handleInputChange("s3Region", e.target.value)
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "s3AccessKey", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "S3 Access Key" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "s3AccessKey",
              name: "s3AccessKey",
              type: "password",
              value: settings.s3AccessKey,
              onChange: (e) => handleInputChange("s3AccessKey", e.target.value)
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "maxFileSize", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Max File Size (MB)" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "maxFileSize",
            name: "maxFileSize",
            type: "number",
            min: "1",
            max: "1000",
            value: settings.maxFileSize,
            onChange: (e) => handleInputChange("maxFileSize", parseInt(e.target.value))
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Storage"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Storage Settings"
        }
      ) })
    ] })
  ] });
  const renderSecurityTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Security Settings" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "sessionTimeout", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Session Timeout (minutes)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "sessionTimeout",
              name: "sessionTimeout",
              type: "number",
              min: "5",
              max: "1440",
              value: settings.sessionTimeout,
              onChange: (e) => handleInputChange("sessionTimeout", parseInt(e.target.value))
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "passwordMinLength", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Min Password Length" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "passwordMinLength",
              name: "passwordMinLength",
              type: "number",
              min: "6",
              max: "32",
              value: settings.passwordMinLength,
              onChange: (e) => handleInputChange("passwordMinLength", parseInt(e.target.value))
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "maxLoginAttempts", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Max Login Attempts" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "maxLoginAttempts",
              name: "maxLoginAttempts",
              type: "number",
              min: "3",
              max: "10",
              value: settings.maxLoginAttempts,
              onChange: (e) => handleInputChange("maxLoginAttempts", parseInt(e.target.value))
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Require Multi-Factor Authentication (MFA)" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "All users must enable MFA to access the platform" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.requireMFA,
            onChange: (e) => handleInputChange("requireMFA", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Allow Password Reset" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Users can request password reset via email" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.allowPasswordReset,
            onChange: (e) => handleInputChange("allowPasswordReset", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Security"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Security Settings"
        }
      ) })
    ] })
  ] });
  const renderFeaturesTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Platform Features" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "AI Course Generation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Enable AI-powered course and content generation" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.enableCourseGeneration,
            onChange: (e) => handleInputChange("enableCourseGeneration", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Lab Environments" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Enable interactive coding lab environments" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.enableLabEnvironments,
            onChange: (e) => handleInputChange("enableLabEnvironments", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Certificates" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Enable course completion certificates" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.enableCertificates,
            onChange: (e) => handleInputChange("enableCertificates", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Analytics" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Enable learning analytics and reporting" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.enableAnalytics,
            onChange: (e) => handleInputChange("enableAnalytics", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => handleUpdateSettings("Features"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Save Feature Settings"
        }
      ) })
    ] })
  ] });
  const renderMaintenanceTab = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.25rem", marginBottom: "1.5rem" }, children: "Maintenance Mode" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "1rem", backgroundColor: "#fef2f2", border: "1px solid #fecaca", borderRadius: "0.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 600, margin: 0, marginBottom: "0.5rem", color: "#991b1b" }, children: "⚠️ Warning: Maintenance Mode" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#991b1b", margin: 0 }, children: "Enabling maintenance mode will prevent all users (except site admins) from accessing the platform." })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.375rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, margin: 0, marginBottom: "0.25rem" }, children: "Enable Maintenance Mode" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: "Put the platform in maintenance mode" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            type: "checkbox",
            checked: settings.maintenanceMode,
            onChange: (e) => handleInputChange("maintenanceMode", e.target.checked),
            style: { width: "20px", height: "20px", cursor: "pointer" }
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "maintenanceMessage", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Maintenance Message" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "textarea",
          {
            id: "maintenanceMessage",
            name: "maintenanceMessage",
            value: settings.maintenanceMessage,
            onChange: (e) => handleInputChange("maintenanceMessage", e.target.value),
            rows: 4,
            style: {
              width: "100%",
              padding: "0.75rem",
              fontSize: "0.875rem",
              border: "1px solid #d1d5db",
              borderRadius: "0.375rem",
              fontFamily: "inherit"
            }
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginTop: "0.5rem" }, children: "This message will be displayed to users during maintenance" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { paddingTop: "1rem", borderTop: "1px solid #e5e7eb" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "danger",
          onClick: () => handleUpdateSettings("Maintenance"),
          disabled: isSaving,
          children: isSaving ? "Saving..." : "Update Maintenance Settings"
        }
      ) })
    ] })
  ] });
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "1200px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "System Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Configure platform-wide settings and integrations" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard/site-admin", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Back to Dashboard" }) })
    ] }),
    renderTabs(),
    activeTab === "general" && renderGeneralTab(),
    activeTab === "email" && renderEmailTab(),
    activeTab === "storage" && renderStorageTab(),
    activeTab === "security" && renderSecurityTab(),
    activeTab === "features" && renderFeaturesTab(),
    activeTab === "maintenance" && renderMaintenanceTab()
  ] }) });
};
export {
  SystemSettings
};
//# sourceMappingURL=SystemSettings-D6bY3ZMd.js.map
