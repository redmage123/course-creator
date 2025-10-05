/**
 * AI Assistant Module - Context-Aware Chatbot with RAG and Web Search
 *
 * BUSINESS CONTEXT:
 * Provides an intelligent AI assistant that adapts to the current creation context
 * (projects, courses, slides, labs, exercises, quizzes). Includes web search
 * capabilities to research information and populate the RAG knowledge base.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Context detection based on current UI state
 * - Web search integration for research
 * - RAG database population from web results
 * - Conversation history management
 * - Multi-modal support (text, code, diagrams)
 *
 * @module ai-assistant
 */

import { showNotification, escapeHtml } from './org-admin-utils.js';
import { getAuthHeaders } from './org-admin-api.js';

// Context types
export const CONTEXT_TYPES = {
    PROJECT_CREATION: 'project_creation',
    COURSE_CREATION: 'course_creation',
    SLIDE_CREATION: 'slide_creation',
    LAB_CREATION: 'lab_creation',
    EXERCISE_CREATION: 'exercise_creation',
    QUIZ_CREATION: 'quiz_creation',
    GENERAL: 'general'
};

// Current context state
let currentContext = {
    type: CONTEXT_TYPES.GENERAL,
    data: {},
    conversationHistory: [],
    ragContext: null
};

/**
 * Initialize AI Assistant with context
 *
 * BUSINESS CONTEXT:
 * Sets up the AI assistant for a specific creation mode with relevant context data
 *
 * @param {string} contextType - Type of context (from CONTEXT_TYPES)
 * @param {Object} contextData - Context-specific data
 */
export function initializeAIAssistant(contextType, contextData = {}) {
    console.log('🤖 Initializing AI Assistant with context:', contextType);

    currentContext = {
        type: contextType,
        data: contextData,
        conversationHistory: [],
        ragContext: null
    };

    // Add system prompt based on context
    const systemPrompt = getContextSystemPrompt(contextType);
    currentContext.conversationHistory.push({
        role: 'system',
        content: systemPrompt
    });

    console.log('✅ AI Assistant initialized for:', contextType);
}

/**
 * Get system prompt based on context type
 *
 * BUSINESS CONTEXT:
 * Provides context-specific instructions to the AI to guide its behavior
 *
 * @param {string} contextType - Type of context
 * @returns {string} System prompt
 */
function getContextSystemPrompt(contextType) {
    const prompts = {
        [CONTEXT_TYPES.PROJECT_CREATION]: `
You are an AI assistant helping to create a training project. Your role is to:
- Suggest appropriate learning tracks and structure
- Recommend learning objectives aligned with target roles
- Estimate realistic timelines and resource requirements
- Leverage existing course content from the RAG knowledge base
- Research industry best practices via web search when needed
- Help organize content into progressive learning paths

Context: Project creation wizard
`,
        [CONTEXT_TYPES.COURSE_CREATION]: `
You are an AI assistant helping to create educational course content. Your role is to:
- Design comprehensive course structures and modules
- Suggest pedagogically sound learning sequences
- Recommend appropriate content types (slides, labs, exercises, quizzes)
- Ensure alignment with learning objectives
- Research current industry standards and technologies
- Leverage RAG knowledge base for similar successful courses

Context: Course creation and content design
`,
        [CONTEXT_TYPES.SLIDE_CREATION]: `
You are an AI assistant helping to create presentation slides. Your role is to:
- Suggest clear, concise slide content
- Recommend effective visual layouts and diagrams
- Ensure information hierarchy and flow
- Provide examples and code snippets when relevant
- Research current examples and best practices
- Follow instructional design principles

Context: Slide deck creation
`,
        [CONTEXT_TYPES.LAB_CREATION]: `
You are an AI assistant helping to create hands-on lab exercises. Your role is to:
- Design practical, scenario-based lab activities
- Suggest appropriate tools and environments
- Create step-by-step instructions
- Define clear success criteria and validation steps
- Research real-world use cases and scenarios
- Ensure labs match learner skill levels

Context: Lab exercise creation
`,
        [CONTEXT_TYPES.EXERCISE_CREATION]: `
You are an AI assistant helping to create practice exercises. Your role is to:
- Design exercises that reinforce learning objectives
- Suggest appropriate difficulty levels
- Provide detailed solution approaches
- Create variations for different skill levels
- Research industry-standard problems and patterns
- Ensure exercises build practical skills

Context: Exercise and practice problem creation
`,
        [CONTEXT_TYPES.QUIZ_CREATION]: `
You are an AI assistant helping to create quiz questions and assessments. Your role is to:
- Design effective multiple-choice, true/false, and open-ended questions
- Ensure questions test understanding, not just memorization
- Suggest appropriate difficulty distribution
- Provide clear explanations for correct answers
- Research common misconceptions to address
- Align questions with learning objectives

Context: Quiz and assessment creation
`,
        [CONTEXT_TYPES.GENERAL]: `
You are a helpful AI assistant for a course creation platform. You can help with:
- Answering questions about platform features
- Providing guidance on course design
- Researching educational content and best practices
- Suggesting improvements to learning materials
`
    };

    return prompts[contextType] || prompts[CONTEXT_TYPES.GENERAL];
}

