import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { H as Heading, C as Card, B as Button, b as authService } from "./index-C0G9mbri.js";
import "./state-vendor-B_izx0oA.js";
const styles = {
  "forgot-password-page": "_forgot-password-page_1wqxy_20",
  "forgot-password-container": "_forgot-password-container_1wqxy_34",
  "forgot-password-header": "_forgot-password-header_1wqxy_46",
  "forgot-password-subtitle": "_forgot-password-subtitle_1wqxy_51",
  "forgot-password-form": "_forgot-password-form_1wqxy_65",
  "forgot-password-error-banner": "_forgot-password-error-banner_1wqxy_75",
  "forgot-password-success": "_forgot-password-success_1wqxy_108",
  "success-icon": "_success-icon_1wqxy_118",
  "success-message": "_success-message_1wqxy_134",
  "success-note": "_success-note_1wqxy_143",
  "retry-link": "_retry-link_1wqxy_152",
  "back-to-login": "_back-to-login_1wqxy_179",
  "forgot-password-link": "_forgot-password-link_1wqxy_190",
  "forgot-password-footer": "_forgot-password-footer_1wqxy_216"
};
const ForgotPasswordPage = () => {
  const [formData, setFormData] = reactExports.useState({
    email: ""
  });
  const [errors, setErrors] = reactExports.useState({});
  const [isLoading, setIsLoading] = reactExports.useState(false);
  const [isSuccess, setIsSuccess] = reactExports.useState(false);
  const validateForm = () => {
    const newErrors = {};
    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
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
    setIsLoading(true);
    try {
      await authService.requestPasswordReset({ email: formData.email });
      setIsSuccess(true);
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : "Failed to send reset email. Please try again."
      });
    } finally {
      setIsLoading(false);
    }
  };
  const handleChange = (e) => {
    setFormData({ email: e.target.value });
    if (errors.email) {
      setErrors((prev) => ({
        ...prev,
        email: void 0
      }));
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["forgot-password-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["forgot-password-container"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["forgot-password-header"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", align: "center", gutterBottom: false, children: "Forgot Password?" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["forgot-password-subtitle"], children: "Enter your email address and we'll send you a link to reset your password" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "elevated", padding: "large", children: isSuccess ? (
      // Success confirmation
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["forgot-password-success"], children: [
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
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", align: "center", gutterBottom: true, children: "Check Your Email" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles["success-message"], children: [
          "We've sent a password reset link to ",
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: formData.email }),
          ". Please check your inbox and follow the instructions to reset your password."
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles["success-note"], children: [
          "Didn't receive the email? Check your spam folder or",
          " ",
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              onClick: () => setIsSuccess(false),
              className: styles["retry-link"],
              children: "try again"
            }
          ),
          "."
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/login", className: styles["back-to-login"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "large", fullWidth: true, children: "Back to Login" }) })
      ] })
    ) : (
      // Request form
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "form",
        {
          onSubmit: handleSubmit,
          className: styles["forgot-password-form"],
          noValidate: true,
          children: [
            errors.submit && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["forgot-password-error-banner"], role: "alert", children: errors.submit }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                type: "email",
                label: "Email Address",
                placeholder: "you@example.com",
                value: formData.email,
                onChange: handleChange,
                error: errors.email,
                required: true,
                autoComplete: "email",
                autoFocus: true,
                disabled: isLoading
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Button,
              {
                type: "submit",
                variant: "primary",
                size: "large",
                fullWidth: true,
                loading: isLoading,
                disabled: isLoading,
                children: isLoading ? "Sending..." : "Send Reset Link"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["forgot-password-footer"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/login", className: styles["forgot-password-link"], children: "← Back to Login" }) })
          ]
        }
      )
    ) })
  ] }) });
};
export {
  ForgotPasswordPage
};
//# sourceMappingURL=ForgotPassword-C0ilY6dX.js.map
