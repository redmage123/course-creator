"""
TDD RED Phase: Demo Service Interactive Chatbot Tests

BUSINESS REQUIREMENT:
The demo service needs an interactive chatbot that acts as a virtual salesperson,
answering questions about platform features, pricing, use cases, and capabilities.
This helps convert demo users into paying customers by providing personalized guidance.

TECHNICAL REQUIREMENT:
- Natural language question answering about platform features
- Context-aware responses based on conversation history
- Showcase RAG/AI capabilities
- Track common questions for marketing insights
- Lead qualification (identify serious prospects)
- Conversion prompts (suggest next steps, pricing, demos)

TEST METHODOLOGY: Test-Driven Development (TDD)
These tests are written FIRST (RED phase) and will FAIL until implementation is complete.
"""

import pytest
from typing import Dict, List, Any


class TestDemoChatbotBasicResponses:
    """
    Test Suite: Demo Chatbot Basic Question Answering

    BUSINESS CONTEXT:
    Chatbot must answer common questions about platform features, like a
    knowledgeable salesperson explaining the product.
    """

    def test_chatbot_answers_what_is_platform_question(self):
        """
        Test: Chatbot answers "What is this platform?" question

        REQUIREMENT: Provide clear, concise platform overview
        """
        # This will FAIL until we add generate_chatbot_response() function
        from demo_data_generator import generate_chatbot_response

        question = "What is this platform?"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Validate response structure
        assert 'answer' in response
        assert 'confidence' in response
        assert 'follow_up_questions' in response
        assert 'related_features' in response

        # Validate answer quality
        assert len(response['answer']) > 50  # Meaningful answer
        assert 'learning' in response['answer'].lower() or 'course' in response['answer'].lower()
        assert response['confidence'] >= 0.8  # High confidence on basic questions

    def test_chatbot_answers_features_question(self):
        """
        Test: Chatbot answers "What features do you have?" question

        REQUIREMENT: List key platform features like a salesperson highlighting benefits
        """
        from demo_data_generator import generate_chatbot_response

        question = "What features do you have?"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should mention key features
        answer_lower = response['answer'].lower()
        assert 'ai' in answer_lower or 'artificial intelligence' in answer_lower
        assert 'lab' in answer_lower or 'hands-on' in answer_lower
        assert len(response['related_features']) >= 3  # Suggest specific features

    def test_chatbot_answers_pricing_question(self):
        """
        Test: Chatbot answers pricing questions

        REQUIREMENT: Provide pricing information and suggest sales contact
        """
        from demo_data_generator import generate_chatbot_response

        question = "How much does this cost?"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should include pricing guidance
        assert 'price' in response['answer'].lower() or 'pricing' in response['answer'].lower()
        assert 'next_step' in response  # Suggest contacting sales
        assert response['next_step']['type'] in ['contact_sales', 'view_pricing']

    def test_chatbot_answers_use_case_question(self):
        """
        Test: Chatbot answers "Who is this for?" questions

        REQUIREMENT: Explain target users and use cases
        """
        from demo_data_generator import generate_chatbot_response

        question = "Who is this platform for?"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should mention target audiences
        answer_lower = response['answer'].lower()
        assert any(word in answer_lower for word in ['instructor', 'teacher', 'student', 'organization'])


class TestDemoChatbotContextAwareness:
    """
    Test Suite: Demo Chatbot Context-Aware Responses

    BUSINESS CONTEXT:
    Like a good salesperson, chatbot should remember previous conversation
    and provide contextually relevant follow-up answers.
    """

    def test_chatbot_uses_conversation_history(self):
        """
        Test: Chatbot provides context-aware follow-up responses

        REQUIREMENT: Remember previous questions and provide relevant follow-ups
        """
        from demo_data_generator import generate_chatbot_response

        # First question
        conversation_history = []
        question1 = "Tell me about AI features"
        response1 = generate_chatbot_response(question1, conversation_history)

        # Second question (follow-up)
        conversation_history.append({'question': question1, 'answer': response1['answer']})
        question2 = "Can you show me an example?"
        response2 = generate_chatbot_response(question2, conversation_history)

        # Should reference AI features from context
        assert 'ai' in response2['answer'].lower() or 'example' in response2['answer'].lower()
        assert 'context_used' in response2
        assert response2['context_used'] is True

    def test_chatbot_tracks_user_interest_areas(self):
        """
        Test: Chatbot identifies user's areas of interest from questions

        REQUIREMENT: Track interest areas for lead qualification
        """
        from demo_data_generator import generate_chatbot_response

        conversation_history = []
        questions = [
            "Tell me about AI content generation",
            "How does the lab environment work?",
            "What about analytics dashboards?"
        ]

        all_responses = []
        for question in questions:
            response = generate_chatbot_response(question, conversation_history)
            all_responses.append(response)
            conversation_history.append({'question': question, 'answer': response['answer']})

        # Last response should include interest tracking
        last_response = all_responses[-1]
        assert 'user_interests' in last_response
        assert len(last_response['user_interests']) >= 2
        assert 'ai' in last_response['user_interests']
        assert 'labs' in last_response['user_interests'] or 'analytics' in last_response['user_interests']