/**
 * Send message to AI assistant with context awareness
 *
 * BUSINESS CONTEXT:
 * Processes user messages with full context awareness, RAG integration,
 * and optional web search capabilities
 *
 * @param {string} userMessage - User's message
 * @param {Object} options - Options for message processing
 * @returns {Promise<Object>} AI response with metadata
 */
export async function sendContextAwareMessage(userMessage, options = {}) {
    console.log('💬 Processing context-aware message:', {
        context: currentContext.type,
        message: userMessage.substring(0, 50) + '...'
    });

    // Add user message to history
    currentContext.conversationHistory.push({
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
    });

    try {
        // Step 0: NLP Preprocessing (NEW - Intent classification, entity extraction, query expansion)
        console.log('🧠 Running NLP preprocessing...');
        const nlpResult = await preprocessQuery(userMessage, currentContext);

        console.log('📊 NLP Preprocessing Results:', {
            intent: nlpResult.intent.intent_type,
            should_call_llm: nlpResult.should_call_llm,
            entities: nlpResult.entities.length,
            expansions: nlpResult.expanded_query?.expansions?.length || 0
        });

        // Check if we can bypass LLM with direct response
        if (!nlpResult.should_call_llm && nlpResult.direct_response) {
            console.log('⚡ Using direct response (bypassing LLM):', nlpResult.direct_response.type);
            return handleDirectResponse(nlpResult, userMessage);
        }

        // Step 1: Check if web search is needed
        const needsWebSearch = detectWebSearchIntent(userMessage);
        let webSearchResults = null;

        if (needsWebSearch || options.forceWebSearch) {
            console.log('🔍 Web search detected/requested');
            webSearchResults = await performWebSearch(userMessage);

            // Add web search results to RAG database
            if (webSearchResults && webSearchResults.results.length > 0) {
                await addWebResultsToRAG(webSearchResults, currentContext.type);
            }
        }

        // Step 2: Query RAG for relevant context (use expanded query for better recall)
        console.log('📚 Querying RAG knowledge base...');
        const searchQuery = nlpResult.expanded_query?.combined || userMessage;
        const ragContext = await queryRAGWithContext(searchQuery, currentContext, nlpResult);

        // Step 2.5: Query metadata service with fuzzy search for additional context
        console.log('🔍 Querying metadata service with fuzzy search...');
        const metadataContext = await queryMetadataWithFuzzySearch(userMessage, currentContext);

        // Step 2.6: Query knowledge graph for relationships and learning paths
        console.log('🕸️ Querying knowledge graph for relationships...');
        const knowledgeGraphContext = await queryKnowledgeGraph(userMessage, currentContext, metadataContext);

        // Step 3: Build context-aware prompt
        const enhancedPrompt = buildContextAwarePrompt(
            userMessage,
            currentContext,
            ragContext,
            metadataContext,
            knowledgeGraphContext,
            webSearchResults
        );

        // Step 4: Call AI service
        console.log('🤖 Calling AI service...');
        const aiResponse = await callAIService(enhancedPrompt, currentContext);

        // Add AI response to history
        currentContext.conversationHistory.push({
            role: 'assistant',
            content: aiResponse.message,
            timestamp: new Date().toISOString(),
            metadata: aiResponse.metadata
        });

        return {
            message: aiResponse.message,
            suggestions: aiResponse.suggestions || [],
            actions: aiResponse.actions || [],
            webSearchUsed: needsWebSearch || options.forceWebSearch,
            ragSources: ragContext?.sources || [],
            metadata: aiResponse.metadata || {}
        };

    } catch (error) {
        console.error('❌ Error processing AI message:', error);
        throw error;
    }
}

