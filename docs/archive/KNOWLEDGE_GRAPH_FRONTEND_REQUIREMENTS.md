# Knowledge Graph Frontend Integration Requirements

**Date**: 2025-10-05
**Status**: Planning Phase
**Priority**: High

## 📋 Overview

The knowledge graph backend needs comprehensive frontend integration to visualize relationships, display learning paths, and enable interactive exploration of course dependencies.

---

## 🎯 Required Frontend Components

### 1. **Graph Visualization Component** (Priority: High)
**Purpose**: Interactive visualization of the knowledge graph

**Features Needed**:
- D3.js force-directed graph visualization
- Node types with different colors/shapes (courses, concepts, skills)
- Edge types with different line styles (prerequisite, teaches, builds_on)
- Zoom and pan controls
- Node click for details
- Edge weight visualization (line thickness)
- Search and filter capabilities
- Layout algorithms (force, hierarchical, circular)

**Users**: Students, Instructors, Org Admins

**Where Used**:
- Course catalog exploration
- Prerequisite visualization
- Curriculum planning dashboard
- Concept map browser

---

### 2. **Learning Path Display** (Priority: High)
**Purpose**: Show optimal learning paths from point A to B

**Features Needed**:
- Step-by-step path visualization
- Current position indicator for students
- Completed courses marked
- Upcoming courses highlighted
- Alternative path suggestions
- Estimated completion time
- Difficulty progression indicator
- Export to calendar/plan

**Users**: Students (primary), Instructors

**Where Used**:
- Student dashboard
- Course enrollment page
- Career path planning

---

### 3. **Prerequisite Checker Widget** (Priority: High)
**Purpose**: Show prerequisites for a course and student's readiness

**Features Needed**:
- Tree view of prerequisites
- Completed prerequisites (green checkmarks)
- Missing prerequisites (red X)
- Optional prerequisites (yellow warning)
- Alternative prerequisite paths
- "Enroll anyway" option with warning
- Recommended courses to take first

**Users**: Students, Instructors

**Where Used**:
- Course detail pages
- Enrollment workflow
- Student dashboard

---

### 4. **Concept Map Browser** (Priority: Medium)
**Purpose**: Explore relationships between concepts

**Features Needed**:
- Hierarchical topic/concept tree
- Collapsible/expandable nodes
- Concept dependency visualization
- Related concepts sidebar
- Courses that teach each concept
- Mastery level indicators (for students)
- Search within concept map

**Users**: Students, Instructors, Content Creators

**Where Used**:
- Learning resources section
- Course content planning
- Student progress tracking

---

### 5. **Skill Progression Tracker** (Priority: Medium)
**Purpose**: Visualize skill development across courses

**Features Needed**:
- Skill tree visualization
- Current skill levels
- Courses that develop each skill
- Skill gaps for target roles/certifications
- Recommended learning sequence
- Industry skill comparisons
- Achievement badges/milestones

**Users**: Students, Career Advisors

**Where Used**:
- Student profile/dashboard
- Career planning section
- Course recommendations

---

### 6. **Curriculum Builder (Admin)** (Priority: Medium)
**Purpose**: Visual tool for creating/editing the knowledge graph

**Features Needed**:
- Drag-and-drop node creation
- Connect nodes with edges
- Set edge weights and properties
- Batch import from CSV/JSON
- Validation (no cycles in prerequisites)
- Preview mode
- Export graph data
- Undo/redo functionality

**Users**: Org Admins, Instructors

**Where Used**:
- Admin dashboard
- Curriculum management section

---

### 7. **Related Content Sidebar** (Priority: Low)
**Purpose**: Show related courses/concepts based on graph relationships

**Features Needed**:
- "Students also took" (graph-based)
- "Similar courses" (graph similarity)
- "Next recommended" (path-based)
- "Alternative courses" (parallel paths)
- Compact list view
- Quick enrollment

**Users**: Students

**Where Used**:
- Course pages
- Student dashboard
- Search results

---

## 🏗️ Technical Architecture

### Frontend Stack:
- **Visualization**: D3.js v7
- **Graph Library**: vis-network or Cytoscape.js (evaluation needed)
- **UI Components**: Existing platform components
- **State Management**: Local state + API calls
- **API Client**: Fetch API with knowledge graph service

### Component Structure:
```
frontend/js/
├── knowledge-graph-client.js          # API client
├── components/
│   ├── graph-visualization.js         # Main graph viz
│   ├── learning-path-display.js       # Path visualization
│   ├── prerequisite-checker.js        # Prerequisites widget
│   ├── concept-map-browser.js         # Concept explorer
│   ├── skill-progression-tracker.js   # Skill tree
│   └── curriculum-builder.js          # Admin graph editor
└── utils/
    ├── graph-layout.js                # Layout algorithms
    ├── graph-utils.js                 # Utilities
    └── graph-styles.js                # Styling configs
```

---

## 🎨 Visual Design Patterns

