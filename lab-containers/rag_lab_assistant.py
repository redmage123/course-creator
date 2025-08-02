"""
RAG-Enhanced Lab Assistant - Intelligent Programming Help and Learning System

BUSINESS REQUIREMENT:
Implement a comprehensive RAG-enhanced lab assistant that provides progressively
smarter programming help, debugging assistance, and educational guidance by
learning from student interactions, successful problem solutions, and accumulated
programming knowledge across all lab sessions.

TECHNICAL ARCHITECTURE:
This lab assistant integrates with the RAG service to provide:
1. **Context-Aware Programming Help**: Intelligent assistance based on student's
   current code, problem context, and accumulated knowledge from similar situations
2. **Progressive Learning**: Continuous improvement through learning from successful
   solutions, debugging patterns, and effective teaching approaches
3. **Personalized Assistance**: Tailored help based on student's skill level,
   learning progress, and interaction history
4. **Multi-Language Support**: Comprehensive programming assistance across various
   languages and frameworks used in lab environments

RAG-ENHANCED CAPABILITIES:
- **Code Pattern Recognition**: Learn from successful code implementations
- **Debugging Intelligence**: Accumulate knowledge of effective debugging strategies
- **Concept Explanation**: Build repository of effective programming concept explanations
- **Error Resolution**: Learn from successful error resolution patterns
- **Learning Path Optimization**: Understand which explanations work best for different students

INTEGRATION POINTS:
- Lab Container Management: Real-time assistance during coding sessions
- Student Progress Tracking: Learn from student success patterns
- Code Analysis: Intelligent code review and suggestion system
- Educational Content: Integration with course materials and assignments
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum

import httpx
import ast
from pydantic import BaseModel

from logging_setup import setup_logging

# Setup logging
logger = setup_logging(__name__)

class AssistanceType(Enum):
    """
    Types of programming assistance provided by the RAG-enhanced lab assistant
    
    ASSISTANCE CATEGORIZATION:
    Different types of help require different RAG context and learning approaches:
    - DEBUGGING: Error analysis and resolution strategies
    - CODE_REVIEW: Code quality assessment and improvement suggestions
    - CONCEPT_EXPLANATION: Programming concept clarification and examples
    - IMPLEMENTATION_HELP: Guidance on implementing specific functionality
    - OPTIMIZATION: Performance and code quality optimization suggestions
    """
    DEBUGGING = "debugging"
    CODE_REVIEW = "code_review"
    CONCEPT_EXPLANATION = "concept_explanation"
    IMPLEMENTATION_HELP = "implementation_help"
    OPTIMIZATION = "optimization"
    GENERAL_QUESTION = "general_question"

class SkillLevel(Enum):
    """Student skill level classification for personalized assistance"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

@dataclass
class CodeContext:
    """
    Comprehensive code context for RAG-enhanced assistance
    
    CONTEXT INTELLIGENCE:
    Captures all relevant information about the student's current coding situation
    to enable the RAG system to provide the most appropriate and helpful assistance.
    """
    code: str
    language: str
    file_name: str
    error_message: Optional[str] = None
    line_number: Optional[int] = None
    function_context: Optional[str] = None
    imports: List[str] = None
    student_intent: Optional[str] = None
    
    def __post_init__(self):
        if self.imports is None:
            self.imports = []

@dataclass
class StudentContext:
    """
    Student learning context for personalized assistance
    
    PERSONALIZATION DATA:
    Information about the student's learning journey, preferences, and progress
    to enable personalized and effective assistance delivery.
    """
    student_id: str
    skill_level: SkillLevel
    preferred_explanation_style: str  # "detailed", "concise", "example-heavy"
    learning_goals: List[str]
    recent_topics: List[str]
    common_mistakes: List[str]
    successful_patterns: List[str]
    
    def __post_init__(self):
        if not isinstance(self.skill_level, SkillLevel):
            self.skill_level = SkillLevel(self.skill_level)

@dataclass
class AssistanceRequest:
    """
    Comprehensive assistance request structure for RAG-enhanced help
    
    REQUEST INTELLIGENCE:
    Combines code context, student context, and specific assistance needs
    to enable the RAG system to provide the most relevant and effective help.
    """
    assistance_type: AssistanceType
    code_context: CodeContext
    student_context: StudentContext
    specific_question: str
    priority_level: str  # "low", "medium", "high", "urgent"
    timestamp: datetime
    
    def __post_init__(self):
        if not isinstance(self.assistance_type, AssistanceType):
            self.assistance_type = AssistanceType(self.assistance_type)

