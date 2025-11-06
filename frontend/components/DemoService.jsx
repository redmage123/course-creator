/**
 * Demo Service React Component
 *
 * BUSINESS REQUIREMENT:
 * Provides an interactive demo interface for the Course Creator Platform,
 * allowing potential customers and stakeholders to explore platform features
 * with realistic data without requiring actual system access.
 *
 * FEATURES:
 * - Multi-role demo experiences (Instructor, Student, Admin)
 * - Session management with time limits
 * - Real-time demo data visualization
 * - Interactive feature showcase
 * - Analytics and reporting demos
 * - Lab environment demonstrations
 *
 * TECHNICAL IMPLEMENTATION:
 * - React 18+ with Hooks
 * - Fetch API for demo service communication
 * - Material-UI components for consistent styling
 * - Session state management with localStorage fallback
 * - HTTPS-only communication with demo backend
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  LinearProgress,
  Paper,
  Tab,
  Tabs,
  Typography,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  School,
  Person,
  AdminPanelSettings,
  Analytics,
  Science,
  Feedback,
  AddCircle,
} from '@mui/icons-material';

// Demo service API base URL
const DEMO_API_BASE = process.env.REACT_APP_DEMO_API_URL || 'https://localhost:8010/api/v1/demo';

/**
 * Custom hook for demo session management
 */
const useDemoSession = () => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Start a new demo session
  const startSession = useCallback(async (role = 'instructor') => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${DEMO_API_BASE}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ role }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start demo session: ${response.statusText}`);
      }

      const data = await response.json();
      setSession(data);

      // Store session in localStorage for persistence
      localStorage.setItem('demo_session', JSON.stringify(data));

      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // End the current demo session
  const endSession = useCallback(async () => {
    if (!session) return;

    setLoading(true);
    setError(null);

    try {
      await fetch(`${DEMO_API_BASE}/session`, {
        method: 'DELETE',
        headers: {
          'X-Demo-Session-ID': session.session_id,
        },
      });

      setSession(null);
      localStorage.removeItem('demo_session');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [session]);

  // Get session info
  const getSessionInfo = useCallback(async () => {
    if (!session) return null;

    try {
      const response = await fetch(`${DEMO_API_BASE}/session/info`, {
        headers: {
          'X-Demo-Session-ID': session.session_id,
        },
      });

      if (!response.ok) {
        throw new Error('Session expired or invalid');
      }

      return await response.json();
    } catch (err) {
      setError(err.message);
      return null;
    }
  }, [session]);

  // Restore session from localStorage on mount
  useEffect(() => {
    const storedSession = localStorage.getItem('demo_session');
    if (storedSession) {
      try {
        const parsedSession = JSON.parse(storedSession);
        // Validate session is still active
        fetch(`${DEMO_API_BASE}/session/info`, {
          headers: {
            'X-Demo-Session-ID': parsedSession.session_id,
          },
        })
          .then(response => {
            if (response.ok) {
              setSession(parsedSession);
            } else {
              localStorage.removeItem('demo_session');
            }
          })
          .catch(() => {
            localStorage.removeItem('demo_session');
          });
      } catch (err) {
        localStorage.removeItem('demo_session');
      }
    }
  }, []);

  return { session, startSession, endSession, getSessionInfo, loading, error };
};

/**
 * Custom hook for demo data fetching
 */
const useDemoData = (session) => {
  const [courses, setCourses] = useState([]);
  const [students, setStudents] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [labs, setLabs] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async (endpoint) => {
    if (!session) return null;

    const response = await fetch(`${DEMO_API_BASE}/${endpoint}`, {
      headers: {
        'X-Demo-Session-ID': session.session_id,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch ${endpoint}`);
    }

    return await response.json();
  }, [session]);

  const loadAllData = useCallback(async () => {
    if (!session) return;

    setLoading(true);
    try {
      const [coursesData, studentsData, analyticsData, labsData, feedbackData] = await Promise.all([
        fetchData('courses'),
        fetchData('students'),
        fetchData('analytics'),
        fetchData('labs'),
        fetchData('feedback'),
      ]);

      setCourses(coursesData.courses || []);
      setStudents(studentsData.students || []);
      setAnalytics(analyticsData);
      setLabs(labsData.labs || []);
      setFeedback(feedbackData.feedback || []);
    } catch (err) {
      console.error('Error loading demo data:', err);
    } finally {
      setLoading(false);
    }
  }, [session, fetchData]);

  useEffect(() => {
    if (session) {
      loadAllData();
    }
  }, [session, loadAllData]);

  return { courses, students, analytics, labs, feedback, loading, refresh: loadAllData };
};