### Node Colors by Type:
- **Courses**: Blue (#4285f4)
- **Topics**: Green (#34a853)
- **Concepts**: Orange (#fbbc04)
- **Skills**: Purple (#9c27b0)
- **Learning Outcomes**: Teal (#00bcd4)
- **Resources**: Gray (#757575)

### Edge Styles by Type:
- **Prerequisite**: Solid arrow, thick
- **Teaches**: Dashed line, medium
- **Builds On**: Dotted line, thin
- **Relates To**: Dotted line, very thin

### Edge Weight Visualization:
- Strong (0.8-1.0): Thick line, dark color
- Medium (0.5-0.8): Medium line, medium color
- Weak (0.0-0.5): Thin line, light color

---

## 📡 API Integration Points

### Knowledge Graph Service Endpoints (to be implemented):

1. **GET /api/v1/graph/visualize/courses**
   - Returns graph data for course visualization
   - Filters: organization, difficulty, category
   - Response: nodes[], edges[], metadata

2. **GET /api/v1/graph/visualize/concepts**
   - Returns concept map data
   - Filters: topic, domain
   - Response: hierarchical structure

3. **GET /api/v1/graph/paths/learning-path**
   - Query params: start_course, end_course, student_id
   - Returns: optimal path with alternatives

4. **GET /api/v1/graph/prerequisites/{course_id}**
   - Query params: student_id (optional)
   - Returns: prerequisite tree + student readiness

5. **GET /api/v1/graph/neighbors/{node_id}**
   - Query params: edge_types, depth, direction
   - Returns: connected nodes

6. **POST /api/v1/graph/nodes**
   - Admin endpoint for creating nodes
   - Body: node data

7. **POST /api/v1/graph/edges**
   - Admin endpoint for creating edges
   - Body: edge data

---

## 🔧 Implementation Priority

### Phase 1 (Week 1) - Essential Student Features:
1. **Learning Path Display** - Most valuable for students
2. **Prerequisite Checker** - Removes enrollment confusion
3. **Basic Graph Visualization** - Course dependency view

### Phase 2 (Week 2) - Enhanced Exploration:
4. **Concept Map Browser** - Deeper learning exploration
5. **Related Content Sidebar** - Discovery enhancement

### Phase 3 (Week 3) - Admin & Advanced:
6. **Curriculum Builder** - Admin graph management
7. **Skill Progression Tracker** - Career planning

---

## 💻 Code Examples

### Example 1: Learning Path Display
```javascript
// frontend/js/components/learning-path-display.js

class LearningPathDisplay {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
    }

    async displayPath(startCourseId, endCourseId, studentId) {
        const response = await fetch(
            `/api/v1/graph/paths/learning-path?` +
            `start=${startCourseId}&end=${endCourseId}&student=${studentId}`
        );
        const pathData = await response.json();

        this.renderPath(pathData);
    }

    renderPath(pathData) {
        // Render step-by-step path
        const pathHTML = pathData.path.map((course, index) => `
            <div class="path-step ${course.completed ? 'completed' : ''}
                                   ${course.current ? 'current' : ''}">
                <div class="step-number">${index + 1}</div>
                <div class="step-content">
                    <h4>${course.title}</h4>
                    <div class="step-meta">
                        <span class="difficulty ${course.difficulty}">
                            ${course.difficulty}
                        </span>
                        <span class="duration">${course.duration}h</span>
                    </div>
                </div>
                <div class="step-status">
                    ${course.completed ? '✓' : course.current ? '→' : ''}
                </div>
            </div>
        `).join('');

        this.container.innerHTML = `
            <div class="learning-path">
                <div class="path-header">
                    <h3>Your Learning Path</h3>
                    <div class="path-stats">
                        <span>${pathData.completed_courses}/${pathData.total_courses} completed</span>
                        <span>${pathData.estimated_time_remaining}h remaining</span>
                    </div>
                </div>
                <div class="path-steps">
                    ${pathHTML}
                </div>
            </div>
        `;
    }
}
```

### Example 2: Prerequisite Checker
```javascript
// frontend/js/components/prerequisite-checker.js

class PrerequisiteChecker {
    constructor(courseId, studentId) {
        this.courseId = courseId;
        this.studentId = studentId;
    }

    async checkPrerequisites() {
        const response = await fetch(
            `/api/v1/graph/prerequisites/${this.courseId}?student=${this.studentId}`
        );
        return await response.json();
    }

    async render(containerId) {
        const data = await this.checkPrerequisites();
        const container = document.getElementById(containerId);

        const prerequisitesHTML = data.prerequisites.map(prereq => `
            <div class="prerequisite-item ${prereq.status}">
                <span class="status-icon">
                    ${prereq.completed ? '✓' : prereq.in_progress ? '⟳' : '○'}
                </span>
                <span class="prereq-title">${prereq.title}</span>
                ${prereq.alternative ? `
                    <span class="alternative-badge">or ${prereq.alternative}</span>
                ` : ''}
            </div>
        `).join('');

        container.innerHTML = `
            <div class="prerequisite-checker">
                <div class="readiness-status ${data.ready ? 'ready' : 'not-ready'}">
                    <h4>${data.ready ? 'You\'re ready!' : 'Prerequisites needed'}</h4>
                    <p>${data.message}</p>
                </div>
                <div class="prerequisites-list">
                    <h5>Prerequisites:</h5>
                    ${prerequisitesHTML}
                </div>
                ${!data.ready && data.recommended_courses.length > 0 ? `
                    <div class="recommendations">
                        <h5>Recommended to take first:</h5>
                        ${data.recommended_courses.map(course => `
                            <a href="/course/${course.id}" class="recommended-course">
                                ${course.title}
                            </a>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
}
```

### Example 3: Graph Visualization
```javascript
// frontend/js/components/graph-visualization.js

class GraphVisualization {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            width: options.width || 800,
            height: options.height || 600,
            nodeRadius: options.nodeRadius || 30,
            ...options
        };
        this.svg = null;
        this.simulation = null;
    }

    async loadGraph(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(
            `/api/v1/graph/visualize/courses?${params}`
        );
        const graphData = await response.json();
        this.renderGraph(graphData);
    }

    renderGraph(data) {
        // D3.js force-directed graph
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height);

        // Create force simulation
        this.simulation = d3.forceSimulation(data.nodes)
            .force('link', d3.forceLink(data.edges).id(d => d.id))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(
                this.options.width / 2,
                this.options.height / 2
            ));

        // Render edges
        const link = this.svg.append('g')
            .selectAll('line')
            .data(data.edges)
            .enter().append('line')
            .attr('class', d => `edge edge-${d.type}`)
            .attr('stroke-width', d => d.weight * 3);

        // Render nodes
        const node = this.svg.append('g')
            .selectAll('circle')
            .data(data.nodes)
            .enter().append('circle')
            .attr('r', this.options.nodeRadius)
            .attr('class', d => `node node-${d.type}`)
            .call(this.drag(this.simulation))
            .on('click', (event, d) => this.onNodeClick(d));

        // Add labels
        const label = this.svg.append('g')
            .selectAll('text')
            .data(data.nodes)
            .enter().append('text')
            .text(d => d.label)
            .attr('class', 'node-label');

        // Update positions on simulation tick
        this.simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);

            label
                .attr('x', d => d.x)
                .attr('y', d => d.y - this.options.nodeRadius - 5);
        });
    }

    drag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }

    onNodeClick(node) {
        // Show node details in modal or sidebar
        console.log('Node clicked:', node);
    }
}
```

---

## 📱 Responsive Design Considerations

### Mobile Adaptations:
- Touch-friendly node sizes (min 44px)
- Simplified graph layouts for small screens
- Swipe gestures for navigation
- Collapsible sections
- Bottom sheet for node details

### Tablet Optimizations:
- Side-by-side graph and details
- Larger touch targets
- Stylus support for graph editing

---

## ♿ Accessibility Requirements

- **Keyboard Navigation**: All graph interactions accessible via keyboard
- **Screen Readers**: ARIA labels for nodes and edges
- **High Contrast**: Support for high contrast mode
- **Focus Indicators**: Clear focus states
- **Alternative Views**: List/table view option for screen reader users

---

## 🧪 Testing Requirements

### Unit Tests:
- Graph layout algorithms
- Data transformations
- Utility functions

### Integration Tests:
- API data fetching
- Graph rendering
- User interactions

### Visual Regression Tests:
- Graph layout consistency
- Theme support
- Responsive breakpoints

### Performance Tests:
- Large graphs (1000+ nodes)
- Animation smoothness
- Memory usage

---

## 📊 Success Metrics

### User Engagement:
- Graph visualization usage rate
- Learning path follow-through rate
- Prerequisite checker usage
- Time spent exploring graph

### Business Impact:
- Reduced prerequisite confusion (support tickets)
- Increased course discovery
- Higher completion rates
- Better learning path adherence

---

## 🔮 Future Enhancements

### Phase 4+:
- **AR/VR Visualization**: 3D graph exploration
- **Collaborative Graph Editing**: Real-time co-editing
- **AI-Powered Layouts**: ML-optimized graph layouts
- **Time-Based Graphs**: Animate graph evolution over time
- **Personalized Views**: Student-specific graph highlighting

---

## ✅ Implementation Checklist

### Phase 1 - Essential Components:
- [ ] Create knowledge-graph-client.js API wrapper
- [ ] Implement LearningPathDisplay component
- [ ] Implement PrerequisiteChecker component
- [ ] Create basic GraphVisualization with D3.js
- [ ] Add to student dashboard
- [ ] Add to course detail pages

### Phase 2 - Enhanced Features:
- [ ] Implement ConceptMapBrowser
- [ ] Add RelatedContentSidebar
- [ ] Create SkillProgressionTracker
- [ ] Add graph search/filter

### Phase 3 - Admin Tools:
- [ ] Implement CurriculumBuilder
- [ ] Add batch import functionality
- [ ] Create graph validation tools
- [ ] Build analytics dashboard

---

**Priority**: High - Frontend is critical for knowledge graph value
**Timeline**: 3 weeks (parallel with backend completion)
**Dependencies**: Knowledge graph API endpoints