/**
 * Detect if user message requires web search
 *
 * BUSINESS CONTEXT:
 * Identifies when the AI needs current information from the web
 * vs. when it can rely on existing knowledge base
 *
 * @param {string} message - User message
 * @returns {boolean} True if web search needed
 */
function detectWebSearchIntent(message) {
    const webSearchKeywords = [
        'research',
        'find out',
        'look up',
        'search for',
        'what\'s new',
        'current',
        'latest',
        'recent',
        'industry standard',
        'best practice',
        'example',
        'how do companies',
        'real-world'
    ];

    const lowerMessage = message.toLowerCase();
    return webSearchKeywords.some(keyword => lowerMessage.includes(keyword));
}

/**
 * Perform web search for research
 *
 * BUSINESS CONTEXT:
 * Searches the web for current information, examples, and best practices
 * to enhance AI responses and populate RAG database
 *
 * TECHNICAL IMPLEMENTATION:
 * Calls web search API (e.g., Brave Search, Google Custom Search)
 *
 * @param {string} query - Search query
 * @returns {Promise<Object>} Search results
 */
async function performWebSearch(query) {
    try {
        console.log('🌐 Performing web search:', query);

        // TODO: Replace with actual web search API
        // const response = await fetch('https://localhost:8011/api/v1/web-search', {
        //     method: 'POST',
        //     headers: await getAuthHeaders(),
        //     body: JSON.stringify({
        //         query: query,
        //         num_results: 5,
        //         safe_search: true
        //     })
        // });

        // Mock web search results
        const mockResults = {
            query: query,
            results: [
                {
                    title: 'Industry Best Practices Guide 2025',
                    url: 'https://example.com/best-practices-2025',
                    snippet: 'Comprehensive guide to current industry standards and methodologies...',
                    relevance: 0.95
                },
                {
                    title: 'Real-World Implementation Examples',
                    url: 'https://example.com/examples',
                    snippet: 'Case studies and practical examples from leading organizations...',
                    relevance: 0.88
                },
                {
                    title: 'Tutorial: Step-by-Step Implementation',
                    url: 'https://example.com/tutorial',
                    snippet: 'Detailed tutorial with code examples and explanations...',
                    relevance: 0.82
                }
            ],
            metadata: {
                search_time_ms: 234,
                total_results: 156000
            }
        };

        console.log('✅ Web search completed:', mockResults.results.length, 'results');
        return mockResults;

    } catch (error) {
        console.error('❌ Web search error:', error);
        return null;
    }
}

/**
 * Add web search results to RAG database
 *
 * BUSINESS CONTEXT:
 * Populates the RAG knowledge base with researched information
 * to improve future AI responses and build institutional knowledge
 *
 * @param {Object} searchResults - Web search results
 * @param {string} contextType - Current context type
 * @returns {Promise<void>}
 */
async function addWebResultsToRAG(searchResults, contextType) {
    try {
        console.log('📥 Adding web results to RAG database...');

        // Map context types to RAG domains
        const domainMap = {
            [CONTEXT_TYPES.PROJECT_CREATION]: 'content_generation',
            [CONTEXT_TYPES.COURSE_CREATION]: 'content_generation',
            [CONTEXT_TYPES.SLIDE_CREATION]: 'content_generation',
            [CONTEXT_TYPES.LAB_CREATION]: 'lab_assistant',
            [CONTEXT_TYPES.EXERCISE_CREATION]: 'lab_assistant',
            [CONTEXT_TYPES.QUIZ_CREATION]: 'content_generation',
            [CONTEXT_TYPES.GENERAL]: 'content_generation'
        };

        const domain = domainMap[contextType] || 'content_generation';

        // Add each web result as a document to RAG
        for (const result of searchResults.results) {
            const content = `${result.title}\n\n${result.snippet}`;

            const response = await fetch('https://localhost:8009/api/v1/rag/add-document', {
                method: 'POST',
                headers: await getAuthHeaders(),
                body: JSON.stringify({
                    content: content,
                    domain: domain,
                    source: 'web_search',
                    metadata: {
                        type: 'web_search_result',
                        title: result.title,
                        url: result.url,
                        context_type: contextType,
                        relevance: result.relevance,
                        search_query: searchResults.query,
                        timestamp: new Date().toISOString()
                    }
                })
            });

            if (!response.ok) {
                console.warn('⚠️ Failed to add document to RAG:', response.status);
            }
        }

        console.log('✅ Web results added to RAG database:', searchResults.results.length, 'documents');

    } catch (error) {
        console.error('❌ Error adding web results to RAG:', error);
    }
}

