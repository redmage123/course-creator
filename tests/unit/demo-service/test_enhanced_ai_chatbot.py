"""
TDD RED Phase: Enhanced AI Chatbot with NLP, Personalization, and Guest Recognition

BUSINESS REQUIREMENT:
Transform static chatbot into intelligent AI sales agent that:
- Asks personalized onboarding questions (skippable)
- Uses NLP for intent classification and entity extraction
- Integrates knowledge graph for smart recommendations
- Recognizes returning guests and remembers preferences
- Tailors demo experience to guest's specific needs
- Includes AI avatar stubs for future voice/video interface

TECHNICAL INTEGRATION:
- NLP Preprocessing service (intent classification, entity extraction, fuzzy search)
- Knowledge Graph service (concept relationships, recommendations)
- Guest session persistence (recognize returning users)
- Adaptive conversation flow based on user profile
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

# Add services to path
demo_service_path = Path(__file__).parent.parent.parent / 'services' / 'demo-service'
sys.path.insert(0, str(demo_service_path))

from demo_data_generator import (
    generate_chatbot_response,
    DemoSession
)
from organization_management.domain.entities.guest_session import GuestSession


class TestPersonalizedOnboarding:
    """
    Test: Chatbot asks personalized onboarding questions

    BUSINESS REQUIREMENT:
    Like a real sales agent, chatbot should learn about guest's:
    - Role (instructor, student, admin, IT director)
    - Organization type (K-12, university, corporate training)
    - Pain points (specific problems they're trying to solve)
    - Timeline (evaluating now vs. future)
    """

    def test_chatbot_starts_with_personalized_greeting(self):
        """
        Test: First message is personalized greeting with optional onboarding

        EXPECTED BEHAVIOR:
        - Friendly greeting
        - Offers to ask a few questions (skippable)
        - Sets conversation_mode = 'onboarding' or 'exploration'
        """
        guest_session = GuestSession()

        # First interaction - should trigger onboarding offer
        response = generate_chatbot_response(
            question="Hello",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'greeting' in response
        assert 'onboarding_offered' in response
        assert response['onboarding_offered'] is True
        assert response['skip_onboarding_option'] is True
        assert response['conversation_mode'] in ['onboarding', 'exploration']

    def test_chatbot_asks_about_user_role(self):
        """
        Test: Chatbot asks about user's role/position

        EXPECTED BEHAVIOR:
        - Asks "What's your role?" or similar
        - Provides role options (instructor, student, admin, IT)
        - Stores role in guest_session.user_profile
        """
        guest_session = GuestSession()
        guest_session.conversation_mode = 'onboarding'

        response = generate_chatbot_response(
            question="I'd like to answer a few questions",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'role_question' in response
        assert 'role_options' in response
        assert 'instructor' in str(response['role_options']).lower()
        assert 'student' in str(response['role_options']).lower()
        assert 'admin' in str(response['role_options']).lower()

    def test_chatbot_extracts_role_from_response(self):
        """
        Test: Chatbot uses NLP to extract role from user response

        EXPECTED BEHAVIOR:
        - Uses entity extraction to identify role
        - Stores in guest_session.user_profile['role']
        - Adapts next question based on role
        """
        guest_session = GuestSession()
        guest_session.conversation_mode = 'onboarding'

        response = generate_chatbot_response(
            question="I'm a computer science instructor at a university",
            conversation_history=[
                {'question': 'What brings you here?', 'answer': 'Exploring platform'}
            ],
            guest_session=guest_session
        )

        assert hasattr(guest_session, 'user_profile')
        assert 'role' in guest_session.user_profile
        assert guest_session.user_profile['role'] == 'instructor'
        assert 'organization_type' in guest_session.user_profile  # Should extract 'university'
        assert guest_session.user_profile['organization_type'] == 'university'

    def test_chatbot_asks_about_pain_points(self):
        """
        Test: Chatbot asks about specific problems/challenges

        EXPECTED BEHAVIOR:
        - Asks "What challenges are you facing?"
        - Uses NLP intent classification to understand pain points
        - Stores pain points in guest_session.user_profile
        """
        guest_session = GuestSession()
        guest_session.conversation_mode = 'onboarding'
        guest_session.user_profile = {'role': 'instructor'}

        response = generate_chatbot_response(
            question="Continue with questions",
            conversation_history=[
                {'question': 'What is your role?', 'answer': 'I am an instructor'}
            ],
            guest_session=guest_session
        )

        assert 'pain_point_question' in response
        assert 'challenge' in response['answer'].lower() or 'problem' in response['answer'].lower()

    def test_chatbot_allows_skipping_onboarding(self):
        """
        Test: Guest can skip onboarding and jump to exploration

        EXPECTED BEHAVIOR:
        - If user says "skip" or "just show me features"
        - Switches to conversation_mode = 'exploration'
        - Starts general platform tour
        """
        guest_session = GuestSession()
        guest_session.conversation_mode = 'onboarding'

        response = generate_chatbot_response(
            question="Skip this, just show me the features",
            conversation_history=[],
            guest_session=guest_session
        )

        assert guest_session.conversation_mode == 'exploration'
        assert 'features_overview' in response
        assert response['onboarding_skipped'] is True


class TestNLPIntegration:
    """
    Test: Chatbot integrates NLP preprocessing service

    BUSINESS REQUIREMENT:
    Use existing NLP infrastructure for:
    - Intent classification (question type, urgency level)
    - Entity extraction (role, organization, technologies mentioned)
    - Query expansion (understand variations like "how much" = pricing)
    - Fuzzy matching (typos, synonyms)
    """

    def test_chatbot_uses_intent_classification(self):
        """
        Test: Chatbot classifies user intent using NLP service

        EXPECTED BEHAVIOR:
        - Calls nlp_preprocessing service
        - Returns intent classification (pricing, demo, technical, support)
        - Uses intent to route response
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="How much does this cost?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'nlp_analysis' in response
        assert 'intent' in response['nlp_analysis']
        assert response['nlp_analysis']['intent'] == 'pricing_inquiry'
        assert 'confidence' in response['nlp_analysis']
        assert response['nlp_analysis']['confidence'] > 0.7

    def test_chatbot_extracts_entities_from_questions(self):
        """
        Test: Chatbot extracts entities (technologies, roles, numbers)

        EXPECTED BEHAVIOR:
        - Extracts named entities from user input
        - Stores entities in conversation context
        - Uses entities to personalize responses
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="We have 500 students learning Python and Java",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'entities' in response['nlp_analysis']
        entities = response['nlp_analysis']['entities']

        assert any(e['type'] == 'number' and e['value'] == 500 for e in entities)
        assert any(e['type'] == 'technology' and e['value'] in ['Python', 'Java'] for e in entities)
        assert guest_session.user_profile['student_count'] == 500
        assert 'Python' in guest_session.user_profile['technologies']

    def test_chatbot_handles_fuzzy_matching(self):
        """
        Test: Chatbot understands typos and variations

        EXPECTED BEHAVIOR:
        - Uses fuzzy matching for misspellings
        - Recognizes synonyms (e.g., "cost" = "price" = "pricing")
        - Corrects and responds appropriately
        """
        guest_session = GuestSession()

        # Typo: "knowlege graph" instead of "knowledge graph"
        response = generate_chatbot_response(
            question="Tell me about the knowlege grahp",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'fuzzy_match_applied' in response['nlp_analysis']
        assert response['nlp_analysis']['fuzzy_match_applied'] is True
        assert 'knowledge graph' in response['answer'].lower()
        assert 'corrected_query' in response['nlp_analysis']

    def test_chatbot_expands_queries_using_nlp(self):
        """
        Test: Chatbot expands queries to understand variations

        EXPECTED BEHAVIOR:
        - "How much?" → pricing_inquiry + budget_question
        - "Show me" → demo_request
        - "I need help with" → technical_support
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="How much for 100 users?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'query_expansion' in response['nlp_analysis']
        expansions = response['nlp_analysis']['query_expansion']
        assert 'pricing' in expansions
        assert 'user_count' in expansions
        assert 'budget' in expansions


class TestKnowledgeGraphIntegration:
    """
    Test: Chatbot uses knowledge graph for smart recommendations

    BUSINESS REQUIREMENT:
    Based on user's interests/role, recommend relevant features:
    - Instructor → AI content generation, student analytics
    - Student → Learning paths, Docker labs
    - Admin → Organization management, RBAC, compliance
    """

    def test_chatbot_queries_knowledge_graph_for_recommendations(self):
        """
        Test: Chatbot queries knowledge graph based on user profile

        EXPECTED BEHAVIOR:
        - Uses guest_session.user_profile to build query
        - Gets related features from knowledge graph
        - Recommends top 3 most relevant features
        """
        guest_session = GuestSession()
        guest_session.user_profile = {
            'role': 'instructor',
            'pain_points': ['time-consuming content creation', 'grading'],
            'technologies': ['Python']
        }

        response = generate_chatbot_response(
            question="What features would help me?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'knowledge_graph_query' in response
        assert 'recommendations' in response
        assert len(response['recommendations']) >= 3

        # Should recommend AI content generation for instructor with content creation pain point
        assert any('AI' in r['feature_name'] or 'content' in r['feature_name'].lower()
                   for r in response['recommendations'])

    def test_chatbot_adapts_demo_path_to_user_needs(self):
        """
        Test: Chatbot creates personalized demo path

        EXPECTED BEHAVIOR:
        - Based on user_profile, creates step-by-step demo
        - Prioritizes features matching pain points
        - Suggests optimal order (prerequisites first)
        """
        guest_session = GuestSession()
        guest_session.user_profile = {
            'role': 'instructor',
            'pain_points': ['student engagement', 'hands-on practice']
        }

        response = generate_chatbot_response(
            question="Give me a personalized tour",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'personalized_demo_path' in response
        demo_path = response['personalized_demo_path']

        assert 'steps' in demo_path
        assert len(demo_path['steps']) > 0

        # Should prioritize Docker labs (hands-on practice) and analytics (engagement)
        feature_names = ' '.join([s['feature_name'].lower() for s in demo_path['steps']])
        assert 'lab' in feature_names or 'analytics' in feature_names

    def test_chatbot_suggests_related_features(self):
        """
        Test: Chatbot suggests related features based on current interest

        EXPECTED BEHAVIOR:
        - If user asks about feature X, suggest related features Y, Z
        - Uses knowledge graph edges (prerequisites, related_to)
        - Explains why features are related
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="Tell me about Docker labs",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'related_features' in response
        related = response['related_features']

        # Docker labs should be related to: code execution, student progress tracking
        assert len(related) > 0
        assert all('reason' in r for r in related)  # Each should have explanation


class TestGuestRecognition:
    """
    Test: Chatbot recognizes returning guests

    BUSINESS REQUIREMENT:
    Like a real sales agent, remember:
    - Previous conversations (by session ID or cookie)
    - User profile (role, pain points, interests)
    - Features already viewed
    - Where they left off in demo
    """

    def test_chatbot_recognizes_returning_guest(self):
        """
        Test: Chatbot welcomes back returning guest

        EXPECTED BEHAVIOR:
        - Checks if guest_session.id exists in storage
        - If returning, loads previous user_profile
        - Greets with "Welcome back!" instead of "Welcome!"
        """
        # Simulate returning guest (session from yesterday)
        guest_session = GuestSession()
        guest_session.id = uuid4()
        guest_session.user_profile = {
            'role': 'instructor',
            'name': 'Dr. Smith',
            'last_visit': (datetime.utcnow() - timedelta(days=1)).isoformat()
        }
        guest_session.is_returning_guest = True

        response = generate_chatbot_response(
            question="Hello",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'welcome_back' in response
        assert response['welcome_back'] is True
        assert 'Dr. Smith' in response['answer'] or 'instructor' in response['answer'].lower()

    def test_chatbot_resumes_previous_conversation(self):
        """
        Test: Chatbot picks up where guest left off

        EXPECTED BEHAVIOR:
        - Loads guest_session.features_viewed
        - Suggests next logical feature in demo path
        - Doesn't repeat information already shown
        """
        guest_session = GuestSession()
        guest_session.is_returning_guest = True
        guest_session.features_viewed = ['chatbot', 'ai_content_generation']
        guest_session.user_profile = {'role': 'instructor'}

        response = generate_chatbot_response(
            question="What should I look at next?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'resume_suggestion' in response
        assert 'next_feature' in response

        # Should NOT suggest features already viewed
        next_feature = response['next_feature']['feature_name'].lower()
        assert 'chatbot' not in next_feature
        assert 'ai_content_generation' not in next_feature

    def test_chatbot_updates_guest_preferences_over_time(self):
        """
        Test: Chatbot learns from guest behavior

        EXPECTED BEHAVIOR:
        - Tracks which topics guest asks most about
        - Identifies preferred communication style (technical vs. business)
        - Adapts language and depth accordingly
        """
        guest_session = GuestSession()
        guest_session.user_profile = {
            'role': 'IT director',
            'communication_style': 'unknown'
        }

        # Guest asks very technical question
        response = generate_chatbot_response(
            question="What's the Docker orchestration architecture? Do you use Kubernetes?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'communication_style' in guest_session.user_profile
        assert guest_session.user_profile['communication_style'] == 'technical'

        # Next response should be more technical
        assert response['response_style'] == 'technical'
        assert 'technical_detail_level' in response


class TestAIAvatarStubs:
    """
    Test: AI avatar interface stubs for future voice/video

    BUSINESS REQUIREMENT:
    Prepare infrastructure for AI avatar features:
    - Voice synthesis (text-to-speech)
    - Speech recognition (voice input)
    - Video avatar (animated face, lip sync)
    - Emotion detection (adjust tone based on user sentiment)
    """

    def test_chatbot_includes_voice_synthesis_stub(self):
        """
        Test: Chatbot response includes voice synthesis data

        EXPECTED BEHAVIOR:
        - Every response has 'voice_synthesis' field (stub)
        - Contains SSML markup for future TTS
        - Includes voice profile (gender, accent, tone)
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="Tell me about pricing",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'voice_synthesis' in response
        voice = response['voice_synthesis']

        assert 'ssml_text' in voice  # Speech Synthesis Markup Language
        assert 'voice_profile' in voice
        assert voice['voice_profile']['gender'] in ['male', 'female', 'neutral']
        assert 'tone' in voice['voice_profile']  # friendly, professional, enthusiastic
        assert voice['enabled'] is False  # Stub - not implemented yet

    def test_chatbot_includes_video_avatar_stub(self):
        """
        Test: Chatbot response includes video avatar data

        EXPECTED BEHAVIOR:
        - Response has 'video_avatar' field (stub)
        - Contains animation cues (gestures, expressions)
        - Includes avatar appearance settings
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="Show me the platform features",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'video_avatar' in response
        avatar = response['video_avatar']

        assert 'animation_cues' in avatar
        assert 'expression' in avatar['animation_cues']  # smile, thinking, enthusiastic
        assert 'gesture' in avatar['animation_cues']  # pointing, waving, nodding
        assert 'avatar_appearance' in avatar
        assert avatar['enabled'] is False  # Stub - not implemented yet

    def test_chatbot_detects_user_sentiment(self):
        """
        Test: Chatbot analyzes user sentiment from text (stub for emotion detection)

        EXPECTED BEHAVIOR:
        - Uses NLP to detect sentiment (positive, negative, frustrated, excited)
        - Adjusts response tone accordingly
        - Prepares for future video emotion detection
        """
        guest_session = GuestSession()

        # Frustrated user
        response = generate_chatbot_response(
            question="This is confusing and I can't find what I need",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'sentiment_analysis' in response['nlp_analysis']
        sentiment = response['nlp_analysis']['sentiment_analysis']

        assert sentiment['detected_emotion'] in ['frustrated', 'negative', 'confused']
        assert 'empathy_response' in response  # Should include empathetic language
        assert 'help_escalation' in response  # Offer to connect with human agent


class TestRAGIntegration:
    """
    Test: Chatbot uses RAG (Retrieval-Augmented Generation) for intelligent responses

    BUSINESS REQUIREMENT:
    Integrate RAG system to:
    - Retrieve relevant platform documentation dynamically
    - Answer questions with context from knowledge base
    - Provide accurate technical details (not hallucinated)
    - Learn from conversation history (contextual memory)
    """

    def test_chatbot_retrieves_context_from_knowledge_base(self):
        """
        Test: Chatbot uses RAG to fetch relevant documentation

        EXPECTED BEHAVIOR:
        - Query embeddings generated from user question
        - Semantic search against knowledge base
        - Retrieves top-K relevant documents
        - Grounds response in retrieved context
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="How does the RBAC system handle multi-tenant organizations?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'rag_context' in response
        rag = response['rag_context']

        assert 'retrieved_documents' in rag
        assert len(rag['retrieved_documents']) > 0
        assert all('relevance_score' in doc for doc in rag['retrieved_documents'])
        assert all('content' in doc for doc in rag['retrieved_documents'])

        # Response should reference retrieved content
        assert 'grounded_in_context' in response
        assert response['grounded_in_context'] is True

    def test_chatbot_uses_conversation_history_for_rag_context(self):
        """
        Test: RAG considers full conversation context

        EXPECTED BEHAVIOR:
        - Builds context from conversation_history
        - Uses previous questions to disambiguate current query
        - Maintains conversational coherence
        """
        guest_session = GuestSession()

        conversation_history = [
            {'question': 'Tell me about Docker labs', 'answer': 'Docker labs provide...'},
            {'question': 'How do students access them?', 'answer': 'Students click...'}
        ]

        # "What languages?" should understand it's asking about Docker labs
        response = generate_chatbot_response(
            question="What programming languages are supported?",
            conversation_history=conversation_history,
            guest_session=guest_session
        )

        assert 'rag_context' in response
        assert 'conversation_context_used' in response['rag_context']
        assert response['rag_context']['conversation_context_used'] is True

        # Should understand context is about Docker labs
        assert 'docker' in response['answer'].lower() or 'lab' in response['answer'].lower()

    def test_chatbot_generates_embeddings_for_semantic_search(self):
        """
        Test: Chatbot creates embeddings for semantic matching

        EXPECTED BEHAVIOR:
        - Question converted to embedding vector
        - Semantic search (not keyword matching)
        - Finds conceptually similar content
        """
        guest_session = GuestSession()

        # Question uses different words than documentation
        response = generate_chatbot_response(
            question="Can I monitor student learning progression?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'embeddings' in response['rag_context']
        assert 'query_embedding' in response['rag_context']['embeddings']
        assert len(response['rag_context']['embeddings']['query_embedding']) > 0  # Vector

        # Should match "analytics" and "progress tracking" via semantic similarity
        assert 'analytics' in response['answer'].lower() or 'progress' in response['answer'].lower()

    def test_chatbot_handles_no_rag_context_found(self):
        """
        Test: Chatbot gracefully handles questions without knowledge base match

        EXPECTED BEHAVIOR:
        - If no relevant docs found (low relevance scores)
        - Admits limitation
        - Offers to connect with human expert
        - Doesn't hallucinate information
        """
        guest_session = GuestSession()

        # Question outside platform scope
        response = generate_chatbot_response(
            question="What's the weather like today?",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'rag_context' in response
        assert len(response['rag_context']['retrieved_documents']) == 0 or \
               all(doc['relevance_score'] < 0.3 for doc in response['rag_context']['retrieved_documents'])

        # Should admit not knowing
        assert 'not_in_scope' in response or 'cant_answer' in response
        assert "I'm not sure" in response['answer'] or "outside my expertise" in response['answer'].lower()

    def test_chatbot_updates_rag_knowledge_base_from_conversation(self):
        """
        Test: Chatbot learns from successful conversations (future stub)

        EXPECTED BEHAVIOR:
        - If guest finds answer helpful (positive feedback)
        - Conversation added to knowledge base
        - Future guests benefit from this Q&A
        """
        guest_session = GuestSession()

        response = generate_chatbot_response(
            question="This answer was very helpful, thank you!",
            conversation_history=[
                {'question': 'How do I bulk import students?', 'answer': 'Use CSV upload...'}
            ],
            guest_session=guest_session
        )

        assert 'knowledge_base_update' in response
        update = response['knowledge_base_update']

        assert update['conversation_flagged_for_training'] is True
        assert update['reason'] == 'positive_feedback'
        assert update['enabled'] is False  # Stub - requires manual review before adding


class TestAdaptiveDemoPaths:
    """
    Test: Chatbot tailors demo to guest's specific requirements

    BUSINESS REQUIREMENT:
    Based on onboarding + conversation, create personalized demo:
    - Instructor + content creation → AI generation workflow
    - Student + struggling → Learning paths + knowledge graph
    - Admin + compliance → RBAC + audit logs
    - IT director + integration → API docs + Docker architecture
    """

    def test_chatbot_creates_instructor_demo_path(self):
        """
        Test: Instructor gets course creation workflow demo

        EXPECTED BEHAVIOR:
        - Demo path: AI syllabus → slides → quiz → lab → analytics
        - Emphasizes time savings and automation
        - Shows student engagement metrics
        """
        guest_session = GuestSession()
        guest_session.user_profile = {
            'role': 'instructor',
            'pain_points': ['time-consuming course creation', 'student engagement']
        }

        response = generate_chatbot_response(
            question="Show me how this helps instructors",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'personalized_demo_path' in response
        path = response['personalized_demo_path']

        # Should include AI content generation early in path
        assert path['steps'][0]['category'] in ['ai_content', 'course_creation']
        assert any('time savings' in s.get('benefit', '').lower() for s in path['steps'])

    def test_chatbot_creates_admin_demo_path(self):
        """
        Test: Admin gets organization management demo

        EXPECTED BEHAVIOR:
        - Demo path: RBAC → user management → tracks → compliance reports
        - Emphasizes control and oversight
        - Shows administrative efficiency
        """
        guest_session = GuestSession()
        guest_session.user_profile = {
            'role': 'organization_admin',
            'pain_points': ['user access control', 'compliance tracking']
        }

        response = generate_chatbot_response(
            question="Show me administrative features",
            conversation_history=[],
            guest_session=guest_session
        )

        assert 'personalized_demo_path' in response
        path = response['personalized_demo_path']

        # Should prioritize RBAC and compliance features
        feature_categories = [s['category'] for s in path['steps']]
        assert 'rbac' in feature_categories or 'user_management' in feature_categories

    def test_chatbot_adjusts_technical_depth_by_role(self):
        """
        Test: Technical depth matches user's role

        EXPECTED BEHAVIOR:
        - IT director → technical architecture, APIs, Docker details
        - Instructor → pedagogical benefits, ease of use
        - Student → learning outcomes, progress tracking
        """
        guest_session = GuestSession()
        guest_session.user_profile = {'role': 'IT director'}

        response = generate_chatbot_response(
            question="Tell me about the platform",
            conversation_history=[],
            guest_session=guest_session
        )

        assert response['technical_depth'] == 'high'
        assert 'architecture' in response['answer'].lower() or 'api' in response['answer'].lower()

        # Now test with non-technical role
        guest_session.user_profile = {'role': 'instructor'}

        response = generate_chatbot_response(
            question="Tell me about the platform",
            conversation_history=[],
            guest_session=guest_session
        )

        assert response['technical_depth'] == 'low'
        assert 'easy' in response['answer'].lower() or 'simple' in response['answer'].lower()
