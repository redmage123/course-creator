# AI Tour Guide for Demo Player - Design Document

## Overview
Add an interactive AI assistant to the demo player that answers questions about the platform in real-time.

## Business Goals
1. **Reduce friction** - Answer common questions without requiring human sales contact
2. **Qualify leads** - Understand visitor needs through conversation
3. **Extend engagement** - Keep visitors on site longer
4. **Address gaps** - Answer "WHO/WHY/HOW MUCH/NEXT STEPS" questions identified in user evaluation

## User Experience

### Visual Design
- **Floating chat button** - Bottom right corner (standard pattern)
- **Slide-out panel** - Opens from right side, doesn't obstruct video
- **Always available** - Accessible during demo playback and after
- **Minimizable** - Users can dismiss and reopen anytime

### Interaction Flow
```
1. User watches demo
2. Has question → Clicks "Ask AI Guide" button
3. Chat panel slides in from right
4. User types question
5. AI responds with contextual answer
6. Follow-up questions encouraged
7. User can minimize or continue watching
```

## UI Components

### 1. Chat Trigger Button
```html
<button id="ai-tour-guide-trigger" class="ai-guide-btn">
    <svg><!-- AI icon --></svg>
    <span>Ask AI Guide</span>
    <span class="pulse-indicator"></span>
</button>
```

**Position:** Fixed bottom-right, above video controls
**Design:**
- Primary color with subtle glow
- Pulsing animation to draw attention
- Tooltip: "Have questions? Ask our AI guide!"

### 2. Chat Panel
```html
<div id="ai-tour-guide-panel" class="ai-guide-panel">
    <div class="ai-guide-header">
        <div class="ai-guide-avatar">🤖</div>
        <div class="ai-guide-info">
            <h3>AI Tour Guide</h3>
            <p class="status">Online • Instant responses</p>
        </div>
        <button class="close-btn">×</button>
    </div>

    <div class="ai-guide-messages" id="ai-guide-messages">
        <!-- Messages appear here -->
    </div>

    <div class="ai-guide-suggestions">
        <!-- Quick question buttons -->
    </div>

    <div class="ai-guide-input">
        <input type="text" placeholder="Ask anything about the platform...">
        <button class="send-btn">Send</button>
    </div>
</div>
```

**Design:**
- Width: 400px (desktop), 100% (mobile)
- Height: 600px max
- Smooth slide-in animation (0.3s ease)
- Frosted glass effect background
- Rounded corners, modern shadow

### 3. Message Types

**AI Welcome Message (auto-sent on open):**
```
👋 Hi! I'm your AI tour guide. I can answer questions about:
• Who this platform is for
• Key features and capabilities
• AI-powered course development
• Integrations (Zoom, Teams, Slack)
• Getting started

What would you like to know?
```

**Quick Suggestion Buttons:**
```
[Who is this for?]
[How does AI help?]
[What integrations exist?]
[Can I try it?]
[How do I get started?]
```

**User Message:**
- Right-aligned
- Blue background
- User avatar (generic icon)

**AI Response:**
- Left-aligned
- Light gray background
- AI avatar (robot icon)
- Typing indicator before response

## Backend Integration

### Option 1: Use Existing RAG Service (RECOMMENDED)
**Endpoint:** `https://localhost:8007/api/v1/rag/query`

**Advantages:**
- Already has context about the platform
- Can reference documentation
- Intelligent, not scripted responses
- Maintains conversation context

**Knowledge Base Setup:**
```
Create demo_tour_guide_knowledge.md with:
- Target audience (corporate training, individual instructors)
- Key features (AI course generation, analytics, integrations)
- Platform capabilities (browser IDEs, quiz generation)
- Integrations (Zoom, Teams, Slack)
- Getting started process
- Development status (beta, no pricing yet)
```

### Option 2: Simple Pattern Matching (Fallback)
If RAG service unavailable, use keyword matching:

```javascript
const FAQ_RESPONSES = {
    'who|audience|for whom': 'Course Creator Platform is built for corporate training teams and professional instructors...',
    'ai|artificial intelligence|automation': 'Our AI handles course structure generation, content drafting, quiz creation...',
    'price|cost|pricing': 'The platform is currently in development. Pricing will be announced soon...',
    'integration|zoom|teams|slack': 'We integrate seamlessly with Zoom and Teams for live sessions, Slack for notifications...',
    // ... more patterns
};
```

## Technical Implementation

### Frontend JavaScript
```javascript
class AITourGuide {
    constructor() {
        this.panel = document.getElementById('ai-tour-guide-panel');
        this.messages = document.getElementById('ai-guide-messages');
        this.isOpen = false;
        this.conversationHistory = [];
    }

    async sendMessage(userMessage) {
        this.addMessage('user', userMessage);
        this.showTypingIndicator();

        const response = await fetch('https://localhost:8007/api/v1/rag/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: userMessage,
                context: 'demo_tour_guide',
                conversation_history: this.conversationHistory
            })
        });

        const data = await response.json();
        this.hideTypingIndicator();
        this.addMessage('ai', data.answer);

        this.conversationHistory.push({
            user: userMessage,
            ai: data.answer
        });
    }

    addMessage(type, content) {
        const messageEl = document.createElement('div');
        messageEl.className = `ai-guide-message ${type}-message`;
        messageEl.innerHTML = `
            <div class="message-avatar">${type === 'ai' ? '🤖' : '👤'}</div>
            <div class="message-content">${this.formatMessage(content)}</div>
        `;
        this.messages.appendChild(messageEl);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Convert markdown to HTML
        // Add links, emphasis, code blocks
        return marked.parse(content);
    }
}
```

### Styling (CSS)
```css
.ai-guide-btn {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 50px;
    padding: 12px 24px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
    transition: all 0.3s ease;
    z-index: 1000;
}

.ai-guide-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 30px rgba(99, 102, 241, 0.6);
}

.pulse-indicator {
    position: absolute;
    top: 5px;
    right: 5px;
    width: 12px;
    height: 12px;
    background: #10b981;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
}

.ai-guide-panel {
    position: fixed;
    right: 0;
    top: 0;
    width: 400px;
    height: 100vh;
    background: rgba(255, 255, 255, 0.98);
    backdrop-filter: blur(10px);
    box-shadow: -4px 0 30px rgba(0, 0, 0, 0.1);
    transform: translateX(100%);
    transition: transform 0.3s ease;
    z-index: 1001;
    display: flex;
    flex-direction: column;
}

.ai-guide-panel.open {
    transform: translateX(0);
}

.ai-guide-header {
    padding: 20px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    gap: 12px;
}

.ai-guide-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.ai-guide-message {
    display: flex;
    gap: 12px;
    max-width: 85%;
}

.user-message {
    align-self: flex-end;
    flex-direction: row-reverse;
}

.message-content {
    background: #f3f4f6;
    padding: 12px 16px;
    border-radius: 16px;
    font-size: 14px;
    line-height: 1.5;
}

.user-message .message-content {
    background: #6366f1;
    color: white;
}

.ai-guide-suggestions {
    padding: 12px 20px;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.suggestion-btn {
    background: white;
    border: 1px solid #e5e7eb;
    padding: 8px 16px;
    border-radius: 20px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.suggestion-btn:hover {
    background: #f3f4f6;
    border-color: #6366f1;
}

.ai-guide-input {
    padding: 20px;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
    display: flex;
    gap: 12px;
}

.ai-guide-input input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid #e5e7eb;
    border-radius: 24px;
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s ease;
}

.ai-guide-input input:focus {
    border-color: #6366f1;
}
```

## Sample Conversations

### Conversation 1: Who is this for?
```
User: Who is this platform for?

AI: Course Creator Platform is designed for two primary audiences:

1. **Corporate Training Teams** - Organizations that need to quickly develop and deploy technical training programs for their employees. Our AI-powered course generation and browser-based IDEs (VSCode, PyCharm, JupyterLab) make it perfect for software development and IT training.

2. **Professional Instructors** - Independent teachers and subject matter experts who want to create and sell courses without the technical complexity. Our AI handles the heavy lifting while you focus on your expertise.

Both groups benefit from seamless integrations with Zoom, Microsoft Teams, and Slack, making it easy to incorporate into existing workflows.

Does one of these sound like you? I can provide more specific information based on your needs.
```