/**
 * Query RAG with context awareness
 *
 * BUSINESS CONTEXT:
 * Retrieves relevant information from RAG database based on
 * current context (project, course, lab, etc.)
 *
 * @param {string} query - Query text
 * @param {Object} context - Current context
 * @returns {Promise<Object>} RAG results with sources
 */
async function queryRAGWithContext(query, context, nlpResult = null) {
    try {
        console.log('📚 Querying RAG with context:', context.type);

        // Map context types to RAG domains
        const domainMap = {
            [CONTEXT_TYPES.PROJECT_CREATION]: 'content_generation',
            [CONTEXT_TYPES.COURSE_CREATION]: 'content_generation',
            [CONTEXT_TYPES.SLIDE_CREATION]: 'content_generation',
            [CONTEXT_TYPES.LAB_CREATION]: 'lab_assistant',
            [CONTEXT_TYPES.EXERCISE_CREATION]: 'lab_assistant',
            [CONTEXT_TYPES.QUIZ_CREATION]: 'content_generation',
            [CONTEXT_TYPES.GENERAL]: 'content_generation'
        };

        const domain = domainMap[context.type] || 'content_generation';

        // Build metadata filter from context data
        const metadataFilter = {
            context_type: context.type
        };

        // Add organization ID if available
        if (context.data.organizationId) {
            metadataFilter.organization_id = context.data.organizationId;
        }

        // Use hybrid search for better retrieval accuracy
        const response = await fetch('https://localhost:8009/api/v1/rag/hybrid-search', {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify({
                query: query,
                domain: domain,
                n_results: 5,
                metadata_filter: metadataFilter
            })
        });

        if (!response.ok) {
            console.warn('⚠️ RAG service responded with:', response.status);
            // Fall back to mock data on error
            return getContextSpecificRAGResults(context.type, query);
        }

        const ragResults = await response.json();

        // Transform RAG service results to expected format
        const sources = ragResults.results?.map(result => ({
            type: result.metadata?.type || 'knowledge_base',
            title: result.metadata?.title || 'RAG Knowledge',
            content: result.content || result.text,
            relevance: result.score || 0.8,
            metadata: result.metadata
        })) || [];

        console.log('✅ RAG hybrid search completed:', sources.length, 'sources');
        return { sources };

    } catch (error) {
        console.error('❌ RAG query error:', error);
        // Fall back to mock data on error
        return getContextSpecificRAGResults(context.type, query);
    }
}

/**
 * Query metadata service with fuzzy search
 *
 * BUSINESS CONTEXT:
 * Uses fuzzy search to find relevant courses, projects, and content
 * even with typos or partial matches. Helps AI understand existing content.
 *
 * @param {string} query - Search query
 * @param {Object} context - Current context
 * @returns {Promise<Object>} Metadata search results
 */
async function queryMetadataWithFuzzySearch(query, context) {
    try {
        console.log('🔍 Fuzzy searching metadata...');

        // Map context types to entity types
        const entityTypeMap = {
            [CONTEXT_TYPES.PROJECT_CREATION]: ['course', 'project'],
            [CONTEXT_TYPES.COURSE_CREATION]: ['course', 'module'],
            [CONTEXT_TYPES.SLIDE_CREATION]: ['slide', 'module'],
            [CONTEXT_TYPES.LAB_CREATION]: ['lab', 'exercise'],
            [CONTEXT_TYPES.EXERCISE_CREATION]: ['exercise', 'lab'],
            [CONTEXT_TYPES.QUIZ_CREATION]: ['quiz', 'assessment'],
            [CONTEXT_TYPES.GENERAL]: ['course', 'project', 'module']
        };

        const entityTypes = entityTypeMap[context.type] || ['course'];

        const response = await fetch('https://localhost:8011/api/v1/metadata/search/fuzzy', {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify({
                query: query,
                entity_types: entityTypes,
                similarity_threshold: 0.2,  // Forgiving threshold for student typos
                limit: 10
            })
        });

        if (!response.ok) {
            console.warn('⚠️ Metadata service responded with:', response.status);
            return { results: [] };
        }

        const metadataResults = await response.json();

        // Transform results to consistent format
        const results = (metadataResults.results || []).map(result => ({
            entity_type: result.entity_type,
            title: result.title,
            description: result.description,
            tags: result.tags || [],
            keywords: result.keywords || [],
            similarity_score: result.similarity_score,
            metadata: result.metadata
        }));

        console.log('✅ Fuzzy search completed:', results.length, 'results');
        return { results };

    } catch (error) {
        console.error('❌ Metadata fuzzy search error:', error);
        return { results: [] };
    }
}

