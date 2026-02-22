import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { u as useAuth, C as Card, H as Heading, B as Button, S as Spinner } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import "./state-vendor-B_izx0oA.js";
const subtitle = "_subtitle_12ul8_23";
const divider = "_divider_12ul8_84";
const styles = {
  "login-container": "_login-container_12ul8_2",
  "login-card": "_login-card_12ul8_11",
  "login-header": "_login-header_12ul8_18",
  subtitle,
  "login-form": "_login-form_12ul8_30",
  "form-group": "_form-group_12ul8_36",
  "error-message": "_error-message_12ul8_43",
  "form-options": "_form-options_12ul8_54",
  "checkbox-label": "_checkbox-label_12ul8_61",
  "forgot-password-link": "_forgot-password-link_12ul8_73",
  divider,
  "register-section": "_register-section_12ul8_110",
  "register-text": "_register-text_12ul8_115",
  "register-link": "_register-link_12ul8_121",
  "demo-info": "_demo-info_12ul8_132",
  "demo-credentials": "_demo-credentials_12ul8_136",
  "sr-only": "_sr-only_12ul8_150"
};
const LoginPage = () => {
  const { login, isLoading } = useAuth();
  useNavigate();
  const [identifier, setIdentifier] = reactExports.useState("");
  const [password, setPassword] = reactExports.useState("");
  const [showPassword, setShowPassword] = reactExports.useState(false);
  const [rememberMe, setRememberMe] = reactExports.useState(false);
  const [error, setError] = reactExports.useState("");
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!identifier || !password) {
      setError("Please enter your email/username and password");
      return;
    }
    if (identifier.length < 3) {
      setError("Please enter a valid email or username");
      return;
    }
    try {
      await login({ username: identifier, password });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["login-container"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "elevated", padding: "large", className: styles["login-card"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["login-header"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "Welcome Back" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["subtitle"], children: "Sign in to your Course Creator Platform account" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, className: styles["login-form"], children: [
      error && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["error-message"], role: "alert", children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["form-group"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        Input,
        {
          type: "text",
          label: "Email or Username",
          value: identifier,
          onChange: (e) => setIdentifier(e.target.value),
          placeholder: "you@example.com or username",
          disabled: isLoading,
          autoComplete: "username",
          required: true,
          fullWidth: true
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Input,
          {
            type: "password",
            label: "Password",
            value: password,
            onChange: (e) => setPassword(e.target.value),
            placeholder: "Enter your password",
            disabled: isLoading,
            autoComplete: "current-password",
            required: true,
            fullWidth: true,
            showPasswordToggle: true,
            "aria-describedby": "password-requirements"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { id: "password-requirements", className: styles["sr-only"], children: "Enter your password to sign in to your account" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-options"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles["checkbox-label"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "checkbox",
              checked: rememberMe,
              onChange: (e) => setRememberMe(e.target.checked),
              disabled: isLoading
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Remember me" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Link,
          {
            to: "/forgot-password",
            className: styles["forgot-password-link"],
            children: "Forgot password?"
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
          disabled: isLoading,
          children: isLoading ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
            "Signing in..."
          ] }) : "Sign In"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["divider"], children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "or" }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["register-section"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles["register-text"], children: [
      "Don't have an account?",
      " ",
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/register", className: styles["register-link"], children: "Sign up now" })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "small", className: styles["demo-info"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h5", gutterBottom: true, children: "Demo Credentials" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["demo-credentials"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Instructor:" }),
          " instructor@example.com / password123"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Org Admin:" }),
          " orgadmin@example.com / password123"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Student:" }),
          " student@example.com / password123"
        ] })
      ] })
    ] })
  ] }) });
};
export {
  LoginPage
};
//# sourceMappingURL=Login-CYrpdU9j.js.map
