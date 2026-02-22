import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, h as useSearchParams, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { H as Heading, C as Card, B as Button, b as authService } from "./index-C0G9mbri.js";
import "./state-vendor-B_izx0oA.js";
const styles = {
  "reset-password-page": "_reset-password-page_12oxv_20",
  "reset-password-container": "_reset-password-container_12oxv_34",
  "reset-password-header": "_reset-password-header_12oxv_46",
  "reset-password-subtitle": "_reset-password-subtitle_12oxv_51",
  "reset-password-form": "_reset-password-form_12oxv_65",
  "reset-password-error-banner": "_reset-password-error-banner_12oxv_75",
  "password-requirements": "_password-requirements_12oxv_108",
  "requirements-title": "_requirements-title_12oxv_116",
  "requirements-list": "_requirements-list_12oxv_124",
  "reset-password-success": "_reset-password-success_12oxv_148",
  "success-icon": "_success-icon_12oxv_158",
  "success-message": "_success-message_12oxv_174",
  "success-note": "_success-note_12oxv_183",
  "go-to-login": "_go-to-login_12oxv_192",
  "reset-password-link": "_reset-password-link_12oxv_203",
  "reset-password-footer": "_reset-password-footer_12oxv_229"
};
const ResetPasswordPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [formData, setFormData] = reactExports.useState({
    password: "",
    confirmPassword: ""
  });
  const [errors, setErrors] = reactExports.useState({});
  const [isLoading, setIsLoading] = reactExports.useState(false);
  const [isSuccess, setIsSuccess] = reactExports.useState(false);
  reactExports.useEffect(() => {
    if (!token) {
      setErrors({
        submit: "Invalid or missing reset token. Please request a new password reset."
      });
    }
  }, [token]);
  const validateForm = () => {
    const newErrors = {};
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
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) {
      setErrors({
        submit: "Invalid or missing reset token. Please request a new password reset."
      });
      return;
    }
    setErrors((prev) => ({ ...prev, submit: void 0 }));
    if (!validateForm()) {
      return;
    }
    setIsLoading(true);
    try {
      await authService.confirmPasswordReset({
        token,
        newPassword: formData.password
      });
      setIsSuccess(true);
      navigate("/login");
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : "Failed to reset password. The token may be expired."
      });
    } finally {
      setIsLoading(false);
    }
  };
  const handleChange = (field) => (e) => {
    setFormData((prev) => ({
      ...prev,
      [field]: e.target.value
    }));
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: void 0
      }));
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["reset-password-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["reset-password-container"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["reset-password-header"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", align: "center", gutterBottom: false, children: "Reset Password" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["reset-password-subtitle"], children: "Enter your new password below" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "large", children: isSuccess ? (
      // Success confirmation
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["reset-password-success"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["success-icon"], "aria-hidden": "true", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("svg", { width: "64", height: "64", viewBox: "0 0 64 64", fill: "none", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("circle", { cx: "32", cy: "32", r: "32", fill: "#dcfce7" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "path",
            {
              d: "M20 32L28 40L44 24",
              stroke: "#16a34a",
              strokeWidth: "4",
              strokeLinecap: "round",
              strokeLinejoin: "round"
            }
          )
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", align: "center", gutterBottom: true, children: "Password Reset Successful" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["success-message"], children: "Your password has been successfully reset. You can now sign in with your new password." }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["success-note"], children: "Redirecting to login page in 3 seconds..." }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/login", className: styles["go-to-login"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "large", fullWidth: true, children: "Go to Login" }) })
      ] })
    ) : (
      // Reset form
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "form",
        {
          onSubmit: handleSubmit,
          className: styles["reset-password-form"],
          noValidate: true,
          children: [
            errors.submit && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["reset-password-error-banner"], role: "alert", children: [
              errors.submit,
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { marginTop: "12px" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/forgot-password", className: styles["reset-password-link"], children: "Request a new password reset" }) })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "password",
                label: "New Password",
                placeholder: "Enter your new password",
                value: formData.password,
                onChange: handleChange("password"),
                error: errors.password,
                required: true,
                autoComplete: "new-password",
                autoFocus: true,
                disabled: isLoading || !token
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "password",
                label: "Confirm Password",
                placeholder: "Re-enter your new password",
                value: formData.confirmPassword,
                onChange: handleChange("confirmPassword"),
                error: errors.confirmPassword,
                required: true,
                autoComplete: "new-password",
                disabled: isLoading || !token
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["password-requirements"], children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["requirements-title"], children: "Password must contain:" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: styles["requirements-list"], children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "At least 8 characters" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "One uppercase letter" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "One lowercase letter" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "One number" })
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Button,
              {
                type: "submit",
                variant: "primary",
                size: "large",
                fullWidth: true,
                loading: isLoading,
                disabled: isLoading || !token,
                children: isLoading ? "Resetting Password..." : "Reset Password"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["reset-password-footer"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/login", className: styles["reset-password-link"], children: "← Back to Login" }) })
          ]
        }
      )
    ) })
  ] }) });
};
export {
  ResetPasswordPage
};
//# sourceMappingURL=ResetPassword-BrnPUJvk.js.map