/**
 * Query knowledge graph for relationships and learning paths
 *
 * BUSINESS CONTEXT:
 * Leverages the knowledge graph to understand relationships between courses,
 * prerequisites, and learning paths. This helps AI provide contextually aware
 * suggestions based on actual course structure.
 *
 * @param {string} query - User query
 * @param {Object} context - Current context
 * @param {Object} metadataContext - Metadata search results (to find related courses)
 * @returns {Promise<Object>} Knowledge graph data
 */
async function queryKnowledgeGraph(query, context, metadataContext) {
    try {
        console.log('🕸️ Querying knowledge graph...');

        // Extract course IDs from metadata results to query relationships
        const courseIds = (metadataContext?.results || [])
            .filter(result => result.entity_type === 'course')
            .map(result => result.entity_id)
            .slice(0, 5);  // Limit to top 5 courses

        if (courseIds.length === 0) {
            console.log('⚠️ No courses found in metadata to query knowledge graph');
            return { relationships: [], paths: [] };
        }

        // Query knowledge graph for course relationships
        const graphData = {
            relationships: [],
            paths: [],
            prerequisites: []
        };

        // Get prerequisite information for each course
        for (const courseId of courseIds) {
            try {
                const response = await fetch(`https://localhost:8012/api/v1/graph/prerequisites/${courseId}/check`, {
                    method: 'GET',
                    headers: await getAuthHeaders()
                });

                if (response.ok) {
                    const prereqData = await response.json();
                    if (prereqData.prerequisites && prereqData.prerequisites.length > 0) {
                        graphData.prerequisites.push({
                            courseId: courseId,
                            prerequisites: prereqData.prerequisites
                        });
                    }
                }
            } catch (error) {
                console.warn(`Could not fetch prerequisites for course ${courseId}:`, error);
            }
        }

        // If we have multiple courses, try to find learning paths between them
        if (courseIds.length >= 2) {
            try {
                const startCourse = courseIds[0];
                const endCourse = courseIds[courseIds.length - 1];

                const response = await fetch(
                    `https://localhost:8012/api/v1/graph/paths/learning-path?start=${startCourse}&end=${endCourse}&optimization=shortest`,
                    {
                        method: 'GET',
                        headers: await getAuthHeaders()
                    }
                );

                if (response.ok) {
                    const pathData = await response.json();
                    if (pathData.path && pathData.path.length > 0) {
                        graphData.paths.push(pathData);
                    }
                }
            } catch (error) {
                console.warn('Could not find learning path:', error);
            }
        }

        console.log('✅ Knowledge graph query completed:', {
            prerequisites: graphData.prerequisites.length,
            paths: graphData.paths.length
        });

        return graphData;

    } catch (error) {
        console.error('❌ Knowledge graph query error:', error);
        return { relationships: [], paths: [], prerequisites: [] };
    }
}

/**
 * Get context-specific RAG results
 */
function getContextSpecificRAGResults(contextType, query) {
    const results = {
        [CONTEXT_TYPES.PROJECT_CREATION]: {
            sources: [
                {
                    type: 'project_template',
                    title: 'Similar successful project structure',
                    content: 'Progressive learning path with 4 tracks: Fundamentals → Intermediate → Advanced → Capstone',
                    relevance: 0.93
                },
                {
                    type: 'best_practice',
                    title: 'Project timeline recommendations',
                    content: '8-12 weeks optimal for comprehensive training with hands-on practice',
                    relevance: 0.87
                }
            ]
        },
        [CONTEXT_TYPES.COURSE_CREATION]: {
            sources: [
                {
                    type: 'course_template',
                    title: 'Successful course structure pattern',
                    content: 'Intro → Theory → Practice → Assessment → Reflection cycle per module',
                    relevance: 0.91
                },
                {
                    type: 'pedagogy',
                    title: 'Effective learning sequence',
                    content: 'Bloom\'s taxonomy progression: Remember → Understand → Apply → Analyze',
                    relevance: 0.88
                }
            ]
        },
        [CONTEXT_TYPES.LAB_CREATION]: {
            sources: [
                {
                    type: 'lab_template',
                    title: 'Hands-on lab best practices',
                    content: 'Scenario → Prerequisites → Step-by-step → Validation → Challenges',
                    relevance: 0.94
                },
                {
                    type: 'example',
                    title: 'Real-world lab scenarios',
                    content: 'Industry-standard problems with practical solutions',
                    relevance: 0.86
                }
            ]
        }
    };

    return results[contextType] || { sources: [] };
}

