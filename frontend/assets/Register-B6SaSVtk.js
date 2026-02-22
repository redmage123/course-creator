import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { u as useAuth, a as SEO, H as Heading, C as Card, B as Button } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { C as Checkbox } from "./Checkbox-CEUsiksA.js";
import "./state-vendor-B_izx0oA.js";
const styles = {
  "registration-page": "_registration-page_10v5u_20",
  "registration-container": "_registration-container_10v5u_34",
  "registration-header": "_registration-header_10v5u_46",
  "registration-subtitle": "_registration-subtitle_10v5u_51",
  "registration-form": "_registration-form_10v5u_65",
  "registration-error-banner": "_registration-error-banner_10v5u_75",
  "registration-legal": "_registration-legal_10v5u_108",
  "registration-link": "_registration-link_10v5u_123",
  "registration-footer": "_registration-footer_10v5u_149",
  "registration-footer-text": "_registration-footer-text_10v5u_155"
};
const RegistrationPage = () => {
  useNavigate();
  const { register, isLoading } = useAuth();
  const [formData, setFormData] = reactExports.useState({
    email: "",
    username: "",
    fullName: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
    acceptPrivacy: false,
    newsletterOptIn: false
  });
  const [errors, setErrors] = reactExports.useState({});
  const validateForm = () => {
    const newErrors = {};
    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }
    if (!formData.username) {
      newErrors.username = "Username is required";
    } else if (formData.username.length < 3) {
      newErrors.username = "Username must be at least 3 characters";
    } else if (formData.username.length > 30) {
      newErrors.username = "Username must be at most 30 characters";
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      newErrors.username = "Username can only contain letters, numbers, hyphens, and underscores";
    }
    if (!formData.fullName) {
      newErrors.fullName = "Full name is required";
    } else if (formData.fullName.length < 2) {
      newErrors.fullName = "Full name must be at least 2 characters";
    } else if (formData.fullName.length > 100) {
      newErrors.fullName = "Full name must be at most 100 characters";
    }
    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    } else if (!/(?=.*[a-z])/.test(formData.password)) {
      newErrors.password = "Password must contain at least one lowercase letter";
    } else if (!/(?=.*[A-Z])/.test(formData.password)) {
      newErrors.password = "Password must contain at least one uppercase letter";
    } else if (!/(?=.*\d)/.test(formData.password)) {
      newErrors.password = "Password must contain at least one number";
    }
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }
    if (!formData.acceptTerms) {
      newErrors.acceptTerms = "You must accept the Terms of Service";
    }
    if (!formData.acceptPrivacy) {
      newErrors.acceptPrivacy = "You must accept the Privacy Policy";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors((prev) => ({ ...prev, submit: void 0 }));
    if (!validateForm()) {
      return;
    }
    try {
      await register({
        email: formData.email,
        username: formData.username,
        fullName: formData.fullName,
        password: formData.password,
        acceptTerms: formData.acceptTerms,
        acceptPrivacy: formData.acceptPrivacy,
        newsletterOptIn: formData.newsletterOptIn
      });
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : "Registration failed. Please try again."
      });
    }
  };
  const handleChange = (field) => (e) => {
    const value = field === "acceptTerms" || field === "acceptPrivacy" || field === "newsletterOptIn" ? e.target.checked : e.target.value;
    setFormData((prev) => ({
      ...prev,
      [field]: value
    }));
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: void 0
      }));
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      SEO,
      {
        title: "Register",
        description: "Create your Course Creator Platform account. Join thousands of learners and instructors. GDPR and CCPA compliant registration with secure data handling.",
        keywords: "register, sign up, create account, join course creator, student registration, instructor registration"
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx("main", { className: styles["registration-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["registration-container"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["registration-header"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", align: "center", gutterBottom: false, children: "Create Account" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["registration-subtitle"], children: "Join the Course Creator Platform" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "form",
        {
          onSubmit: handleSubmit,
          className: styles["registration-form"],
          noValidate: true,
          children: [
            errors.submit && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["registration-error-banner"], role: "alert", children: errors.submit }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "email",
                label: "Email Address",
                placeholder: "you@example.com",
                value: formData.email,
                onChange: handleChange("email"),
                error: errors.email,
                required: true,
                autoComplete: "email",
                autoFocus: true,
                disabled: isLoading
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "text",
                label: "Username",
                placeholder: "Choose a unique username",
                value: formData.username,
                onChange: handleChange("username"),
                error: errors.username,
                required: true,
                autoComplete: "username",
                disabled: isLoading
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "text",
                label: "Full Name",
                placeholder: "Enter your full name",
                value: formData.fullName,
                onChange: handleChange("fullName"),
                error: errors.fullName,
                required: true,
                autoComplete: "name",
                disabled: isLoading
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "password",
                label: "Password",
                placeholder: "Create a strong password",
                value: formData.password,
                onChange: handleChange("password"),
                error: errors.password,
                required: true,
                autoComplete: "new-password",
                disabled: isLoading
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "password",
                label: "Confirm Password",
                placeholder: "Re-enter your password",
                value: formData.confirmPassword,
                onChange: handleChange("confirmPassword"),
                error: errors.confirmPassword,
                required: true,
                autoComplete: "new-password",
                disabled: isLoading
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["registration-legal"], children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Checkbox,
                {
                  label: /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                    "I accept the",
                    " ",
                    /* @__PURE__ */ jsxRuntimeExports.jsx(
                      Link,
                      {
                        to: "/terms",
                        className: styles["registration-link"],
                        target: "_blank",
                        rel: "noopener noreferrer",
                        children: "Terms of Service"
                      }
                    )
                  ] }),
                  checked: formData.acceptTerms,
                  onChange: handleChange("acceptTerms"),
                  error: errors.acceptTerms,
                  disabled: isLoading,
                  required: true
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Checkbox,
                {
                  label: /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                    "I accept the",
                    " ",
                    /* @__PURE__ */ jsxRuntimeExports.jsx(
                      Link,
                      {
                        to: "/privacy",
                        className: styles["registration-link"],
                        target: "_blank",
                        rel: "noopener noreferrer",
                        children: "Privacy Policy"
                      }
                    )
                  ] }),
                  checked: formData.acceptPrivacy,
                  onChange: handleChange("acceptPrivacy"),
                  error: errors.acceptPrivacy,
                  disabled: isLoading,
                  required: true
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                Checkbox,
                {
                  label: "Send me updates and educational content via email",
                  checked: formData.newsletterOptIn,
                  onChange: handleChange("newsletterOptIn"),
                  disabled: isLoading
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Button,
              {
                type: "submit",
                variant: "primary",
                size: "large",
                fullWidth: true,
                loading: isLoading,
                disabled: isLoading,
                children: isLoading ? "Creating Account..." : "Create Account"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["registration-footer"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles["registration-footer-text"], children: [
              "Already have an account?",
              " ",
              /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/login", className: styles["registration-link"], children: "Sign in" })
            ] }) })
          ]
        }
      ) })
    ] }) })
  ] });
};
export {
  RegistrationPage as RegisterPage
};
//# sourceMappingURL=Register-B6SaSVtk.js.map
