import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { u as useAuth, C as Card, H as Heading, B as Button, S as Spinner, a as SEO, b as authService } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const passwordChangeContainer = "_passwordChangeContainer_2hiop_5";
const passwordChangeCard = "_passwordChangeCard_2hiop_11";
const header = "_header_2hiop_15";
const title = "_title_2hiop_20";
const subtitle = "_subtitle_2hiop_26";
const form = "_form_2hiop_31";
const passwordRequirements = "_passwordRequirements_2hiop_37";
const requirementsTitle = "_requirementsTitle_2hiop_45";
const requirementsList = "_requirementsList_2hiop_52";
const met = "_met_2hiop_76";
const submitError = "_submitError_2hiop_85";
const submitSuccess = "_submitSuccess_2hiop_98";
const actions = "_actions_2hiop_111";
const submitButton = "_submitButton_2hiop_121";
const footer = "_footer_2hiop_125";
const footerText = "_footerText_2hiop_132";
const styles = {
  passwordChangeContainer,
  passwordChangeCard,
  header,
  title,
  subtitle,
  form,
  passwordRequirements,
  requirementsTitle,
  requirementsList,
  met,
  submitError,
  submitSuccess,
  actions,
  submitButton,
  footer,
  footerText
};
const PasswordChange = () => {
  const navigate = useNavigate();
  useAuth();
  const [formData, setFormData] = reactExports.useState({
    current_password: "",
    new_password: "",
    confirm_password: ""
  });
  const [errors, setErrors] = reactExports.useState({});
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [submitError2, setSubmitError] = reactExports.useState(null);
  const [submitSuccess2, setSubmitSuccess] = reactExports.useState(false);
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value
    }));
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };
  const validateForm = () => {
    const newErrors = {};
    if (!formData.current_password) {
      newErrors.current_password = "Current password is required";
    }
    if (!formData.new_password) {
      newErrors.new_password = "New password is required";
    } else if (formData.new_password.length < 8) {
      newErrors.new_password = "Password must be at least 8 characters";
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.new_password)) {
      newErrors.new_password = "Password must contain uppercase, lowercase, and number";
    }
    if (formData.new_password === formData.current_password) {
      newErrors.new_password = "New password must be different from current password";
    }
    if (!formData.confirm_password) {
      newErrors.confirm_password = "Please confirm your new password";
    } else if (formData.new_password !== formData.confirm_password) {
      newErrors.confirm_password = "Passwords do not match";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      setSubmitError("Please fix the errors above");
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    setSubmitSuccess(false);
    try {
      await authService.changePassword({
        current_password: formData.current_password,
        new_password: formData.new_password
      });
      setSubmitSuccess(true);
      setFormData({
        current_password: "",
        new_password: "",
        confirm_password: ""
      });
      setTimeout(() => {
        navigate("/dashboard");
      }, 2e3);
    } catch (error) {
      console.error("Password change error:", error);
      if (error.response?.status === 401) {
        setSubmitError("Current password is incorrect");
      } else if (error.response?.data?.detail) {
        setSubmitError(error.response.data.detail);
      } else if (error.response?.data?.message) {
        setSubmitError(error.response.data.message);
      } else {
        setSubmitError("Failed to change password. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  const seoElement = /* @__PURE__ */ jsxRuntimeExports.jsx(
    SEO,
    {
      title: "Change Password",
      description: "Update your account password securely",
      keywords: "change password, account security, update password"
    }
  );
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { seo: seoElement, children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.passwordChangeContainer, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: styles.passwordChangeCard, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: 1, className: styles.title, children: "Change Password" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.subtitle, children: "Update your password to keep your account secure" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, className: styles.form, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          label: "Current Password",
          type: "password",
          name: "current_password",
          value: formData.current_password,
          onChange: handleInputChange,
          error: errors.current_password,
          required: true,
          placeholder: "Enter your current password",
          autoComplete: "current-password"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.passwordRequirements, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: 3, className: styles.requirementsTitle, children: "New Password Requirements:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: styles.requirementsList, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: formData.new_password.length >= 8 ? styles.met : "", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: formData.new_password.length >= 8 ? "fas fa-check-circle" : "fas fa-circle" }),
            "At least 8 characters"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: /[A-Z]/.test(formData.new_password) ? styles.met : "", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: /[A-Z]/.test(formData.new_password) ? "fas fa-check-circle" : "fas fa-circle" }),
            "At least one uppercase letter"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: /[a-z]/.test(formData.new_password) ? styles.met : "", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: /[a-z]/.test(formData.new_password) ? "fas fa-check-circle" : "fas fa-circle" }),
            "At least one lowercase letter"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: /\d/.test(formData.new_password) ? styles.met : "", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: /\d/.test(formData.new_password) ? "fas fa-check-circle" : "fas fa-circle" }),
            "At least one number"
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          label: "New Password",
          type: "password",
          name: "new_password",
          value: formData.new_password,
          onChange: handleInputChange,
          error: errors.new_password,
          required: true,
          placeholder: "Enter your new password",
          autoComplete: "new-password"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          label: "Confirm New Password",
          type: "password",
          name: "confirm_password",
          value: formData.confirm_password,
          onChange: handleInputChange,
          error: errors.confirm_password,
          required: true,
          placeholder: "Confirm your new password",
          autoComplete: "new-password"
        }
      ),
      submitError2 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.submitError, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-exclamation-circle" }),
        submitError2
      ] }),
      submitSuccess2 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.submitSuccess, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-check-circle" }),
        "Password changed successfully! Redirecting to dashboard..."
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.actions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "submit",
            variant: "primary",
            size: "large",
            disabled: isSubmitting || submitSuccess2,
            className: styles.submitButton,
            children: isSubmitting ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
              "Changing Password..."
            ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-key" }),
              "Change Password"
            ] })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/dashboard", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "large", disabled: isSubmitting, children: "Cancel" }) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.footer, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.footerText, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-info-circle" }),
      "Forgot your password? ",
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/forgot-password", children: "Reset it here" })
    ] }) })
  ] }) }) });
};
export {
  PasswordChange
};
//# sourceMappingURL=PasswordChange-DAfUQ1tf.js.map