/**
 * Build context-aware prompt for AI
 *
 * BUSINESS CONTEXT:
 * Constructs a comprehensive prompt that includes:
 * - Current context and task
 * - RAG knowledge base content
 * - Metadata fuzzy search results (existing courses/content)
 * - Knowledge graph relationships and learning paths
 * - Web search results (if any)
 * - Conversation history
 *
 * @param {string} userMessage - User's message
 * @param {Object} context - Current context
 * @param {Object} ragContext - RAG results
 * @param {Object} metadataContext - Metadata fuzzy search results
 * @param {Object} knowledgeGraphContext - Knowledge graph relationships
 * @param {Object} webResults - Web search results (optional)
 * @returns {string} Enhanced prompt
 */
function buildContextAwarePrompt(userMessage, context, ragContext, metadataContext, knowledgeGraphContext, webResults) {
    let prompt = `
CONTEXT: ${context.type}
USER MESSAGE: ${userMessage}
`;

    // Add context data
    if (Object.keys(context.data).length > 0) {
        prompt += `\nCONTEXT DATA:\n${JSON.stringify(context.data, null, 2)}\n`;
    }

    // Add RAG sources
    if (ragContext?.sources && ragContext.sources.length > 0) {
        prompt += `\nKNOWLEDGE BASE CONTEXT (from RAG):\n`;
        ragContext.sources.forEach(source => {
            prompt += `- [${source.type}] ${source.title}: ${source.content}\n`;
        });
    }

    // Add metadata fuzzy search results
    if (metadataContext?.results && metadataContext.results.length > 0) {
        prompt += `\nEXISTING CONTENT (from metadata search):\n`;
        metadataContext.results.forEach(result => {
            prompt += `- [${result.entity_type}] ${result.title}`;
            if (result.description) {
                prompt += `: ${result.description}`;
            }
            if (result.tags && result.tags.length > 0) {
                prompt += ` (Tags: ${result.tags.join(', ')})`;
            }
            prompt += ` [Match: ${(result.similarity_score * 100).toFixed(0)}%]\n`;
        });
    }

    // Add knowledge graph relationships
    if (knowledgeGraphContext && (knowledgeGraphContext.prerequisites?.length > 0 || knowledgeGraphContext.paths?.length > 0)) {
        prompt += `\nKNOWLEDGE GRAPH RELATIONSHIPS:\n`;

        // Add prerequisite information
        if (knowledgeGraphContext.prerequisites && knowledgeGraphContext.prerequisites.length > 0) {
            prompt += `\nPrerequisites:\n`;
            knowledgeGraphContext.prerequisites.forEach(prereq => {
                prompt += `- Course has ${prereq.prerequisites.length} prerequisite(s)\n`;
                prereq.prerequisites.forEach(p => {
                    prompt += `  → ${p.title || p.name}\n`;
                });
            });
        }

        // Add learning path information
        if (knowledgeGraphContext.paths && knowledgeGraphContext.paths.length > 0) {
            prompt += `\nLearning Paths:\n`;
            knowledgeGraphContext.paths.forEach(pathData => {
                if (pathData.path && pathData.path.length > 0) {
                    prompt += `- Path (${pathData.path.length} courses): `;
                    prompt += pathData.path.map(node => node.title || node.name).join(' → ');
                    prompt += `\n`;
                    if (pathData.total_duration) {
                        prompt += `  Duration: ${pathData.total_duration} hours\n`;
                    }
                }
            });
        }
    }

    // Add web search results
    if (webResults?.results && webResults.results.length > 0) {
        prompt += `\nWEB RESEARCH RESULTS:\n`;
        webResults.results.forEach(result => {
            prompt += `- ${result.title}\n  URL: ${result.url}\n  ${result.snippet}\n\n`;
        });
    }

    // Add recent conversation history (last 5 exchanges)
    const recentHistory = context.conversationHistory.slice(-10);
    if (recentHistory.length > 1) {
        prompt += `\nRECENT CONVERSATION:\n`;
        recentHistory.forEach(msg => {
            if (msg.role !== 'system') {
                prompt += `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}\n`;
            }
        });
    }

    return prompt;
}

/**
 * Call AI service with context-aware prompt
 *
 * @param {string} prompt - Enhanced prompt
 * @param {Object} context - Current context
 * @returns {Promise<Object>} AI response
 */