class TestDemoChatbotFeatureDeepDive:
    """
    Test Suite: Demo Chatbot Feature-Specific Explanations

    BUSINESS CONTEXT:
    When users ask about specific features, chatbot should provide detailed
    explanations with examples, like a salesperson giving a product demo.
    """

    def test_chatbot_explains_ai_content_generation(self):
        """
        Test: Chatbot provides detailed AI content generation explanation

        REQUIREMENT: Explain AI features with concrete examples
        """
        from demo_data_generator import generate_chatbot_response

        question = "How does AI content generation work?"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should provide detailed explanation with examples
        assert 'answer' in response
        assert len(response['answer']) > 100  # Detailed response
        assert 'example' in response
        assert response['example']['feature'] == 'ai_content_generation'
        assert 'demo_available' in response['example']

    def test_chatbot_explains_docker_labs(self):
        """
        Test: Chatbot explains Docker lab environments

        REQUIREMENT: Explain technical features in accessible language
        """
        from demo_data_generator import generate_chatbot_response

        question = "What are Docker lab environments?"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should explain in accessible terms
        assert 'example' in response
        assert 'hands-on' in response['answer'].lower() or 'practice' in response['answer'].lower()

    def test_chatbot_explains_rag_knowledge_graph(self):
        """
        Test: Chatbot explains RAG knowledge graph feature

        REQUIREMENT: Explain complex features with benefits focus
        """
        from demo_data_generator import generate_chatbot_response

        question = "What is the knowledge graph?"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should focus on benefits, not just technical details
        assert 'benefit' in response or 'benefits' in response
        assert 'personalized' in response['answer'].lower() or 'adaptive' in response['answer'].lower()


class TestDemoChatbotLeadQualification:
    """
    Test Suite: Demo Chatbot Lead Qualification

    BUSINESS CONTEXT:
    Chatbot should identify serious prospects and route them to sales team,
    like a salesperson qualifying leads.
    """

    def test_chatbot_detects_high_intent_questions(self):
        """
        Test: Chatbot identifies high-intent purchase questions

        REQUIREMENT: Flag users asking about pricing, implementation, timelines
        """
        from demo_data_generator import generate_chatbot_response

        high_intent_questions = [
            "How much does this cost for 100 users?",
            "How long does implementation take?",
            "Do you offer enterprise support?"
        ]

        for question in high_intent_questions:
            response = generate_chatbot_response(question, [])

            assert 'lead_score' in response
            assert response['lead_score'] >= 7  # High score (out of 10)
            assert 'sales_action_recommended' in response
            assert response['sales_action_recommended'] is True

    def test_chatbot_provides_next_steps_for_qualified_leads(self):
        """
        Test: Chatbot suggests appropriate next steps

        REQUIREMENT: Guide qualified leads toward conversion
        """
        from demo_data_generator import generate_chatbot_response

        question = "I need this for my organization of 500 students"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should suggest concrete next steps
        assert 'next_step' in response
        assert response['next_step']['type'] in ['schedule_demo', 'contact_sales', 'start_trial']
        assert 'contact_info_form' in response['next_step']


class TestDemoChatbotCommonQuestions:
    """
    Test Suite: Demo Chatbot Common Questions Tracking

    BUSINESS CONTEXT:
    Track frequently asked questions for marketing insights and
    product improvement, like analyzing customer feedback.
    """

    def test_chatbot_categorizes_question_type(self):
        """
        Test: Chatbot categorizes each question for analytics

        REQUIREMENT: Track question categories for insights
        """
        from demo_data_generator import generate_chatbot_response

        questions_and_categories = [
            ("What is this platform?", "product_overview"),
            ("How much does it cost?", "pricing"),
            ("How does AI work?", "feature_specific"),
            ("Who uses this?", "use_cases")
        ]

        for question, expected_category in questions_and_categories:
            response = generate_chatbot_response(question, [])

            assert 'question_category' in response
            assert response['question_category'] == expected_category

    def test_chatbot_tracks_question_for_analytics(self):
        """
        Test: Chatbot returns analytics data for each question

        REQUIREMENT: Collect data for marketing team
        """
        from demo_data_generator import generate_chatbot_response

        question = "Tell me about analytics features"
        conversation_history = []

        response = generate_chatbot_response(question, conversation_history)

        # Should include analytics tracking
        assert 'analytics_data' in response
        analytics = response['analytics_data']
        assert 'timestamp' in analytics
        assert 'question_length' in analytics
        assert 'response_time_ms' in analytics
        assert 'feature_mentioned' in analytics


class TestDemoChatbotConversionPrompts:
    """
    Test Suite: Demo Chatbot Conversion Prompts

    BUSINESS CONTEXT:
    Chatbot should naturally guide users toward conversion actions
    without being pushy, like a skilled salesperson.
    """

    def test_chatbot_suggests_live_demo_after_multiple_questions(self):
        """
        Test: Chatbot suggests live demo after user shows interest

        REQUIREMENT: Convert interested users to demo requests
        """
        from demo_data_generator import generate_chatbot_response

        # Simulate interested user asking multiple questions
        conversation_history = []
        questions = [
            "What features do you have?",
            "How does AI work?",
            "Tell me about labs",
            "What about analytics?"
        ]

        for question in questions:
            response = generate_chatbot_response(question, conversation_history)
            conversation_history.append({'question': question, 'answer': response['answer']})

        # After 4+ questions, should suggest demo
        last_response = response
        assert 'conversion_prompt' in last_response
        assert 'schedule_demo' in last_response['conversion_prompt'] or 'live_demo' in last_response['conversion_prompt']

    def test_chatbot_offers_trial_signup_to_engaged_users(self):
        """
        Test: Chatbot offers trial signup at appropriate time

        REQUIREMENT: Convert engaged users to trial signups
        """
        from demo_data_generator import generate_chatbot_response

        question = "This looks great! Can I try it out?"
        conversation_history = [
            {'question': 'What is this?', 'answer': 'Platform overview...'},
            {'question': 'How does it work?', 'answer': 'Feature explanation...'}
        ]

        response = generate_chatbot_response(question, conversation_history)

        # Should offer trial signup
        assert 'next_step' in response
        assert response['next_step']['type'] in ['start_trial', 'create_account']
        assert 'registration_url' in response['next_step']


# Mark all tests in this file as TDD RED phase
pytestmark = pytest.mark.tdd_red
