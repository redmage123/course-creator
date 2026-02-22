import { u as useQuery, j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { u as useAuth, H as Heading, S as Spinner, C as Card, B as Button, a as SEO } from "./index-C0G9mbri.js";
import { L as Link } from "./react-vendor-cEae-lCc.js";
import "./state-vendor-B_izx0oA.js";
const certificatesContainer = "_certificatesContainer_6wjxf_5";
const header = "_header_6wjxf_11";
const pageTitle = "_pageTitle_6wjxf_18";
const backLink = "_backLink_6wjxf_24";
const loadingState = "_loadingState_6wjxf_38";
const errorState = "_errorState_6wjxf_48";
const noCertificates = "_noCertificates_6wjxf_63";
const noCertificatesIcon = "_noCertificatesIcon_6wjxf_68";
const noCertificatesTitle = "_noCertificatesTitle_6wjxf_74";
const noCertificatesMessage = "_noCertificatesMessage_6wjxf_81";
const certificatesGrid = "_certificatesGrid_6wjxf_88";
const certificateCard = "_certificateCard_6wjxf_93";
const certificateHeader = "_certificateHeader_6wjxf_104";
const certificateBadge = "_certificateBadge_6wjxf_111";
const certificateInfo = "_certificateInfo_6wjxf_124";
const certificateTitle = "_certificateTitle_6wjxf_128";
const certificateDate = "_certificateDate_6wjxf_135";
const certificateGrade = "_certificateGrade_6wjxf_136";
const certificateId = "_certificateId_6wjxf_150";
const certificateActions = "_certificateActions_6wjxf_161";
const downloadBtn = "_downloadBtn_6wjxf_167";
const shareBtn = "_shareBtn_6wjxf_168";
const completionBadge = "_completionBadge_6wjxf_173";
const styles = {
  certificatesContainer,
  header,
  pageTitle,
  backLink,
  loadingState,
  errorState,
  noCertificates,
  noCertificatesIcon,
  noCertificatesTitle,
  noCertificatesMessage,
  certificatesGrid,
  certificateCard,
  certificateHeader,
  certificateBadge,
  certificateInfo,
  certificateTitle,
  certificateDate,
  certificateGrade,
  certificateId,
  certificateActions,
  downloadBtn,
  shareBtn,
  completionBadge
};
const StudentCertificates = () => {
  const { user } = useAuth();
  const {
    data: certificates = [],
    isLoading,
    error
  } = useQuery({
    queryKey: ["certificates", user?.id],
    queryFn: async () => {
      return [];
    },
    enabled: !!user?.id
  });
  const handleDownload = async (certificate) => {
    if (certificate.pdf_url) {
      window.open(certificate.pdf_url, "_blank");
    } else {
      try {
        const response = await fetch(`/api/v1/certificates/${certificate.id}/download`, {
          headers: {
            "Authorization": `Bearer ${localStorage.getItem("access_token")}`
          }
        });
        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `certificate-${certificate.certificate_id}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }
      } catch (error2) {
        console.error("Failed to download certificate:", error2);
        alert("Failed to download certificate. Please try again.");
      }
    }
  };
  const handleShare = (certificate) => {
    const shareUrl = certificate.share_url || `${window.location.origin}/certificates/verify/${certificate.certificate_id}`;
    if (navigator.share) {
      navigator.share({
        title: `Certificate: ${certificate.course_name}`,
        text: `I earned a certificate in ${certificate.course_name}!`,
        url: shareUrl
      }).catch((error2) => console.log("Error sharing:", error2));
    } else {
      navigator.clipboard.writeText(shareUrl).then(() => {
        alert("Certificate link copied to clipboard!");
      });
    }
  };
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };
  const seoElement = /* @__PURE__ */ jsxRuntimeExports.jsx(
    SEO,
    {
      title: "My Certificates",
      description: "View and download your earned course completion certificates",
      keywords: "certificates, achievements, course completion, credentials"
    }
  );
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { seo: seoElement, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.certificatesContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.header, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: 1, className: styles.pageTitle, children: "My Certificates" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Link, { to: "/dashboard/student", className: styles.backLink, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-arrow-left" }),
        "Back to Dashboard"
      ] })
    ] }),
    isLoading ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.loadingState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading your certificates..." })
    ] }) : error ? /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: styles.errorState, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-exclamation-circle" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Failed to load certificates. Please refresh the page." })
    ] }) : certificates.length === 0 ? (
      // Empty State
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: styles.noCertificates, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.noCertificatesIcon, children: /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-certificate" }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: 2, className: styles.noCertificatesTitle, children: "No Certificates Yet" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.noCertificatesMessage, children: "Complete your courses to earn certificates and showcase your achievements!" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/courses/my-courses", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { variant: "primary", size: "large", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-book" }),
          "Browse Your Courses"
        ] }) })
      ] })
    ) : (
      // Certificates Grid
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.certificatesGrid, children: certificates.map((certificate) => /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: styles.certificateCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.certificateHeader, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.certificateBadge, children: /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-award" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.certificateInfo, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: 3, className: styles.certificateTitle, children: certificate.course_name }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.certificateDate, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-calendar" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "Earned on ",
                formatDate(certificate.earned_date)
              ] })
            ] }),
            certificate.grade && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.certificateGrade, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-star" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                "Final Grade: ",
                certificate.grade
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.certificateId, children: [
              "Certificate ID: ",
              certificate.certificate_id
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.certificateActions, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              Button,
              {
                onClick: () => handleDownload(certificate),
                variant: "secondary",
                size: "small",
                className: styles.downloadBtn,
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-download" }),
                  "Download"
                ]
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              Button,
              {
                onClick: () => handleShare(certificate),
                variant: "secondary",
                size: "small",
                className: styles.shareBtn,
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-share" }),
                  "Share"
                ]
              }
            )
          ] })
        ] }),
        certificate.completion_percentage === 100 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.completionBadge, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("i", { className: "fas fa-check-circle" }),
          "100% Complete"
        ] })
      ] }, certificate.id)) })
    )
  ] }) });
};
export {
  StudentCertificates
};
//# sourceMappingURL=StudentCertificates-BvmBScRq.js.map
