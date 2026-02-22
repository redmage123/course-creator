import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports } from "./react-vendor-cEae-lCc.js";
const styles = {
  "checkbox-container": "_checkbox-container_1k3tl_15",
  "checkbox-wrapper": "_checkbox-wrapper_1k3tl_27",
  "checkbox-input": "_checkbox-input_1k3tl_38",
  "checkbox-label-wrapper": "_checkbox-label-wrapper_1k3tl_51",
  "checkbox-custom": "_checkbox-custom_1k3tl_72",
  "checkbox-icon": "_checkbox-icon_1k3tl_119",
  "checkbox-indeterminate-icon": "_checkbox-indeterminate-icon_1k3tl_120",
  "checkbox-label": "_checkbox-label_1k3tl_51",
  "checkbox-small": "_checkbox-small_1k3tl_175",
  "checkbox-medium": "_checkbox-medium_1k3tl_191",
  "checkbox-large": "_checkbox-large_1k3tl_207",
  "checkbox-error": "_checkbox-error_1k3tl_227",
  "checkbox-disabled": "_checkbox-disabled_1k3tl_256",
  "checkbox-message": "_checkbox-message_1k3tl_285",
  "checkbox-helper-text": "_checkbox-helper-text_1k3tl_303",
  "checkbox-error-text": "_checkbox-error-text_1k3tl_307"
};
const Checkbox = reactExports.forwardRef(({
  label,
  helperText,
  error,
  indeterminate = false,
  size = "medium",
  className,
  disabled,
  id,
  ...rest
}, ref) => {
  const inputRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    if (ref && inputRef.current) {
      if (typeof ref === "function") {
        ref(inputRef.current);
      } else {
        ref.current = inputRef.current;
      }
    }
  }, [ref]);
  reactExports.useEffect(() => {
    if (inputRef.current) {
      inputRef.current.indeterminate = indeterminate;
    }
  }, [indeterminate]);
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;
  const containerClasses = [
    styles["checkbox-container"],
    styles[`checkbox-${size}`],
    error && styles["checkbox-error"],
    disabled && styles["checkbox-disabled"],
    className
  ].filter(Boolean).join(" ");
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: containerClasses, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["checkbox-wrapper"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "input",
        {
          ref: inputRef,
          type: "checkbox",
          id: checkboxId,
          className: styles["checkbox-input"],
          disabled,
          "aria-invalid": !!error,
          "aria-describedby": error || helperText ? `${checkboxId}-message` : void 0,
          ...rest
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: checkboxId, className: styles["checkbox-label-wrapper"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles["checkbox-custom"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "svg",
            {
              className: styles["checkbox-icon"],
              width: "16",
              height: "16",
              viewBox: "0 0 16 16",
              fill: "none",
              "aria-hidden": "true",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                "path",
                {
                  d: "M13.333 4L6 11.333L2.667 8",
                  stroke: "currentColor",
                  strokeWidth: "2",
                  strokeLinecap: "round",
                  strokeLinejoin: "round"
                }
              )
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "svg",
            {
              className: styles["checkbox-indeterminate-icon"],
              width: "16",
              height: "16",
              viewBox: "0 0 16 16",
              fill: "none",
              "aria-hidden": "true",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                "path",
                {
                  d: "M3 8H13",
                  stroke: "currentColor",
                  strokeWidth: "2",
                  strokeLinecap: "round"
                }
              )
            }
          )
        ] }),
        label && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["checkbox-label"], children: label })
      ] })
    ] }),
    (helperText || error) && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { id: `${checkboxId}-message`, className: styles["checkbox-message"], children: error ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["checkbox-error-text"], role: "alert", children: error }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["checkbox-helper-text"], children: helperText }) })
  ] });
});
Checkbox.displayName = "Checkbox";
export {
  Checkbox as C
};
//# sourceMappingURL=Checkbox-CEUsiksA.js.map
