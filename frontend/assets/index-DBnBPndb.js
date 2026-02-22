import { j as jsxRuntimeExports, c as useQueryClient, u as useQuery, d as useMutation } from "./query-vendor-BigVEegc.js";
import { L as Link, u as useNavigate, a as reactExports, i as useParams } from "./react-vendor-cEae-lCc.js";
import { D as DashboardLayout } from "./DashboardLayout-AOzVVxgF.js";
import { C as Card, B as Button, u as useAuth, H as Heading, S as Spinner } from "./index-C0G9mbri.js";
import { t as trainingProgramService } from "./trainingProgramService-B-up7yl_.js";
import "./state-vendor-B_izx0oA.js";
const tag$2 = "_tag_kgg0v_128";
const styles$4 = {
  "program-card": "_program-card_kgg0v_8",
  "card-header": "_card-header_kgg0v_21",
  "title-section": "_title-section_kgg0v_25",
  "program-title": "_program-title_kgg0v_31",
  "status-badges": "_status-badges_kgg0v_44",
  "status-badge": "_status-badge_kgg0v_44",
  "status-published": "_status-published_kgg0v_59",
  "status-draft": "_status-draft_kgg0v_64",
  "category-badge": "_category-badge_kgg0v_69",
  "card-body": "_card-body_kgg0v_79",
  "program-description": "_program-description_kgg0v_86",
  "metadata-grid": "_metadata-grid_kgg0v_98",
  "metadata-item": "_metadata-item_kgg0v_107",
  "metadata-label": "_metadata-label_kgg0v_113",
  "metadata-value": "_metadata-value_kgg0v_121",
  "tags-section": "_tags-section_kgg0v_128",
  tag: tag$2,
  "tag-more": "_tag-more_kgg0v_142",
  "card-footer": "_card-footer_kgg0v_152",
  "action-buttons": "_action-buttons_kgg0v_158"
};
const TrainingProgramCard = ({
  program,
  viewerRole,
  onEdit,
  onDelete,
  onTogglePublish
}) => {
  const formatDuration = () => {
    if (!program.estimated_duration) return "Duration not specified";
    const unit = program.duration_unit || "hours";
    return `${program.estimated_duration} ${unit}`;
  };
  const formatDifficulty = (level) => {
    return level.charAt(0).toUpperCase() + level.slice(1);
  };
  const getPublishStatusClass = () => {
    return program.published ? styles$4["status-published"] : styles$4["status-draft"];
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "medium", className: styles$4["program-card"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4["card-header"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["title-section"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Link,
        {
          to: `/courses/${program.id}`,
          className: styles$4["program-title"],
          children: program.title
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["status-badges"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: `${styles$4["status-badge"]} ${getPublishStatusClass()}`, children: program.published ? "Published" : "Draft" }),
        program.category && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["category-badge"], children: program.category })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["card-body"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$4["program-description"], children: program.description || "No description available" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["metadata-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["metadata-label"], children: "Difficulty:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["metadata-value"], children: formatDifficulty(program.difficulty_level) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["metadata-label"], children: "Duration:" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["metadata-value"], children: formatDuration() })
        ] }),
        viewerRole !== "student" && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["metadata-item"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["metadata-label"], children: "Enrolled:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4["metadata-value"], children: [
              program.enrolled_students || 0,
              " students"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["metadata-item"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["metadata-label"], children: "Completion:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["metadata-value"], children: program.completion_rate ? `${Math.round(program.completion_rate)}%` : "N/A" })
          ] })
        ] })
      ] }),
      program.tags && program.tags.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["tags-section"], children: [
        program.tags.slice(0, 5).map((tag2, index) => /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$4["tag"], children: tag2 }, index)),
        program.tags.length > 5 && /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$4["tag-more"], children: [
          "+",
          program.tags.length - 5,
          " more"
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["card-footer"], children: [
      viewerRole === "student" && /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/courses/${program.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "small", children: "View Course" }) }),
      (viewerRole === "instructor" || viewerRole === "org_admin") && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$4["action-buttons"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/courses/${program.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", size: "small", children: "View Details" }) }),
        viewerRole === "instructor" && onEdit && /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "secondary",
            size: "small",
            onClick: () => onEdit(program.id),
            children: "Edit"
          }
        ),
        viewerRole === "instructor" && onTogglePublish && /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: program.published ? "secondary" : "primary",
            size: "small",
            onClick: () => onTogglePublish(program.id, program.published),
            children: program.published ? "Unpublish" : "Publish"
          }
        ),
        viewerRole === "instructor" && onDelete && !program.published && /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "danger",
            size: "small",
            onClick: () => onDelete(program.id),
            children: "Delete"
          }
        )
      ] }),
      viewerRole === "site_admin" && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$4["action-buttons"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: `/courses/${program.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "small", children: "View Details" }) }) })
    ] })
  ] });
};
const styles$3 = {
  "list-page": "_list-page_1vd0j_8",
  "page-header": "_page-header_1vd0j_15",
  "header-content": "_header-content_1vd0j_23",
  "header-description": "_header-description_1vd0j_27",
  "filters-card": "_filters-card_1vd0j_35",
  "filters-grid": "_filters-grid_1vd0j_39",
  "filter-group": "_filter-group_1vd0j_46",
  "filter-label": "_filter-label_1vd0j_52",
  "search-input": "_search-input_1vd0j_58",
  "filter-select": "_filter-select_1vd0j_59",
  "results-count": "_results-count_1vd0j_79",
  "programs-grid": "_programs-grid_1vd0j_87",
  "empty-state": "_empty-state_1vd0j_94"
};
const TrainingProgramListPage = ({
  context
}) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = reactExports.useState("");
  const [categoryFilter, setCategoryFilter] = reactExports.useState("all");
  const [difficultyFilter, setDifficultyFilter] = reactExports.useState("all");
  const [publishStatusFilter, setPublishStatusFilter] = reactExports.useState("all");
  const { data: programs, isLoading, error } = useQuery({
    queryKey: ["trainingPrograms", context, user?.id],
    queryFn: async () => {
      let response;
      if (context === "instructor") {
        response = await trainingProgramService.getInstructorPrograms(user.id);
      } else {
        response = await trainingProgramService.getOrganizationPrograms(user.organizationId);
      }
      if (Array.isArray(response)) {
        return {
          data: response,
          total: response.length,
          page: 1,
          limit: response.length,
          pages: 1
        };
      }
      return response;
    },
    enabled: !!user?.id && (context === "instructor" || !!user?.organizationId),
    staleTime: 2 * 60 * 1e3
    // Cache for 2 minutes
  });
  const togglePublishMutation = useMutation({
    mutationFn: ({ programId, shouldPublish }) => shouldPublish ? trainingProgramService.publishTrainingProgram(programId) : trainingProgramService.unpublishTrainingProgram(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trainingPrograms"] });
    }
  });
  const deleteMutation = useMutation({
    mutationFn: (programId) => trainingProgramService.deleteTrainingProgram(programId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trainingPrograms"] });
    }
  });
  const filteredPrograms = reactExports.useMemo(() => {
    if (!programs?.data) return [];
    return programs.data.filter((program) => {
      const matchesSearch = !searchQuery || program.title.toLowerCase().includes(searchQuery.toLowerCase()) || program.description?.toLowerCase().includes(searchQuery.toLowerCase()) || program.tags?.some((tag2) => tag2.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesCategory = categoryFilter === "all" || program.category === categoryFilter;
      const matchesDifficulty = difficultyFilter === "all" || program.difficulty_level === difficultyFilter;
      const matchesPublishStatus = publishStatusFilter === "all" || publishStatusFilter === "published" && program.published || publishStatusFilter === "draft" && !program.published;
      return matchesSearch && matchesCategory && matchesDifficulty && matchesPublishStatus;
    });
  }, [programs, searchQuery, categoryFilter, difficultyFilter, publishStatusFilter]);
  const availableCategories = reactExports.useMemo(() => {
    if (!programs?.data) return [];
    const categories = programs.data.map((p) => p.category).filter((c) => !!c);
    return Array.from(new Set(categories)).sort();
  }, [programs]);
  const handleEdit = (programId) => {
    const basePath = context === "instructor" ? "/instructor" : "/organization";
    navigate(`${basePath}/programs/${programId}/edit`);
  };
  const handleDelete = async (programId) => {
    if (window.confirm("Are you sure you want to delete this training program?")) {
      await deleteMutation.mutateAsync(programId);
    }
  };
  const handleTogglePublish = async (programId, currentStatus) => {
    await togglePublishMutation.mutateAsync({
      programId,
      shouldPublish: !currentStatus
    });
  };
  const getPageTitle = () => {
    return context === "instructor" ? "My Training Programs" : "Organization Training Programs";
  };
  const getCreatePath = () => {
    if (context === "instructor") {
      return "/instructor/programs/create";
    } else if (context === "organization") {
      return "/organization/programs/create";
    }
    return void 0;
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["list-page"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3["page-header"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: getPageTitle() }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) })
    ] }) });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["list-page"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3["page-header"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: getPageTitle() }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "var(--color-error)", textAlign: "center" }, children: "Unable to load training programs. Please try refreshing the page." }) })
    ] }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["list-page"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["page-header"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["header-content"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: getPageTitle() }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$3["header-description"], children: context === "instructor" ? "Manage your IT training programs, create new courses, and track student progress" : "View and manage all training programs in your organization" })
      ] }),
      getCreatePath() && /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: () => navigate(getCreatePath()), children: "Create New Program" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "medium", className: styles$3["filters-card"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["filters-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["filter-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "search", className: styles$3["filter-label"], children: "Search" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              id: "search",
              type: "text",
              placeholder: "Search by title, description, or tags...",
              value: searchQuery,
              onChange: (e) => setSearchQuery(e.target.value),
              className: styles$3["search-input"]
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["filter-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "category", className: styles$3["filter-label"], children: "Category" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              id: "category",
              value: categoryFilter,
              onChange: (e) => setCategoryFilter(e.target.value),
              className: styles$3["filter-select"],
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Categories" }),
                availableCategories.map((category) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: category, children: category }, category))
              ]
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["filter-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "difficulty", className: styles$3["filter-label"], children: "Difficulty" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              id: "difficulty",
              value: difficultyFilter,
              onChange: (e) => setDifficultyFilter(e.target.value),
              className: styles$3["filter-select"],
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Levels" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "beginner", children: "Beginner" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "intermediate", children: "Intermediate" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "advanced", children: "Advanced" })
              ]
            }
          )
        ] }),
        context === "instructor" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["filter-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "publishStatus", className: styles$3["filter-label"], children: "Status" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              id: "publishStatus",
              value: publishStatusFilter,
              onChange: (e) => setPublishStatusFilter(e.target.value),
              className: styles$3["filter-select"],
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All Status" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "published", children: "Published" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "draft", children: "Draft" })
              ]
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3["results-count"], children: [
        "Showing ",
        filteredPrograms.length,
        " of ",
        programs?.data.length || 0,
        " programs"
      ] })
    ] }),
    filteredPrograms.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", className: styles$3["empty-state"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "No Training Programs Found" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: searchQuery || categoryFilter !== "all" || difficultyFilter !== "all" ? "Try adjusting your filters to see more results." : context === "instructor" ? "Get started by creating your first training program." : "No training programs have been created yet." }),
      context === "instructor" && getCreatePath() && /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => navigate(getCreatePath()),
          style: { marginTop: "1rem" },
          children: "Create First Program"
        }
      )
    ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3["programs-grid"], children: filteredPrograms.map((program) => /* @__PURE__ */ jsxRuntimeExports.jsx(
      TrainingProgramCard,
      {
        program,
        viewerRole: context === "instructor" ? "instructor" : "org_admin",
        onEdit: handleEdit,
        onDelete: context === "instructor" ? handleDelete : void 0,
        onTogglePublish: context === "instructor" ? handleTogglePublish : void 0
      },
      program.id
    )) })
  ] }) });
};
const breadcrumb = "_breadcrumb_176j0_15";
const description$1 = "_description_176j0_72";
const tag$1 = "_tag_176j0_110";
const styles$2 = {
  "detail-page": "_detail-page_176j0_8",
  breadcrumb,
  "header-card": "_header-card_176j0_20",
  "header-content": "_header-content_176j0_24",
  "title-section": "_title-section_176j0_32",
  "status-badges": "_status-badges_176j0_36",
  "status-badge": "_status-badge_176j0_36",
  "status-published": "_status-published_176j0_52",
  "status-draft": "_status-draft_176j0_57",
  "category-badge": "_category-badge_176j0_62",
  description: description$1,
  "metadata-grid": "_metadata-grid_176j0_80",
  "metadata-item": "_metadata-item_176j0_89",
  "metadata-label": "_metadata-label_176j0_95",
  "metadata-value": "_metadata-value_176j0_103",
  "tags-section": "_tags-section_176j0_110",
  "tags-label": "_tags-label_176j0_117",
  "tags-list": "_tags-list_176j0_123",
  tag: tag$1,
  "content-card": "_content-card_176j0_138",
  "content-description": "_content-description_176j0_142",
  "content-features": "_content-features_176j0_149",
  "coming-soon": "_coming-soon_176j0_161",
  "enrollment-card": "_enrollment-card_176j0_172",
  "enrollment-description": "_enrollment-description_176j0_176",
  "enrollment-actions": "_enrollment-actions_176j0_183",
  "student-actions-card": "_student-actions-card_176j0_190",
  "action-description": "_action-description_176j0_194"
};
const TrainingProgramDetailPage = () => {
  const { courseId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const { data: program, isLoading, error } = useQuery({
    queryKey: ["trainingProgram", courseId],
    queryFn: () => trainingProgramService.getTrainingProgramById(courseId),
    enabled: !!courseId,
    staleTime: 5 * 60 * 1e3
    // Cache for 5 minutes
  });
  const formatDuration = () => {
    if (!program?.estimated_duration) return "Duration not specified";
    const unit = program.duration_unit || "hours";
    return `${program.estimated_duration} ${unit}`;
  };
  const formatDifficulty = (level) => {
    if (!level) return "Not specified";
    return level.charAt(0).toUpperCase() + level.slice(1);
  };
  const formatPrice = (price) => {
    if (price === void 0 || price === null) return "Free";
    if (price === 0) return "Free";
    return `$${price.toFixed(2)}`;
  };
  const canEdit = () => {
    return user?.role === "instructor" && program?.instructor_id === user?.id;
  };
  const handleEdit = () => {
    navigate(`/instructor/programs/${courseId}/edit`);
  };
  const handleBack = () => {
    if (user?.role === "instructor") {
      navigate("/instructor/programs");
    } else if (user?.role === "org_admin") {
      navigate("/organization/programs");
    } else if (user?.role === "student") {
      navigate("/courses/my-courses");
    } else {
      navigate(-1);
    }
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2["detail-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) }) });
  }
  if (error || !program) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2["detail-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { style: { color: "var(--color-error)", textAlign: "center" }, children: "Unable to load training program details. Please try refreshing the page." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { textAlign: "center", marginTop: "1rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", onClick: handleBack, children: "Go Back" }) })
    ] }) }) });
  }
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["detail-page"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2["breadcrumb"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "text", onClick: handleBack, children: "← Back to Programs" }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", className: styles$2["header-card"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["header-content"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["title-section"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: program.title }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["status-badges"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "span",
              {
                className: `${styles$2["status-badge"]} ${program.published ? styles$2["status-published"] : styles$2["status-draft"]}`,
                children: program.published ? "Published" : "Draft"
              }
            ),
            program.category && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["category-badge"], children: program.category })
          ] })
        ] }),
        canEdit() && /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: handleEdit, children: "Edit Program" })
      ] }),
      program.description && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2["description"], children: program.description }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["metadata-grid"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-label"], children: "Difficulty Level" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-value"], children: formatDifficulty(program.difficulty_level) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-label"], children: "Duration" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-value"], children: formatDuration() })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["metadata-item"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-label"], children: "Price" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-value"], children: formatPrice(program.price) })
        ] }),
        (user?.role === "instructor" || user?.role === "org_admin") && /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["metadata-item"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-label"], children: "Enrolled Students" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-value"], children: program.enrolled_students || 0 })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["metadata-item"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-label"], children: "Completion Rate" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["metadata-value"], children: program.completion_rate ? `${Math.round(program.completion_rate)}%` : "N/A" })
          ] })
        ] })
      ] }),
      program.tags && program.tags.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["tags-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["tags-label"], children: "Tags:" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$2["tags-list"], children: program.tags.map((tag2, index) => /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2["tag"], children: tag2 }, index)) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", className: styles$2["content-card"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Course Content" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2["content-description"], children: "Detailed course syllabus, modules, and learning materials will be displayed here. This section will include:" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: styles$2["content-features"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Course modules and lessons" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Video lectures and presentations" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Lab exercises and assignments" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Quizzes and assessments" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Downloadable resources" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2["coming-soon"], children: "📋 Detailed syllabus view coming in next phase" })
    ] }),
    (user?.role === "instructor" || user?.role === "org_admin") && program.published && /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", className: styles$2["enrollment-card"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Student Enrollment" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2["enrollment-description"], children: "Manage student enrollments, track progress, and view analytics for this program." }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$2["enrollment-actions"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "View Enrolled Students" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Enroll New Students" })
      ] })
    ] }),
    user?.role === "student" && program.published && /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", className: styles$2["student-actions-card"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h2", gutterBottom: true, children: "Get Started" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$2["action-description"], children: "Ready to begin your learning journey with this training program?" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", size: "large", children: "Start Learning" })
    ] })
  ] }) });
};
const required = "_required_fd3rg_67";
const tag = "_tag_fd3rg_131";
const styles$1 = {
  "form-page": "_form-page_fd3rg_8",
  "page-header": "_page-header_fd3rg_15",
  "header-description": "_header-description_fd3rg_19",
  "program-form": "_program-form_fd3rg_27",
  "form-section": "_form-section_fd3rg_34",
  "form-group": "_form-group_fd3rg_48",
  "form-row": "_form-row_fd3rg_54",
  "form-label": "_form-label_fd3rg_61",
  required,
  "form-input": "_form-input_fd3rg_72",
  "form-textarea": "_form-textarea_fd3rg_73",
  "form-select": "_form-select_fd3rg_74",
  "input-error": "_input-error_fd3rg_103",
  "char-count": "_char-count_fd3rg_114",
  "error-message": "_error-message_fd3rg_124",
  "tags-input-group": "_tags-input-group_fd3rg_131",
  "tags-display": "_tags-display_fd3rg_141",
  tag,
  "tag-remove": "_tag-remove_fd3rg_160",
  "form-actions": "_form-actions_fd3rg_182",
  "submission-error": "_submission-error_fd3rg_191"
};
const CreateEditTrainingProgramPage = () => {
  const { programId } = useParams();
  const { organizationId } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditMode = !!programId;
  const isOrgAdminContext = window.location.pathname.startsWith("/organization");
  const [title, setTitle] = reactExports.useState("");
  const [description2, setDescription] = reactExports.useState("");
  const [category, setCategory] = reactExports.useState("");
  const [difficultyLevel, setDifficultyLevel] = reactExports.useState("beginner");
  const [estimatedDuration, setEstimatedDuration] = reactExports.useState(0);
  const [durationUnit, setDurationUnit] = reactExports.useState("hours");
  const [tags, setTags] = reactExports.useState([]);
  const [newTag, setNewTag] = reactExports.useState("");
  const [errors, setErrors] = reactExports.useState({});
  const { data: existingProgram, isLoading: loadingProgram } = useQuery({
    queryKey: ["trainingProgram", programId],
    queryFn: () => trainingProgramService.getTrainingProgramById(programId),
    enabled: isEditMode
  });
  reactExports.useEffect(() => {
    if (existingProgram) {
      setTitle(existingProgram.title);
      setDescription(existingProgram.description || "");
      setCategory(existingProgram.category || "");
      setDifficultyLevel(existingProgram.difficulty_level);
      setEstimatedDuration(existingProgram.estimated_duration || 0);
      setDurationUnit(existingProgram.duration_unit);
      setTags(existingProgram.tags || []);
    }
  }, [existingProgram]);
  const getRedirectPath = () => {
    return isOrgAdminContext ? "/organization/programs" : "/instructor/programs";
  };
  const createMutation = useMutation({
    mutationFn: (data) => trainingProgramService.createTrainingProgram(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trainingPrograms"] });
      navigate(getRedirectPath());
    }
  });
  const updateMutation = useMutation({
    mutationFn: (data) => trainingProgramService.updateTrainingProgram(programId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trainingPrograms"] });
      queryClient.invalidateQueries({ queryKey: ["trainingProgram", programId] });
      navigate(getRedirectPath());
    }
  });
  const validateForm = () => {
    const newErrors = {};
    if (!title.trim()) {
      newErrors.title = "Program title is required";
    }
    if (title.length > 200) {
      newErrors.title = "Title must be less than 200 characters";
    }
    if (description2.length > 2e3) {
      newErrors.description = "Description must be less than 2000 characters";
    }
    if (estimatedDuration && estimatedDuration <= 0) {
      newErrors.estimatedDuration = "Duration must be greater than 0";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }
    const formData = {
      title: title.trim(),
      description: description2.trim() || "",
      category: category.trim() || void 0,
      difficulty_level: difficultyLevel,
      estimated_duration: estimatedDuration || void 0,
      duration_unit: durationUnit,
      tags,
      organization_id: organizationId
      // Note: instructor_id will be set automatically by the backend based on the authenticated user
    };
    try {
      if (isEditMode) {
        await updateMutation.mutateAsync(formData);
      } else {
        await createMutation.mutateAsync(formData);
      }
    } catch (error) {
      console.error("Failed to save program:", error);
    }
  };
  const handleAddTag = () => {
    const trimmedTag = newTag.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag]);
      setNewTag("");
    }
  };
  const handleRemoveTag = (tagToRemove) => {
    setTags(tags.filter((tag2) => tag2 !== tagToRemove));
  };
  const handleCancel = () => {
    navigate(getRedirectPath());
  };
  if (isEditMode && loadingProgram) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["form-page"], children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { style: { display: "flex", justifyContent: "center", padding: "4rem" }, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "large" }) }) }) });
  }
  const isSaving = createMutation.isPending || updateMutation.isPending;
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-page"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["page-header"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: isEditMode ? "Edit Training Program" : "Create New Training Program" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1["header-description"], children: isEditMode ? "Update program details and save changes" : "Fill in the details below to create a new training program. The program will be saved as a draft." })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "large", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("form", { onSubmit: handleSubmit, className: styles$1["program-form"], noValidate: true, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "Basic Information" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "title", className: styles$1["form-label"], children: [
            "Program Title ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["required"], children: "*" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              id: "title",
              type: "text",
              value: title,
              onChange: (e) => setTitle(e.target.value),
              className: `${styles$1["form-input"]} ${errors.title ? styles$1["input-error"] : ""}`,
              placeholder: "e.g., Advanced Machine Learning for Data Scientists",
              required: true
            }
          ),
          errors.title && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["error-message"], role: "alert", children: errors.title })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "description", className: styles$1["form-label"], children: "Program Description" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "textarea",
            {
              id: "description",
              value: description2,
              onChange: (e) => setDescription(e.target.value),
              className: `${styles$1["form-textarea"]} ${errors.description ? styles$1["input-error"] : ""}`,
              placeholder: "Provide a detailed description of the training program...",
              rows: 6,
              maxLength: 2e3
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1["char-count"], children: [
            description2.length,
            " / 2000 characters"
          ] }),
          errors.description && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["error-message"], role: "alert", children: errors.description })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "category", className: styles$1["form-label"], children: "Category" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              id: "category",
              type: "text",
              value: category,
              onChange: (e) => setCategory(e.target.value),
              className: styles$1["form-input"],
              placeholder: "e.g., Artificial Intelligence, Cloud Computing, Cybersecurity"
            }
          )
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "Program Details" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { htmlFor: "difficulty", className: styles$1["form-label"], children: [
            "Difficulty Level ",
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["required"], children: "*" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "select",
            {
              id: "difficulty",
              value: difficultyLevel,
              onChange: (e) => setDifficultyLevel(e.target.value),
              className: styles$1["form-select"],
              required: true,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "beginner", children: "Beginner" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "intermediate", children: "Intermediate" }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "advanced", children: "Advanced" })
              ]
            }
          )
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-row"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "duration", className: styles$1["form-label"], children: "Estimated Duration" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "duration",
                type: "number",
                value: estimatedDuration || "",
                onChange: (e) => setEstimatedDuration(Number(e.target.value)),
                className: `${styles$1["form-input"]} ${errors.estimatedDuration ? styles$1["input-error"] : ""}`,
                placeholder: "0",
                min: "0"
              }
            ),
            errors.estimatedDuration && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1["error-message"], role: "alert", children: errors.estimatedDuration })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "durationUnit", className: styles$1["form-label"], children: "Duration Unit" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "select",
              {
                id: "durationUnit",
                value: durationUnit,
                onChange: (e) => setDurationUnit(e.target.value),
                className: styles$1["form-select"],
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "hours", children: "Hours" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "days", children: "Days" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "weeks", children: "Weeks" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "months", children: "Months" })
                ]
              }
            )
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-section"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "Tags" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["tags-input-group"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "text",
              value: newTag,
              onChange: (e) => setNewTag(e.target.value),
              onKeyPress: (e) => e.key === "Enter" && (e.preventDefault(), handleAddTag()),
              className: styles$1["form-input"],
              placeholder: "Add a tag (e.g., Python, Machine Learning)"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            Button,
            {
              type: "button",
              variant: "secondary",
              onClick: handleAddTag,
              disabled: !newTag.trim(),
              children: "Add Tag"
            }
          )
        ] }),
        tags.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["tags-display"], children: tags.map((tag2, index) => /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1["tag"], children: [
          tag2,
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "button",
            {
              type: "button",
              onClick: () => handleRemoveTag(tag2),
              className: styles$1["tag-remove"],
              "aria-label": `Remove ${tag2} tag`,
              children: "×"
            }
          )
        ] }, index)) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1["form-actions"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "button",
            variant: "secondary",
            onClick: handleCancel,
            disabled: isSaving,
            children: "Cancel"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            type: "submit",
            variant: "primary",
            disabled: isSaving,
            children: isSaving ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
              isEditMode ? "Saving Changes..." : "Creating Program..."
            ] }) : isEditMode ? "Save Changes" : "Create Program"
          }
        )
      ] }),
      (createMutation.isError || updateMutation.isError) && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1["submission-error"], role: "alert", children: createMutation.error?.message || updateMutation.error?.message || "Failed to save program. Please try again." })
    ] }) })
  ] }) });
};
const tabs = "_tabs_105o9_40";
const tab = "_tab_105o9_40";
const description = "_description_105o9_85";
const styles = {
  "content-gen-page": "_content-gen-page_105o9_8",
  "page-header": "_page-header_105o9_15",
  "header-content": "_header-content_105o9_23",
  "header-description": "_header-description_105o9_27",
  "program-selector": "_program-selector_105o9_35",
  tabs,
  tab,
  "tab-active": "_tab-active_105o9_66",
  "tab-content": "_tab-content_105o9_72",
  "generation-form": "_generation-form_105o9_79",
  description,
  "form-group": "_form-group_105o9_93",
  "form-row": "_form-row_105o9_99",
  "form-label": "_form-label_105o9_105",
  "form-input": "_form-input_105o9_111",
  "form-select": "_form-select_105o9_112",
  "generate-actions": "_generate-actions_105o9_134",
  "results-preview": "_results-preview_105o9_142",
  "preview-content": "_preview-content_105o9_150",
  "placeholder-text": "_placeholder-text_105o9_168",
  "coming-soon": "_coming-soon_105o9_174",
  "preview-actions": "_preview-actions_105o9_184",
  "info-card": "_info-card_105o9_192",
  "feature-list": "_feature-list_105o9_208"
};
const ContentGenerationPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = reactExports.useState("quiz");
  const [selectedProgram, setSelectedProgram] = reactExports.useState("");
  const [quizTopic, setQuizTopic] = reactExports.useState("");
  const [quizDifficulty, setQuizDifficulty] = reactExports.useState("intermediate");
  const [questionCount, setQuestionCount] = reactExports.useState(5);
  const [slidesTopic, setSlidesTopic] = reactExports.useState("");
  const [slideCount, setSlideCount] = reactExports.useState(10);
  const [exerciseTopic, setExerciseTopic] = reactExports.useState("");
  const [exerciseType, setExerciseType] = reactExports.useState("coding");
  const [syllabusTopic, setSyllabusTopic] = reactExports.useState("");
  const [courseDuration, setCourseDuration] = reactExports.useState(4);
  const { data: programs, isLoading: loadingPrograms } = useQuery({
    queryKey: ["trainingPrograms", "instructor", user?.id],
    queryFn: async () => {
      if (!user?.id) return { data: [] };
      return trainingProgramService.getInstructorPrograms(user.id);
    },
    enabled: !!user?.id
  });
  const generateMutation = useMutation({
    mutationFn: async (params) => {
      await new Promise((resolve) => setTimeout(resolve, 2e3));
      return { success: true, content: "Generated content will appear here" };
    }
  });
  const handleGenerate = () => {
    if (!selectedProgram) {
      alert("Please select a training program first");
      return;
    }
    let data = {};
    switch (activeTab) {
      case "quiz":
        if (!quizTopic) {
          alert("Please enter a quiz topic");
          return;
        }
        data = { topic: quizTopic, difficulty: quizDifficulty, questionCount };
        break;
      case "slides":
        if (!slidesTopic) {
          alert("Please enter a slides topic");
          return;
        }
        data = { topic: slidesTopic, slideCount };
        break;
      case "exercise":
        if (!exerciseTopic) {
          alert("Please enter an exercise topic");
          return;
        }
        data = { topic: exerciseTopic, type: exerciseType };
        break;
      case "syllabus":
        if (!syllabusTopic) {
          alert("Please enter a course topic");
          return;
        }
        data = { topic: syllabusTopic, duration: courseDuration };
        break;
    }
    generateMutation.mutate({ type: activeTab, data });
  };
  const renderTabContent = () => {
    switch (activeTab) {
      case "quiz":
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["generation-form"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "Generate Quiz Questions" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["description"], children: "AI will generate multiple-choice quiz questions based on your topic and difficulty level." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "quizTopic", className: styles["form-label"], children: "Quiz Topic" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "quizTopic",
                type: "text",
                value: quizTopic,
                onChange: (e) => setQuizTopic(e.target.value),
                className: styles["form-input"],
                placeholder: "e.g., Python List Comprehensions, Neural Networks Basics"
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-row"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "quizDifficulty", className: styles["form-label"], children: "Difficulty Level" }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs(
                "select",
                {
                  id: "quizDifficulty",
                  value: quizDifficulty,
                  onChange: (e) => setQuizDifficulty(e.target.value),
                  className: styles["form-select"],
                  children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "beginner", children: "Beginner" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "intermediate", children: "Intermediate" }),
                    /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "advanced", children: "Advanced" })
                  ]
                }
              )
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "questionCount", className: styles["form-label"], children: "Number of Questions" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(
                "input",
                {
                  id: "questionCount",
                  type: "number",
                  value: questionCount,
                  onChange: (e) => setQuestionCount(Number(e.target.value)),
                  className: styles["form-input"],
                  min: "1",
                  max: "20"
                }
              )
            ] })
          ] })
        ] });
      case "slides":
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["generation-form"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "Generate Presentation Slides" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["description"], children: "AI will generate PowerPoint-style slides with key concepts, examples, and visuals." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "slidesTopic", className: styles["form-label"], children: "Presentation Topic" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "slidesTopic",
                type: "text",
                value: slidesTopic,
                onChange: (e) => setSlidesTopic(e.target.value),
                className: styles["form-input"],
                placeholder: "e.g., Introduction to Machine Learning, Docker Fundamentals"
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "slideCount", className: styles["form-label"], children: "Number of Slides" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "slideCount",
                type: "number",
                value: slideCount,
                onChange: (e) => setSlideCount(Number(e.target.value)),
                className: styles["form-input"],
                min: "5",
                max: "50"
              }
            )
          ] })
        ] });
      case "exercise":
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["generation-form"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "Generate Lab Exercise" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["description"], children: "AI will generate hands-on exercises with instructions, starter code, and solution." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "exerciseTopic", className: styles["form-label"], children: "Exercise Topic" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "exerciseTopic",
                type: "text",
                value: exerciseTopic,
                onChange: (e) => setExerciseTopic(e.target.value),
                className: styles["form-input"],
                placeholder: "e.g., Build a REST API, Create a React Component"
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "exerciseType", className: styles["form-label"], children: "Exercise Type" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(
              "select",
              {
                id: "exerciseType",
                value: exerciseType,
                onChange: (e) => setExerciseType(e.target.value),
                className: styles["form-select"],
                children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "coding", children: "Coding Exercise" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "written", children: "Written Assignment" }),
                  /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "project", children: "Project-Based" })
                ]
              }
            )
          ] })
        ] });
      case "syllabus":
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["generation-form"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h3", gutterBottom: true, children: "Generate Course Syllabus" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["description"], children: "AI will generate a complete course syllabus with modules, lessons, and learning objectives." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "syllabusTopic", className: styles["form-label"], children: "Course Topic" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "syllabusTopic",
                type: "text",
                value: syllabusTopic,
                onChange: (e) => setSyllabusTopic(e.target.value),
                className: styles["form-input"],
                placeholder: "e.g., Full Stack Web Development, Data Science Fundamentals"
              }
            )
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "courseDuration", className: styles["form-label"], children: "Course Duration (weeks)" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              "input",
              {
                id: "courseDuration",
                type: "number",
                value: courseDuration,
                onChange: (e) => setCourseDuration(Number(e.target.value)),
                className: styles["form-input"],
                min: "1",
                max: "52"
              }
            )
          ] })
        ] });
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(DashboardLayout, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["content-gen-page"], children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["page-header"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["header-content"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h1", gutterBottom: true, children: "AI Content Generator" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["header-description"], children: "Generate quizzes, slides, exercises, and syllabi using AI. Select a training program and choose the type of content you want to create." })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", onClick: () => navigate("/instructor/programs"), children: "Back to Programs" })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { variant: "outlined", padding: "medium", className: styles["program-selector"], children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["form-group"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("label", { htmlFor: "program", className: styles["form-label"], children: "Select Training Program" }),
      loadingPrograms ? /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }) : /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "select",
        {
          id: "program",
          value: selectedProgram,
          onChange: (e) => setSelectedProgram(e.target.value),
          className: styles["form-select"],
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "-- Select a program --" }),
            programs?.data.map((program) => /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: program.id, children: program.title }, program.id))
          ]
        }
      )
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "large", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["tabs"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles["tab"]} ${activeTab === "quiz" ? styles["tab-active"] : ""}`,
            onClick: () => setActiveTab("quiz"),
            children: "Quiz Questions"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles["tab"]} ${activeTab === "slides" ? styles["tab-active"] : ""}`,
            onClick: () => setActiveTab("slides"),
            children: "Presentation Slides"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles["tab"]} ${activeTab === "exercise" ? styles["tab-active"] : ""}`,
            onClick: () => setActiveTab("exercise"),
            children: "Lab Exercise"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "button",
          {
            className: `${styles["tab"]} ${activeTab === "syllabus" ? styles["tab-active"] : ""}`,
            onClick: () => setActiveTab("syllabus"),
            children: "Course Syllabus"
          }
        )
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["tab-content"], children: [
        renderTabContent(),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles["generate-actions"], children: /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "primary",
            size: "large",
            onClick: handleGenerate,
            disabled: generateMutation.isPending || !selectedProgram,
            children: generateMutation.isPending ? /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(Spinner, { size: "small" }),
              "Generating Content..."
            ] }) : "Generate with AI"
          }
        ) }),
        generateMutation.isSuccess && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["results-preview"], children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h4", gutterBottom: true, children: "Generated Content Preview" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["preview-content"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "✨ AI content generation completed successfully!" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["placeholder-text"], children: "Preview of generated content will be displayed here. This will include:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Generated questions, slides, or exercises" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Edit and refine options" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: "Save to course button" })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles["coming-soon"], children: "🚀 Full AI integration with course-generator service coming in Phase 6" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles["preview-actions"], children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", children: "Regenerate" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", children: "Save to Course" })
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { variant: "outlined", padding: "medium", className: styles["info-card"], children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Heading, { level: "h4", gutterBottom: true, children: "💡 AI-Powered Content Generation" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Our AI content generator uses advanced language models to create high-quality educational content tailored to your training program. Features include:" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("ul", { className: styles["feature-list"], children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Quiz Generator:" }),
          " Multiple-choice, true/false, and short-answer questions"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Slide Creator:" }),
          " Professional presentation slides with diagrams and examples"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Exercise Builder:" }),
          " Hands-on coding labs with starter code and solutions"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Syllabus Designer:" }),
          " Complete course structure with learning objectives"
        ] })
      ] })
    ] })
  ] }) });
};
export {
  ContentGenerationPage,
  CreateEditTrainingProgramPage,
  TrainingProgramDetailPage,
  TrainingProgramListPage
};
//# sourceMappingURL=index-DBnBPndb.js.map
