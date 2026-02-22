import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports } from "./react-vendor-cEae-lCc.js";
import { c as apiClient } from "./index-C0G9mbri.js";
import "./state-vendor-B_izx0oA.js";
var FontSizePreference = /* @__PURE__ */ ((FontSizePreference2) => {
  FontSizePreference2["DEFAULT"] = "default";
  FontSizePreference2["LARGE"] = "large";
  FontSizePreference2["EXTRA_LARGE"] = "xlarge";
  FontSizePreference2["HUGE"] = "huge";
  return FontSizePreference2;
})(FontSizePreference || {});
var ColorSchemePreference = /* @__PURE__ */ ((ColorSchemePreference2) => {
  ColorSchemePreference2["SYSTEM"] = "system";
  ColorSchemePreference2["LIGHT"] = "light";
  ColorSchemePreference2["DARK"] = "dark";
  ColorSchemePreference2["HIGH_CONTRAST"] = "high_contrast";
  return ColorSchemePreference2;
})(ColorSchemePreference || {});
var MotionPreference = /* @__PURE__ */ ((MotionPreference2) => {
  MotionPreference2["NO_PREFERENCE"] = "no_preference";
  MotionPreference2["REDUCE"] = "reduce";
  MotionPreference2["NO_MOTION"] = "no_motion";
  return MotionPreference2;
})(MotionPreference || {});
var FocusIndicatorStyle = /* @__PURE__ */ ((FocusIndicatorStyle2) => {
  FocusIndicatorStyle2["DEFAULT"] = "default";
  FocusIndicatorStyle2["ENHANCED"] = "enhanced";
  FocusIndicatorStyle2["HIGH_VISIBILITY"] = "high_visibility";
  return FocusIndicatorStyle2;
})(FocusIndicatorStyle || {});
class AccessibilityService {
  baseURL = "/organizations";
  // organization-management service
  // =========================================================================
  // PREFERENCES MANAGEMENT
  // =========================================================================
  /**
   * Get user accessibility preferences
   *
   * BUSINESS LOGIC:
   * Retrieves user's saved accessibility settings from the backend.
   * If no preferences exist, returns default settings.
   *
   * @param userId - UUID of the user
   * @returns User's accessibility preferences
   */
  async getUserPreferences(userId) {
    try {
      const response = await apiClient.get(
        `${this.baseURL}/users/${userId}/accessibility-preferences`
      );
      return response;
    } catch (error2) {
      console.error("[AccessibilityService] Failed to get preferences:", error2);
      if (error2.response?.status === 404) {
        return this.getDefaultPreferences(userId);
      }
      throw error2;
    }
  }
  /**
   * Update user accessibility preferences
   *
   * BUSINESS LOGIC:
   * Updates one or more accessibility settings for the user.
   * Validates settings before saving to ensure WCAG compliance.
   *
   * @param userId - UUID of the user
   * @param preferences - Partial preferences to update
   * @returns Updated preferences
   */
  async updateUserPreferences(userId, preferences) {
    try {
      if (preferences.timeoutMultiplier !== void 0) {
        if (preferences.timeoutMultiplier < 1 || preferences.timeoutMultiplier > 5) {
          throw new Error("Timeout multiplier must be between 1.0 and 5.0");
        }
      }
      const response = await apiClient.put(
        `${this.baseURL}/users/${userId}/accessibility-preferences`,
        preferences
      );
      this.applyPreferences(response);
      return response;
    } catch (error2) {
      console.error("[AccessibilityService] Failed to update preferences:", error2);
      throw error2;
    }
  }
  /**
   * Reset user preferences to defaults
   *
   * BUSINESS LOGIC:
   * Resets all accessibility settings to platform defaults.
   * Useful when user wants to start fresh.
   *
   * @param userId - UUID of the user
   * @returns Default preferences
   */
  async resetUserPreferences(userId) {
    try {
      const response = await apiClient.post(
        `${this.baseURL}/users/${userId}/accessibility-preferences/reset`
      );
      this.applyPreferences(response);
      return response;
    } catch (error2) {
      console.error("[AccessibilityService] Failed to reset preferences:", error2);
      throw error2;
    }
  }
  /**
   * Get default accessibility preferences
   *
   * BUSINESS LOGIC:
   * Returns platform default accessibility settings.
   * Used for new users or as fallback.
   *
   * @param userId - UUID of the user
   * @returns Default preferences
   */
  getDefaultPreferences(userId) {
    return {
      id: "default",
      userId,
      fontSize: "default",
      colorScheme: "system",
      focusIndicatorStyle: "default",
      highContrastMode: false,
      motionPreference: "no_preference",
      reduceTransparency: false,
      screenReaderOptimizations: false,
      announcePageChanges: true,
      verboseAnnouncements: false,
      keyboardShortcutsEnabled: true,
      skipLinksAlwaysVisible: false,
      focusHighlightEnabled: true,
      autoPlayMedia: false,
      captionsEnabled: true,
      audioDescriptionsEnabled: false,
      extendTimeouts: false,
      timeoutMultiplier: 1,
      disableAutoRefresh: false,
      createdAt: (/* @__PURE__ */ new Date()).toISOString(),
      updatedAt: (/* @__PURE__ */ new Date()).toISOString()
    };
  }
  /**
   * Apply preferences to document
   *
   * TECHNICAL IMPLEMENTATION:
   * Sets CSS custom properties on document root for immediate effect.
   * Updates ARIA attributes and accessibility settings.
   *
   * @param preferences - Preferences to apply
   */
  applyPreferences(preferences) {
    const root = document.documentElement;
    const fontSizeMultipliers = {
      [
        "default"
        /* DEFAULT */
      ]: 1,
      [
        "large"
        /* LARGE */
      ]: 1.25,
      [
        "xlarge"
        /* EXTRA_LARGE */
      ]: 1.5,
      [
        "huge"
        /* HUGE */
      ]: 2
    };
    root.style.setProperty("--a11y-font-size-multiplier", fontSizeMultipliers[preferences.fontSize].toString());
    const animationMultipliers = {
      [
        "no_preference"
        /* NO_PREFERENCE */
      ]: 1,
      [
        "reduce"
        /* REDUCE */
      ]: 0.3,
      [
        "no_motion"
        /* NO_MOTION */
      ]: 0
    };
    root.style.setProperty("--a11y-animation-multiplier", animationMultipliers[preferences.motionPreference].toString());
    root.style.setProperty("--a11y-reduce-transparency", preferences.reduceTransparency ? "0.5" : "0");
    const focusWidths = {
      [
        "default"
        /* DEFAULT */
      ]: "2px",
      [
        "enhanced"
        /* ENHANCED */
      ]: "3px",
      [
        "high_visibility"
        /* HIGH_VISIBILITY */
      ]: "4px"
    };
    root.style.setProperty("--a11y-focus-ring-width", focusWidths[preferences.focusIndicatorStyle]);
    if (preferences.colorScheme !== "system") {
      root.setAttribute("data-color-scheme", preferences.colorScheme);
    } else {
      root.removeAttribute("data-color-scheme");
    }
    root.classList.toggle("high-contrast", preferences.highContrastMode);
    root.classList.toggle("skip-links-always-visible", preferences.skipLinksAlwaysVisible);
    localStorage.setItem("accessibility-preferences", JSON.stringify(preferences));
  }
  // =========================================================================
  // COLOR CONTRAST VALIDATION
  // =========================================================================
  /**
   * Validate color contrast ratio
   *
   * BUSINESS LOGIC:
   * Validates that two colors meet WCAG 2.1 contrast requirements.
   * Used in design system and component validation.
   *
   * @param foreground - Foreground hex color (e.g., "#000000")
   * @param background - Background hex color (e.g., "#FFFFFF")
   * @param level - WCAG contrast level requirement
   * @param componentName - Optional component identifier
   * @returns Validation result with pass/fail status
   */
  async validateColorContrast(foreground, background, level = "normal_text_aa", componentName) {
    try {
      const response = await apiClient.post(
        `${this.baseURL}/accessibility/validate-contrast`,
        { foreground, background, level, componentName }
      );
      return response;
    } catch (error2) {
      console.error("[AccessibilityService] Failed to validate contrast:", error2);
      throw error2;
    }
  }
  /**
   * Calculate contrast ratio between two colors
   *
   * TECHNICAL IMPLEMENTATION:
   * Client-side calculation of WCAG contrast ratio.
   * Formula: (L1 + 0.05) / (L2 + 0.05) where L is relative luminance.
   *
   * @param foreground - Foreground hex color
   * @param background - Background hex color
   * @returns Contrast ratio (1:1 to 21:1)
   */
  calculateContrastRatio(foreground, background) {
    const getLuminance = (hex) => {
      const rgb = this.hexToRgb(hex);
      if (!rgb) return 0;
      const [r, g, b] = rgb.map((val) => {
        const v = val / 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const lum1 = getLuminance(foreground);
    const lum2 = getLuminance(background);
    const lighter = Math.max(lum1, lum2);
    const darker = Math.min(lum1, lum2);
    return (lighter + 0.05) / (darker + 0.05);
  }
  /**
   * Convert hex color to RGB
   *
   * @param hex - Hex color code
   * @returns RGB array or null if invalid
   */
  hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
      parseInt(result[1], 16),
      parseInt(result[2], 16),
      parseInt(result[3], 16)
    ] : null;
  }
  // =========================================================================
  // KEYBOARD SHORTCUTS MANAGEMENT
  // =========================================================================
  /**
   * Get keyboard shortcuts
   *
   * BUSINESS LOGIC:
   * Retrieves available keyboard shortcuts for the platform.
   * Includes both default and user-customized shortcuts.
   *
   * @param userId - Optional user ID for customized shortcuts
   * @param context - Shortcut context filter (global, modal, form, etc.)
   * @returns List of keyboard shortcuts
   */
  async getKeyboardShortcuts(userId, context = "global") {
    try {
      const params = new URLSearchParams();
      if (userId) params.append("userId", userId);
      if (context) params.append("context", context);
      const response = await apiClient.get(
        `${this.baseURL}/accessibility/keyboard-shortcuts?${params.toString()}`
      );
      return response;
    } catch (error2) {
      console.error("[AccessibilityService] Failed to get shortcuts:", error2);
      return this.getDefaultShortcuts();
    }
  }
  /**
   * Get default keyboard shortcuts
   *
   * BUSINESS LOGIC:
   * Returns platform default keyboard shortcuts.
   * Follows WCAG 2.1.1 (Keyboard) and 2.1.4 (Character Key Shortcuts).
   *
   * @returns Default keyboard shortcuts
   */
  getDefaultShortcuts() {
    return [
      {
        id: "skip-to-main",
        key: "KeyS",
        modifiers: ["alt"],
        action: "skip_to_main",
        description: "Skip to main content",
        context: "global",
        enabled: true,
        isCustomizable: true
      },
      {
        id: "skip-to-nav",
        key: "KeyN",
        modifiers: ["alt"],
        action: "skip_to_nav",
        description: "Skip to navigation",
        context: "global",
        enabled: true,
        isCustomizable: true
      },
      {
        id: "open-help",
        key: "KeyH",
        modifiers: ["alt"],
        action: "open_help",
        description: "Open keyboard shortcuts help",
        context: "global",
        enabled: true,
        isCustomizable: true
      },
      {
        id: "go-dashboard",
        key: "KeyD",
        modifiers: ["alt"],
        action: "go_to_dashboard",
        description: "Go to dashboard",
        context: "global",
        enabled: true,
        isCustomizable: true
      },
      {
        id: "go-courses",
        key: "KeyC",
        modifiers: ["alt"],
        action: "go_to_courses",
        description: "Go to courses",
        context: "global",
        enabled: true,
        isCustomizable: true
      },
      {
        id: "close-modal",
        key: "Escape",
        modifiers: [],
        action: "close_modal",
        description: "Close current modal or dialog",
        context: "modal",
        enabled: true,
        isCustomizable: false
      }
    ];
  }
  /**
   * Update keyboard shortcut
   *
   * BUSINESS LOGIC:
   * Customizes a keyboard shortcut for the user.
   * Validates for conflicts with existing shortcuts.
   *
   * @param userId - UUID of the user
   * @param action - Action to customize
   * @param key - New key code
   * @param modifiers - New modifier keys
   * @returns Updated shortcut
   */
  async updateKeyboardShortcut(userId, action, key, modifiers) {
    try {
      const response = await apiClient.put(
        `${this.baseURL}/users/${userId}/keyboard-shortcuts/${action}`,
        { key, modifiers }
      );
      return response;
    } catch (error2) {
      console.error("[AccessibilityService] Failed to update shortcut:", error2);
      throw error2;
    }
  }
  // =========================================================================
  // SCREEN READER SUPPORT
  // =========================================================================
  /**
   * Create screen reader announcement
   *
   * BUSINESS LOGIC:
   * Creates an announcement for assistive technology users.
   * Uses ARIA live regions to announce dynamic content changes.
   *
   * @param message - Message to announce
   * @param politeness - Urgency level ("polite" or "assertive")
   * @param delayMs - Delay before announcement
   * @returns Announcement configuration
   */
  createAnnouncement(message, politeness = "polite", delayMs = 0) {
    return {
      id: `announcement-${Date.now()}`,
      message,
      politeness,
      atomic: true,
      relevant: "additions text",
      delayMs
    };
  }
  /**
   * Announce to screen reader
   *
   * TECHNICAL IMPLEMENTATION:
   * Dynamically creates ARIA live region and announces message.
   * Automatically cleans up after announcement.
   *
   * @param message - Message to announce
   * @param politeness - Urgency level
   * @param delayMs - Delay before announcement
   */
  announce(message, politeness = "polite", delayMs = 0) {
    const announce = () => {
      const liveRegion = document.getElementById("a11y-announcer") || this.createLiveRegion();
      liveRegion.setAttribute("aria-live", politeness);
      liveRegion.textContent = message;
      setTimeout(() => {
        liveRegion.textContent = "";
      }, 3e3);
    };
    if (delayMs > 0) {
      setTimeout(announce, delayMs);
    } else {
      announce();
    }
  }
  /**
   * Create ARIA live region
   *
   * TECHNICAL IMPLEMENTATION:
   * Creates a visually hidden live region for screen reader announcements.
   *
   * @returns Live region element
   */
  createLiveRegion() {
    const existing = document.getElementById("a11y-announcer");
    if (existing) return existing;
    const liveRegion = document.createElement("div");
    liveRegion.id = "a11y-announcer";
    liveRegion.setAttribute("role", "status");
    liveRegion.setAttribute("aria-live", "polite");
    liveRegion.setAttribute("aria-atomic", "true");
    liveRegion.className = "sr-only";
    liveRegion.style.cssText = `
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    `;
    document.body.appendChild(liveRegion);
    return liveRegion;
  }
}
const accessibilityService = new AccessibilityService();
const AccessibilityContext = reactExports.createContext(void 0);
const useAccessibilityContext = () => {
  const context = reactExports.useContext(AccessibilityContext);
  if (context === void 0) {
    throw new Error("useAccessibilityContext must be used within AccessibilityProvider");
  }
  return context;
};
const container$5 = "_container_mk35g_6";
const fieldset$3 = "_fieldset_mk35g_10";
const legend$3 = "_legend_mk35g_16";
const helpText$4 = "_helpText_mk35g_26";
const options$3 = "_options_mk35g_32";
const option$3 = "_option_mk35g_32";
const selected$3 = "_selected_mk35g_55";
const radio$3 = "_radio_mk35g_60";
const optionLabel$3 = "_optionLabel_mk35g_72";
const optionSize = "_optionSize_mk35g_81";
const styles$7 = {
  container: container$5,
  fieldset: fieldset$3,
  legend: legend$3,
  helpText: helpText$4,
  options: options$3,
  option: option$3,
  selected: selected$3,
  radio: radio$3,
  optionLabel: optionLabel$3,
  optionSize
};
const FontSizeSelector = ({
  value,
  onChange,
  disabled = false
}) => {
  const options2 = [
    { value: FontSizePreference.DEFAULT, label: "Default", size: "100%" },
    { value: FontSizePreference.LARGE, label: "Large", size: "125%" },
    { value: FontSizePreference.EXTRA_LARGE, label: "Extra Large", size: "150%" },
    { value: FontSizePreference.HUGE, label: "Huge", size: "200%" }
  ];
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$7.container, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("fieldset", { className: styles$7.fieldset, disabled, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("legend", { className: styles$7.legend, children: [
      "Font Size",
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$7.helpText, children: "Adjust text size for better readability" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$7.options, role: "radiogroup", "aria-label": "Font size options", children: options2.map((option2) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "label",
      {
        className: `${styles$7.option} ${value === option2.value ? styles$7.selected : ""}`,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "radio",
              name: "font-size",
              value: option2.value,
              checked: value === option2.value,
              onChange: () => onChange(option2.value),
              disabled,
              className: styles$7.radio,
              "aria-describedby": `font-size-${option2.value}-desc`
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$7.optionLabel, children: [
            option2.label,
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "span",
              {
                id: `font-size-${option2.value}-desc`,
                className: styles$7.optionSize,
                children: option2.size
              }
            )
          ] })
        ]
      },
      option2.value
    )) })
  ] }) });
};
const container$4 = "_container_1y6za_6";
const fieldset$2 = "_fieldset_1y6za_13";
const legend$2 = "_legend_1y6za_19";
const helpText$3 = "_helpText_1y6za_29";
const options$2 = "_options_1y6za_35";
const option$2 = "_option_1y6za_35";
const selected$2 = "_selected_1y6za_58";
const radio$2 = "_radio_1y6za_63";
const optionLabel$2 = "_optionLabel_1y6za_75";
const optionDescription$2 = "_optionDescription_1y6za_84";
const highContrast = "_highContrast_1y6za_90";
const checkboxLabel = "_checkboxLabel_1y6za_96";
const checkbox$1 = "_checkbox_1y6za_96";
const checkboxText = "_checkboxText_1y6za_115";
const checkboxHelp = "_checkboxHelp_1y6za_123";
const styles$6 = {
  container: container$4,
  fieldset: fieldset$2,
  legend: legend$2,
  helpText: helpText$3,
  options: options$2,
  option: option$2,
  selected: selected$2,
  radio: radio$2,
  optionLabel: optionLabel$2,
  optionDescription: optionDescription$2,
  highContrast,
  checkboxLabel,
  checkbox: checkbox$1,
  checkboxText,
  checkboxHelp
};
const ColorSchemeSelector = ({
  value,
  highContrastMode,
  onColorSchemeChange,
  onHighContrastChange,
  disabled = false
}) => {
  const options2 = [
    { value: ColorSchemePreference.SYSTEM, label: "System", description: "Follow system preference" },
    { value: ColorSchemePreference.LIGHT, label: "Light", description: "Light background" },
    { value: ColorSchemePreference.DARK, label: "Dark", description: "Dark background" },
    { value: ColorSchemePreference.HIGH_CONTRAST, label: "High Contrast", description: "Maximum contrast" }
  ];
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$6.container, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("fieldset", { className: styles$6.fieldset, disabled, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("legend", { className: styles$6.legend, children: [
        "Color Scheme",
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.helpText, children: "Choose your preferred color theme" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$6.options, role: "radiogroup", "aria-label": "Color scheme options", children: options2.map((option2) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "label",
        {
          className: `${styles$6.option} ${value === option2.value ? styles$6.selected : ""}`,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                type: "radio",
                name: "color-scheme",
                value: option2.value,
                checked: value === option2.value,
                onChange: () => onColorSchemeChange(option2.value),
                disabled,
                className: styles$6.radio,
                "aria-describedby": `color-scheme-${option2.value}-desc`
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$6.optionLabel, children: [
              option2.label,
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "span",
                {
                  id: `color-scheme-${option2.value}-desc`,
                  className: styles$6.optionDescription,
                  children: option2.description
                }
              )
            ] })
          ]
        },
        option2.value
      )) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$6.highContrast, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "high-contrast-mode", className: styles$6.checkboxLabel, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "input",
        {
          type: "checkbox",
          id: "high-contrast-mode",
          checked: highContrastMode,
          onChange: (e) => onHighContrastChange(e.target.checked),
          disabled,
          className: styles$6.checkbox
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$6.checkboxText, children: [
        "Enable High Contrast Mode",
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$6.checkboxHelp, children: "Increases contrast beyond standard levels (WCAG AAA)" })
      ] })
    ] }) })
  ] });
};
const container$3 = "_container_3wvwg_6";
const fieldset$1 = "_fieldset_3wvwg_10";
const legend$1 = "_legend_3wvwg_16";
const helpText$2 = "_helpText_3wvwg_26";
const options$1 = "_options_3wvwg_32";
const option$1 = "_option_3wvwg_32";
const selected$1 = "_selected_3wvwg_55";
const radio$1 = "_radio_3wvwg_60";
const optionLabel$1 = "_optionLabel_3wvwg_72";
const optionDescription$1 = "_optionDescription_3wvwg_81";
const styles$5 = {
  container: container$3,
  fieldset: fieldset$1,
  legend: legend$1,
  helpText: helpText$2,
  options: options$1,
  option: option$1,
  selected: selected$1,
  radio: radio$1,
  optionLabel: optionLabel$1,
  optionDescription: optionDescription$1
};
const MotionPreferences = ({
  value,
  onChange,
  disabled = false
}) => {
  const options2 = [
    {
      value: MotionPreference.NO_PREFERENCE,
      label: "Full Motion",
      description: "Use all animations and transitions"
    },
    {
      value: MotionPreference.REDUCE,
      label: "Reduced Motion",
      description: "Minimize non-essential motion effects"
    },
    {
      value: MotionPreference.NO_MOTION,
      label: "No Motion",
      description: "Disable all animations and transitions"
    }
  ];
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$5.container, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("fieldset", { className: styles$5.fieldset, disabled, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("legend", { className: styles$5.legend, children: [
      "Motion & Animation",
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$5.helpText, children: "Control motion effects for comfort and accessibility" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$5.options, role: "radiogroup", "aria-label": "Motion preference options", children: options2.map((option2) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "label",
      {
        className: `${styles$5.option} ${value === option2.value ? styles$5.selected : ""}`,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "radio",
              name: "motion-preference",
              value: option2.value,
              checked: value === option2.value,
              onChange: () => onChange(option2.value),
              disabled,
              className: styles$5.radio,
              "aria-describedby": `motion-${option2.value}-desc`
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$5.optionLabel, children: [
            option2.label,
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "span",
              {
                id: `motion-${option2.value}-desc`,
                className: styles$5.optionDescription,
                children: option2.description
              }
            )
          ] })
        ]
      },
      option2.value
    )) })
  ] }) });
};
const container$2 = "_container_1rka8_6";
const title$1 = "_title_1rka8_13";
const loading$1 = "_loading_1rka8_20";
const table = "_table_1rka8_26";
const headerCell = "_headerCell_1rka8_34";
const row = "_row_1rka8_44";
const cell = "_cell_1rka8_56";
const kbd = "_kbd_1rka8_62";
const styles$4 = {
  container: container$2,
  title: title$1,
  loading: loading$1,
  table,
  headerCell,
  row,
  cell,
  kbd
};
const KeyboardShortcutsPanel = () => {
  const [shortcuts, setShortcuts] = reactExports.useState([]);
  const [isLoading, setIsLoading] = reactExports.useState(true);
  reactExports.useEffect(() => {
    const loadShortcuts = async () => {
      try {
        const loaded = await accessibilityService.getKeyboardShortcuts();
        setShortcuts(loaded);
      } catch (error2) {
        console.error("[KeyboardShortcutsPanel] Failed to load shortcuts:", error2);
        setShortcuts(accessibilityService.getDefaultShortcuts());
      } finally {
        setIsLoading(false);
      }
    };
    loadShortcuts();
  }, []);
  const formatShortcut = (shortcut) => {
    const parts = [...shortcut.modifiers.map((m) => m.charAt(0).toUpperCase() + m.slice(1))];
    const key = shortcut.key.replace("Key", "");
    parts.push(key);
    return parts.join(" + ");
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4.loading, children: "Loading keyboard shortcuts..." });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4.container, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: styles$4.title, children: "Available Keyboard Shortcuts" }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("table", { className: styles$4.table, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { scope: "col", className: styles$4.headerCell, children: "Shortcut" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("th", { scope: "col", className: styles$4.headerCell, children: "Action" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { children: shortcuts.map((shortcut) => /* @__PURE__ */ jsxRuntimeExports.jsxs("tr", { className: styles$4.row, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: styles$4.cell, children: /* @__PURE__ */ jsxRuntimeExports.jsx("kbd", { className: styles$4.kbd, children: formatShortcut(shortcut) }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("td", { className: styles$4.cell, children: shortcut.description })
      ] }, shortcut.id)) })
    ] })
  ] });
};
const skipLinks = "_skipLinks_arvoc_6";
const skipLink = "_skipLink_arvoc_6";
const styles$3 = {
  skipLinks,
  skipLink
};
const SkipLinks = () => {
  const skipLinks2 = [
    { href: "#main-content", label: "Skip to main content" },
    { href: "#navigation", label: "Skip to navigation" },
    { href: "#footer", label: "Skip to footer" }
  ];
  return /* @__PURE__ */ jsxRuntimeExports.jsx("nav", { className: styles$3.skipLinks, "aria-label": "Skip navigation", children: skipLinks2.map((link) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "a",
    {
      href: link.href,
      className: styles$3.skipLink,
      children: link.label
    },
    link.href
  )) });
};
const container$1 = "_container_dmca2_6";
const fieldset = "_fieldset_dmca2_10";
const legend = "_legend_dmca2_16";
const helpText$1 = "_helpText_dmca2_26";
const options = "_options_dmca2_32";
const option = "_option_dmca2_32";
const selected = "_selected_dmca2_55";
const radio = "_radio_dmca2_60";
const optionLabel = "_optionLabel_dmca2_72";
const optionDescription = "_optionDescription_dmca2_81";
const styles$2 = {
  container: container$1,
  fieldset,
  legend,
  helpText: helpText$1,
  options,
  option,
  selected,
  radio,
  optionLabel,
  optionDescription
};
const FocusIndicator = ({
  value,
  onChange,
  disabled = false
}) => {
  const options2 = [
    {
      value: FocusIndicatorStyle.DEFAULT,
      label: "Default",
      description: "2px outline"
    },
    {
      value: FocusIndicatorStyle.ENHANCED,
      label: "Enhanced",
      description: "3px outline with offset"
    },
    {
      value: FocusIndicatorStyle.HIGH_VISIBILITY,
      label: "High Visibility",
      description: "4px outline with glow"
    }
  ];
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.container, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("fieldset", { className: styles$2.fieldset, disabled, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("legend", { className: styles$2.legend, children: [
      "Focus Indicator Style",
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.helpText, children: "Customize keyboard focus visibility" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2.options, role: "radiogroup", "aria-label": "Focus indicator style options", children: options2.map((option2) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "label",
      {
        className: `${styles$2.option} ${value === option2.value ? styles$2.selected : ""}`,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "radio",
              name: "focus-indicator",
              value: option2.value,
              checked: value === option2.value,
              onChange: () => onChange(option2.value),
              disabled,
              className: styles$2.radio,
              "aria-describedby": `focus-indicator-${option2.value}-desc`
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$2.optionLabel, children: [
            option2.label,
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "span",
              {
                id: `focus-indicator-${option2.value}-desc`,
                className: styles$2.optionDescription,
                children: option2.description
              }
            )
          ] })
        ]
      },
      option2.value
    )) })
  ] }) });
};
const announcer = "_announcer_1nr2c_6";
const styles$1 = {
  announcer
};
const ScreenReaderAnnouncer = () => {
  const politeRef = reactExports.useRef(null);
  const assertiveRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    const handleAnnounce = (event) => {
      const { message, politeness = "polite" } = event.detail;
      const target = politeness === "assertive" ? assertiveRef.current : politeRef.current;
      if (target) {
        target.textContent = message;
        setTimeout(() => {
          target.textContent = "";
        }, 3e3);
      }
    };
    window.addEventListener("announce", handleAnnounce);
    return () => {
      window.removeEventListener("announce", handleAnnounce);
    };
  }, []);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: politeRef,
        className: styles$1.announcer,
        role: "status",
        "aria-live": "polite",
        "aria-atomic": "true"
      }
    ),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref: assertiveRef,
        className: styles$1.announcer,
        role: "alert",
        "aria-live": "assertive",
        "aria-atomic": "true"
      }
    )
  ] });
};
const container = "_container_gakt3_13";
const header = "_header_gakt3_23";
const title = "_title_gakt3_29";
const description = "_description_gakt3_37";
const loading = "_loading_gakt3_44";
const spinner = "_spinner_gakt3_54";
const error = "_error_gakt3_70";
const saveStatus = "_saveStatus_gakt3_90";
const success = "_success_gakt3_97";
const sections = "_sections_gakt3_110";
const section = "_section_gakt3_110";
const sectionTitle = "_sectionTitle_gakt3_124";
const sectionDescription = "_sectionDescription_gakt3_131";
const controls = "_controls_gakt3_138";
const control = "_control_gakt3_138";
const label = "_label_gakt3_150";
const helpText = "_helpText_gakt3_159";
const checkbox = "_checkbox_gakt3_166";
const slider = "_slider_gakt3_184";
const actions = "_actions_gakt3_225";
const resetButton = "_resetButton_gakt3_233";
const styles = {
  container,
  header,
  title,
  description,
  loading,
  spinner,
  error,
  saveStatus,
  success,
  sections,
  section,
  sectionTitle,
  sectionDescription,
  controls,
  control,
  label,
  helpText,
  checkbox,
  slider,
  actions,
  resetButton
};
const AccessibilitySettings = () => {
  const {
    preferences,
    isLoading,
    error: error2,
    updatePreferences,
    resetPreferences,
    announce
  } = useAccessibilityContext();
  const [isSaving, setIsSaving] = reactExports.useState(false);
  const [saveMessage, setSaveMessage] = reactExports.useState(null);
  const handleUpdate = async (updates) => {
    if (!preferences) return;
    setIsSaving(true);
    setSaveMessage(null);
    try {
      await updatePreferences(updates);
      setSaveMessage("Settings saved successfully");
      announce("Settings saved successfully");
      setTimeout(() => setSaveMessage(null), 3e3);
    } catch (err) {
      setSaveMessage(`Error: ${err.message}`);
      announce("Failed to save settings", "assertive");
    } finally {
      setIsSaving(false);
    }
  };
  const handleReset = async () => {
    if (!confirm("Reset all accessibility settings to defaults? This cannot be undone.")) {
      return;
    }
    setIsSaving(true);
    setSaveMessage(null);
    try {
      await resetPreferences();
      setSaveMessage("Settings reset to defaults");
      announce("Settings reset to defaults");
      setTimeout(() => setSaveMessage(null), 3e3);
    } catch (err) {
      setSaveMessage(`Error: ${err.message}`);
      announce("Failed to reset settings", "assertive");
    } finally {
      setIsSaving(false);
    }
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.container, role: "main", "aria-busy": "true", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.loading, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.spinner, "aria-label": "Loading accessibility settings" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading accessibility settings..." })
    ] }) });
  }
  if (!preferences) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.container, role: "main", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.error, role: "alert", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: "Error Loading Settings" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error2 || "Failed to load accessibility preferences" })
    ] }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(SkipLinks, {}),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.container, role: "main", id: "main-content", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { className: styles.header, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: styles.title, children: "Accessibility Settings" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.description, children: "Customize your accessibility preferences to personalize your learning experience. All changes are saved automatically." })
      ] }),
      saveMessage && /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          className: `${styles.saveStatus} ${saveMessage.startsWith("Error") ? styles.error : styles.success}`,
          role: "status",
          "aria-live": "polite",
          children: saveMessage
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.sections, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, "aria-labelledby": "visual-heading", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { id: "visual-heading", className: styles.sectionTitle, children: "Visual Preferences" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "Customize text size, color scheme, and visual appearance" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.controls, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              FontSizeSelector,
              {
                value: preferences.fontSize,
                onChange: (fontSize) => handleUpdate({ fontSize }),
                disabled: isSaving
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              ColorSchemeSelector,
              {
                value: preferences.colorScheme,
                highContrastMode: preferences.highContrastMode,
                onColorSchemeChange: (colorScheme) => handleUpdate({ colorScheme }),
                onHighContrastChange: (highContrastMode) => handleUpdate({ highContrastMode }),
                disabled: isSaving
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              FocusIndicator,
              {
                value: preferences.focusIndicatorStyle,
                onChange: (focusIndicatorStyle) => handleUpdate({ focusIndicatorStyle }),
                disabled: isSaving
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "reduce-transparency", className: styles.label, children: [
                "Reduce Transparency",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Reduces transparency effects for better visibility" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "reduce-transparency",
                  checked: preferences.reduceTransparency,
                  onChange: (e) => handleUpdate({ reduceTransparency: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, "aria-labelledby": "motion-heading", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { id: "motion-heading", className: styles.sectionTitle, children: "Motion & Animation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "Control animations and motion effects" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.controls, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            MotionPreferences,
            {
              value: preferences.motionPreference,
              onChange: (motionPreference) => handleUpdate({ motionPreference }),
              disabled: isSaving
            }
          ) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, "aria-labelledby": "keyboard-heading", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { id: "keyboard-heading", className: styles.sectionTitle, children: "Keyboard Navigation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "Configure keyboard shortcuts and navigation" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.controls, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "keyboard-shortcuts", className: styles.label, children: [
                "Enable Keyboard Shortcuts",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Enable custom keyboard shortcuts for faster navigation" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "keyboard-shortcuts",
                  checked: preferences.keyboardShortcutsEnabled,
                  onChange: (e) => handleUpdate({ keyboardShortcutsEnabled: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "skip-links-visible", className: styles.label, children: [
                "Always Show Skip Links",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Keep skip navigation links always visible (normally shown on focus)" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "skip-links-visible",
                  checked: preferences.skipLinksAlwaysVisible,
                  onChange: (e) => handleUpdate({ skipLinksAlwaysVisible: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "focus-highlight", className: styles.label, children: [
                "Enable Focus Highlights",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Show visual highlight for focused elements" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "focus-highlight",
                  checked: preferences.focusHighlightEnabled,
                  onChange: (e) => handleUpdate({ focusHighlightEnabled: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            preferences.keyboardShortcutsEnabled && /* @__PURE__ */ jsxRuntimeExports.jsx(KeyboardShortcutsPanel, {})
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, "aria-labelledby": "screen-reader-heading", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { id: "screen-reader-heading", className: styles.sectionTitle, children: "Screen Reader" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "Optimize for screen reader users" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.controls, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "screen-reader-optimizations", className: styles.label, children: [
                "Enable Screen Reader Optimizations",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Optimizes interface for screen reader users" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "screen-reader-optimizations",
                  checked: preferences.screenReaderOptimizations,
                  onChange: (e) => handleUpdate({ screenReaderOptimizations: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "announce-page-changes", className: styles.label, children: [
                "Announce Page Changes",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Announce when navigating to new pages" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "announce-page-changes",
                  checked: preferences.announcePageChanges,
                  onChange: (e) => handleUpdate({ announcePageChanges: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "verbose-announcements", className: styles.label, children: [
                "Verbose Announcements",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Provide more detailed screen reader announcements" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "verbose-announcements",
                  checked: preferences.verboseAnnouncements,
                  onChange: (e) => handleUpdate({ verboseAnnouncements: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, "aria-labelledby": "media-heading", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { id: "media-heading", className: styles.sectionTitle, children: "Media Preferences" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "Configure audio and video settings" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.controls, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "auto-play-media", className: styles.label, children: [
                "Auto-play Media",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Automatically play videos and audio when loaded" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "auto-play-media",
                  checked: preferences.autoPlayMedia,
                  onChange: (e) => handleUpdate({ autoPlayMedia: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "captions-enabled", className: styles.label, children: [
                "Enable Captions",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Show captions for video content by default" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "captions-enabled",
                  checked: preferences.captionsEnabled,
                  onChange: (e) => handleUpdate({ captionsEnabled: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "audio-descriptions", className: styles.label, children: [
                "Enable Audio Descriptions",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Enable audio descriptions for video content" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "audio-descriptions",
                  checked: preferences.audioDescriptionsEnabled,
                  onChange: (e) => handleUpdate({ audioDescriptionsEnabled: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("section", { className: styles.section, "aria-labelledby": "timing-heading", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { id: "timing-heading", className: styles.sectionTitle, children: "Timing & Timeouts" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "Adjust timing and auto-refresh settings" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.controls, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "extend-timeouts", className: styles.label, children: [
                "Extend Session Timeouts",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Extend session timeout durations" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "extend-timeouts",
                  checked: preferences.extendTimeouts,
                  onChange: (e) => handleUpdate({ extendTimeouts: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] }),
            preferences.extendTimeouts && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "timeout-multiplier", className: styles.label, children: [
                "Timeout Extension (1.0x to 5.0x)",
                /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.helpText, children: [
                  "Current: ",
                  preferences.timeoutMultiplier.toFixed(1),
                  "x"
                ] })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "range",
                  id: "timeout-multiplier",
                  min: "1.0",
                  max: "5.0",
                  step: "0.5",
                  value: preferences.timeoutMultiplier,
                  onChange: (e) => handleUpdate({ timeoutMultiplier: parseFloat(e.target.value) }),
                  disabled: isSaving,
                  className: styles.slider,
                  "aria-valuemin": 1,
                  "aria-valuemax": 5,
                  "aria-valuenow": preferences.timeoutMultiplier
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.control, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "disable-auto-refresh", className: styles.label, children: [
                "Disable Auto-refresh",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.helpText, children: "Prevent automatic page refresh" })
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  id: "disable-auto-refresh",
                  checked: preferences.disableAutoRefresh,
                  onChange: (e) => handleUpdate({ disableAutoRefresh: e.target.checked }),
                  disabled: isSaving,
                  className: styles.checkbox
                }
              )
            ] })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.actions, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          type: "button",
          onClick: handleReset,
          disabled: isSaving,
          className: styles.resetButton,
          "aria-label": "Reset all accessibility settings to defaults",
          children: "Reset to Defaults"
        }
      ) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(ScreenReaderAnnouncer, {})
  ] });
};
export {
  AccessibilitySettings,
  AccessibilitySettings as default
};
//# sourceMappingURL=AccessibilitySettings-BA0oiMVN.js.map
