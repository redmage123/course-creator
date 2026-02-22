import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { u as useNavigate, c as useLocation, a as reactExports, L as Link } from "./react-vendor-cEae-lCc.js";
import { u as useAuth, B as Button } from "./index-C0G9mbri.js";
const navbar = "_navbar_16mhz_20";
const styles$1 = {
  navbar,
  "navbar-container": "_navbar-container_16mhz_35",
  "navbar-logo": "_navbar-logo_16mhz_50",
  "logo-text": "_logo-text_16mhz_64",
  "navbar-links": "_navbar-links_16mhz_76",
  "nav-link": "_nav-link_16mhz_85",
  "nav-link-active": "_nav-link-active_16mhz_112",
  "navbar-right": "_navbar-right_16mhz_139",
  "help-link": "_help-link_16mhz_147",
  "icon-button": "_icon-button_16mhz_173",
  "user-menu-container": "_user-menu-container_16mhz_203",
  "user-menu-trigger": "_user-menu-trigger_16mhz_207",
  "user-avatar": "_user-avatar_16mhz_234",
  "user-avatar-placeholder": "_user-avatar-placeholder_16mhz_241",
  "user-name": "_user-name_16mhz_261",
  "dropdown-icon": "_dropdown-icon_16mhz_271",
  "user-dropdown": "_user-dropdown_16mhz_281",
  "user-info": "_user-info_16mhz_314",
  "user-info-name": "_user-info-name_16mhz_318",
  "user-info-email": "_user-info-email_16mhz_325",
  "user-info-role": "_user-info-role_16mhz_332",
  "dropdown-divider": "_dropdown-divider_16mhz_340",
  "dropdown-item": "_dropdown-item_16mhz_346",
  "dropdown-item-button": "_dropdown-item-button_16mhz_366",
  "mobile-menu-toggle": "_mobile-menu-toggle_16mhz_395",
  "mobile-menu": "_mobile-menu_16mhz_395",
  "mobile-menu-link": "_mobile-menu-link_16mhz_436",
  "mobile-menu-link-active": "_mobile-menu-link-active_16mhz_459"
};
const Navbar = ({
  logo = "Course Creator",
  className
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isMenuOpen, setIsMenuOpen] = reactExports.useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = reactExports.useState(false);
  const userMenuRef = reactExports.useRef(null);
  const userMenuTriggerRef = reactExports.useRef(null);
  reactExports.useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        if (isUserMenuOpen) {
          setIsUserMenuOpen(false);
          userMenuTriggerRef.current?.focus();
        }
        if (isMenuOpen) {
          setIsMenuOpen(false);
        }
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isUserMenuOpen, isMenuOpen]);
  reactExports.useEffect(() => {
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    };
    if (isUserMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [isUserMenuOpen]);
  const isLinkActive = reactExports.useMemo(() => {
    return (linkPath) => {
      const currentPath = location.pathname;
      if (currentPath === linkPath) return true;
      if (linkPath === "/dashboard") {
        return currentPath.startsWith("/dashboard");
      }
      if (linkPath !== "/" && currentPath.startsWith(linkPath + "/")) {
        return true;
      }
      return false;
    };
  }, [location.pathname]);
  const handleLogout = () => {
    logout();
    navigate("/login");
  };
  const getNavLinks = () => {
    if (!isAuthenticated || !user) return [];
    const commonLinks = [
      { to: "/dashboard", label: "Dashboard" }
    ];
    switch (user.role) {
      case "site_admin":
        return [
          ...commonLinks,
          { to: "/admin/organizations", label: "Organizations" },
          { to: "/admin/users", label: "Users" },
          { to: "/admin/analytics", label: "Analytics" }
        ];
      case "organization_admin":
        return [
          ...commonLinks,
          { to: "/organization/members", label: "Members" },
          { to: "/organization/courses", label: "Courses" },
          { to: "/organization/analytics", label: "Analytics" }
        ];
      case "instructor":
        return [
          ...commonLinks,
          { to: "/courses", label: "My Courses" },
          { to: "/students", label: "Students" },
          { to: "/analytics", label: "Analytics" }
        ];
      case "student":
        return [
          ...commonLinks,
          { to: "/courses/my-courses", label: "My Courses" },
          { to: "/labs", label: "Labs" },
          { to: "/progress", label: "Progress" }
        ];
      default:
        return commonLinks;
    }
  };
  const navLinks = getNavLinks();
  const getUserDisplayName = () => {
    if (!user) return "";
    if (user.firstName && user.lastName) {
      return `${user.firstName} ${user.lastName}`;
    }
    return user.username;
  };
  const getUserInitials = () => {
    if (!user) return "?";
    if (user.firstName && user.lastName) {
      return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
    }
    return user.username[0].toUpperCase();
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("nav", { className: `${styles$1.navbar} ${className || ""}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["navbar-container"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/", className: styles$1["navbar-logo"], children: typeof logo === "string" ? /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["logo-text"], children: logo }) : logo }),
      isAuthenticated && navLinks.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["navbar-links"], children: navLinks.map((link) => {
        const active = isLinkActive(link.to);
        return /* @__PURE__ */ jsxRuntimeExports.jsx(
          Link,
          {
            to: link.to,
            className: `${styles$1["nav-link"]} ${active ? styles$1["nav-link-active"] : ""}`,
            "aria-current": active ? "page" : void 0,
            children: link.label
          },
          link.to
        );
      }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["navbar-right"], children: isAuthenticated && user ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Link,
          {
            to: "/bugs/submit",
            className: styles$1["icon-button"],
            title: "Report a Bug",
            "aria-label": "Report a bug",
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "20", height: "20", viewBox: "0 0 24 24", fill: "none", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
              "path",
              {
                d: "M8 2v4M16 2v4M12 14v4M12 14l-3 3m3-3l3 3M9 10h.01M15 10h.01M3 8h18v13a2 2 0 01-2 2H5a2 2 0 01-2-2V8zM5 8V6a2 2 0 012-2h10a2 2 0 012 2v2",
                stroke: "currentColor",
                strokeWidth: "2",
                strokeLinecap: "round",
                strokeLinejoin: "round"
              }
            ) })
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { ref: userMenuRef, className: styles$1["user-menu-container"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "button",
            {
              ref: userMenuTriggerRef,
              className: styles$1["user-menu-trigger"],
              onClick: () => setIsUserMenuOpen(!isUserMenuOpen),
              "aria-label": "User menu",
              "aria-expanded": isUserMenuOpen,
              "aria-haspopup": "true",
              children: [
                user.avatar ? /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "img",
                  {
                    src: user.avatar,
                    alt: getUserDisplayName(),
                    className: styles$1["user-avatar"]
                  }
                ) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["user-avatar-placeholder"], children: getUserInitials() }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["user-name"], children: getUserDisplayName() }),
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "svg",
                  {
                    className: styles$1["dropdown-icon"],
                    width: "12",
                    height: "12",
                    viewBox: "0 0 12 12",
                    fill: "none",
                    children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                      "path",
                      {
                        d: "M2 4L6 8L10 4",
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
          isUserMenuOpen && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["user-dropdown"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["user-info"], children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["user-info-name"], children: getUserDisplayName() }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["user-info-email"], children: user.email }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["user-info-role"], children: user.role.replace("_", " ").toUpperCase() })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["dropdown-divider"] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Link,
              {
                to: "/settings",
                className: styles$1["dropdown-item"],
                onClick: () => setIsUserMenuOpen(false),
                children: "Settings"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Link,
              {
                to: "/profile",
                className: styles$1["dropdown-item"],
                onClick: () => setIsUserMenuOpen(false),
                children: "Profile"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              Link,
              {
                to: "/bugs/submit",
                className: styles$1["dropdown-item"],
                onClick: () => setIsUserMenuOpen(false),
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "svg",
                    {
                      width: "16",
                      height: "16",
                      viewBox: "0 0 24 24",
                      fill: "none",
                      style: { marginRight: "8px", verticalAlign: "middle" },
                      children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                        "path",
                        {
                          d: "M8 2v4M16 2v4M12 14v4M12 14l-3 3m3-3l3 3M9 10h.01M15 10h.01M3 8h18v13a2 2 0 01-2 2H5a2 2 0 01-2-2V8zM5 8V6a2 2 0 012-2h10a2 2 0 012 2v2",
                          stroke: "currentColor",
                          strokeWidth: "2",
                          strokeLinecap: "round",
                          strokeLinejoin: "round"
                        }
                      )
                    }
                  ),
                  "Report Bug"
                ]
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "a",
              {
                href: "/docs/USER_GUIDE.pdf",
                download: "Course_Creator_User_Guide.pdf",
                className: styles$1["dropdown-item"],
                onClick: () => setIsUserMenuOpen(false),
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsxs(
                    "svg",
                    {
                      width: "16",
                      height: "16",
                      viewBox: "0 0 24 24",
                      fill: "none",
                      style: { marginRight: "8px", verticalAlign: "middle" },
                      children: [
                        /* @__PURE__ */ jsxRuntimeExports.jsx(
                          "path",
                          {
                            d: "M4 19.5A2.5 2.5 0 0 1 6.5 17H20",
                            stroke: "currentColor",
                            strokeWidth: "2",
                            strokeLinecap: "round",
                            strokeLinejoin: "round"
                          }
                        ),
                        /* @__PURE__ */ jsxRuntimeExports.jsx(
                          "path",
                          {
                            d: "M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z",
                            stroke: "currentColor",
                            strokeWidth: "2",
                            strokeLinecap: "round",
                            strokeLinejoin: "round"
                          }
                        )
                      ]
                    }
                  ),
                  "User Guide (PDF)"
                ]
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["dropdown-divider"] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                className: styles$1["dropdown-item-button"],
                onClick: handleLogout,
                children: "Logout"
              }
            )
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: styles$1["mobile-menu-toggle"],
            onClick: () => setIsMenuOpen(!isMenuOpen),
            "aria-label": "Toggle mobile menu",
            "aria-expanded": isMenuOpen,
            children: /* @__PURE__ */ jsxRuntimeExports.jsx("svg", { width: "24", height: "24", viewBox: "0 0 24 24", fill: "none", children: isMenuOpen ? /* @__PURE__ */ jsxRuntimeExports.jsx(
              "path",
              {
                d: "M6 18L18 6M6 6L18 18",
                stroke: "currentColor",
                strokeWidth: "2",
                strokeLinecap: "round"
              }
            ) : /* @__PURE__ */ jsxRuntimeExports.jsx(
              "path",
              {
                d: "M4 6H20M4 12H20M4 18H20",
                stroke: "currentColor",
                strokeWidth: "2",
                strokeLinecap: "round"
              }
            ) })
          }
        )
      ] }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "a",
          {
            href: "/docs/USER_GUIDE.pdf",
            download: "Course_Creator_User_Guide.pdf",
            className: styles$1["help-link"],
            title: "Download User Guide",
            children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "svg",
              {
                width: "20",
                height: "20",
                viewBox: "0 0 24 24",
                fill: "none",
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "path",
                    {
                      d: "M4 19.5A2.5 2.5 0 0 1 6.5 17H20",
                      stroke: "currentColor",
                      strokeWidth: "2",
                      strokeLinecap: "round",
                      strokeLinejoin: "round"
                    }
                  ),
                  /* @__PURE__ */ jsxRuntimeExports.jsx(
                    "path",
                    {
                      d: "M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z",
                      stroke: "currentColor",
                      strokeWidth: "2",
                      strokeLinecap: "round",
                      strokeLinejoin: "round"
                    }
                  )
                ]
              }
            )
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/login", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "ghost", size: "medium", children: "Login" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/register", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "medium", children: "Sign Up" }) })
      ] }) })
    ] }),
    isAuthenticated && isMenuOpen && navLinks.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["mobile-menu"], children: navLinks.map((link) => {
      const active = isLinkActive(link.to);
      return /* @__PURE__ */ jsxRuntimeExports.jsx(
        Link,
        {
          to: link.to,
          className: `${styles$1["mobile-menu-link"]} ${active ? styles$1["mobile-menu-link-active"] : ""}`,
          onClick: () => setIsMenuOpen(false),
          "aria-current": active ? "page" : void 0,
          children: link.label
        },
        link.to
      );
    }) })
  ] });
};
const styles = {
  "dashboard-layout": "_dashboard-layout_9ti9k_19",
  "dashboard-container": "_dashboard-container_9ti9k_29",
  "dashboard-main": "_dashboard-main_9ti9k_35",
  "dashboard-with-sidebar": "_dashboard-with-sidebar_9ti9k_46",
  "dashboard-sidebar": "_dashboard-sidebar_9ti9k_53",
  "dashboard-content": "_dashboard-content_9ti9k_70"
};
const DashboardLayout = ({
  children,
  sidebar,
  maxWidth = "1440px",
  logo,
  className
}) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `${styles["dashboard-layout"]} ${className || ""}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Navbar, { logo }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["dashboard-container"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      "main",
      {
        className: styles["dashboard-main"],
        style: { maxWidth },
        children: sidebar ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["dashboard-with-sidebar"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("aside", { className: styles["dashboard-sidebar"], children: sidebar }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["dashboard-content"], children })
        ] }) : (
          // Content without sidebar
          children
        )
      }
    ) })
  ] });
};
export {
  DashboardLayout as D
};
//# sourceMappingURL=DashboardLayout-AOzVVxgF.js.map
