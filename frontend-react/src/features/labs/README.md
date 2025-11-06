# Lab Environment - React Implementation

## Overview

Comprehensive React-based lab environment interface for the Course Creator Platform, providing students with an interactive, multi-IDE coding environment with real-time collaboration, AI assistance, and resource monitoring.

## Architecture

### Component Hierarchy

```
LabEnvironment (Main Container)
├── IDESelector (IDE type switcher)
├── LabControls (Session controls)
├── FileExplorer (File tree sidebar)
├── CodeEditor (Monaco Editor)
├── TerminalEmulator (xterm.js)
├── ResourceMonitor (Usage metrics)
└── AIAssistant (Chat interface)
```

### Custom Hooks

- **useLabSession**: Lab session lifecycle management
- **useFileSystem**: File CRUD operations
- **useTerminal**: Command execution and history

### Services

- **labService**: Centralized API client for lab-manager service (port 8005)

## Features

### Multi-IDE Support
- **VSCode Mode**: Monaco Editor with IntelliSense, syntax highlighting
- **Jupyter Mode**: Interactive notebook interface (iframe)
- **Terminal Mode**: Full terminal emulator with xterm.js

### File Management
- Create, open, save, delete, rename files
- Folder creation and organization
- File modification tracking
- Auto-save functionality
- Language detection from file extension

### Terminal Emulator
- Command execution in Docker container
- Command history (up/down arrows)
- Output streaming
- Clear screen (Ctrl+L)
- Copy/paste support
- Multi-line input

### Code Editor
- Monaco Editor (VSCode engine)
- Syntax highlighting for 10+ languages
- IntelliSense and autocomplete
- Keyboard shortcuts (Ctrl+S save, Ctrl+Enter run)
- Theme customization (VS Dark, Light, High Contrast)
- Read-only mode when lab stopped

### Resource Monitoring
- Real-time CPU, memory, disk usage
- Network I/O tracking (optional)
- Session time tracking
- Usage level indicators (normal/warning/critical)
- Resource alerts for high usage

### AI Assistant
- Context-aware help (current file, code, errors)
- Quick actions (explain code, debug error, improve code, get hint)
- Chat history
- Code explanation and suggestions
- Error debugging assistance

### Session Management
- Start, pause, resume, stop lab
- WebSocket for real-time updates
- Resource usage tracking
- Auto-reconnection on page refresh

### Keyboard Shortcuts
- `Ctrl+S`: Save current file
- `Ctrl+Enter`: Run code
- `Ctrl+B`: Toggle file explorer
- `Ctrl+\``: Toggle terminal
- `Ctrl+L`: Clear terminal
- Up/Down arrows: Terminal history

### Accessibility
- WCAG 2.1 AA compliant
- Keyboard navigation support
- ARIA labels and roles
- Focus indicators
- High contrast mode support
- Screen reader friendly

### Responsive Design
- Mobile-friendly layout
- Breakpoints at 768px and 1024px
- Touch-optimized controls
- Collapsible panels on mobile

## Technology Stack

### Core
- React 19.1.1
- TypeScript 5.9.3
- CSS Modules

### Editor & Terminal
- @monaco-editor/react (Monaco Editor)
- @xterm/xterm (Terminal emulator)
- @xterm/addon-fit (Terminal resize)
- @xterm/addon-web-links (Terminal URL support)

### State Management
- React Hooks (useState, useEffect, useCallback, useRef)
- Custom hooks for business logic
- WebSocket for real-time updates

## API Integration

### Lab Manager Service (Port 8005)

Base URL: `https://176.9.99.103:8005/api/v1/labs`

#### Session Endpoints
- `GET /session?labId={id}&courseId={id}` - Check existing session
- `POST /start` - Start lab session
- `POST /{sessionId}/pause` - Pause session
- `POST /{sessionId}/resume` - Resume session
- `POST /{sessionId}/stop` - Stop session
- `GET /{sessionId}/resources` - Get resource usage

#### File System Endpoints
- `GET /{sessionId}/files` - List files
- `GET /{sessionId}/files/{fileId}` - Get file
- `POST /{sessionId}/files` - Create file
- `PUT /{sessionId}/files/{fileId}` - Update file
- `DELETE /{sessionId}/files/{fileId}` - Delete file
- `PATCH /{sessionId}/files/{fileId}/rename` - Rename file
- `POST /{sessionId}/folders` - Create folder

#### Terminal Endpoints
- `POST /{sessionId}/execute` - Execute command
- `GET /{sessionId}/history` - Get command history

#### AI Assistant Endpoints
- `POST /{sessionId}/ai/chat` - Send message
- `GET /{sessionId}/ai/history` - Get chat history
- `POST /{sessionId}/ai/explain` - Explain code
- `POST /{sessionId}/ai/debug` - Debug error

#### Analytics Endpoints
- `POST /{sessionId}/analytics/event` - Track event
- `GET /{sessionId}/analytics` - Get analytics summary

### WebSocket Connection
- URL: `wss://176.9.99.103:8005/ws/lab/{sessionId}`
- Real-time status updates
- Resource usage updates
- Session updates

## File Structure