/**
 * Role Selection Dialog
 */
const RoleSelectionDialog = ({ open, onClose, onSelectRole }) => {
  const roles = [
    {
      value: 'instructor',
      label: 'Instructor',
      icon: <School fontSize="large" />,
      description: 'Create courses, manage content, track student progress',
    },
    {
      value: 'student',
      label: 'Student',
      icon: <Person fontSize="large" />,
      description: 'Browse courses, take quizzes, access lab environments',
    },
    {
      value: 'admin',
      label: 'Administrator',
      icon: <AdminPanelSettings fontSize="large" />,
      description: 'Manage platform, view analytics, configure settings',
    },
  ];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Select Demo Role</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" paragraph>
          Choose a role to explore the platform's features and capabilities
        </Typography>
        <Grid container spacing={2}>
          {roles.map((role) => (
            <Grid item xs={12} md={4} key={role.value}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.3s',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => {
                  onSelectRole(role.value);
                  onClose();
                }}
              >
                <CardContent sx={{ textAlign: 'center' }}>
                  <Box sx={{ color: 'primary.main', mb: 2 }}>
                    {role.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {role.label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {role.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * Session Info Display
 */
const SessionInfo = ({ session, onEndSession }) => {
  const [sessionInfo, setSessionInfo] = useState(null);
  const { getSessionInfo } = useDemoSession();

  useEffect(() => {
    if (session) {
      getSessionInfo().then(setSessionInfo);

      // Refresh session info every 30 seconds
      const interval = setInterval(() => {
        getSessionInfo().then(setSessionInfo);
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [session, getSessionInfo]);

  if (!session) return null;

  const timeRemaining = sessionInfo?.time_remaining || 'Unknown';
  const role = session.user?.role || 'Unknown';

  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h6" gutterBottom>
            Demo Session Active
          </Typography>
          <Box display="flex" gap={2}>
            <Chip label={`Role: ${role}`} color="primary" size="small" />
            <Chip label={`Time Remaining: ${timeRemaining}`} color="secondary" size="small" />
            <Chip label={`Session ID: ${session.session_id.slice(0, 8)}...`} size="small" />
          </Box>
        </Box>
        <Button
          variant="outlined"
          color="error"
          startIcon={<Stop />}
          onClick={onEndSession}
        >
          End Demo
        </Button>
      </Box>
    </Paper>
  );
};

/**
 * Courses Tab Content
 */
const CoursesTab = ({ courses }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Demo Courses ({courses.length})
    </Typography>
    <Grid container spacing={2}>
      {courses.map((course) => (
        <Grid item xs={12} md={6} key={course.id}>
          <Card>
            <CardHeader
              title={course.title}
              subheader={`${course.enrollment_count} students enrolled`}
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary" paragraph>
                {course.description}
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                <Chip label={course.difficulty} size="small" />
                <Chip label={`${course.duration} hours`} size="small" />
                <Chip label={`${course.modules} modules`} size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  </Box>
);

/**
 * Students Tab Content
 */
const StudentsTab = ({ students }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Demo Students ({students.length})
    </Typography>
    <List>
      {students.map((student, index) => (
        <React.Fragment key={student.id}>
          <ListItem>
            <ListItemText
              primary={student.name}
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Email: {student.email}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Enrolled: {student.enrolled_courses} courses
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Progress: {student.avg_progress}%
                  </Typography>
                </Box>
              }
            />
            <Chip
              label={`${student.avg_score}% avg`}
              color={student.avg_score >= 70 ? 'success' : 'warning'}
              size="small"
            />
          </ListItem>
          {index < students.length - 1 && <Divider />}
        </React.Fragment>
      ))}
    </List>
  </Box>
);

/**
 * Analytics Tab Content
 */
const AnalyticsTab = ({ analytics }) => {
  if (!analytics) return <Typography>No analytics data available</Typography>;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Platform Analytics
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="primary">
                {analytics.total_courses || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Courses
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="secondary">
                {analytics.total_students || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Students
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main">
                {analytics.avg_completion_rate || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Completion Rate
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="info.main">
                {analytics.avg_satisfaction || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Satisfaction
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

/**
 * Labs Tab Content
 */
const LabsTab = ({ labs }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Lab Environments ({labs.length})
    </Typography>
    <Grid container spacing={2}>
      {labs.map((lab) => (
        <Grid item xs={12} md={6} key={lab.id}>
          <Card>
            <CardHeader
              title={lab.name}
              subheader={`${lab.type} environment`}
            />
            <CardContent>
              <Typography variant="body2" color="text.secondary" paragraph>
                {lab.description}
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                <Chip label={lab.language} size="small" icon={<Science />} />
                <Chip label={`${lab.active_sessions} active`} size="small" color="success" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  </Box>
);

/**
 * Feedback Tab Content
 */
const FeedbackTab = ({ feedback }) => (
  <Box>
    <Typography variant="h6" gutterBottom>
      Student Feedback ({feedback.length})
    </Typography>
    <List>
      {feedback.map((item, index) => (
        <React.Fragment key={item.id}>
          <ListItem>
            <ListItemText
              primary={item.course_title}
              secondary={
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    "{item.comment}"
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    - {item.student_name} • Rating: {item.rating}/5
                  </Typography>
                </Box>
              }
            />
          </ListItem>
          {index < feedback.length - 1 && <Divider />}
        </React.Fragment>
      ))}
    </List>
  </Box>
);

/**
 * Main Demo Service Component
 */
export const DemoService = () => {
  const { session, startSession, endSession, loading, error } = useDemoSession();
  const { courses, students, analytics, labs, feedback, loading: dataLoading, refresh } = useDemoData(session);
  const [roleDialogOpen, setRoleDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  const handleStartDemo = useCallback(() => {
    setRoleDialogOpen(true);
  }, []);

  const handleSelectRole = useCallback(async (role) => {
    try {
      await startSession(role);
    } catch (err) {
      console.error('Failed to start demo:', err);
    }
  }, [startSession]);

  const handleEndDemo = useCallback(async () => {
    try {
      await endSession();
      setActiveTab(0);
    } catch (err) {
      console.error('Failed to end demo:', err);
    }
  }, [endSession]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Course Creator Platform Demo
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Experience the full platform capabilities with realistic demo data
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {!session && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<PlayArrow />}
            onClick={handleStartDemo}
            disabled={loading}
          >
            Start Interactive Demo
          </Button>
        </Box>
      )}

      {session && (
        <>
          <SessionInfo session={session} onEndSession={handleEndDemo} />

          {dataLoading && <LinearProgress sx={{ mb: 2 }} />}

          <Paper sx={{ mb: 2 }}>
            <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} variant="scrollable">
              <Tab label="Courses" icon={<School />} iconPosition="start" />
              <Tab label="Students" icon={<Person />} iconPosition="start" />
              <Tab label="Analytics" icon={<Analytics />} iconPosition="start" />
              <Tab label="Labs" icon={<Science />} iconPosition="start" />
              <Tab label="Feedback" icon={<Feedback />} iconPosition="start" />
            </Tabs>
          </Paper>

          <Paper sx={{ p: 3 }}>
            {activeTab === 0 && <CoursesTab courses={courses} />}
            {activeTab === 1 && <StudentsTab students={students} />}
            {activeTab === 2 && <AnalyticsTab analytics={analytics} />}
            {activeTab === 3 && <LabsTab labs={labs} />}
            {activeTab === 4 && <FeedbackTab feedback={feedback} />}
          </Paper>

          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Button variant="outlined" onClick={refresh} disabled={dataLoading}>
              Refresh Data
            </Button>
          </Box>
        </>
      )}

      <RoleSelectionDialog
        open={roleDialogOpen}
        onClose={() => setRoleDialogOpen(false)}
        onSelectRole={handleSelectRole}
      />
    </Container>
  );
};

export default DemoService;
