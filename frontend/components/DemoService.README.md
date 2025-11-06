# Demo Service React Component

## Overview

A comprehensive React component for interacting with the Course Creator Platform demo service. Provides an interactive demonstration interface for potential customers, stakeholders, and training purposes.

## Features

- **Multi-Role Demo Experiences**: Instructor, Student, and Administrator roles
- **Session Management**: Automatic session creation, tracking, and cleanup
- **Real-Time Data Visualization**: Live demo data for courses, students, analytics, labs, and feedback
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **HTTPS-Only**: Secure communication with demo backend
- **Persistent Sessions**: Session data persists across page refreshes via localStorage

## Installation

### Required Dependencies

```bash
npm install react react-dom @mui/material @mui/icons-material @emotion/react @emotion/styled
```

Or with yarn:

```bash
yarn add react react-dom @mui/material @mui/icons-material @emotion/react @emotion/styled
```

### package.json Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@mui/material": "^5.14.0",
    "@mui/icons-material": "^5.14.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0"
  }
}
```

## Usage

### Basic Integration

```jsx
import { DemoService } from './components/DemoService';

function App() {
  return (
    <div className="App">
      <DemoService />
    </div>
  );
}
```

### With Custom API URL

Set the demo service URL via environment variable:

```bash
# .env file
REACT_APP_DEMO_API_URL=https://your-domain.com:8010/api/v1/demo
```

Or directly in your code:

```jsx
// Before importing the component
process.env.REACT_APP_DEMO_API_URL = 'https://localhost:8010/api/v1/demo';

import { DemoService } from './components/DemoService';
```

### Integration with Existing App

```jsx
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { DemoService } from './components/DemoService';
import { ThemeProvider, createTheme } from '@mui/material';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <Router>
        <Routes>
          <Route path="/demo" element={<DemoService />} />
          {/* Other routes */}
        </Routes>
      </Router>
    </ThemeProvider>
  );
}
```

## Component Structure

### Custom Hooks

#### `useDemoSession`
Manages demo session lifecycle:
- `startSession(role)` - Start new demo session with specified role
- `endSession()` - End current demo session
- `getSessionInfo()` - Get current session information
- `session` - Current session object
- `loading` - Loading state
- `error` - Error state

#### `useDemoData`
Fetches and manages demo data:
- `courses` - Array of demo courses
- `students` - Array of demo students
- `analytics` - Platform analytics data
- `labs` - Lab environments data
- `feedback` - Student feedback data
- `loading` - Loading state
- `refresh()` - Refresh all data

### Sub-Components

- **RoleSelectionDialog**: Modal for selecting demo role
- **SessionInfo**: Displays active session information
- **CoursesTab**: Shows demo courses
- **StudentsTab**: Shows demo students
- **AnalyticsTab**: Displays platform analytics
- **LabsTab**: Shows lab environments
- **FeedbackTab**: Displays student feedback

## API Integration

The component communicates with the demo service backend at these endpoints:

### Session Management
- `POST /api/v1/demo/start` - Start demo session
- `GET /api/v1/demo/session/info` - Get session info
- `DELETE /api/v1/demo/session` - End session

### Data Endpoints
- `GET /api/v1/demo/courses` - Get demo courses
- `GET /api/v1/demo/students` - Get demo students
- `GET /api/v1/demo/analytics` - Get analytics data
- `GET /api/v1/demo/labs` - Get lab environments
- `GET /api/v1/demo/feedback` - Get student feedback

All data endpoints require `X-Demo-Session-ID` header.

## Customization

### Theming

Customize the Material-UI theme:

```jsx
import { ThemeProvider, createTheme } from '@mui/material';

const customTheme = createTheme({
  palette: {
    primary: {
      main: '#your-color',
    },
  },
  typography: {
    fontFamily: 'Your Font',
  },
});

<ThemeProvider theme={customTheme}>
  <DemoService />
</ThemeProvider>
```

### Custom Styling

Override component styles:

```jsx
import { styled } from '@mui/material/styles';
import { DemoService } from './components/DemoService';

const StyledDemoService = styled(DemoService)(({ theme }) => ({
  '& .MuiPaper-root': {
    borderRadius: theme.spacing(2),
  },
}));
```

## Session Management

### Session Storage
- Sessions are stored in `localStorage` as `demo_session`
- Automatic session validation on component mount
- Sessions automatically expire after configured time limit

### Session Recovery
If a page refresh occurs, the component automatically:
1. Checks localStorage for existing session
2. Validates session with backend
3. Restores session if still active
4. Clears invalid sessions

## Error Handling

The component handles:
- Network errors
- Session expiration
- Invalid session IDs
- API endpoint failures

All errors are displayed to users via Material-UI Alert components.

## Performance Considerations

- Data fetching is debounced to prevent excessive API calls
- Session info refreshes every 30 seconds (configurable)
- Lazy loading for tab content
- Optimized re-renders with `useCallback` and `useMemo`

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Security

- HTTPS-only communication
- CORS-compliant requests
- No sensitive data in localStorage
- Session validation on every request
- Automatic session cleanup on expiration

## Development

### Running Locally

1. Ensure demo service is running:
   ```bash
   cd services/demo-service
   python main.py
   ```

2. Start React development server:
   ```bash
   npm start
   ```

3. Navigate to demo component:
   ```
   http://localhost:3000/demo
   ```

### Testing

```bash
# Run component tests
npm test DemoService

# Run with coverage
npm test -- --coverage --watchAll=false
```

## Troubleshooting

### "Failed to start demo session"
- Ensure demo service is running on correct port (8010)
- Check CORS configuration in demo service
- Verify SSL certificates for HTTPS

### "Session expired or invalid"
- Clear localStorage: `localStorage.removeItem('demo_session')`
- Restart demo service
- Check session timeout configuration

### Data not loading
- Check browser console for network errors
- Verify API endpoint URLs
- Ensure demo service has data generation enabled

## Future Enhancements

- [ ] Real-time updates via WebSocket
- [ ] Demo tour/walkthrough feature
- [ ] Screen recording for demos
- [ ] Shareable demo links
- [ ] Custom demo scenarios
- [ ] Multi-language support

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-repo/issues
- Documentation: https://docs.your-domain.com/demo-service
- Email: support@your-domain.com