async function callAIService(prompt, context) {
    try {
        /**
         * BUSINESS CONTEXT:
         * Calls the course-generator AI service with RAG-enhanced context.
         * Uses the ChatGenerator for context-aware responses.
         *
         * TECHNICAL IMPLEMENTATION:
         * Calls the /api/v1/chat endpoint with full context and conversation history
         */

        // Prepare conversation history for the AI
        const conversationHistory = context.conversationHistory
            .filter(msg => msg.role !== 'system')
            .map(msg => ({
                role: msg.role,
                content: msg.content
            }));

        // Extract context data for the AI
        const contextData = {
            project_name: context.data.projectName,
            project_description: context.data.projectDescription,
            target_roles: context.data.targetRoles,
            organization_id: context.data.organizationId,
            context_type: context.type
        };

        console.log('🤖 Calling course-generator chat endpoint...');

        // Call actual chat endpoint
        const response = await fetch('https://localhost:8001/api/v1/chat', {
            method: 'POST',
            headers: await getAuthHeaders(),
            body: JSON.stringify({
                question: prompt,
                context: contextData,
                conversation_history: conversationHistory
            })
        });

        if (!response.ok) {
            console.warn('⚠️ Chat endpoint returned:', response.status);
            // Fall back to mock response on error
            return generateContextAwareResponse(prompt, context);
        }

        const chatResponse = await response.json();

        // Transform to expected format
        return {
            message: chatResponse.answer,
            suggestions: chatResponse.suggestions || [],
            actions: [],  // Not provided by chat endpoint yet
            metadata: chatResponse.metadata || {}
        };

    } catch (error) {
        console.error('❌ AI service error:', error);
        // Fall back to mock response on error
        return generateContextAwareResponse(prompt, context);
    }
}

/**
 * Generate context-aware mock response
 */
function generateContextAwareResponse(prompt, context) {
    const responses = {
        [CONTEXT_TYPES.PROJECT_CREATION]: {
            message: 'Based on your project requirements and similar successful projects in our knowledge base, I recommend a structured approach with 4 progressive tracks. The web research shows current industry practices align with this structure.',
            suggestions: [
                'Start with a 2-week Fundamentals track',
                'Follow with 3-week Intermediate skills development',
                'Include hands-on labs in each module',
                'Conclude with a capstone project'
            ],
            actions: ['update_track_structure', 'adjust_timeline'],
            metadata: { confidence: 0.92, sources_used: 3 }
        },
        [CONTEXT_TYPES.COURSE_CREATION]: {
            message: 'For effective course design, I recommend following proven pedagogical patterns from our knowledge base. Each module should follow the learning cycle: Introduction → Theory → Practice → Assessment.',
            suggestions: [
                'Include practical examples in theory sections',
                'Add hands-on exercises after each concept',
                'Create formative assessments throughout',
                'End with summative project assessment'
            ],
            actions: ['add_practice_sections', 'create_assessments'],
            metadata: { confidence: 0.89, sources_used: 4 }
        },
        [CONTEXT_TYPES.LAB_CREATION]: {
            message: 'Based on successful lab patterns and current industry scenarios, I recommend creating scenario-based labs with clear objectives and validation steps.',
            suggestions: [
                'Start with a realistic business scenario',
                'Provide step-by-step guided instructions',
                'Include checkpoints for validation',
                'Add challenge tasks for advanced learners'
            ],
            actions: ['add_scenario', 'create_validation_steps'],
            metadata: { confidence: 0.95, sources_used: 2 }
        }
    };

    return responses[context.type] || {
        message: 'I can help you with that. What specific aspect would you like to focus on?',
        suggestions: [],
        actions: [],
        metadata: { confidence: 0.7, sources_used: 0 }
    };
}

/**
 * Get current context
 */
export function getCurrentContext() {
    return currentContext;
}

/**
 * Clear conversation history
 */
export function clearConversationHistory() {
    const systemMessage = currentContext.conversationHistory[0];
    currentContext.conversationHistory = [systemMessage];
    console.log('🗑️ Conversation history cleared');
}

/**
 * Export conversation history
 */
export function exportConversationHistory() {
    return {
        context: currentContext.type,
        contextData: currentContext.data,
        history: currentContext.conversationHistory,
        exportedAt: new Date().toISOString()
    };
}