@dataclass
class AssistanceResponse:
    """
    Comprehensive assistance response with learning integration
    
    RESPONSE INTELLIGENCE:
    Provides not just the answer but also learning data for continuous
    improvement of the assistance system.
    """
    response_text: str
    code_examples: List[str]
    helpful_links: List[str]
    confidence_score: float
    reasoning: str
    rag_context_used: str
    learning_feedback: Dict[str, Any]
    response_metadata: Dict[str, Any]

class RAGLabAssistant:
    """
    RAG-Enhanced Lab Assistant for Intelligent Programming Help
    
    ARCHITECTURAL RESPONSIBILITY:
    Provides comprehensive programming assistance that learns and improves over time
    through RAG integration, offering personalized help that becomes more effective
    with each student interaction.
    
    INTELLIGENCE FEATURES:
    - Context-aware assistance based on code and learning situation
    - Progressive learning from successful problem resolutions
    - Personalized help adapted to student skill level and preferences
    - Multi-language programming support with specialized knowledge bases
    - Error pattern recognition and resolution strategy optimization
    """
    
    def __init__(self, rag_service_url: str = "http://rag-service:8009"):
        """
        Initialize RAG-Enhanced Lab Assistant
        
        RAG INTEGRATION CONFIGURATION:
        - HTTP client for RAG service communication
        - Circuit breaker for service reliability
        - Performance monitoring and optimization
        - Multi-domain knowledge base access
        """
        self.rag_service_url = rag_service_url.rstrip('/')
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 3
        self.circuit_breaker_reset_time = 300  # 5 minutes
        self.last_failure_time = None
        
        # Assistant performance metrics
        self.assistance_stats = {
            "total_requests": 0,
            "successful_responses": 0,
            "rag_enhanced_responses": 0,
            "learning_operations": 0
        }
        
        logger.info(f"RAG Lab Assistant initialized with RAG service: {rag_service_url}")
    
    async def is_rag_service_available(self) -> bool:
        """
        Check RAG service availability with circuit breaker pattern
        
        RELIABILITY STRATEGY:
        Ensures lab assistant can function even when RAG service is temporarily
        unavailable, providing graceful degradation and automatic recovery.
        """
        try:
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                if self.last_failure_time and (
                    time.time() - self.last_failure_time < self.circuit_breaker_reset_time
                ):
                    return False
                else:
                    # Reset circuit breaker
                    self.circuit_breaker_failures = 0
                    self.last_failure_time = None
            
            response = await self.http_client.get(f"{self.rag_service_url}/api/v1/rag/health")
            if response.status_code == 200:
                self.circuit_breaker_failures = 0
                return True
            else:
                self._record_failure()
                return False
                
        except Exception as e:
            logger.warning(f"RAG service health check failed: {str(e)}")
            self._record_failure()
            return False
    
    def _record_failure(self):
        """Record RAG service failure for circuit breaker logic"""
        self.circuit_breaker_failures += 1
        self.last_failure_time = time.time()
        logger.warning(f"RAG service failure recorded: {self.circuit_breaker_failures}/{self.circuit_breaker_threshold}")
    
    async def provide_assistance(self, request: AssistanceRequest) -> AssistanceResponse:
        """
        Provide RAG-enhanced programming assistance
        
        ASSISTANCE WORKFLOW:
        1. Analyze code context and student needs
        2. Query RAG system for relevant programming knowledge
        3. Generate contextual assistance using accumulated wisdom
        4. Learn from interaction for continuous improvement
        5. Provide comprehensive response with examples and explanations
        
        INTELLIGENCE ENHANCEMENT:
        - Code pattern matching with successful solutions
        - Error pattern recognition and resolution strategies
        - Personalized explanation styles based on student preferences
        - Learning from successful teaching interactions
        
        Args:
            request: Comprehensive assistance request with context
        
        Returns:
            AssistanceResponse with RAG-enhanced help and learning data
        """
        self.assistance_stats["total_requests"] += 1
        
        try:
            # Generate RAG-enhanced response
            rag_context = ""
            rag_available = await self.is_rag_service_available()
            
            if rag_available:
                rag_context = await self._get_rag_context(request)
                self.assistance_stats["rag_enhanced_responses"] += 1
            else:
                logger.warning("RAG service unavailable, providing standard assistance")
            
            # Generate assistance response
            response = await self._generate_assistance_response(request, rag_context)
            
            # Learn from this interaction asynchronously
            if rag_available:
                asyncio.create_task(self._learn_from_assistance(request, response))
            
            self.assistance_stats["successful_responses"] += 1
            logger.info(f"Provided {request.assistance_type.value} assistance for {request.code_context.language}")
            
            return response
            
        except Exception as e:
            logger.error(f"Assistance provision failed: {str(e)}")
            return self._generate_fallback_response(request, str(e))
    
    async def _get_rag_context(self, request: AssistanceRequest) -> str:
        """
        Retrieve relevant context from RAG system for assistance
        
        RAG QUERY STRATEGY:
        - Multi-faceted queries for comprehensive context retrieval
        - Language-specific knowledge base queries
        - Error pattern and solution retrieval
        - Student skill level appropriate content filtering
        """
        try:
            # Construct RAG query based on assistance type and context
            query_parts = []
            
            # Add assistance type context
            query_parts.append(f"{request.assistance_type.value} help")
            
            # Add programming language context
            if request.code_context.language:
                query_parts.append(f"{request.code_context.language} programming")
            
            # Add specific question context
            if request.specific_question:
                query_parts.append(request.specific_question)
            
            # Add error context if available
            if request.code_context.error_message:
                query_parts.append(f"error: {request.code_context.error_message}")
            
            query = " ".join(query_parts)
            
            # Prepare metadata filter for targeted retrieval
            metadata_filter = {
                "programming_language": request.code_context.language,
                "problem_type": request.assistance_type.value,
                "student_level": request.student_context.skill_level.value
            }
            
            # Query RAG system
            query_request = {
                "query": query,
                "domain": "lab_assistant",
                "n_results": 5,
                "metadata_filter": metadata_filter
            }
            
            response = await self.http_client.post(
                f"{self.rag_service_url}/api/v1/rag/query",
                json=query_request
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("enhanced_context", "")
            else:
                logger.warning(f"RAG query failed with status {response.status_code}")
                self._record_failure()
                return ""
                
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {str(e)}")
            self._record_failure()
            return ""
    
    async def _generate_assistance_response(
        self,
        request: AssistanceRequest,
        rag_context: str
    ) -> AssistanceResponse:
        """
        Generate comprehensive assistance response using RAG context
        
        RESPONSE GENERATION STRATEGY:
        - Integrate RAG context with current code situation
        - Adapt explanation style to student skill level and preferences
        - Provide practical examples and actionable guidance
        - Include relevant resources and learning materials
        """
        
        # Analyze code context for specific insights
        code_insights = self._analyze_code_context(request.code_context)
        
        # Generate response based on assistance type
        response_text = ""
        code_examples = []
        helpful_links = []
        reasoning = ""
        
        if request.assistance_type == AssistanceType.DEBUGGING:
            response_text, code_examples, reasoning = await self._generate_debugging_help(
                request, rag_context, code_insights
            )
        elif request.assistance_type == AssistanceType.CODE_REVIEW:
            response_text, code_examples, reasoning = await self._generate_code_review(
                request, rag_context, code_insights
            )
        elif request.assistance_type == AssistanceType.CONCEPT_EXPLANATION:
            response_text, code_examples, reasoning = await self._generate_concept_explanation(
                request, rag_context, code_insights
            )
        elif request.assistance_type == AssistanceType.IMPLEMENTATION_HELP:
            response_text, code_examples, reasoning = await self._generate_implementation_help(
                request, rag_context, code_insights
            )
        else:
            response_text = await self._generate_general_help(request, rag_context, code_insights)
            reasoning = "General assistance based on available context"
        
        # Calculate confidence score based on RAG context quality
        confidence_score = self._calculate_confidence_score(rag_context, code_insights)
        
        return AssistanceResponse(
            response_text=response_text,
            code_examples=code_examples,
            helpful_links=helpful_links,
            confidence_score=confidence_score,
            reasoning=reasoning,
            rag_context_used=rag_context[:500] if rag_context else "",  # Truncate for storage
            learning_feedback={
                "assistance_type": request.assistance_type.value,
                "student_level": request.student_context.skill_level.value,
                "code_language": request.code_context.language,
                "context_quality": len(rag_context) > 0
            },
            response_metadata={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "rag_enhanced": bool(rag_context),
                "code_analysis_insights": len(code_insights)
            }
        )
    
    def _analyze_code_context(self, code_context: CodeContext) -> Dict[str, Any]:
        """
        Analyze code context to extract insights for assistance
        
        CODE ANALYSIS FEATURES:
        - Syntax analysis and structure assessment
        - Import and dependency analysis
        - Function and variable extraction
        - Error location and context analysis
        - Code complexity and quality metrics
        """
        insights = {
            "has_syntax_errors": False,
            "complexity_level": "simple",
            "functions_defined": [],
            "variables_used": [],
            "imports_analysis": {},
            "potential_issues": []
        }
        
        try:
            if code_context.code and code_context.language.lower() == "python":
                # Python-specific analysis
                try:
                    tree = ast.parse(code_context.code)
                    
                    # Extract functions
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            insights["functions_defined"].append(node.name)
                        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                            insights["variables_used"].append(node.id)
                    
                    # Analyze imports
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                insights["imports_analysis"][alias.name] = "import"
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ""
                            for alias in node.names:
                                insights["imports_analysis"][f"{module}.{alias.name}"] = "from_import"
                    
                except SyntaxError as e:
                    insights["has_syntax_errors"] = True
                    insights["syntax_error_details"] = str(e)
            
            # General code quality analysis
            lines = code_context.code.split('\n')
            insights["line_count"] = len(lines)
            insights["non_empty_lines"] = len([line for line in lines if line.strip()])
            
            # Complexity estimation
            if insights["line_count"] > 50:
                insights["complexity_level"] = "complex"
            elif insights["line_count"] > 20:
                insights["complexity_level"] = "moderate"
                
        except Exception as e:
            logger.warning(f"Code analysis failed: {str(e)}")
            insights["analysis_error"] = str(e)
        
        return insights
    
    async def _generate_debugging_help(
        self,
        request: AssistanceRequest,
        rag_context: str,
        code_insights: Dict[str, Any]
    ) -> Tuple[str, List[str], str]:
        """
        Generate debugging assistance with RAG-enhanced context
        
        DEBUGGING INTELLIGENCE:
        - Error pattern recognition from accumulated knowledge
        - Solution strategies from successful debugging sessions
        - Code-specific debugging approaches
        - Step-by-step debugging guidance
        """
        
        response_parts = []
        code_examples = []
        
        # Error analysis
        if request.code_context.error_message:
            response_parts.append(f"**Error Analysis:**\n{request.code_context.error_message}")
            
            # Add RAG context if available
            if rag_context:
                response_parts.append(f"\n**Similar Issues and Solutions:**\n{rag_context}")
        
        # Code-specific debugging suggestions
        if code_insights.get("has_syntax_errors"):
            response_parts.append("\n**Syntax Issues Detected:**")
            response_parts.append("- Check for missing colons, parentheses, or indentation issues")
            response_parts.append("- Verify variable names and function calls are spelled correctly")
        
        # Debugging steps based on programming language
        if request.code_context.language.lower() == "python":
            response_parts.append("\n**Python Debugging Steps:**")
            response_parts.append("1. Add print statements to trace variable values")
            response_parts.append("2. Use the Python debugger (pdb) for step-by-step execution")
            response_parts.append("3. Check data types and variable scopes")
            
            code_examples.append("""
# Debug example: Add print statements
def debug_function(x, y):
    print(f"Input values: x={x}, y={y}")  # Debug line
    result = x + y
    print(f"Result: {result}")  # Debug line
    return result
""")
        
        reasoning = "Generated debugging help based on error context and accumulated debugging knowledge"
        
        return "\n".join(response_parts), code_examples, reasoning
    
    async def _generate_code_review(
        self,
        request: AssistanceRequest,
        rag_context: str,
        code_insights: Dict[str, Any]
    ) -> Tuple[str, List[str], str]:
        """Generate code review assistance with best practices"""
        
        response_parts = ["**Code Review Analysis:**"]
        code_examples = []
        
        # Structure analysis
        if code_insights.get("complexity_level") == "complex":
            response_parts.append("- Consider breaking down complex functions into smaller, focused functions")
        
        # Add RAG context for best practices
        if rag_context:
            response_parts.append(f"\n**Best Practices from Similar Code:**\n{rag_context}")
        
        # Language-specific suggestions
        if request.code_context.language.lower() == "python":
            response_parts.append("\n**Python Best Practices:**")
            response_parts.append("- Follow PEP 8 style guidelines")
            response_parts.append("- Use descriptive variable and function names")
            response_parts.append("- Add docstrings to functions and classes")
            
            if code_insights.get("functions_defined"):
                code_examples.append("""
# Good practice: Function with docstring
def calculate_area(length, width):
    \"\"\"
    Calculate the area of a rectangle.
    
    Args:
        length (float): Length of the rectangle
        width (float): Width of the rectangle
    
    Returns:
        float: Area of the rectangle
    \"\"\"
    return length * width
""")
        
        reasoning = "Generated code review based on code analysis and best practices knowledge"
        
        return "\n".join(response_parts), code_examples, reasoning
    
    async def _generate_concept_explanation(
        self,
        request: AssistanceRequest,
        rag_context: str,
        code_insights: Dict[str, Any]
    ) -> Tuple[str, List[str], str]:
        """Generate concept explanation with examples"""
        
        response_parts = [f"**Concept Explanation: {request.specific_question}**"]
        code_examples = []
        
        # Add RAG context for detailed explanations
        if rag_context:
            response_parts.append(f"\n{rag_context}")
        else:
            response_parts.append("\nI'll explain this concept based on general programming principles.")
        
        # Adapt explanation to skill level
        if request.student_context.skill_level == SkillLevel.BEGINNER:
            response_parts.append("\n**Simple Explanation:**")
            response_parts.append("Let me break this down into easy-to-understand parts...")
        elif request.student_context.skill_level == SkillLevel.ADVANCED:
            response_parts.append("\n**Advanced Details:**")
            response_parts.append("Here are the technical details and advanced considerations...")
        
        reasoning = "Generated concept explanation adapted to student skill level"
        
        return "\n".join(response_parts), code_examples, reasoning
    
    async def _generate_implementation_help(
        self,
        request: AssistanceRequest,
        rag_context: str,
        code_insights: Dict[str, Any]
    ) -> Tuple[str, List[str], str]:
        """Generate implementation guidance"""
        
        response_parts = ["**Implementation Guidance:**"]
        code_examples = []
        
        # Add RAG context for implementation patterns
        if rag_context:
            response_parts.append(f"\n**Similar Implementation Patterns:**\n{rag_context}")
        
        # Step-by-step guidance
        response_parts.append("\n**Implementation Steps:**")
        response_parts.append("1. Plan your approach and identify key components")
        response_parts.append("2. Start with a simple version and iterate")
        response_parts.append("3. Test each component as you build")
        
        reasoning = "Generated implementation help with step-by-step guidance"
        
        return "\n".join(response_parts), code_examples, reasoning
    
    async def _generate_general_help(
        self,
        request: AssistanceRequest,
        rag_context: str,
        code_insights: Dict[str, Any]
    ) -> str:
        """Generate general programming help"""
        
        response_parts = ["I'm here to help with your programming question!"]
        
        if rag_context:
            response_parts.append(f"\n**Relevant Information:**\n{rag_context}")
        
        response_parts.append("\nFeel free to ask more specific questions about:")
        response_parts.append("- Debugging errors")
        response_parts.append("- Code review and improvements")
        response_parts.append("- Programming concepts")
        response_parts.append("- Implementation guidance")
        
        return "\n".join(response_parts)
    
    def _calculate_confidence_score(self, rag_context: str, code_insights: Dict[str, Any]) -> float:
        """Calculate confidence score for the assistance response"""
        
        score = 0.5  # Base confidence
        
        # Boost confidence with RAG context
        if rag_context and len(rag_context) > 100:
            score += 0.3
        
        # Boost confidence with code analysis
        if code_insights and not code_insights.get("analysis_error"):
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_fallback_response(self, request: AssistanceRequest, error: str) -> AssistanceResponse:
        """Generate fallback response when assistance fails"""
        
        return AssistanceResponse(
            response_text=f"I encountered an issue providing assistance: {error}. Please try rephrasing your question or check your code syntax.",
            code_examples=[],
            helpful_links=[],
            confidence_score=0.1,
            reasoning="Fallback response due to system error",
            rag_context_used="",
            learning_feedback={"error": error},
            response_metadata={
                "fallback": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    
    async def _learn_from_assistance(self, request: AssistanceRequest, response: AssistanceResponse):
        """
        Learn from assistance interaction for continuous improvement
        
        LEARNING STRATEGY:
        - Store successful assistance patterns
        - Learn from code contexts and effective solutions
        - Build knowledge base of programming help interactions
        - Improve assistance quality over time
        """
        try:
            learning_data = {
                "assistance_type": request.assistance_type.value,
                "programming_language": request.code_context.language,
                "student_level": request.student_context.skill_level.value,
                "question": request.specific_question,
                "response_confidence": response.confidence_score,
                "context_analysis": request.code_context.error_message or "no_error",
                "interaction_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add document to RAG system
            add_document_request = {
                "content": f"Q: {request.specific_question}\nA: {response.response_text[:1000]}",  # Truncate
                "domain": "lab_assistant",
                "source": "assistance_interaction",
                "metadata": {
                    "programming_language": request.code_context.language,
                    "problem_type": request.assistance_type.value,
                    "student_level": request.student_context.skill_level.value,
                    "success": response.confidence_score > 0.7,
                    "complexity": len(request.code_context.code) > 100
                }
            }
            
            response_doc = await self.http_client.post(
                f"{self.rag_service_url}/api/v1/rag/add-document",
                json=add_document_request
            )
            
            # Learn from interaction
            learning_request = {
                "interaction_type": "lab_assistance",
                "content": json.dumps(learning_data),
                "success": response.confidence_score > 0.7,
                "feedback": "",
                "quality_score": response.confidence_score,
                "metadata": learning_data
            }
            
            await self.http_client.post(
                f"{self.rag_service_url}/api/v1/rag/learn",
                json=learning_request
            )
            
            self.assistance_stats["learning_operations"] += 1
            logger.info(f"Learned from {request.assistance_type.value} assistance interaction")
            
        except Exception as e:
            logger.error(f"Learning from assistance failed: {str(e)}")
    
    async def get_assistance_stats(self) -> Dict[str, Any]:
        """Get lab assistant performance statistics"""
        
        try:
            # Get RAG service stats
            rag_stats = {}
            if await self.is_rag_service_available():
                response = await self.http_client.get(f"{self.rag_service_url}/api/v1/rag/stats")
                if response.status_code == 200:
                    rag_stats = response.json()
            
            return {
                "assistant_stats": self.assistance_stats,
                "rag_service_stats": rag_stats,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get assistance stats: {str(e)}")
            return {"error": str(e)}
    
    async def close(self):
        """Close HTTP client and cleanup resources"""
        await self.http_client.aclose()
        logger.info("RAG Lab Assistant closed")

# Global RAG lab assistant instance
rag_lab_assistant = RAGLabAssistant()

# Convenience functions for lab integration
async def get_programming_help(
    code: str,
    language: str,
    question: str,
    error_message: Optional[str] = None,
    student_id: str = "anonymous",
    skill_level: str = "intermediate"
) -> AssistanceResponse:
    """
    Convenience function for getting programming help
    
    SIMPLE INTERFACE:
    Provides easy access to RAG-enhanced programming assistance
    for integration with lab environments and coding interfaces.
    """
    
    code_context = CodeContext(
        code=code,
        language=language,
        file_name="current_file",
        error_message=error_message
    )
    
    student_context = StudentContext(
        student_id=student_id,
        skill_level=SkillLevel(skill_level),
        preferred_explanation_style="detailed",
        learning_goals=[],
        recent_topics=[],
        common_mistakes=[],
        successful_patterns=[]
    )
    
    assistance_request = AssistanceRequest(
        assistance_type=AssistanceType.DEBUGGING if error_message else AssistanceType.GENERAL_QUESTION,
        code_context=code_context,
        student_context=student_context,
        specific_question=question,
        priority_level="medium",
        timestamp=datetime.now(timezone.utc)
    )
    
    return await rag_lab_assistant.provide_assistance(assistance_request)

# Export key components for lab integration
__all__ = [
    'RAGLabAssistant',
    'AssistanceRequest',
    'AssistanceResponse', 
    'CodeContext',
    'StudentContext',
    'AssistanceType',
    'SkillLevel',
    'get_programming_help',
    'rag_lab_assistant'
]