### Conversation 2: AI Features
```
User: How does the AI help with course creation?

AI: Great question! Our AI accelerates course development in several ways:

**Course Structure Generation:**
- Describe your topic and target audience
- AI generates complete course outline with modules and learning objectives
- You review and refine (saves days of curriculum planning)

**Content Creation:**
- AI drafts lesson content based on your topics
- Suggests quiz questions (multiple choice, code challenges, scenarios)
- You add your expertise and real-world examples

**Intelligent Analytics:**
- AI identifies at-risk students automatically
- Surfaces engagement patterns across courses
- Recommends quiz difficulty adjustments

Think of it as having an instructional designer, content writer, and data analyst working 24/7. You guide the direction, AI handles the time-consuming work.

What type of courses are you thinking about creating?
```

### Conversation 3: Getting Started
```
User: How do I get started?

AI: The platform is currently in active development (beta phase), so here's what you can do:

**Right now:**
1. Explore this interactive demo to see all features
2. Ask me any questions you have
3. Note any specific features important to you

**When we launch:**
1. Create your organization (takes ~60 seconds)
2. Set up your first course using AI assistance
3. Invite instructors or start teaching immediately

**Want to stay updated?**
I can connect you with our team to be notified when we launch and potentially participate in early access.

Are you looking to build courses for a specific topic or industry?
```

## Analytics & Tracking

Track user interactions with AI guide:
```javascript
{
    event: 'ai_guide_interaction',
    demo_slide: 5, // Which slide user was watching
    question_asked: 'How does AI help?',
    conversation_length: 3, // Number of exchanges
    time_spent: 120, // Seconds in conversation
    suggested_vs_typed: 'typed' // How question was asked
}
```

## Mobile Responsiveness

```css
@media (max-width: 768px) {
    .ai-guide-panel {
        width: 100%;
        height: 80vh;
        bottom: 0;
        top: auto;
        border-radius: 20px 20px 0 0;
    }

    .ai-guide-btn {
        bottom: 10px;
        right: 10px;
        padding: 10px 20px;
        font-size: 14px;
    }
}
```

## Success Metrics

1. **Engagement Rate:** % of demo viewers who open AI guide
2. **Question Count:** Average questions per session
3. **Conversation Length:** Time spent chatting
4. **Common Questions:** Track frequent queries to improve narrations
5. **Conversion Rate:** Users who ask about "getting started" or "pricing"

## Future Enhancements

1. **Proactive Suggestions:** AI offers help based on demo progress
   - After Slide 5: "Want to know more about AI course generation?"
   - After Slide 9: "Curious about setting up browser IDEs?"

2. **Lead Capture:** Seamless transition to contact form
   - "Would you like me to connect you with our team?"
   - Collect email for launch notification

3. **Screen Sharing:** AI guide references specific demo moments
   - "Let me rewind to Slide 6 where we showed that feature"

4. **Voice Interaction:** Optional voice input/output

5. **Multi-language:** Support for non-English demos

---

## Implementation Priority

**Phase 1 (MVP):**
- [x] Design chat UI components
- [ ] Integrate with RAG service
- [ ] Add to demo-player.html
- [ ] Test with common questions
- [ ] Deploy and monitor

**Phase 2 (Enhanced):**
- [ ] Add proactive suggestions
- [ ] Lead capture integration
- [ ] Analytics dashboard
- [ ] A/B test different AI personalities

**Phase 3 (Advanced):**
- [ ] Voice interaction
- [ ] Multi-language support
- [ ] Screen sharing/demo navigation

---

**Status:** Ready for implementation
**Estimated Dev Time:** 8-12 hours for Phase 1
**Dependencies:** RAG service (port 8007), demo-player.html