/**
 * Preprocess query using NLP service
 *
 * BUSINESS CONTEXT:
 * Uses NLP preprocessing to classify intent, extract entities, and expand queries.
 * Enables 30-40% cost reduction by routing simple queries away from LLM.
 *
 * @param {string} query - User query
 * @param {Object} context - Current conversation context
 * @returns {Promise<Object>} NLP preprocessing results
 */
async function preprocessQuery(query, context) {
    try {
        const response = await fetch('https://localhost:8013/api/v1/preprocess', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                conversation_history: null, // TODO: Add conversation history with embeddings
                enable_deduplication: false,
                deduplication_threshold: 0.95
            })
        });

        if (!response.ok) {
            console.warn('⚠️ NLP preprocessing failed, continuing without it');
            // Return minimal result to allow processing to continue
            return {
                intent: { intent_type: 'unknown', should_call_llm: true },
                entities: [],
                expanded_query: { original: query, expansions: [], combined: query },
                should_call_llm: true,
                direct_response: null
            };
        }

        const result = await response.json();
        console.log('✅ NLP preprocessing complete:', result);
        return result;

    } catch (error) {
        console.error('❌ NLP preprocessing error:', error);
        // Return minimal result to allow processing to continue
        return {
            intent: { intent_type: 'unknown', should_call_llm: true },
            entities: [],
            expanded_query: { original: query, expansions: [], combined: query },
            should_call_llm: true,
            direct_response: null
        };
    }
}

/**
 * Handle direct response without calling LLM
 *
 * BUSINESS CONTEXT:
 * Routes simple queries directly to appropriate services (metadata, knowledge graph, etc.)
 * without invoking expensive LLM calls. Reduces costs by 30-40% for simple queries.
 *
 * @param {Object} nlpResult - NLP preprocessing result
 * @param {string} userMessage - Original user message
 * @returns {Promise<Object>} Response object
 */
async function handleDirectResponse(nlpResult, userMessage) {
    const { direct_response, intent, entities } = nlpResult;

    console.log('🎯 Handling direct response for intent:', intent.intent_type);

    let message = '';
    let suggestions = [];
    let metadata = {};

    switch (direct_response.type) {
        case 'greeting':
            message = direct_response.message;
            suggestions = direct_response.suggestions || [];
            break;

        case 'prerequisite_check':
            // Extract course names from entities
            const courseNames = entities
                .filter(e => e.entity_type === 'course')
                .map(e => e.text);

            if (courseNames.length > 0) {
                message = `I'll check the prerequisites for: ${courseNames.join(', ')}. Let me query the knowledge graph...`;
                suggestions = [
                    'Show me the full learning path',
                    'What skills will I need?',
                    'Are there any beginner courses?'
                ];
                metadata = {
                    routing: 'knowledge-graph',
                    courses: courseNames
                };
            } else {
                message = 'I can help you check prerequisites. Which course are you interested in?';
                suggestions = [
                    'Prerequisites for Python Advanced',
                    'What do I need for Machine Learning?'
                ];
            }
            break;

        case 'metadata_search':
        case 'course_lookup':
            // Extract search terms from entities
            const searchTerms = entities.map(e => ({
                type: e.entity_type,
                text: e.text,
                confidence: e.confidence
            }));

            message = `I found ${searchTerms.length} search criteria. Let me find relevant courses for you...`;
            suggestions = [
                'Show me more details',
                'Filter by difficulty level',
                'What are the prerequisites?'
            ];
            metadata = {
                routing: 'metadata-service',
                search_terms: searchTerms
            };
            break;

        case 'learning_path':
            message = 'I\'ll find the optimal learning path for you using our knowledge graph...';
            suggestions = [
                'Show prerequisites for each step',
                'Estimate time to complete',
                'Suggest alternative paths'
            ];
            metadata = {
                routing: 'knowledge-graph'
            };
            break;

        default:
            message = direct_response.message || 'I\'ll help you with that.';
            suggestions = [];
    }

    // Add response to history
    currentContext.conversationHistory.push({
        role: 'assistant',
        content: message,
        timestamp: new Date().toISOString(),
        metadata: {
            ...metadata,
            nlp_preprocessing: {
                intent: intent.intent_type,
                entities: entities.length,
                bypassed_llm: true
            }
        }
    });

    return {
        message,
        suggestions,
        actions: [],
        ragSources: [],
        metadata: {
            ...metadata,
            nlp_preprocessing: {
                intent: intent.intent_type,
                entities,
                cost_saved: true,
                processing_time_ms: nlpResult.processing_time_ms
            }
        }
    };
}
