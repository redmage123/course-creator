import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, u as useNavigate, L as Link } from "./react-vendor-cEae-lCc.js";
import { C as Card, H as Heading, B as Button, S as Spinner } from "./index-C0G9mbri.js";
import { I as Input } from "./Input-O5-QH4ck.js";
import { T as Textarea } from "./Textarea-sTT_CGBL.js";
import { S as Select } from "./Select-D3EGugkq.js";
import { o as organizationService } from "./organizationService-DsJ0Nzue.js";
import "./state-vendor-B_izx0oA.js";
const countries = [
  // Default: United States at the top
  { code: "US", name: "United States", dialCode: "+1", flag: "🇺🇸" },
  // Alphabetically sorted countries
  { code: "AF", name: "Afghanistan", dialCode: "+93", flag: "🇦🇫" },
  { code: "AL", name: "Albania", dialCode: "+355", flag: "🇦🇱" },
  { code: "DZ", name: "Algeria", dialCode: "+213", flag: "🇩🇿" },
  { code: "AD", name: "Andorra", dialCode: "+376", flag: "🇦🇩" },
  { code: "AO", name: "Angola", dialCode: "+244", flag: "🇦🇴" },
  { code: "AG", name: "Antigua and Barbuda", dialCode: "+1", flag: "🇦🇬" },
  { code: "AR", name: "Argentina", dialCode: "+54", flag: "🇦🇷" },
  { code: "AM", name: "Armenia", dialCode: "+374", flag: "🇦🇲" },
  { code: "AU", name: "Australia", dialCode: "+61", flag: "🇦🇺" },
  { code: "AT", name: "Austria", dialCode: "+43", flag: "🇦🇹" },
  { code: "AZ", name: "Azerbaijan", dialCode: "+994", flag: "🇦🇿" },
  { code: "BS", name: "Bahamas", dialCode: "+1", flag: "🇧🇸" },
  { code: "BH", name: "Bahrain", dialCode: "+973", flag: "🇧🇭" },
  { code: "BD", name: "Bangladesh", dialCode: "+880", flag: "🇧🇩" },
  { code: "BB", name: "Barbados", dialCode: "+1", flag: "🇧🇧" },
  { code: "BY", name: "Belarus", dialCode: "+375", flag: "🇧🇾" },
  { code: "BE", name: "Belgium", dialCode: "+32", flag: "🇧🇪" },
  { code: "BZ", name: "Belize", dialCode: "+501", flag: "🇧🇿" },
  { code: "BJ", name: "Benin", dialCode: "+229", flag: "🇧🇯" },
  { code: "BT", name: "Bhutan", dialCode: "+975", flag: "🇧🇹" },
  { code: "BO", name: "Bolivia", dialCode: "+591", flag: "🇧🇴" },
  { code: "BA", name: "Bosnia and Herzegovina", dialCode: "+387", flag: "🇧🇦" },
  { code: "BW", name: "Botswana", dialCode: "+267", flag: "🇧🇼" },
  { code: "BR", name: "Brazil", dialCode: "+55", flag: "🇧🇷" },
  { code: "BN", name: "Brunei", dialCode: "+673", flag: "🇧🇳" },
  { code: "BG", name: "Bulgaria", dialCode: "+359", flag: "🇧🇬" },
  { code: "BF", name: "Burkina Faso", dialCode: "+226", flag: "🇧🇫" },
  { code: "BI", name: "Burundi", dialCode: "+257", flag: "🇧🇮" },
  { code: "KH", name: "Cambodia", dialCode: "+855", flag: "🇰🇭" },
  { code: "CM", name: "Cameroon", dialCode: "+237", flag: "🇨🇲" },
  { code: "CA", name: "Canada", dialCode: "+1", flag: "🇨🇦" },
  { code: "CV", name: "Cape Verde", dialCode: "+238", flag: "🇨🇻" },
  { code: "CF", name: "Central African Republic", dialCode: "+236", flag: "🇨🇫" },
  { code: "TD", name: "Chad", dialCode: "+235", flag: "🇹🇩" },
  { code: "CL", name: "Chile", dialCode: "+56", flag: "🇨🇱" },
  { code: "CN", name: "China", dialCode: "+86", flag: "🇨🇳" },
  { code: "CO", name: "Colombia", dialCode: "+57", flag: "🇨🇴" },
  { code: "KM", name: "Comoros", dialCode: "+269", flag: "🇰🇲" },
  { code: "CG", name: "Congo", dialCode: "+242", flag: "🇨🇬" },
  { code: "CD", name: "Congo (DRC)", dialCode: "+243", flag: "🇨🇩" },
  { code: "CR", name: "Costa Rica", dialCode: "+506", flag: "🇨🇷" },
  { code: "HR", name: "Croatia", dialCode: "+385", flag: "🇭🇷" },
  { code: "CU", name: "Cuba", dialCode: "+53", flag: "🇨🇺" },
  { code: "CY", name: "Cyprus", dialCode: "+357", flag: "🇨🇾" },
  { code: "CZ", name: "Czech Republic", dialCode: "+420", flag: "🇨🇿" },
  { code: "DK", name: "Denmark", dialCode: "+45", flag: "🇩🇰" },
  { code: "DJ", name: "Djibouti", dialCode: "+253", flag: "🇩🇯" },
  { code: "DM", name: "Dominica", dialCode: "+1", flag: "🇩🇲" },
  { code: "DO", name: "Dominican Republic", dialCode: "+1", flag: "🇩🇴" },
  { code: "EC", name: "Ecuador", dialCode: "+593", flag: "🇪🇨" },
  { code: "EG", name: "Egypt", dialCode: "+20", flag: "🇪🇬" },
  { code: "SV", name: "El Salvador", dialCode: "+503", flag: "🇸🇻" },
  { code: "GQ", name: "Equatorial Guinea", dialCode: "+240", flag: "🇬🇶" },
  { code: "ER", name: "Eritrea", dialCode: "+291", flag: "🇪🇷" },
  { code: "EE", name: "Estonia", dialCode: "+372", flag: "🇪🇪" },
  { code: "SZ", name: "Eswatini", dialCode: "+268", flag: "🇸🇿" },
  { code: "ET", name: "Ethiopia", dialCode: "+251", flag: "🇪🇹" },
  { code: "FJ", name: "Fiji", dialCode: "+679", flag: "🇫🇯" },
  { code: "FI", name: "Finland", dialCode: "+358", flag: "🇫🇮" },
  { code: "FR", name: "France", dialCode: "+33", flag: "🇫🇷" },
  { code: "GA", name: "Gabon", dialCode: "+241", flag: "🇬🇦" },
  { code: "GM", name: "Gambia", dialCode: "+220", flag: "🇬🇲" },
  { code: "GE", name: "Georgia", dialCode: "+995", flag: "🇬🇪" },
  { code: "DE", name: "Germany", dialCode: "+49", flag: "🇩🇪" },
  { code: "GH", name: "Ghana", dialCode: "+233", flag: "🇬🇭" },
  { code: "GR", name: "Greece", dialCode: "+30", flag: "🇬🇷" },
  { code: "GD", name: "Grenada", dialCode: "+1", flag: "🇬🇩" },
  { code: "GT", name: "Guatemala", dialCode: "+502", flag: "🇬🇹" },
  { code: "GN", name: "Guinea", dialCode: "+224", flag: "🇬🇳" },
  { code: "GW", name: "Guinea-Bissau", dialCode: "+245", flag: "🇬🇼" },
  { code: "GY", name: "Guyana", dialCode: "+592", flag: "🇬🇾" },
  { code: "HT", name: "Haiti", dialCode: "+509", flag: "🇭🇹" },
  { code: "HN", name: "Honduras", dialCode: "+504", flag: "🇭🇳" },
  { code: "HK", name: "Hong Kong", dialCode: "+852", flag: "🇭🇰" },
  { code: "HU", name: "Hungary", dialCode: "+36", flag: "🇭🇺" },
  { code: "IS", name: "Iceland", dialCode: "+354", flag: "🇮🇸" },
  { code: "IN", name: "India", dialCode: "+91", flag: "🇮🇳" },
  { code: "ID", name: "Indonesia", dialCode: "+62", flag: "🇮🇩" },
  { code: "IR", name: "Iran", dialCode: "+98", flag: "🇮🇷" },
  { code: "IQ", name: "Iraq", dialCode: "+964", flag: "🇮🇶" },
  { code: "IE", name: "Ireland", dialCode: "+353", flag: "🇮🇪" },
  { code: "IL", name: "Israel", dialCode: "+972", flag: "🇮🇱" },
  { code: "IT", name: "Italy", dialCode: "+39", flag: "🇮🇹" },
  { code: "CI", name: "Ivory Coast", dialCode: "+225", flag: "🇨🇮" },
  { code: "JM", name: "Jamaica", dialCode: "+1", flag: "🇯🇲" },
  { code: "JP", name: "Japan", dialCode: "+81", flag: "🇯🇵" },
  { code: "JO", name: "Jordan", dialCode: "+962", flag: "🇯🇴" },
  { code: "KZ", name: "Kazakhstan", dialCode: "+7", flag: "🇰🇿" },
  { code: "KE", name: "Kenya", dialCode: "+254", flag: "🇰🇪" },
  { code: "KI", name: "Kiribati", dialCode: "+686", flag: "🇰🇮" },
  { code: "KW", name: "Kuwait", dialCode: "+965", flag: "🇰🇼" },
  { code: "KG", name: "Kyrgyzstan", dialCode: "+996", flag: "🇰🇬" },
  { code: "LA", name: "Laos", dialCode: "+856", flag: "🇱🇦" },
  { code: "LV", name: "Latvia", dialCode: "+371", flag: "🇱🇻" },
  { code: "LB", name: "Lebanon", dialCode: "+961", flag: "🇱🇧" },
  { code: "LS", name: "Lesotho", dialCode: "+266", flag: "🇱🇸" },
  { code: "LR", name: "Liberia", dialCode: "+231", flag: "🇱🇷" },
  { code: "LY", name: "Libya", dialCode: "+218", flag: "🇱🇾" },
  { code: "LI", name: "Liechtenstein", dialCode: "+423", flag: "🇱🇮" },
  { code: "LT", name: "Lithuania", dialCode: "+370", flag: "🇱🇹" },
  { code: "LU", name: "Luxembourg", dialCode: "+352", flag: "🇱🇺" },
  { code: "MO", name: "Macau", dialCode: "+853", flag: "🇲🇴" },
  { code: "MG", name: "Madagascar", dialCode: "+261", flag: "🇲🇬" },
  { code: "MW", name: "Malawi", dialCode: "+265", flag: "🇲🇼" },
  { code: "MY", name: "Malaysia", dialCode: "+60", flag: "🇲🇾" },
  { code: "MV", name: "Maldives", dialCode: "+960", flag: "🇲🇻" },
  { code: "ML", name: "Mali", dialCode: "+223", flag: "🇲🇱" },
  { code: "MT", name: "Malta", dialCode: "+356", flag: "🇲🇹" },
  { code: "MH", name: "Marshall Islands", dialCode: "+692", flag: "🇲🇭" },
  { code: "MR", name: "Mauritania", dialCode: "+222", flag: "🇲🇷" },
  { code: "MU", name: "Mauritius", dialCode: "+230", flag: "🇲🇺" },
  { code: "MX", name: "Mexico", dialCode: "+52", flag: "🇲🇽" },
  { code: "FM", name: "Micronesia", dialCode: "+691", flag: "🇫🇲" },
  { code: "MD", name: "Moldova", dialCode: "+373", flag: "🇲🇩" },
  { code: "MC", name: "Monaco", dialCode: "+377", flag: "🇲🇨" },
  { code: "MN", name: "Mongolia", dialCode: "+976", flag: "🇲🇳" },
  { code: "ME", name: "Montenegro", dialCode: "+382", flag: "🇲🇪" },
  { code: "MA", name: "Morocco", dialCode: "+212", flag: "🇲🇦" },
  { code: "MZ", name: "Mozambique", dialCode: "+258", flag: "🇲🇿" },
  { code: "MM", name: "Myanmar", dialCode: "+95", flag: "🇲🇲" },
  { code: "NA", name: "Namibia", dialCode: "+264", flag: "🇳🇦" },
  { code: "NR", name: "Nauru", dialCode: "+674", flag: "🇳🇷" },
  { code: "NP", name: "Nepal", dialCode: "+977", flag: "🇳🇵" },
  { code: "NL", name: "Netherlands", dialCode: "+31", flag: "🇳🇱" },
  { code: "NZ", name: "New Zealand", dialCode: "+64", flag: "🇳🇿" },
  { code: "NI", name: "Nicaragua", dialCode: "+505", flag: "🇳🇮" },
  { code: "NE", name: "Niger", dialCode: "+227", flag: "🇳🇪" },
  { code: "NG", name: "Nigeria", dialCode: "+234", flag: "🇳🇬" },
  { code: "KP", name: "North Korea", dialCode: "+850", flag: "🇰🇵" },
  { code: "MK", name: "North Macedonia", dialCode: "+389", flag: "🇲🇰" },
  { code: "NO", name: "Norway", dialCode: "+47", flag: "🇳🇴" },
  { code: "OM", name: "Oman", dialCode: "+968", flag: "🇴🇲" },
  { code: "PK", name: "Pakistan", dialCode: "+92", flag: "🇵🇰" },
  { code: "PW", name: "Palau", dialCode: "+680", flag: "🇵🇼" },
  { code: "PS", name: "Palestine", dialCode: "+970", flag: "🇵🇸" },
  { code: "PA", name: "Panama", dialCode: "+507", flag: "🇵🇦" },
  { code: "PG", name: "Papua New Guinea", dialCode: "+675", flag: "🇵🇬" },
  { code: "PY", name: "Paraguay", dialCode: "+595", flag: "🇵🇾" },
  { code: "PE", name: "Peru", dialCode: "+51", flag: "🇵🇪" },
  { code: "PH", name: "Philippines", dialCode: "+63", flag: "🇵🇭" },
  { code: "PL", name: "Poland", dialCode: "+48", flag: "🇵🇱" },
  { code: "PT", name: "Portugal", dialCode: "+351", flag: "🇵🇹" },
  { code: "PR", name: "Puerto Rico", dialCode: "+1", flag: "🇵🇷" },
  { code: "QA", name: "Qatar", dialCode: "+974", flag: "🇶🇦" },
  { code: "RO", name: "Romania", dialCode: "+40", flag: "🇷🇴" },
  { code: "RU", name: "Russia", dialCode: "+7", flag: "🇷🇺" },
  { code: "RW", name: "Rwanda", dialCode: "+250", flag: "🇷🇼" },
  { code: "KN", name: "Saint Kitts and Nevis", dialCode: "+1", flag: "🇰🇳" },
  { code: "LC", name: "Saint Lucia", dialCode: "+1", flag: "🇱🇨" },
  { code: "VC", name: "Saint Vincent and the Grenadines", dialCode: "+1", flag: "🇻🇨" },
  { code: "WS", name: "Samoa", dialCode: "+685", flag: "🇼🇸" },
  { code: "SM", name: "San Marino", dialCode: "+378", flag: "🇸🇲" },
  { code: "ST", name: "Sao Tome and Principe", dialCode: "+239", flag: "🇸🇹" },
  { code: "SA", name: "Saudi Arabia", dialCode: "+966", flag: "🇸🇦" },
  { code: "SN", name: "Senegal", dialCode: "+221", flag: "🇸🇳" },
  { code: "RS", name: "Serbia", dialCode: "+381", flag: "🇷🇸" },
  { code: "SC", name: "Seychelles", dialCode: "+248", flag: "🇸🇨" },
  { code: "SL", name: "Sierra Leone", dialCode: "+232", flag: "🇸🇱" },
  { code: "SG", name: "Singapore", dialCode: "+65", flag: "🇸🇬" },
  { code: "SK", name: "Slovakia", dialCode: "+421", flag: "🇸🇰" },
  { code: "SI", name: "Slovenia", dialCode: "+386", flag: "🇸🇮" },
  { code: "SB", name: "Solomon Islands", dialCode: "+677", flag: "🇸🇧" },
  { code: "SO", name: "Somalia", dialCode: "+252", flag: "🇸🇴" },
  { code: "ZA", name: "South Africa", dialCode: "+27", flag: "🇿🇦" },
  { code: "KR", name: "South Korea", dialCode: "+82", flag: "🇰🇷" },
  { code: "SS", name: "South Sudan", dialCode: "+211", flag: "🇸🇸" },
  { code: "ES", name: "Spain", dialCode: "+34", flag: "🇪🇸" },
  { code: "LK", name: "Sri Lanka", dialCode: "+94", flag: "🇱🇰" },
  { code: "SD", name: "Sudan", dialCode: "+249", flag: "🇸🇩" },
  { code: "SR", name: "Suriname", dialCode: "+597", flag: "🇸🇷" },
  { code: "SE", name: "Sweden", dialCode: "+46", flag: "🇸🇪" },
  { code: "CH", name: "Switzerland", dialCode: "+41", flag: "🇨🇭" },
  { code: "SY", name: "Syria", dialCode: "+963", flag: "🇸🇾" },
  { code: "TW", name: "Taiwan", dialCode: "+886", flag: "🇹🇼" },
  { code: "TJ", name: "Tajikistan", dialCode: "+992", flag: "🇹🇯" },
  { code: "TZ", name: "Tanzania", dialCode: "+255", flag: "🇹🇿" },
  { code: "TH", name: "Thailand", dialCode: "+66", flag: "🇹🇭" },
  { code: "TL", name: "Timor-Leste", dialCode: "+670", flag: "🇹🇱" },
  { code: "TG", name: "Togo", dialCode: "+228", flag: "🇹🇬" },
  { code: "TO", name: "Tonga", dialCode: "+676", flag: "🇹🇴" },
  { code: "TT", name: "Trinidad and Tobago", dialCode: "+1", flag: "🇹🇹" },
  { code: "TN", name: "Tunisia", dialCode: "+216", flag: "🇹🇳" },
  { code: "TR", name: "Turkey", dialCode: "+90", flag: "🇹🇷" },
  { code: "TM", name: "Turkmenistan", dialCode: "+993", flag: "🇹🇲" },
  { code: "TV", name: "Tuvalu", dialCode: "+688", flag: "🇹🇻" },
  { code: "UG", name: "Uganda", dialCode: "+256", flag: "🇺🇬" },
  { code: "UA", name: "Ukraine", dialCode: "+380", flag: "🇺🇦" },
  { code: "AE", name: "United Arab Emirates", dialCode: "+971", flag: "🇦🇪" },
  { code: "GB", name: "United Kingdom", dialCode: "+44", flag: "🇬🇧" },
  { code: "UY", name: "Uruguay", dialCode: "+598", flag: "🇺🇾" },
  { code: "UZ", name: "Uzbekistan", dialCode: "+998", flag: "🇺🇿" },
  { code: "VU", name: "Vanuatu", dialCode: "+678", flag: "🇻🇺" },
  { code: "VA", name: "Vatican City", dialCode: "+379", flag: "🇻🇦" },
  { code: "VE", name: "Venezuela", dialCode: "+58", flag: "🇻🇪" },
  { code: "VN", name: "Vietnam", dialCode: "+84", flag: "🇻🇳" },
  { code: "YE", name: "Yemen", dialCode: "+967", flag: "🇾🇪" },
  { code: "ZM", name: "Zambia", dialCode: "+260", flag: "🇿🇲" },
  { code: "ZW", name: "Zimbabwe", dialCode: "+263", flag: "🇿🇼" }
];
const defaultCountry = countries[0];
const styles$1 = {
  "phone-input-container": "_phone-input-container_sgwf4_12",
  "phone-input-label": "_phone-input-label_sgwf4_20",
  "phone-input-required": "_phone-input-required_sgwf4_26",
  "phone-input-wrapper": "_phone-input-wrapper_sgwf4_32",
  "phone-input-error": "_phone-input-error_sgwf4_47",
  "phone-input-disabled": "_phone-input-disabled_sgwf4_55",
  "country-selector": "_country-selector_sgwf4_61",
  "country-flag": "_country-flag_sgwf4_84",
  "country-dial-code": "_country-dial-code_sgwf4_89",
  "dropdown-arrow": "_dropdown-arrow_sgwf4_95",
  "dropdown-arrow-open": "_dropdown-arrow-open_sgwf4_101",
  "phone-number-input": "_phone-number-input_sgwf4_106",
  "country-dropdown": "_country-dropdown_sgwf4_127",
  "search-container": "_search-container_sgwf4_155",
  "search-input": "_search-input_sgwf4_160",
  "country-list": "_country-list_sgwf4_179",
  "country-list-empty": "_country-list-empty_sgwf4_187",
  "country-list-item": "_country-list-item_sgwf4_194",
  "country-list-item-highlighted": "_country-list-item-highlighted_sgwf4_207",
  "country-list-item-selected": "_country-list-item-selected_sgwf4_211",
  "country-item-flag": "_country-item-flag_sgwf4_219",
  "country-item-name": "_country-item-name_sgwf4_225",
  "country-item-dial": "_country-item-dial_sgwf4_234",
  "phone-input-message": "_phone-input-message_sgwf4_241",
  "phone-input-error-text": "_phone-input-error-text_sgwf4_246",
  "phone-input-helper-text": "_phone-input-helper-text_sgwf4_250"
};
const PhoneInput = ({
  label,
  countryCode = "US",
  value = "",
  onChange,
  onCountryChange,
  placeholder = "Phone number",
  error: error2,
  helperText,
  required: required2 = false,
  disabled = false,
  name,
  className
}) => {
  const [isOpen, setIsOpen] = reactExports.useState(false);
  const [searchTerm, setSearchTerm] = reactExports.useState("");
  const [highlightedIndex, setHighlightedIndex] = reactExports.useState(0);
  const containerRef = reactExports.useRef(null);
  const searchInputRef = reactExports.useRef(null);
  const listRef = reactExports.useRef(null);
  const selectedCountry = countries.find((c) => c.code === countryCode) || defaultCountry;
  const filteredCountries = searchTerm ? countries.filter(
    (c) => c.name.toLowerCase().includes(searchTerm.toLowerCase()) || c.dialCode.includes(searchTerm) || c.code.toLowerCase().includes(searchTerm.toLowerCase())
  ) : countries;
  const handleCountrySelect = (country) => {
    onCountryChange?.(country.code, country.dialCode);
    setIsOpen(false);
    setSearchTerm("");
  };
  const handlePhoneChange = (e) => {
    const newValue = e.target.value.replace(/[^0-9\s\-()]/g, "");
    onChange?.(newValue);
  };
  const handleKeyDown = (e) => {
    if (disabled) return;
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
        } else {
          setHighlightedIndex(
            (prev) => prev < filteredCountries.length - 1 ? prev + 1 : prev
          );
        }
        break;
      case "ArrowUp":
        e.preventDefault();
        if (isOpen) {
          setHighlightedIndex((prev) => prev > 0 ? prev - 1 : 0);
        }
        break;
      case "Enter":
        e.preventDefault();
        if (isOpen && filteredCountries[highlightedIndex]) {
          handleCountrySelect(filteredCountries[highlightedIndex]);
        } else {
          setIsOpen(true);
        }
        break;
      case "Escape":
        e.preventDefault();
        setIsOpen(false);
        setSearchTerm("");
        break;
      case "Tab":
        if (isOpen) {
          setIsOpen(false);
          setSearchTerm("");
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
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);
  reactExports.useEffect(() => {
    if (isOpen && listRef.current) {
      const highlightedEl = listRef.current.children[highlightedIndex];
      if (highlightedEl) {
        highlightedEl.scrollIntoView({ block: "nearest", behavior: "smooth" });
      }
    }
  }, [highlightedIndex, isOpen]);
  reactExports.useEffect(() => {
    setHighlightedIndex(0);
  }, [filteredCountries.length]);
  const containerClasses = [
    styles$1["phone-input-container"],
    error2 && styles$1["phone-input-error"],
    disabled && styles$1["phone-input-disabled"],
    className
  ].filter(Boolean).join(" ");
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { ref: containerRef, className: containerClasses, children: [
    label && /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles$1["phone-input-label"], children: [
      label,
      required2 && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["phone-input-required"], children: "*" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["phone-input-wrapper"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "button",
        {
          type: "button",
          className: styles$1["country-selector"],
          onClick: () => !disabled && setIsOpen(!isOpen),
          onKeyDown: handleKeyDown,
          disabled,
          "aria-haspopup": "listbox",
          "aria-expanded": isOpen,
          "aria-label": `Select country, current: ${selectedCountry.name}`,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["country-flag"], children: selectedCountry.flag }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["country-dial-code"], children: selectedCountry.dialCode }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "svg",
              {
                className: `${styles$1["dropdown-arrow"]} ${isOpen ? styles$1["dropdown-arrow-open"] : ""}`,
                width: "12",
                height: "12",
                viewBox: "0 0 12 12",
                fill: "none",
                children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "path",
                  {
                    d: "M3 4.5L6 7.5L9 4.5",
                    stroke: "currentColor",
                    strokeWidth: "1.5",
                    strokeLinecap: "round",
                    strokeLinejoin: "round"
                  }
                )
              }
            )
          ]
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "input",
        {
          type: "tel",
          className: styles$1["phone-number-input"],
          value,
          onChange: handlePhoneChange,
          placeholder,
          disabled,
          name,
          "aria-invalid": !!error2,
          "aria-describedby": error2 ? `${name}-error` : void 0
        }
      ),
      isOpen && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["country-dropdown"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["search-container"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            ref: searchInputRef,
            type: "text",
            className: styles$1["search-input"],
            value: searchTerm,
            onChange: (e) => setSearchTerm(e.target.value),
            placeholder: "Search country...",
            onKeyDown: handleKeyDown
          }
        ) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "ul",
          {
            ref: listRef,
            className: styles$1["country-list"],
            role: "listbox",
            "aria-label": "Select country",
            children: filteredCountries.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx("li", { className: styles$1["country-list-empty"], children: "No countries found" }) : filteredCountries.map((country, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "li",
              {
                className: `${styles$1["country-list-item"]} ${index === highlightedIndex ? styles$1["country-list-item-highlighted"] : ""} ${country.code === countryCode ? styles$1["country-list-item-selected"] : ""}`,
                role: "option",
                "aria-selected": country.code === countryCode,
                onClick: () => handleCountrySelect(country),
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["country-item-flag"], children: country.flag }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["country-item-name"], children: country.name }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["country-item-dial"], children: country.dialCode })
                ]
              },
              country.code
            ))
          }
        )
      ] })
    ] }),
    (error2 || helperText) && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["phone-input-message"], children: error2 ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { id: `${name}-error`, className: styles$1["phone-input-error-text"], children: error2 }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["phone-input-helper-text"], children: helperText }) })
  ] });
};
PhoneInput.displayName = "PhoneInput";
const registrationContainer = "_registrationContainer_1xdfz_7";
const backLink = "_backLink_1xdfz_17";
const registrationCard = "_registrationCard_1xdfz_34";
const registrationHeader = "_registrationHeader_1xdfz_55";
const title = "_title_1xdfz_60";
const subtitle = "_subtitle_1xdfz_66";
const professionalBadge = "_professionalBadge_1xdfz_72";
const form = "_form_1xdfz_84";
const formSection = "_formSection_1xdfz_90";
const sectionTitle = "_sectionTitle_1xdfz_98";
const sectionDescription = "_sectionDescription_1xdfz_110";
const formGrid = "_formGrid_1xdfz_120";
const formGridSingle = "_formGridSingle_1xdfz_126";
const formGroup = "_formGroup_1xdfz_132";
const formLabel = "_formLabel_1xdfz_136";
const optional = "_optional_1xdfz_144";
const required = "_required_1xdfz_150";
const logoUploadArea = "_logoUploadArea_1xdfz_154";
const uploadPlaceholder = "_uploadPlaceholder_1xdfz_169";
const logoPreview = "_logoPreview_1xdfz_187";
const previewImage = "_previewImage_1xdfz_192";
const removeLogo = "_removeLogo_1xdfz_199";
const hiddenFileInput = "_hiddenFileInput_1xdfz_203";
const checkboxGroup = "_checkboxGroup_1xdfz_218";
const checkboxLabel = "_checkboxLabel_1xdfz_224";
const checkbox = "_checkbox_1xdfz_218";
const error = "_error_1xdfz_248";
const submitSection = "_submitSection_1xdfz_254";
const submitError = "_submitError_1xdfz_259";
const submitButton = "_submitButton_1xdfz_273";
const loginLink = "_loginLink_1xdfz_277";
const styles = {
  registrationContainer,
  backLink,
  registrationCard,
  registrationHeader,
  title,
  subtitle,
  professionalBadge,
  form,
  formSection,
  sectionTitle,
  sectionDescription,
  formGrid,
  formGridSingle,
  formGroup,
  formLabel,
  optional,
  required,
  logoUploadArea,
  uploadPlaceholder,
  logoPreview,
  previewImage,
  removeLogo,
  hiddenFileInput,
  checkboxGroup,
  checkboxLabel,
  checkbox,
  error,
  submitSection,
  submitError,
  submitButton,
  loginLink
};
const OrganizationRegistration = () => {
  const navigate = useNavigate();
  const logoInputRef = reactExports.useRef(null);
  const [formData, setFormData] = reactExports.useState({
    name: "",
    slug: "",
    description: "",
    domain: "",
    logo: null,
    logoPreviewUrl: null,
    street_address: "",
    city: "",
    state_province: "",
    postal_code: "",
    country: "US",
    contact_phone_country_code: "US",
    contact_phone: "",
    contact_email: "",
    admin_full_name: "",
    admin_username: "",
    admin_email: "",
    admin_phone_country_code: "US",
    admin_phone: "",
    admin_password: "",
    admin_password_confirm: "",
    terms_accepted: false,
    privacy_accepted: false
  });
  const [errors, setErrors] = reactExports.useState({});
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [submitError2, setSubmitError] = reactExports.useState(null);
  const [slugGenerated, setSlugGenerated] = reactExports.useState(false);
  const [orgEmailManuallyEdited, setOrgEmailManuallyEdited] = reactExports.useState(false);
  const [orgPhoneManuallyEdited, setOrgPhoneManuallyEdited] = reactExports.useState(false);
  reactExports.useEffect(() => {
    if (formData.name && !slugGenerated) {
      const generatedSlug = formData.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
      setFormData((prev) => ({ ...prev, slug: generatedSlug }));
    }
  }, [formData.name, slugGenerated]);
  reactExports.useEffect(() => {
    if (formData.admin_email && !orgEmailManuallyEdited && !formData.contact_email) {
      setFormData((prev) => ({ ...prev, contact_email: formData.admin_email }));
    }
  }, [formData.admin_email, orgEmailManuallyEdited, formData.contact_email]);
  reactExports.useEffect(() => {
    if (formData.admin_phone && !orgPhoneManuallyEdited && !formData.contact_phone) {
      setFormData((prev) => ({
        ...prev,
        contact_phone: formData.admin_phone,
        contact_phone_country_code: formData.admin_phone_country_code
      }));
    }
  }, [formData.admin_phone, formData.admin_phone_country_code, orgPhoneManuallyEdited, formData.contact_phone]);
  const handlePaste = reactExports.useCallback((e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.startsWith("image/")) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) {
          if (file.size > 5 * 1024 * 1024) {
            setErrors((prev) => ({ ...prev, logo: "Logo file must be less than 5MB" }));
            return;
          }
          const previewUrl = URL.createObjectURL(file);
          setFormData((prev) => ({
            ...prev,
            logo: file,
            logoPreviewUrl: previewUrl
          }));
          if (errors.logo) {
            setErrors((prev) => {
              const newErrors = { ...prev };
              delete newErrors.logo;
              return newErrors;
            });
          }
        }
        break;
      }
    }
  }, [errors.logo]);
  reactExports.useEffect(() => {
    document.addEventListener("paste", handlePaste);
    return () => {
      document.removeEventListener("paste", handlePaste);
      if (formData.logoPreviewUrl) {
        URL.revokeObjectURL(formData.logoPreviewUrl);
      }
    };
  }, [handlePaste, formData.logoPreviewUrl]);
  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    const checked = e.target.checked;
    setFormData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
    if (name === "slug") {
      setSlugGenerated(true);
    }
    if (name === "contact_email" && value !== formData.admin_email) {
      setOrgEmailManuallyEdited(true);
    }
    if (name === "contact_phone" && value !== formData.admin_phone) {
      setOrgPhoneManuallyEdited(true);
    }
  };
  const handleSelectChange = (name) => (value) => {
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
  const handleLogoChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.type.startsWith("image/")) {
        setErrors((prev) => ({ ...prev, logo: "Please select an image file" }));
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        setErrors((prev) => ({ ...prev, logo: "Logo file must be less than 5MB" }));
        return;
      }
      if (formData.logoPreviewUrl) {
        URL.revokeObjectURL(formData.logoPreviewUrl);
      }
      const previewUrl = URL.createObjectURL(file);
      setFormData((prev) => ({
        ...prev,
        logo: file,
        logoPreviewUrl: previewUrl
      }));
      if (errors.logo) {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors.logo;
          return newErrors;
        });
      }
    }
  };
  const handleRemoveLogo = () => {
    if (formData.logoPreviewUrl) {
      URL.revokeObjectURL(formData.logoPreviewUrl);
    }
    setFormData((prev) => ({ ...prev, logo: null, logoPreviewUrl: null }));
    if (logoInputRef.current) {
      logoInputRef.current.value = "";
    }
  };
  const handleAdminPhoneChange = (phone) => {
    setFormData((prev) => ({ ...prev, admin_phone: phone }));
    if (errors.admin_phone) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.admin_phone;
        return newErrors;
      });
    }
  };
  const handleAdminPhoneCountryChange = (countryCode, dialCode) => {
    setFormData((prev) => ({ ...prev, admin_phone_country_code: countryCode }));
  };
  const handleContactPhoneChange = (phone) => {
    setFormData((prev) => ({ ...prev, contact_phone: phone }));
    setOrgPhoneManuallyEdited(true);
    if (errors.contact_phone) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.contact_phone;
        return newErrors;
      });
    }
  };
  const handleContactPhoneCountryChange = (countryCode, dialCode) => {
    setFormData((prev) => ({ ...prev, contact_phone_country_code: countryCode }));
    setOrgPhoneManuallyEdited(true);
  };
  const validateForm = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = "Organization name is required";
    }
    if (!formData.slug.trim()) {
      newErrors.slug = "Organization slug is required";
    }
    if (!formData.domain.trim()) {
      newErrors.domain = "Organization domain is required";
    }
    if (!formData.country) {
      newErrors.country = "Country is required";
    }
    if (!formData.contact_email.trim()) {
      newErrors.contact_email = "Contact email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.contact_email)) {
      newErrors.contact_email = "Invalid email format";
    }
    if (!formData.admin_full_name.trim()) {
      newErrors.admin_full_name = "Admin name is required";
    }
    if (!formData.admin_username.trim()) {
      newErrors.admin_username = "Admin username is required";
    }
    if (!formData.admin_email.trim()) {
      newErrors.admin_email = "Admin email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.admin_email)) {
      newErrors.admin_email = "Invalid email format";
    }
    if (!formData.admin_phone.trim()) {
      newErrors.admin_phone = "Admin phone number is required";
    }
    if (!formData.admin_password) {
      newErrors.admin_password = "Password is required";
    } else if (formData.admin_password.length < 8) {
      newErrors.admin_password = "Password must be at least 8 characters";
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.admin_password)) {
      newErrors.admin_password = "Password must contain uppercase, lowercase, and number";
    }
    if (formData.admin_password !== formData.admin_password_confirm) {
      newErrors.admin_password_confirm = "Passwords do not match";
    }
    if (!formData.terms_accepted) {
      newErrors.terms_accepted = "You must accept the Terms of Service";
    }
    if (!formData.privacy_accepted) {
      newErrors.privacy_accepted = "You must accept the Privacy Policy";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      setSubmitError("Please fix the errors above before submitting");
      return;
    }
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const submitData = new FormData();
      submitData.append("name", formData.name);
      submitData.append("slug", formData.slug);
      submitData.append("description", formData.description);
      submitData.append("domain", formData.domain);
      if (formData.logo) {
        submitData.append("logo", formData.logo);
      }
      submitData.append("street_address", formData.street_address);
      submitData.append("city", formData.city);
      submitData.append("state_province", formData.state_province);
      submitData.append("postal_code", formData.postal_code);
      submitData.append("country", formData.country);
      const contactCountry = countries.find((c) => c.code === formData.contact_phone_country_code);
      const adminCountry = countries.find((c) => c.code === formData.admin_phone_country_code);
      submitData.append("contact_phone_country", contactCountry?.dialCode || "+1");
      submitData.append("contact_phone", formData.contact_phone || formData.admin_phone);
      submitData.append("contact_email", formData.contact_email || formData.admin_email);
      submitData.append("admin_full_name", formData.admin_full_name);
      submitData.append("admin_username", formData.admin_username);
      submitData.append("admin_email", formData.admin_email);
      submitData.append("admin_phone_country", adminCountry?.dialCode || "+1");
      submitData.append("admin_phone", formData.admin_phone);
      submitData.append("admin_password", formData.admin_password);
      const response = await organizationService.registerOrganization(submitData);
      navigate("/login?message=registration_success");
    } catch (error2) {
      console.error("Organization registration error:", error2);
      if (error2.response?.data?.detail) {
        setSubmitError(error2.response.data.detail);
      } else if (error2.response?.data?.message) {
        setSubmitError(error2.response.data.message);
      } else {
        setSubmitError("Failed to register organization. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.registrationContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Link, { to: "/", className: styles.backLink, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-arrow-left" }),
      "Back to Homepage"
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: styles.registrationCard, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.registrationHeader, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", className: styles.title, children: "Register Your Organization" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.subtitle, children: "Join the Course Creator Platform and start delivering world-class training programs" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.professionalBadge, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-check-circle" }),
          "Professional Training Platform"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, className: styles.form, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formSection, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.sectionTitle, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-building" }),
            "Organization Details"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGrid, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Organization Name",
                name: "name",
                value: formData.name,
                onChange: handleInputChange,
                error: errors.name,
                required: true,
                placeholder: "Enter your organization name"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Organization Slug",
                name: "slug",
                value: formData.slug,
                onChange: handleInputChange,
                error: errors.slug,
                required: true,
                placeholder: "organization-slug",
                helpText: "Used in URLs. Auto-generated from name."
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGridSingle, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Textarea,
              {
                label: "Organization Description",
                name: "description",
                value: formData.description,
                onChange: handleInputChange,
                error: errors.description,
                placeholder: "Brief description of your organization",
                helpText: "Optional: Tell us about your organization"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Organization Domain",
                name: "domain",
                value: formData.domain,
                onChange: handleInputChange,
                error: errors.domain,
                required: true,
                placeholder: "example.com",
                helpText: "Your organization's website domain"
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles.formLabel, children: [
              "Organization Logo",
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.optional, children: "(Optional)" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.logoUploadArea, onClick: () => logoInputRef.current?.click(), children: formData.logoPreviewUrl ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.logoPreview, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("img", { src: formData.logoPreviewUrl, alt: "Logo preview", className: styles.previewImage }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                Button,
                {
                  type: "button",
                  onClick: (e) => {
                    e.stopPropagation();
                    handleRemoveLogo();
                  },
                  variant: "danger",
                  size: "small",
                  className: styles.removeLogo,
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-times" }),
                    "Remove"
                  ]
                }
              )
            ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.uploadPlaceholder, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-cloud-upload-alt fa-3x" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Click to upload logo, drag and drop, or paste from clipboard" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("small", { children: "PNG, JPG, GIF up to 5MB • Ctrl+V to paste image" })
            ] }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                ref: logoInputRef,
                type: "file",
                accept: "image/*",
                onChange: handleLogoChange,
                className: styles.hiddenFileInput
              }
            ),
            errors.logo && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.error, children: errors.logo })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formSection, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.sectionTitle, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-map-marker-alt" }),
            "Organization Address"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.formGridSingle, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
            Input,
            {
              label: "Street Address",
              name: "street_address",
              value: formData.street_address,
              onChange: handleInputChange,
              error: errors.street_address,
              placeholder: "Street address"
            }
          ) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGrid, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "City",
                name: "city",
                value: formData.city,
                onChange: handleInputChange,
                error: errors.city,
                placeholder: "City"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "State/Province",
                name: "state_province",
                value: formData.state_province,
                onChange: handleInputChange,
                error: errors.state_province,
                placeholder: "State or Province"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Postal Code",
                name: "postal_code",
                value: formData.postal_code,
                onChange: handleInputChange,
                error: errors.postal_code,
                placeholder: "Postal code"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Select,
              {
                label: "Country",
                name: "country",
                value: formData.country,
                onChange: handleSelectChange("country"),
                error: errors.country,
                required: true,
                searchable: true,
                options: countries.map((c) => ({
                  value: c.code,
                  label: `${c.flag} ${c.name}`
                }))
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formSection, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.sectionTitle, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-phone" }),
            "Organization Contact Information"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "These fields will default to the administrator's information if left empty." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGrid, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              PhoneInput,
              {
                label: "Organization Phone Number",
                countryCode: formData.contact_phone_country_code,
                value: formData.contact_phone,
                onChange: handleContactPhoneChange,
                onCountryChange: handleContactPhoneCountryChange,
                error: errors.contact_phone,
                placeholder: "Phone number (defaults to admin)",
                helperText: "Leave empty to use admin's phone number"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Organization Email",
                name: "contact_email",
                value: formData.contact_email,
                onChange: handleInputChange,
                error: errors.contact_email,
                placeholder: "contact@example.com (defaults to admin)",
                type: "email",
                helperText: "Leave empty to use admin's email"
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formSection, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.sectionTitle, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-user-shield" }),
            "Administrator Account"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.sectionDescription, children: "Create the primary administrator account for your organization. This account will have full access to manage users, courses, and settings." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formGrid, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Full Name",
                name: "admin_full_name",
                value: formData.admin_full_name,
                onChange: handleInputChange,
                error: errors.admin_full_name,
                required: true,
                placeholder: "John Doe"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Username",
                name: "admin_username",
                value: formData.admin_username,
                onChange: handleInputChange,
                error: errors.admin_username,
                required: true,
                placeholder: "admin_username"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Email",
                name: "admin_email",
                value: formData.admin_email,
                onChange: handleInputChange,
                error: errors.admin_email,
                required: true,
                placeholder: "admin@example.com",
                type: "email"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              PhoneInput,
              {
                label: "Phone Number",
                countryCode: formData.admin_phone_country_code,
                value: formData.admin_phone,
                onChange: handleAdminPhoneChange,
                onCountryChange: handleAdminPhoneCountryChange,
                error: errors.admin_phone,
                required: true,
                placeholder: "Phone number",
                name: "admin_phone"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Password",
                name: "admin_password",
                value: formData.admin_password,
                onChange: handleInputChange,
                error: errors.admin_password,
                required: true,
                placeholder: "Create a strong password",
                type: "password",
                showPasswordToggle: true,
                helpText: "Min 8 chars, uppercase, lowercase, and number"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                label: "Confirm Password",
                name: "admin_password_confirm",
                value: formData.admin_password_confirm,
                onChange: handleInputChange,
                error: errors.admin_password_confirm,
                required: true,
                placeholder: "Confirm your password",
                type: "password",
                showPasswordToggle: true
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.formSection, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.sectionTitle, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-file-contract" }),
            "Terms & Conditions"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.checkboxGroup, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles.checkboxLabel, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  name: "terms_accepted",
                  checked: formData.terms_accepted,
                  onChange: handleInputChange,
                  className: styles.checkbox
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "I accept the ",
                /* @__PURE__ */ jsxRuntimeExports.jsx("a", { href: "/terms", target: "_blank", rel: "noopener noreferrer", children: "Terms of Service" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.required, children: "*" })
              ] })
            ] }),
            errors.terms_accepted && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.error, children: errors.terms_accepted }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: styles.checkboxLabel, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  type: "checkbox",
                  name: "privacy_accepted",
                  checked: formData.privacy_accepted,
                  onChange: handleInputChange,
                  className: styles.checkbox
                }
              ),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "I accept the ",
                /* @__PURE__ */ jsxRuntimeExports.jsx("a", { href: "/privacy", target: "_blank", rel: "noopener noreferrer", children: "Privacy Policy" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles.required, children: "*" })
              ] })
            ] }),
            errors.privacy_accepted && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.error, children: errors.privacy_accepted })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.submitSection, children: [
          submitError2 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.submitError, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-exclamation-circle" }),
            submitError2
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              type: "submit",
              variant: "primary",
              size: "large",
              disabled: isSubmitting,
              className: styles.submitButton,
              children: isSubmitting ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
                "Creating Organization..."
              ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-check-circle" }),
                "Complete Registration"
              ] })
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: styles.loginLink, children: [
            "Already have an account? ",
            /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/login", children: "Sign in here" })
          ] })
        ] })
      ] })
    ] })
  ] });
};
export {
  OrganizationRegistration
};
//# sourceMappingURL=OrganizationRegistration-d_It6LRN.js.map
