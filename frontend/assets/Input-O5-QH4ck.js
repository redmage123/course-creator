import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, R as React } from "./react-vendor-cEae-lCc.js";
const label = "_label_x814l_29";
const required = "_required_x814l_38";
const input = "_input_x814l_15";
const styles = {
  "input-container": "_input-container_x814l_15",
  "input-full-width": "_input-full-width_x814l_21",
  label,
  required,
  "input-wrapper": "_input-wrapper_x814l_48",
  input,
  "input-disabled": "_input-disabled_x814l_115",
  "input-default": "_input-default_x814l_124",
  "input-success": "_input-success_x814l_129",
  "input-error": "_input-error_x814l_140",
  "input-warning": "_input-warning_x814l_151",
  "input-small": "_input-small_x814l_166",
  "input-medium": "_input-medium_x814l_173",
  "input-large": "_input-large_x814l_180",
  "input-icon-left": "_input-icon-left_x814l_190",
  "input-icon-right": "_input-icon-right_x814l_191",
  "input-with-left-icon": "_input-with-left-icon_x814l_209",
  "input-with-right-icon": "_input-with-right-icon_x814l_213",
  "password-toggle": "_password-toggle_x814l_239",
  "helper-text": "_helper-text_x814l_279",
  "helper-text-default": "_helper-text-default_x814l_286",
  "helper-text-success": "_helper-text-success_x814l_290",
  "helper-text-error": "_helper-text-error_x814l_294",
  "helper-text-warning": "_helper-text-warning_x814l_298"
};
const Input = reactExports.forwardRef(
  ({
    variant = "default",
    size = "medium",
    label: label2,
    helperText,
    helpText,
    error,
    leftIcon,
    rightIcon,
    fullWidth = false,
    required: required2 = false,
    disabled,
    className,
    containerClassName,
    id,
    type = "text",
    showPasswordToggle = false,
    "aria-describedby": ariaDescribedBy,
    ...props
  }, ref) => {
    const [showPassword, setShowPassword] = reactExports.useState(false);
    const isPasswordField = type === "password";
    const shouldShowToggle = isPasswordField && showPasswordToggle;
    const effectiveType = isPasswordField && showPassword ? "text" : type;
    const effectiveVariant = error ? "error" : variant;
    const effectiveHelperText = error || helperText || helpText;
    const inputId = id || `input-${React.useId()}`;
    const helperTextId = effectiveHelperText ? `${inputId}-helper` : void 0;
    const describedBy = [ariaDescribedBy, helperTextId].filter(Boolean).join(" ") || void 0;
    const inputClasses = [
      styles.input,
      styles[`input-${effectiveVariant}`],
      styles[`input-${size}`],
      leftIcon && styles["input-with-left-icon"],
      rightIcon && styles["input-with-right-icon"],
      disabled && styles["input-disabled"],
      className
    ].filter(Boolean).join(" ");
    const containerClasses = [
      styles["input-container"],
      fullWidth && styles["input-full-width"],
      containerClassName
    ].filter(Boolean).join(" ");
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: containerClasses, children: [
      label2 && /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: inputId, className: styles.label, children: [
        label2,
        required2 && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.required, "aria-label": "required", children: "*" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["input-wrapper"], children: [
        leftIcon && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["input-icon-left"], "aria-hidden": "true", children: leftIcon }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            ref,
            id: inputId,
            type: effectiveType,
            className: inputClasses,
            disabled,
            required: required2,
            "aria-invalid": effectiveVariant === "error",
            "aria-describedby": describedBy,
            ...props
          }
        ),
        shouldShowToggle && /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            type: "button",
            className: styles["password-toggle"],
            onClick: () => setShowPassword(!showPassword),
            "aria-label": showPassword ? "Hide password" : "Show password",
            tabIndex: -1,
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: `fas ${showPassword ? "fa-eye-slash" : "fa-eye"}`, "aria-hidden": "true" })
          }
        ),
        rightIcon && !shouldShowToggle && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["input-icon-right"], "aria-hidden": "true", children: rightIcon })
      ] }),
      effectiveHelperText && /* @__PURE__ */ jsxRuntimeExports.jsx(
        "span",
        {
          id: helperTextId,
          className: `${styles["helper-text"]} ${styles[`helper-text-${effectiveVariant}`]}`,
          role: effectiveVariant === "error" ? "alert" : void 0,
          children: effectiveHelperText
        }
      )
    ] });
  }
);
Input.displayName = "Input";
export {
  Input as I
};
//# sourceMappingURL=Input-O5-QH4ck.js.map
