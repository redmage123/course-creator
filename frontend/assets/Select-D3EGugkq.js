import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports } from "./react-vendor-cEae-lCc.js";
const dropdownSlideIn = "_dropdownSlideIn_5cyjv_1";
const styles = {
  "select-container": "_select-container_5cyjv_15",
  "select-label": "_select-label_5cyjv_28",
  "select-required": "_select-required_5cyjv_39",
  "select-trigger": "_select-trigger_5cyjv_49",
  "select-small": "_select-small_5cyjv_93",
  "select-medium": "_select-medium_5cyjv_98",
  "select-large": "_select-large_5cyjv_103",
  "select-value": "_select-value_5cyjv_112",
  "select-search": "_select-search_5cyjv_124",
  "select-arrow": "_select-arrow_5cyjv_150",
  "select-arrow-open": "_select-arrow-open_5cyjv_159",
  "select-dropdown": "_select-dropdown_5cyjv_167",
  dropdownSlideIn,
  "select-option": "_select-option_5cyjv_213",
  "select-option-highlighted": "_select-option-highlighted_5cyjv_237",
  "select-option-selected": "_select-option-selected_5cyjv_241",
  "select-option-disabled": "_select-option-disabled_5cyjv_247",
  "select-option-empty": "_select-option-empty_5cyjv_257",
  "select-option-label": "_select-option-label_5cyjv_274",
  "select-checkbox": "_select-checkbox_5cyjv_286",
  "select-checkmark": "_select-checkmark_5cyjv_316",
  "select-message": "_select-message_5cyjv_326",
  "select-helper-text": "_select-helper-text_5cyjv_333",
  "select-error-text": "_select-error-text_5cyjv_337",
  "select-error": "_select-error_5cyjv_337",
  "select-disabled": "_select-disabled_5cyjv_362"
};
const Select = reactExports.forwardRef(({
  options,
  value,
  defaultValue,
  onChange,
  placeholder = "Select...",
  label,
  helperText,
  error,
  required = false,
  disabled = false,
  searchable = false,
  multiple = false,
  size = "medium",
  className,
  name,
  id
}, ref) => {
  const [isOpen, setIsOpen] = reactExports.useState(false);
  const [searchTerm, setSearchTerm] = reactExports.useState("");
  const [highlightedIndex, setHighlightedIndex] = reactExports.useState(0);
  const [internalValue, setInternalValue] = reactExports.useState(
    defaultValue ?? (multiple ? [] : "")
  );
  const containerRef = reactExports.useRef(null);
  const inputRef = reactExports.useRef(null);
  const listboxRef = reactExports.useRef(null);
  const currentValue = value !== void 0 ? value : internalValue;
  const filteredOptions = searchTerm ? options.filter(
    (option) => option.label.toLowerCase().includes(searchTerm.toLowerCase())
  ) : options;
  const getDisplayText = reactExports.useCallback(() => {
    if (multiple && Array.isArray(currentValue)) {
      if (currentValue.length === 0) return placeholder;
      if (currentValue.length === 1) {
        const option2 = options.find((opt) => opt.value === currentValue[0]);
        return option2?.label || placeholder;
      }
      return `${currentValue.length} selected`;
    }
    const option = options.find((opt) => opt.value === currentValue);
    return option?.label || placeholder;
  }, [currentValue, multiple, options, placeholder]);
  const handleSelect = (optionValue) => {
    let newValue;
    if (multiple && Array.isArray(currentValue)) {
      if (currentValue.includes(optionValue)) {
        newValue = currentValue.filter((v) => v !== optionValue);
      } else {
        newValue = [...currentValue, optionValue];
      }
    } else {
      newValue = optionValue;
      setIsOpen(false);
    }
    if (value === void 0) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
    setSearchTerm("");
  };
  const handleKeyDown = (event) => {
    if (disabled) return;
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(
            (prev) => prev < filteredOptions.length - 1 ? prev + 1 : prev
          );
        }
        break;
      case "ArrowUp":
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex((prev) => prev > 0 ? prev - 1 : 0);
        }
        break;
      case "Enter":
        event.preventDefault();
        if (isOpen && filteredOptions[highlightedIndex]) {
          const option = filteredOptions[highlightedIndex];
          if (!option.disabled) {
            handleSelect(option.value);
          }
        } else {
          setIsOpen(true);
        }
        break;
      case "Escape":
        event.preventDefault();
        setIsOpen(false);
        setSearchTerm("");
        break;
      case " ":
        if (!searchable) {
          event.preventDefault();
          if (!isOpen) {
            setIsOpen(true);
          } else if (filteredOptions[highlightedIndex]) {
            const option = filteredOptions[highlightedIndex];
            if (!option.disabled) {
              handleSelect(option.value);
            }
          }
        }
        break;
      case "Tab":
        if (isOpen) {
          setIsOpen(false);
        }
        break;
      case "Home":
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(0);
        }
        break;
      case "End":
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(filteredOptions.length - 1);
        }
        break;
      case "PageUp":
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex((prev) => Math.max(0, prev - 5));
        }
        break;
      case "PageDown":
        event.preventDefault();
        if (isOpen) {
          setHighlightedIndex(
            (prev) => Math.min(filteredOptions.length - 1, prev + 5)
          );
        }
        break;
    }
  };
  reactExports.useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm("");
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  reactExports.useEffect(() => {
    if (isOpen && listboxRef.current) {
      const highlightedElement = listboxRef.current.children[highlightedIndex];
      if (highlightedElement) {
        highlightedElement.scrollIntoView({
          block: "nearest",
          behavior: "smooth"
        });
      }
    }
  }, [highlightedIndex, isOpen]);
  reactExports.useEffect(() => {
    setHighlightedIndex(0);
  }, [filteredOptions]);
  const isSelected = (optionValue) => {
    if (multiple && Array.isArray(currentValue)) {
      return currentValue.includes(optionValue);
    }
    return currentValue === optionValue;
  };
  const selectId = id || `select-${Math.random().toString(36).substr(2, 9)}`;
  const listboxId = `${selectId}-listbox`;
  const containerClasses = [
    styles["select-container"],
    styles[`select-${size}`],
    error && styles["select-error"],
    disabled && styles["select-disabled"],
    className
  ].filter(Boolean).join(" ");
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { ref: containerRef, className: containerClasses, children: [
    label && /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: selectId, className: styles["select-label"], children: [
      label,
      required && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["select-required"], children: "*" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        ref,
        className: styles["select-trigger"],
        onClick: () => !disabled && setIsOpen(!isOpen),
        onKeyDown: handleKeyDown,
        role: "combobox",
        "aria-expanded": isOpen,
        "aria-haspopup": "listbox",
        "aria-controls": listboxId,
        "aria-labelledby": label ? `${selectId}-label` : void 0,
        "aria-invalid": !!error,
        "aria-required": required,
        tabIndex: disabled ? -1 : 0,
        children: [
          searchable && isOpen ? /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              ref: inputRef,
              type: "text",
              className: styles["select-search"],
              value: searchTerm,
              onChange: (e) => setSearchTerm(e.target.value),
              placeholder: "Type to search..."
            }
          ) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["select-value"], children: getDisplayText() }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "svg",
            {
              className: `${styles["select-arrow"]} ${isOpen ? styles["select-arrow-open"] : ""}`,
              width: "20",
              height: "20",
              viewBox: "0 0 20 20",
              fill: "none",
              children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                "path",
                {
                  d: "M5 7.5L10 12.5L15 7.5",
                  stroke: "currentColor",
                  strokeWidth: "2",
                  strokeLinecap: "round",
                  strokeLinejoin: "round"
                }
              )
            }
          )
        ]
      }
    ),
    isOpen && /* @__PURE__ */ jsxRuntimeExports.jsx(
      "ul",
      {
        ref: listboxRef,
        id: listboxId,
        className: styles["select-dropdown"],
        role: "listbox",
        "aria-multiselectable": multiple,
        children: filteredOptions.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("li", { className: styles["select-option-empty"], role: "option", children: "No options found" }) : filteredOptions.map((option, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
          "li",
          {
            className: `${styles["select-option"]} ${isSelected(option.value) ? styles["select-option-selected"] : ""} ${index === highlightedIndex ? styles["select-option-highlighted"] : ""} ${option.disabled ? styles["select-option-disabled"] : ""}`,
            role: "option",
            "aria-selected": isSelected(option.value),
            "aria-disabled": option.disabled,
            onClick: () => !option.disabled && handleSelect(option.value),
            children: [
              multiple && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["select-checkbox"], children: isSelected(option.value) && /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "16", height: "16", viewBox: "0 0 16 16", fill: "none", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                "path",
                {
                  d: "M13.333 4L6 11.333L2.667 8",
                  stroke: "currentColor",
                  strokeWidth: "2",
                  strokeLinecap: "round",
                  strokeLinejoin: "round"
                }
              ) }) }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["select-option-label"], children: option.label }),
              !multiple && isSelected(option.value) && /* @__PURE__ */ jsxRuntimeExports.jsx(
                "svg",
                {
                  className: styles["select-checkmark"],
                  width: "16",
                  height: "16",
                  viewBox: "0 0 16 16",
                  fill: "none",
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
              )
            ]
          },
          option.value
        ))
      }
    ),
    (helperText || error) && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["select-message"], children: error ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["select-error-text"], children: error }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles["select-helper-text"], children: helperText }) }),
    name && /* @__PURE__ */ jsxRuntimeExports.jsx(
      "input",
      {
        type: "hidden",
        name,
        value: Array.isArray(currentValue) ? currentValue.join(",") : currentValue
      }
    )
  ] });
});
Select.displayName = "Select";
export {
  Select as S
};
//# sourceMappingURL=Select-D3EGugkq.js.map
