import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { H as Heading, B as Button, C as Card } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const PLAN_PRESETS = {
  Trial: {
    maxTrainers: 3,
    maxStudents: 25,
    storageLimit: 10,
    subscriptionMonths: 1
  },
  Professional: {
    maxTrainers: 10,
    maxStudents: 200,
    storageLimit: 50,
    subscriptionMonths: 12
  },
  Enterprise: {
    maxTrainers: 50,
    maxStudents: 1e3,
    storageLimit: 200,
    subscriptionMonths: 12
  }
};
const CreateOrganization = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = reactExports.useState(1);
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [formData, setFormData] = reactExports.useState({
    organizationName: "",
    contactEmail: "",
    contactPhone: "",
    website: "",
    address: "",
    adminFirstName: "",
    adminLastName: "",
    adminEmail: "",
    adminPhone: "",
    subscriptionPlan: "Professional",
    maxTrainers: 10,
    maxStudents: 200,
    storageLimit: 50,
    subscriptionMonths: 12
  });
  const handleInputChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };
  const handlePlanSelect = (plan) => {
    const preset = PLAN_PRESETS[plan];
    setFormData((prev) => ({
      ...prev,
      subscriptionPlan: plan,
      maxTrainers: preset.maxTrainers,
      maxStudents: preset.maxStudents,
      storageLimit: preset.storageLimit,
      subscriptionMonths: preset.subscriptionMonths
    }));
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (currentStep < 3) {
      setCurrentStep(currentStep + 1);
      return;
    }
    try {
      setIsSubmitting(true);
      console.log("Creating organization:", formData);
      await new Promise((resolve) => setTimeout(resolve, 1500));
      alert("Organization created successfully!");
      navigate("/admin/organizations");
    } catch (err) {
      console.error("Failed to create organization:", err);
      alert("Failed to create organization. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };
  const renderProgressBar = () => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }, children: [1, 2, 3].map((step) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: {
      flex: 1,
      textAlign: "center",
      fontSize: "0.875rem",
      fontWeight: currentStep === step ? 600 : 400,
      color: currentStep >= step ? "#3b82f6" : "#9ca3af"
    }, children: [
      "Step ",
      step
    ] }, step)) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", gap: "0.5rem" }, children: [1, 2, 3].map((step) => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: {
      flex: 1,
      height: "4px",
      backgroundColor: currentStep >= step ? "#3b82f6" : "#e5e7eb",
      borderRadius: "2px",
      transition: "background-color 0.3s"
    } }, step)) })
  ] });
  const renderStep1 = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.5rem", marginBottom: "1.5rem" }, children: "Basic Information" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "organizationName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Organization Name *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            id: "organizationName",
            name: "organizationName",
            type: "text",
            placeholder: "Acme Corporation",
            value: formData.organizationName,
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
              placeholder: "contact@acme.com",
              value: formData.contactEmail,
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
              placeholder: "+1 (555) 123-4567",
              value: formData.contactPhone,
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
            placeholder: "https://acme.com",
            value: formData.website,
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
            placeholder: "123 Business St, City, State 12345",
            value: formData.address,
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
      ] })
    ] })
  ] });
  const renderStep2 = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.5rem", marginBottom: "1.5rem" }, children: "Administrator Account" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.875rem", color: "#666", marginBottom: "1.5rem" }, children: "Create the initial administrator account for this organization. They will receive an email with login instructions." }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "adminFirstName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "First Name *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "adminFirstName",
              name: "adminFirstName",
              type: "text",
              placeholder: "John",
              value: formData.adminFirstName,
              onChange: (e) => handleInputChange("adminFirstName", e.target.value),
              required: true
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "adminLastName", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Last Name *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "adminLastName",
              name: "adminLastName",
              type: "text",
              placeholder: "Smith",
              value: formData.adminLastName,
              onChange: (e) => handleInputChange("adminLastName", e.target.value),
              required: true
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: "1rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "adminEmail", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Email Address *" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "adminEmail",
              name: "adminEmail",
              type: "email",
              placeholder: "john.smith@acme.com",
              value: formData.adminEmail,
              onChange: (e) => handleInputChange("adminEmail", e.target.value),
              required: true
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontSize: "0.75rem", color: "#666", marginTop: "0.25rem" }, children: "Login credentials will be sent to this email" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "adminPhone", style: { display: "block", fontWeight: 500, marginBottom: "0.5rem" }, children: "Phone Number" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              id: "adminPhone",
              name: "adminPhone",
              type: "tel",
              placeholder: "+1 (555) 987-6543",
              value: formData.adminPhone,
              onChange: (e) => handleInputChange("adminPhone", e.target.value)
            }
          )
        ] })
      ] })
    ] })
  ] });
  const renderStep3 = () => /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", style: { fontSize: "1.5rem", marginBottom: "1.5rem" }, children: "Subscription & Limits" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gap: "1.5rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { style: { display: "block", fontWeight: 500, marginBottom: "1rem" }, children: "Select Plan *" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1rem" }, children: Object.keys(PLAN_PRESETS).map((plan) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "button",
          {
            type: "button",
            onClick: () => handlePlanSelect(plan),
            style: {
              padding: "1.5rem",
              border: formData.subscriptionPlan === plan ? "2px solid #3b82f6" : "1px solid #d1d5db",
              borderRadius: "0.5rem",
              backgroundColor: formData.subscriptionPlan === plan ? "#eff6ff" : "white",
              cursor: "pointer",
              transition: "all 0.2s",
              textAlign: "left"
            },
            children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 600, fontSize: "1.1rem", margin: "0 0 0.5rem 0" }, children: plan }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "0.875rem", color: "#666", margin: 0 }, children: [
                PLAN_PRESETS[plan].maxTrainers,
                " trainers",
                /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
                PLAN_PRESETS[plan].maxStudents,
                " students",
                /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
                PLAN_PRESETS[plan].storageLimit,
                " GB storage"
              ] })
            ]
          },
          plan
        )) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "0.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 500, marginBottom: "1rem" }, children: "Custom Limits (Optional)" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1rem" }, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "maxTrainers", style: { display: "block", fontSize: "0.875rem", marginBottom: "0.5rem" }, children: "Max Trainers" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "maxTrainers",
                name: "maxTrainers",
                type: "number",
                min: "1",
                value: formData.maxTrainers,
                onChange: (e) => handleInputChange("maxTrainers", parseInt(e.target.value))
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "maxStudents", style: { display: "block", fontSize: "0.875rem", marginBottom: "0.5rem" }, children: "Max Students" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "maxStudents",
                name: "maxStudents",
                type: "number",
                min: "1",
                value: formData.maxStudents,
                onChange: (e) => handleInputChange("maxStudents", parseInt(e.target.value))
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "storageLimit", style: { display: "block", fontSize: "0.875rem", marginBottom: "0.5rem" }, children: "Storage (GB)" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "storageLimit",
                name: "storageLimit",
                type: "number",
                min: "1",
                value: formData.storageLimit,
                onChange: (e) => handleInputChange("storageLimit", parseInt(e.target.value))
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "subscriptionMonths", style: { display: "block", fontSize: "0.875rem", marginBottom: "0.5rem" }, children: "Duration (Months)" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                id: "subscriptionMonths",
                name: "subscriptionMonths",
                type: "number",
                min: "1",
                max: "36",
                value: formData.subscriptionMonths,
                onChange: (e) => handleInputChange("subscriptionMonths", parseInt(e.target.value))
              }
            )
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { padding: "1rem", backgroundColor: "#f0f9ff", border: "1px solid #bae6fd", borderRadius: "0.5rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { fontWeight: 600, marginBottom: "0.5rem", color: "#0c4a6e" }, children: "Summary" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { style: { fontSize: "0.875rem", color: "#0c4a6e", margin: 0 }, children: [
          "Organization: ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: formData.organizationName || "Not specified" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
          "Admin: ",
          /* @__PURE__ */ jsxRuntimeExports.jsxs("strong", { children: [
            formData.adminFirstName,
            " ",
            formData.adminLastName
          ] }),
          " (",
          formData.adminEmail,
          ")",
          /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
          "Plan: ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: formData.subscriptionPlan }),
          " - ",
          formData.subscriptionMonths,
          " month(s)",
          /* @__PURE__ */ jsxRuntimeExports.jsx("br", {}),
          "Limits: ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: formData.maxTrainers }),
          " trainers, ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: formData.maxStudents }),
          " students, ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: formData.storageLimit }),
          " GB"
        ] })
      ] })
    ] })
  ] });
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("main", { style: { padding: "2rem", maxWidth: "900px", margin: "0 auto" }, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem" }, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Create New Organization" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "#666", fontSize: "0.95rem" }, children: "Onboard a new corporate training customer" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/admin/organizations", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Cancel" }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, children: [
      renderProgressBar(),
      currentStep === 1 && renderStep1(),
      currentStep === 2 && renderStep2(),
      currentStep === 3 && renderStep3(),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { style: { display: "flex", gap: "0.75rem", justifyContent: "space-between", paddingTop: "2rem", borderTop: "1px solid #e5e7eb", marginTop: "2rem" }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: currentStep > 1 && /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "button",
            variant: "secondary",
            onClick: () => setCurrentStep(currentStep - 1),
            children: "Previous"
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "submit",
            variant: "primary",
            disabled: isSubmitting,
            children: isSubmitting ? "Creating..." : currentStep < 3 ? "Next" : "Create Organization"
          }
        )
      ] })
    ] }) })
  ] }) });
};
export {
  CreateOrganization
};
//# sourceMappingURL=CreateOrganization-C3hVJFW9.js.map
