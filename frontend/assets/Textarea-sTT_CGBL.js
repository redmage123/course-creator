import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports } from "./react-vendor-cEae-lCc.js";
const textarea = "_textarea_40ri6_15";
const styles = {
  "textarea-container": "_textarea-container_40ri6_15",
  "textarea-label": "_textarea-label_40ri6_28",
  "textarea-required": "_textarea-required_40ri6_39",
  textarea,
  "textarea-resize-none": "_textarea-resize-none_40ri6_93",
  "textarea-resize-vertical": "_textarea-resize-vertical_40ri6_97",
  "textarea-resize-both": "_textarea-resize-both_40ri6_101",
  "textarea-error": "_textarea-error_40ri6_109",
  "textarea-success": "_textarea-success_40ri6_122",
  "textarea-warning": "_textarea-warning_40ri6_135",
  "textarea-disabled": "_textarea-disabled_40ri6_152",
  "textarea-footer": "_textarea-footer_40ri6_171",
  "textarea-message": "_textarea-message_40ri6_184",
  "textarea-helper-text": "_textarea-helper-text_40ri6_191",
  "textarea-error-text": "_textarea-error-text_40ri6_195",
  "textarea-success-text": "_textarea-success-text_40ri6_199",
  "textarea-warning-text": "_textarea-warning-text_40ri6_203",
  "textarea-char-count": "_textarea-char-count_40ri6_211",
  "textarea-char-count-warning": "_textarea-char-count-warning_40ri6_225"
};
const Textarea = reactExports.forwardRef(({
  label,
  helperText,
  error,
  success,
  warning,
  required = false,
  autoResize = true,
  minRows = 3,
  maxRows = 10,
  showCharacterCount = false,
  resize = "vertical",
  className,
  value,
  defaultValue,
  onChange,
  maxLength,
  id,
  disabled,
  ...rest
}, ref) => {
  const textareaRef = reactExports.useRef(null);
  const [charCount, setCharCount] = reactExports.useState(0);
  reactExports.useEffect(() => {
    if (ref && textareaRef.current) {
      if (typeof ref === "function") {
        ref(textareaRef.current);
      } else {
        ref.current = textareaRef.current;
      }
    }
  }, [ref]);
  const adjustHeight = () => {
    if (!autoResize || !textareaRef.current) return;
    const textarea2 = textareaRef.current;
    const lineHeight = parseInt(getComputedStyle(textarea2).lineHeight) || 24;
    const minHeight = minRows * lineHeight;
    const maxHeight = maxRows * lineHeight;
    textarea2.style.height = "auto";
    const newHeight = Math.min(Math.max(textarea2.scrollHeight, minHeight), maxHeight);
    textarea2.style.height = `${newHeight}px`;
    textarea2.style.overflowY = textarea2.scrollHeight > maxHeight ? "auto" : "hidden";
  };
  reactExports.useEffect(() => {
    adjustHeight();
  }, [value, defaultValue, autoResize, minRows, maxRows]);
  const handleChange = (e) => {
    const newValue = e.target.value;
    setCharCount(newValue.length);
    adjustHeight();
    onChange?.(e);
  };
  reactExports.useEffect(() => {
    const initialValue = value || defaultValue || "";
    setCharCount(initialValue.length);
  }, []);
  const validationState = error ? "error" : success ? "success" : warning ? "warning" : "default";
  const containerClasses = [
    styles["textarea-container"],
    styles[`textarea-${validationState}`],
    disabled && styles["textarea-disabled"],
    className
  ].filter(Boolean).join(" ");
  const textareaClasses = [
    styles.textarea,
    !autoResize && styles[`textarea-resize-${resize}`]
  ].filter(Boolean).join(" ");
  const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
  const charPercentage = maxLength ? charCount / maxLength * 100 : 0;
  const showCharWarning = maxLength && charPercentage >= 90;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: containerClasses, children: [
    label && /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: textareaId, className: styles["textarea-label"], children: [
      label,
      required && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["textarea-required"], children: "*" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "textarea",
      {
        ref: textareaRef,
        id: textareaId,
        className: textareaClasses,
        value,
        defaultValue,
        onChange: handleChange,
        maxLength,
        disabled,
        "aria-invalid": !!error,
        "aria-required": required,
        "aria-describedby": error || success || warning || helperText ? `${textareaId}-message` : void 0,
        rows: minRows,
        ...rest
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["textarea-footer"], children: [
      (helperText || error || success || warning) && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { id: `${textareaId}-message`, className: styles["textarea-message"], children: [
        error && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["textarea-error-text"], children: error }),
        !error && success && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["textarea-success-text"], children: success }),
        !error && !success && warning && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["textarea-warning-text"], children: warning }),
        !error && !success && !warning && helperText && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["textarea-helper-text"], children: helperText })
      ] }),
      showCharacterCount && /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "div",
        {
          className: `${styles["textarea-char-count"]} ${showCharWarning ? styles["textarea-char-count-warning"] : ""}`,
          children: [
            charCount,
            maxLength && ` / ${maxLength}`
          ]
        }
      )
    ] })
  ] });
});
Textarea.displayName = "Textarea";
export {
  Textarea as T
};
//# sourceMappingURL=Textarea-sTT_CGBL.js.map