```
src/features/labs/
├── LabEnvironment.tsx              # Main container component
├── LabEnvironment.module.css       # Container styles
├── components/
│   ├── index.ts                    # Component exports
│   ├── FileExplorer.tsx
│   ├── FileExplorer.module.css
│   ├── CodeEditor.tsx
│   ├── CodeEditor.module.css
│   ├── TerminalEmulator.tsx
│   ├── TerminalEmulator.module.css
│   ├── IDESelector.tsx
│   ├── IDESelector.module.css
│   ├── LabControls.tsx
│   ├── LabControls.module.css
│   ├── ResourceMonitor.tsx
│   ├── ResourceMonitor.module.css
│   ├── AIAssistant.tsx
│   └── AIAssistant.module.css
├── hooks/
│   ├── index.ts                    # Hook exports
│   ├── useLabSession.ts
│   ├── useFileSystem.ts
│   └── useTerminal.ts
├── services/
│   └── labService.ts               # API client
└── README.md                       # This file
```

## Routes

### Lab Environment Route
```typescript
<Route
  path="/labs/:labId/course/:courseId"
  element={
    <ProtectedRoute requiredRoles={['student']}>
      <LabEnvironment />
    </ProtectedRoute>
  }
/>
```

**Access**: Students only
**URL Pattern**: `/labs/{labId}/course/{courseId}`

## Usage Example

```typescript
// Navigate to lab
navigate(`/labs/${labId}/course/${courseId}`);

// Lab will automatically:
// 1. Check for existing session
// 2. Load files if session exists
// 3. Connect to WebSocket
// 4. Start monitoring resources
```

## Testing

### E2E Tests
Comprehensive Selenium test suite at:
`/home/bbrelin/course-creator/tests/e2e/test_lab_interface_complete.py`

**Coverage**: 80+ test methods across:
- Lab environment initialization
- Multi-IDE support
- Lab lifecycle operations
- File system operations
- Terminal emulator
- Code execution
- Lab persistence
- Resource management
- AI assistant integration
- Lab analytics

### Run Tests
```bash
# Run all lab tests
HEADLESS=true TEST_BASE_URL=https://localhost:3000 pytest tests/e2e/test_lab_interface_complete.py -v

# Run specific test class
pytest tests/e2e/test_lab_interface_complete.py::TestLabEnvironmentInitialization -v
```

## Development

### Local Development
```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Type check
npm run type-check

# Lint
npm run lint

# Format
npm run format
```

### Adding New Features

1. **New Component**: Create in `components/` with corresponding CSS module
2. **New Hook**: Create in `hooks/` and export in `hooks/index.ts`
3. **New API Endpoint**: Add to `services/labService.ts`
4. **Update Main Component**: Import and integrate in `LabEnvironment.tsx`

## Styling Guidelines

### Color Scheme (VSCode-inspired Dark Theme)
- Background: `#1e1e1e`
- Panels: `#2d2d30`
- Borders: `#3e3e42`
- Accent: `#007acc`
- Text: `#cccccc`
- Highlights: `#ffffff`

### Responsive Breakpoints
- Desktop: 1024px+
- Tablet: 768px - 1023px
- Mobile: < 768px

### Naming Convention
- CSS Modules: `ComponentName.module.css`
- BEM-style class names: `.componentName`, `.componentName__element`, `.componentName--modifier`

## Security Considerations

1. **Authentication**: All API requests include credentials
2. **HTTPS Only**: All endpoints use HTTPS
3. **Session Management**: Sessions tied to authenticated user
4. **Container Isolation**: Each lab runs in isolated Docker container
5. **Resource Limits**: CPU/memory/disk quotas enforced
6. **Code Execution**: Sandboxed in Docker container
7. **WebSocket Security**: WSS (WebSocket Secure) only

## Performance Optimizations

1. **Code Splitting**: Lab components lazy-loaded
2. **Memoization**: useCallback, useMemo for expensive operations
3. **Debouncing**: File auto-save debounced
4. **Virtual Scrolling**: File list and terminal output
5. **WebSocket**: Real-time updates without polling
6. **Monaco Editor**: Lazy-loaded on-demand
7. **CSS Modules**: Scoped styles with minimal bundle size

## Accessibility Features

1. **Keyboard Navigation**: Full keyboard support
2. **ARIA Labels**: All interactive elements labeled
3. **Focus Management**: Logical tab order
4. **Screen Reader**: Descriptive text for all controls
5. **High Contrast**: System preference detection
6. **Reduced Motion**: Respects user preference
7. **Color Contrast**: WCAG AAA compliant

## Known Limitations

1. **Browser Support**: Modern browsers only (ES6+)
2. **Mobile Experience**: Best on tablet/desktop
3. **WebSocket**: Requires stable connection
4. **Resource Monitoring**: 2-second update interval
5. **File Size**: Large files (>5MB) may impact performance
6. **Concurrent Users**: Limited by server resources

## Future Enhancements

1. **Collaborative Editing**: Real-time multi-user editing
2. **Video Integration**: Embedded video tutorials
3. **Debugger Integration**: Step-through debugging
4. **Git Integration**: Version control in labs
5. **Extension System**: Custom lab extensions
6. **Offline Mode**: Local development fallback
7. **Performance Profiling**: Built-in profiler
8. **Custom Themes**: User-selectable themes

## Troubleshooting

### Lab Won't Start
1. Check backend services (port 8005)
2. Verify authentication token
3. Check browser console for errors
4. Ensure Docker is running

### Editor Not Loading
1. Check Monaco Editor CDN
2. Clear browser cache
3. Verify network connectivity
4. Check for CSP violations

### Terminal Not Working
1. Verify WebSocket connection
2. Check for connection errors
3. Ensure xterm.js loaded
4. Test with simple commands

### Files Not Saving
1. Check session status
2. Verify write permissions
3. Check for API errors
4. Test network connectivity

## Support

For issues or questions:
- Create GitHub issue
- Check E2E test suite for examples
- Review API documentation
- Contact platform administrators

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
**Status**: Production Ready
