import { j as jsxRuntimeExports } from "./query-vendor-BigVEegc.js";
import { a as reactExports, i as useParams, u as useNavigate } from "./react-vendor-cEae-lCc.js";
import { B as Button } from "./index-C0G9mbri.js";
import "./state-vendor-B_izx0oA.js";
const questionContainer = "_questionContainer_p7ijp_5";
const questionHeader = "_questionHeader_p7ijp_11";
const questionMeta = "_questionMeta_p7ijp_19";
const questionNumber = "_questionNumber_p7ijp_25";
const difficulty = "_difficulty_p7ijp_31";
const points = "_points_p7ijp_38";
const questionText = "_questionText_p7ijp_44";
const optionsContainer = "_optionsContainer_p7ijp_51";
const option = "_option_p7ijp_51";
const selected = "_selected_p7ijp_74";
const correct = "_correct_p7ijp_79";
const wrong = "_wrong_p7ijp_84";
const radioInput = "_radioInput_p7ijp_89";
const optionText = "_optionText_p7ijp_95";
const correctBadge = "_correctBadge_p7ijp_101";
const wrongBadge = "_wrongBadge_p7ijp_107";
const textInputContainer = "_textInputContainer_p7ijp_113";
const textInput = "_textInput_p7ijp_113";
const textArea = "_textArea_p7ijp_134";
const correctAnswerDisplay = "_correctAnswerDisplay_p7ijp_150";
const explanation = "_explanation_p7ijp_169";
const tags = "_tags_p7ijp_188";
const tag = "_tag_p7ijp_188";
const styles$3 = {
  questionContainer,
  questionHeader,
  questionMeta,
  questionNumber,
  difficulty,
  points,
  questionText,
  optionsContainer,
  option,
  selected,
  correct,
  wrong,
  radioInput,
  optionText,
  correctBadge,
  wrongBadge,
  textInputContainer,
  textInput,
  textArea,
  correctAnswerDisplay,
  explanation,
  tags,
  tag
};
const QuizQuestion = ({
  question,
  questionIndex,
  answer,
  onAnswerChange,
  showCorrectAnswer = false,
  correctAnswer,
  isReview = false
}) => {
  const handleChange = (value) => {
    if (!isReview) {
      onAnswerChange(questionIndex, value);
    }
  };
  const getDifficultyColor = (difficulty2) => {
    switch (difficulty2) {
      case "easy":
        return "#4caf50";
      case "medium":
        return "#ff9800";
      case "hard":
        return "#f44336";
      default:
        return "#666666";
    }
  };
  const renderQuestionInput = () => {
    switch (question.question_type) {
      case "multiple_choice":
        return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.optionsContainer, children: question.options.map((option2, index) => {
          const isSelected = answer === option2;
          const isCorrect = showCorrectAnswer && option2 === correctAnswer;
          const isWrong = showCorrectAnswer && isSelected && option2 !== correctAnswer;
          return /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "label",
            {
              className: `${styles$3.option} ${isSelected ? styles$3.selected : ""} ${isCorrect ? styles$3.correct : ""} ${isWrong ? styles$3.wrong : ""}`,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "input",
                  {
                    type: "radio",
                    name: `question-${questionIndex}`,
                    value: option2,
                    checked: isSelected,
                    onChange: (e) => handleChange(e.target.value),
                    disabled: isReview,
                    className: styles$3.radioInput
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.optionText, children: option2 }),
                isCorrect && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.correctBadge, children: "✓ Correct" }),
                isWrong && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.wrongBadge, children: "✗ Incorrect" })
              ]
            },
            index
          );
        }) });
      case "true_false":
        return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.optionsContainer, children: ["True", "False"].map((option2) => {
          const isSelected = answer === option2;
          const isCorrect = showCorrectAnswer && option2 === correctAnswer;
          const isWrong = showCorrectAnswer && isSelected && option2 !== correctAnswer;
          return /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "label",
            {
              className: `${styles$3.option} ${isSelected ? styles$3.selected : ""} ${isCorrect ? styles$3.correct : ""} ${isWrong ? styles$3.wrong : ""}`,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(
                  "input",
                  {
                    type: "radio",
                    name: `question-${questionIndex}`,
                    value: option2,
                    checked: isSelected,
                    onChange: (e) => handleChange(e.target.value),
                    disabled: isReview,
                    className: styles$3.radioInput
                  }
                ),
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.optionText, children: option2 }),
                isCorrect && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.correctBadge, children: "✓ Correct" }),
                isWrong && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.wrongBadge, children: "✗ Incorrect" })
              ]
            },
            option2
          );
        }) });
      case "short_answer":
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.textInputContainer, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "text",
              value: answer,
              onChange: (e) => handleChange(e.target.value),
              placeholder: "Enter your answer...",
              className: styles$3.textInput,
              disabled: isReview
            }
          ),
          showCorrectAnswer && correctAnswer && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.correctAnswerDisplay, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Correct Answer:" }),
            " ",
            correctAnswer
          ] })
        ] });
      case "essay":
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.textInputContainer, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "textarea",
            {
              value: answer,
              onChange: (e) => handleChange(e.target.value),
              placeholder: "Enter your answer... (Be thorough and specific)",
              className: styles$3.textArea,
              rows: 10,
              disabled: isReview
            }
          ),
          showCorrectAnswer && question.explanation && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.correctAnswerDisplay, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Sample Answer/Key Points:" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: question.explanation })
          ] })
        ] });
      case "fill_in_blank":
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.textInputContainer, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "input",
            {
              type: "text",
              value: answer,
              onChange: (e) => handleChange(e.target.value),
              placeholder: "Fill in the blank...",
              className: styles$3.textInput,
              disabled: isReview
            }
          ),
          showCorrectAnswer && correctAnswer && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.correctAnswerDisplay, children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Correct Answer:" }),
            " ",
            correctAnswer
          ] })
        ] });
      default:
        return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: "Unsupported question type" });
    }
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.questionContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.questionHeader, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.questionMeta, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.questionNumber, children: [
        "Question ",
        questionIndex + 1
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        "span",
        {
          className: styles$3.difficulty,
          style: { color: getDifficultyColor(question.difficulty) },
          children: question.difficulty.toUpperCase()
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$3.points, children: [
        question.points,
        " ",
        question.points === 1 ? "point" : "points"
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.questionText, children: question.question_text }),
    renderQuestionInput(),
    showCorrectAnswer && question.explanation && question.question_type !== "essay" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$3.explanation, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: "Explanation:" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: question.explanation })
    ] }),
    question.tags && question.tags.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$3.tags, children: question.tags.map((tag2, index) => /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$3.tag, children: tag2 }, index)) })
  ] });
};
const timer = "_timer_4i69f_1";
const normal = "_normal_4i69f_12";
const warning = "_warning_4i69f_17";
const critical = "_critical_4i69f_23";
const timerIcon = "_timerIcon_4i69f_34";
const urgentBadge = "_urgentBadge_4i69f_38";
const styles$2 = {
  timer,
  normal,
  warning,
  critical,
  timerIcon,
  urgentBadge
};
const QuizTimer = ({
  timeRemaining: initialTime,
  onTimeExpired
}) => {
  const [timeLeft, setTimeLeft] = reactExports.useState(initialTime);
  reactExports.useEffect(() => {
    if (timeLeft <= 0) {
      onTimeExpired();
      return;
    }
    const timer2 = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1e3);
    return () => clearInterval(timer2);
  }, [timeLeft, onTimeExpired]);
  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor(seconds % 3600 / 60);
    const secs = seconds % 60;
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
    }
    return `${minutes}:${secs.toString().padStart(2, "0")}`;
  };
  const getWarningLevel = () => {
    if (timeLeft <= 60) return styles$2.critical;
    if (timeLeft <= 300) return styles$2.warning;
    return styles$2.normal;
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `${styles$2.timer} ${getWarningLevel()}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.timerIcon, children: "⏱️" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.timerText, children: formatTime(timeLeft) }),
    timeLeft <= 60 && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$2.urgentBadge, children: "Hurry!" })
  ] });
};
const resultsContainer = "_resultsContainer_f7wh9_1";
const resultsCard = "_resultsCard_f7wh9_10";
const resultBanner = "_resultBanner_f7wh9_19";
const passed = "_passed_f7wh9_25";
const failed = "_failed_f7wh9_29";
const resultIcon = "_resultIcon_f7wh9_33";
const performanceMessage = "_performanceMessage_f7wh9_44";
const scoreSection = "_scoreSection_f7wh9_50";
const mainScore = "_mainScore_f7wh9_55";
const scoreCircle = "_scoreCircle_f7wh9_61";
const scorePercentage = "_scorePercentage_f7wh9_72";
const scoreDetails = "_scoreDetails_f7wh9_78";
const passedText = "_passedText_f7wh9_88";
const failedText = "_failedText_f7wh9_93";
const statsSection = "_statsSection_f7wh9_98";
const statCard = "_statCard_f7wh9_106";
const statLabel = "_statLabel_f7wh9_116";
const statValue = "_statValue_f7wh9_123";
const actions = "_actions_f7wh9_129";
const styles$1 = {
  resultsContainer,
  resultsCard,
  resultBanner,
  passed,
  failed,
  resultIcon,
  performanceMessage,
  scoreSection,
  mainScore,
  scoreCircle,
  scorePercentage,
  scoreDetails,
  passedText,
  failedText,
  statsSection,
  statCard,
  statLabel,
  statValue,
  actions
};
const QuizResults = ({
  quiz,
  attempt,
  onRetake,
  onClose
}) => {
  if (!attempt.score) return null;
  const { score } = attempt;
  const isPassed = score.passed;
  const percentage = Math.round(score.percentage);
  const getPerformanceMessage = () => {
    if (percentage >= 90) return "Excellent work!";
    if (percentage >= 80) return "Great job!";
    if (percentage >= 70) return "Good effort!";
    if (percentage >= 60) return "Keep practicing!";
    return "Review the material and try again.";
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.resultsContainer, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.resultsCard, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `${styles$1.resultBanner} ${isPassed ? styles$1.passed : styles$1.failed}`, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.resultIcon, children: isPassed ? "🎉" : "📚" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: isPassed ? "Congratulations!" : "Not Quite There" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles$1.performanceMessage, children: getPerformanceMessage() })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.scoreSection, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.mainScore, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles$1.scoreCircle, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.scorePercentage, children: [
        percentage,
        "%"
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.scoreDetails, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: score.earned_points }),
          " / ",
          score.total_points,
          " points"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("strong", { children: score.correct_count }),
          " / ",
          score.total_questions,
          " correct"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: isPassed ? styles$1.passedText : styles$1.failedText, children: [
          isPassed ? "✓ Passed" : "✗ Did not pass",
          " (Passing: ",
          score.passing_score,
          "%)"
        ] })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.statsSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.statCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.statLabel, children: "Time Spent" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.statValue, children: [
          Math.floor(attempt.time_spent_seconds / 60),
          "min ",
          attempt.time_spent_seconds % 60,
          "s"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.statCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.statLabel, children: "Accuracy" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles$1.statValue, children: [
          percentage,
          "%"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.statCard, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.statLabel, children: "Questions" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: styles$1.statValue, children: score.total_questions })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles$1.actions, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "secondary", onClick: onClose, children: "Close" }),
      onRetake && !isPassed && /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "primary", onClick: onRetake, children: "Retake Quiz" })
    ] })
  ] }) });
};
const CONTENT_API_BASE = "https://176.9.99.103:8001/api/v1";
const COURSE_API_BASE = "https://176.9.99.103:8002/api/v1";
class QuizServiceError extends Error {
  constructor(message, statusCode, detail) {
    super(message);
    this.statusCode = statusCode;
    this.detail = detail;
    this.name = "QuizServiceError";
  }
}
async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: "An error occurred"
    }));
    throw new QuizServiceError(
      errorData.detail || `Request failed with status ${response.status}`,
      response.status,
      errorData.detail
    );
  }
  return response.json();
}
const quizService = {
  /**
   * Get quiz by ID
   */
  async getQuiz(quizId) {
    const response = await fetch(
      `${CONTENT_API_BASE}/quizzes/${quizId}`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get all quizzes for a course
   */
  async getQuizzesForCourse(courseId) {
    const response = await fetch(
      `${CONTENT_API_BASE}/courses/${courseId}/quizzes`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get active quiz attempt for student
   */
  async getActiveAttempt(quizId) {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/active?quizId=${quizId}`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    if (response.status === 404) {
      return null;
    }
    return handleResponse(response);
  },
  /**
   * Start new quiz attempt
   */
  async startQuiz(quizId) {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quiz_id: quizId,
          started_at: (/* @__PURE__ */ new Date()).toISOString()
        })
      }
    );
    return handleResponse(response);
  },
  /**
   * Save answer for a question
   */
  async saveAnswer(attemptId, questionIndex, answer) {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/${attemptId}/answers`,
      {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question_index: questionIndex,
          answer
        })
      }
    );
    return handleResponse(response);
  },
  /**
   * Submit quiz attempt
   */
  async submitQuiz(attemptId, answers) {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/${attemptId}/submit`,
      {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          answers,
          submitted_at: (/* @__PURE__ */ new Date()).toISOString()
        })
      }
    );
    return handleResponse(response);
  },
  /**
   * Get quiz attempts history for student
   */
  async getAttemptHistory(quizId) {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/history?quizId=${quizId}`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  },
  /**
   * Get quiz attempt by ID
   */
  async getAttempt(attemptId) {
    const response = await fetch(
      `${COURSE_API_BASE}/quiz-attempts/${attemptId}`,
      {
        credentials: "include",
        headers: { "Content-Type": "application/json" }
      }
    );
    return handleResponse(response);
  }
};
const useQuizSession = (quizId, courseId) => {
  const [quiz, setQuiz] = reactExports.useState(null);
  const [attempt, setAttempt] = reactExports.useState(null);
  const [answers, setAnswers] = reactExports.useState({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = reactExports.useState(0);
  const [isLoading, setIsLoading] = reactExports.useState(true);
  const [isSubmitting, setIsSubmitting] = reactExports.useState(false);
  const [error, setError] = reactExports.useState(null);
  reactExports.useEffect(() => {
    if (!quizId || !courseId) return;
    const loadQuiz = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const quizData = await quizService.getQuiz(quizId);
        setQuiz(quizData);
        const existingAttempt = await quizService.getActiveAttempt(quizId);
        if (existingAttempt) {
          setAttempt(existingAttempt);
          setAnswers(existingAttempt.answers || {});
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load quiz");
      } finally {
        setIsLoading(false);
      }
    };
    loadQuiz();
  }, [quizId, courseId]);
  const startQuiz = reactExports.useCallback(async () => {
    if (!quizId) return;
    try {
      setIsLoading(true);
      setError(null);
      const newAttempt = await quizService.startQuiz(quizId);
      setAttempt(newAttempt);
      setAnswers({});
      setCurrentQuestionIndex(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start quiz");
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [quizId]);
  const saveAnswer = reactExports.useCallback(async (questionIndex, answer) => {
    if (!attempt) return;
    try {
      const updatedAnswers = { ...answers, [questionIndex]: answer };
      setAnswers(updatedAnswers);
      await quizService.saveAnswer(attempt.id, questionIndex, answer);
    } catch (err) {
      console.error("Failed to save answer:", err);
    }
  }, [attempt, answers]);
  const submitQuiz = reactExports.useCallback(async () => {
    if (!attempt) return null;
    try {
      setIsSubmitting(true);
      setError(null);
      const submittedAttempt = await quizService.submitQuiz(attempt.id, answers);
      setAttempt(submittedAttempt);
      return submittedAttempt;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit quiz");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, [attempt, answers]);
  return {
    quiz,
    attempt,
    answers,
    currentQuestionIndex,
    isLoading,
    isSubmitting,
    error,
    startQuiz,
    saveAnswer,
    submitQuiz,
    setCurrentQuestionIndex
  };
};
const quizContainer = "_quizContainer_19f8q_5";
const loadingContainer = "_loadingContainer_19f8q_13";
const errorContainer = "_errorContainer_19f8q_14";
const spinner = "_spinner_19f8q_23";
const quizHeader = "_quizHeader_19f8q_42";
const quizInfo = "_quizInfo_19f8q_54";
const quizDescription = "_quizDescription_19f8q_64";
const progressSection = "_progressSection_19f8q_70";
const progressBar = "_progressBar_19f8q_78";
const progressFill = "_progressFill_19f8q_87";
const progressText = "_progressText_19f8q_94";
const questionSection = "_questionSection_19f8q_101";
const navigationSection = "_navigationSection_19f8q_110";
const navigationCenter = "_navigationCenter_19f8q_118";
const questionIndicator = "_questionIndicator_19f8q_124";
const questionGrid = "_questionGrid_19f8q_130";
const questionButtons = "_questionButtons_19f8q_143";
const questionButton = "_questionButton_19f8q_143";
const active = "_active_19f8q_167";
const answered = "_answered_19f8q_173";
const modal = "_modal_19f8q_184";
const modalContent = "_modalContent_19f8q_197";
const warningText = "_warningText_19f8q_218";
const modalActions = "_modalActions_19f8q_223";
const styles = {
  quizContainer,
  loadingContainer,
  errorContainer,
  spinner,
  quizHeader,
  quizInfo,
  quizDescription,
  progressSection,
  progressBar,
  progressFill,
  progressText,
  questionSection,
  navigationSection,
  navigationCenter,
  questionIndicator,
  questionGrid,
  questionButtons,
  questionButton,
  active,
  answered,
  modal,
  modalContent,
  warningText,
  modalActions
};
const QuizTaking = () => {
  const { quizId, courseId } = useParams();
  const navigate = useNavigate();
  const {
    quiz,
    attempt,
    answers,
    currentQuestionIndex,
    isLoading,
    isSubmitting,
    error,
    startQuiz,
    saveAnswer,
    submitQuiz,
    setCurrentQuestionIndex
  } = useQuizSession(quizId, courseId);
  const [showResults, setShowResults] = reactExports.useState(false);
  const [showSubmitConfirm, setShowSubmitConfirm] = reactExports.useState(false);
  const [timeRemaining, setTimeRemaining] = reactExports.useState(null);
  reactExports.useEffect(() => {
    if (quiz?.is_timed && quiz.settings.time_limit_minutes && attempt) {
      const startTime = new Date(attempt.started_at).getTime();
      const now = Date.now();
      const elapsed = Math.floor((now - startTime) / 1e3);
      const totalSeconds = quiz.settings.time_limit_minutes * 60;
      const remaining = Math.max(0, totalSeconds - elapsed);
      setTimeRemaining(remaining);
    }
  }, [quiz, attempt]);
  const handleTimeExpired = reactExports.useCallback(async () => {
    if (!isSubmitting) {
      await submitQuiz();
      setShowResults(true);
    }
  }, [isSubmitting, submitQuiz]);
  const handleAnswerChange = reactExports.useCallback(async (questionIndex, answer) => {
    await saveAnswer(questionIndex, answer);
  }, [saveAnswer]);
  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };
  const handleNext = () => {
    if (quiz && currentQuestionIndex < quiz.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };
  const handleSubmit = async () => {
    setShowSubmitConfirm(false);
    const result = await submitQuiz();
    if (result) {
      setShowResults(true);
    }
  };
  const getProgress = () => {
    if (!quiz) return 0;
    const answered2 = Object.keys(answers).length;
    return answered2 / quiz.questions.length * 100;
  };
  if (isLoading) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.loadingContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.spinner }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Loading quiz..." })
    ] });
  }
  if (error) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.errorContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Error Loading Quiz" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: error }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { onClick: () => navigate(-1), children: "Go Back" })
    ] });
  }
  if (!quiz || !attempt) {
    return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.errorContainer, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Quiz Not Found" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { onClick: () => navigate(-1), children: "Go Back" })
    ] });
  }
  if (showResults && attempt.score) {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      QuizResults,
      {
        quiz,
        attempt,
        onRetake: quiz.allows_multiple_attempts ? () => startQuiz() : void 0,
        onClose: () => navigate(`/courses/${courseId}`)
      }
    );
  }
  const currentQuestion = quiz.questions[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === quiz.questions.length - 1;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.quizContainer, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.quizHeader, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.quizInfo, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { children: quiz.title }),
        quiz.description && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.quizDescription, children: quiz.description })
      ] }),
      quiz.is_timed && timeRemaining !== null && /* @__PURE__ */ jsxRuntimeExports.jsx(
        QuizTimer,
        {
          timeRemaining,
          onTimeExpired: handleTimeExpired
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.progressSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.progressBar, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          className: styles.progressFill,
          style: { width: `${getProgress()}%` }
        }
      ) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.progressText, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          Object.keys(answers).length,
          " of ",
          quiz.questions.length,
          " answered"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
          "Question ",
          currentQuestionIndex + 1,
          " of ",
          quiz.questions.length
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.questionSection, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      QuizQuestion,
      {
        question: currentQuestion,
        questionIndex: currentQuestionIndex,
        answer: answers[currentQuestionIndex] || "",
        onAnswerChange: handleAnswerChange
      }
    ) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.navigationSection, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "secondary",
          onClick: handlePrevious,
          disabled: currentQuestionIndex === 0,
          children: "← Previous"
        }
      ),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.navigationCenter, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: styles.questionIndicator, children: [
        currentQuestionIndex + 1,
        " / ",
        quiz.questions.length
      ] }) }),
      !isLastQuestion ? /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: handleNext,
          children: "Next →"
        }
      ) : /* @__PURE__ */ jsxRuntimeExports.jsx(
        Button,
        {
          variant: "primary",
          onClick: () => setShowSubmitConfirm(true),
          disabled: isSubmitting,
          children: "Submit Quiz"
        }
      )
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.questionGrid, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { children: "Questions" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.questionButtons, children: quiz.questions.map((_, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(
        "button",
        {
          className: `${styles.questionButton} ${index === currentQuestionIndex ? styles.active : ""} ${answers[index] ? styles.answered : ""}`,
          onClick: () => setCurrentQuestionIndex(index),
          children: index + 1
        },
        index
      )) })
    ] }),
    showSubmitConfirm && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: styles.modal, children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.modalContent, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { children: "Submit Quiz?" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "You have answered ",
        Object.keys(answers).length,
        " out of ",
        quiz.questions.length,
        " questions."
      ] }),
      Object.keys(answers).length < quiz.questions.length && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: styles.warningText, children: "⚠️ Some questions are unanswered. Are you sure you want to submit?" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: styles.modalActions, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "secondary",
            onClick: () => setShowSubmitConfirm(false),
            children: "Cancel"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Button,
          {
            variant: "primary",
            onClick: handleSubmit,
            disabled: isSubmitting,
            children: isSubmitting ? "Submitting..." : "Yes, Submit"
          }
        )
      ] })
    ] }) })
  ] });
};
export {
  QuizTaking,
  QuizTaking as default
};
//# sourceMappingURL=QuizTaking-BsFopOP7.js.map
