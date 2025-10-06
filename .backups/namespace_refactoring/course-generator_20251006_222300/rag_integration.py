"""
RAG Integration for Course Generator Service - Enhanced AI Content Generation

BUSINESS REQUIREMENT:
Integrate Retrieval-Augmented Generation (RAG) capabilities into the course generation
workflow to create progressively smarter, more contextual, and higher-quality
educational content by leveraging accumulated knowledge and successful generation patterns.

TECHNICAL ARCHITECTURE:
This module provides seamless integration between the Course Generator Service and
the RAG Service, enabling AI content generation that benefits from:
1. Historical successful content generation patterns
2. User feedback and quality assessments
3. Subject-specific knowledge accumulation
4. Content type optimization based on past performance

INTEGRATION STRATEGY:
- **Pre-Generation Context Enhancement**: RAG retrieval before AI generation
- **Post-Generation Learning**: Store successful generations for future reference
- **Quality-Based Learning**: Learn from user feedback and content effectiveness
- **Domain-Specific Optimization**: Specialized knowledge bases for different subjects

RAG-ENHANCED GENERATION WORKFLOW:
1. Query RAG system for relevant context based on generation requirements
2. Enhance AI prompts with retrieved knowledge and successful patterns
3. Generate content using Claude/OpenAI with enriched context
4. Store successful generations and user feedback in RAG system
5. Continuously improve through accumulated knowledge and user interactions
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from pydantic import BaseModel

from logging_setup import setup_docker_logging

# Setup logging
logger = setup_docker_logging("course-generator")

@dataclass
class RAGEnhancedPrompt:
    """
    RAG-Enhanced Prompt Structure for Content Generation
    
    BUSINESS PURPOSE:
    Combines original generation requirements with retrieved contextual knowledge
    to create more effective AI prompts that leverage accumulated experience.
    
    TECHNICAL IMPLEMENTATION:
    - Original prompt preservation for comparison
    - Context integration with source attribution
    - Quality metrics for effectiveness tracking
    - Metadata for learning and optimization
    """
    original_prompt: str
    enhanced_prompt: str
    retrieved_context: str
    context_sources: List[str]
    enhancement_metadata: Dict[str, Any]
    generation_timestamp: datetime

@dataclass 
class ContentGenerationResult:
    """
    Enhanced Content Generation Result with RAG Integration
    
    Comprehensive result structure that includes both the generated content
    and the RAG-enhanced context used for generation, enabling learning
    and continuous improvement of the content generation process.
    """
    content: str
    content_type: str
    generation_method: str  # 'rag_enhanced', 'standard', 'fallback'
    rag_context_used: str
    quality_score: float
    generation_metadata: Dict[str, Any]
    learning_data: Dict[str, Any]

class RAGIntegrationService:
    """
    RAG Integration Service for Enhanced Content Generation
    
    ARCHITECTURAL RESPONSIBILITY:
    Manages the integration between content generation workflows and the RAG system,
    providing context enhancement, learning from generations, and continuous
    improvement of AI-powered educational content creation.
    
    DESIGN PATTERNS:
    - Strategy pattern for different RAG enhancement approaches
    - Decorator pattern for prompt enhancement
    - Observer pattern for learning from generation results
    - Circuit breaker pattern for RAG service reliability
    """
    
    def __init__(self, rag_service_url: str = "http://rag-service:8009"):
        """
        Initialize RAG Integration Service
        
        RAG SERVICE CONFIGURATION:
        - HTTP client for RAG service communication
        - Circuit breaker for service reliability
        - Retry logic for transient failures
        - Performance monitoring and optimization
        """
        self.rag_service_url = rag_service_url.rstrip('/')
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.circuit_breaker_failures = 0
        self.circuit_breaker_threshold = 3
        self.circuit_breaker_reset_time = 300  # 5 minutes
        self.last_failure_time = None
        
        logger.info(f"RAG Integration Service initialized with URL: {rag_service_url}")
    
    async def is_rag_service_available(self) -> bool:
        """
        Check RAG service availability with circuit breaker pattern
        
        RELIABILITY STRATEGY:
        - Circuit breaker to prevent cascading failures
        - Fast failure detection and recovery
        - Graceful degradation when RAG is unavailable
        - Automatic service recovery detection
        """
        try:
            # Check circuit breaker state
            if self.circuit_breaker_failures >= self.circuit_breaker_threshold:
                if self.last_failure_time and (
                    time.time() - self.last_failure_time < self.circuit_breaker_reset_time
                ):
                    return False
                else:
                    # Reset circuit breaker after timeout
                    self.circuit_breaker_failures = 0
                    self.last_failure_time = None
            
            # Health check
            response = await self.http_client.get(f"{self.rag_service_url}/api/v1/rag/health")
            if response.status_code == 200:
                self.circuit_breaker_failures = 0  # Reset on success
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
    
    async def enhance_content_generation_prompt(
        self,
        content_type: str,
        subject: str,
        difficulty_level: str,
        original_prompt: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> RAGEnhancedPrompt:
        """
        Enhance content generation prompt with RAG-retrieved context
        
        PROMPT ENHANCEMENT PROCESS:
        1. Query RAG system for relevant educational content patterns
        2. Retrieve successful generation examples from similar contexts
        3. Extract effective pedagogical approaches and structures
        4. Integrate retrieved knowledge into enhanced prompt
        5. Preserve original prompt for comparison and fallback
        
        CONTEXTUAL INTELLIGENCE:
        The enhanced prompt incorporates accumulated knowledge about:
        - Successful content structures for specific subjects
        - Effective difficulty progression patterns
        - User-preferred educational formats and styles
        - Subject-specific terminology and concepts
        
        Args:
            content_type: Type of content to generate (syllabus, slide, quiz, exercise)
            subject: Academic subject or topic
            difficulty_level: Content difficulty (beginner, intermediate, advanced)
            original_prompt: Original AI generation prompt
            additional_context: Optional additional context metadata
        
        Returns:
            RAGEnhancedPrompt with integrated contextual knowledge
        """
        try:
            if not await self.is_rag_service_available():
                logger.warning("RAG service unavailable, using original prompt")
                return RAGEnhancedPrompt(
                    original_prompt=original_prompt,
                    enhanced_prompt=original_prompt,
                    retrieved_context="",
                    context_sources=[],
                    enhancement_metadata={"rag_available": False},
                    generation_timestamp=datetime.now(timezone.utc)
                )
            
            # Construct RAG query for content generation context
            rag_query = f"Generate {content_type} for {subject} at {difficulty_level} level"
            
            # Query RAG system for relevant context
            query_request = {
                "query": rag_query,
                "domain": "content_generation",
                "n_results": 3,
                "metadata_filter": {
                    "content_type": content_type,
                    "subject": subject,
                    "difficulty_level": difficulty_level
                } if all([content_type, subject, difficulty_level]) else None
            }
            
            response = await self.http_client.post(
                f"{self.rag_service_url}/api/v1/rag/query",
                json=query_request
            )
            
            if response.status_code == 200:
                rag_result = response.json()
                enhanced_context = rag_result.get("enhanced_context", "")
                
                # Create enhanced prompt with retrieved context
                enhanced_prompt = self._create_enhanced_prompt(
                    original_prompt, enhanced_context, content_type, subject, difficulty_level
                )
                
                return RAGEnhancedPrompt(
                    original_prompt=original_prompt,
                    enhanced_prompt=enhanced_prompt,
                    retrieved_context=enhanced_context,
                    context_sources=["rag_content_generation"],
                    enhancement_metadata={
                        "rag_available": True,
                        "n_context_documents": rag_result.get("n_documents", 0),
                        "similarity_scores": rag_result.get("similarity_scores", []),
                        "query": rag_query
                    },
                    generation_timestamp=datetime.now(timezone.utc)
                )
            else:
                logger.warning(f"RAG query failed with status {response.status_code}")
                self._record_failure()
                
        except Exception as e:
            logger.error(f"RAG prompt enhancement failed: {str(e)}")
            self._record_failure()
        
        # Fallback to original prompt
        return RAGEnhancedPrompt(
            original_prompt=original_prompt,
            enhanced_prompt=original_prompt,
            retrieved_context="",
            context_sources=[],
            enhancement_metadata={"rag_available": False, "fallback_reason": "enhancement_failed"},
            generation_timestamp=datetime.now(timezone.utc)
        )
    
    def _create_enhanced_prompt(
        self,
        original_prompt: str,
        rag_context: str,
        content_type: str,
        subject: str,  
        difficulty_level: str
    ) -> str:
        """
        Create enhanced prompt by integrating RAG context with original prompt
        
        PROMPT ENHANCEMENT STRATEGY:
        - Preserve original prompt intent and requirements
        - Integrate relevant context from successful past generations
        - Add pedagogical guidance from accumulated knowledge
        - Maintain prompt clarity and AI model compatibility
        
        ENHANCEMENT PRINCIPLES:
        1. Context relevance: Only include contextually appropriate information
        2. Prompt clarity: Maintain clear structure and instructions
        3. Knowledge integration: Seamlessly blend retrieved knowledge
        4. Quality preservation: Ensure enhanced prompt maintains quality standards
        """
        if not rag_context.strip():
            return original_prompt
        
        enhancement_template = f"""
{original_prompt}

RELEVANT CONTEXT FROM SUCCESSFUL PAST GENERATIONS:
{rag_context}

ADDITIONAL GUIDANCE:
- Consider the successful patterns and structures shown in the context above
- Adapt effective elements to the current {content_type} for {subject} at {difficulty_level} level
- Maintain educational quality and pedagogical soundness
- Ensure content appropriateness for the specified difficulty level

Generate content that incorporates lessons learned from previous successful generations while meeting all original requirements.
"""
        
        return enhancement_template.strip()
    
    async def learn_from_content_generation(
        self,
        content_type: str,
        subject: str,
        difficulty_level: str,
        generated_content: str,
        user_feedback: Optional[str] = None,
        quality_score: float = 0.0,
        generation_metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Learn from content generation results to improve future generations
        
        LEARNING PROCESS:
        1. Analyze generation success based on user feedback and quality metrics
        2. Extract successful patterns and structures from high-quality content
        3. Store effective prompt-content pairs for future reference
        4. Update domain-specific knowledge with new successful examples
        5. Learn from failures to avoid similar issues in future generations
        
        CONTINUOUS IMPROVEMENT STRATEGY:
        - Quality-based learning: Prioritize learning from high-quality generations
        - Pattern recognition: Identify successful content structures and approaches
        - Feedback integration: Incorporate user feedback into learning process
        - Domain optimization: Build subject-specific knowledge bases
        
        Args:
            content_type: Type of generated content
            subject: Academic subject
            difficulty_level: Content difficulty level
            generated_content: The generated content to learn from
            user_feedback: Optional user feedback on content quality
            quality_score: Numeric quality score (0.0-1.0)
            generation_metadata: Additional metadata about the generation process
        
        Returns:
            Success status of learning operation
        """
        try:
            if not await self.is_rag_service_available():
                logger.warning("RAG service unavailable, cannot learn from generation")
                return False
            
            # Prepare learning data
            learning_content = {
                "content_type": content_type,
                "subject": subject,
                "difficulty_level": difficulty_level,
                "generated_content": generated_content[:2000],  # Truncate for storage efficiency
                "user_feedback": user_feedback or "",
                "quality_score": quality_score,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                **(generation_metadata or {})
            }
            
            # Store in RAG system for future learning
            add_document_request = {
                "content": generated_content,
                "domain": "content_generation", 
                "source": "generated_content",
                "metadata": {
                    "content_type": content_type,
                    "subject": subject,
                    "difficulty_level": difficulty_level,
                    "generation_quality": quality_score,
                    "user_feedback": user_feedback or "",
                    "learning_timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
            
            response = await self.http_client.post(
                f"{self.rag_service_url}/api/v1/rag/add-document",
                json=add_document_request
            )
            
            if response.status_code == 200:
                logger.info(f"Learned from {content_type} generation: quality={quality_score}")
                
                # Also learn from the interaction
                await self._learn_from_interaction(
                    interaction_type="content_generation",
                    content=json.dumps(learning_content),
                    success=quality_score > 0.7,  # Consider > 0.7 as successful
                    feedback=user_feedback or "",
                    quality_score=quality_score,
                    metadata=learning_content
                )
                
                return True
            else:
                logger.warning(f"Failed to learn from generation: status {response.status_code}")
                self._record_failure()
                return False
                
        except Exception as e:
            logger.error(f"Learning from content generation failed: {str(e)}")
            self._record_failure()
            return False
    
    async def _learn_from_interaction(
        self,
        interaction_type: str,
        content: str,
        success: bool,
        feedback: str,
        quality_score: float,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Store interaction learning data in RAG system
        
        INTERACTION LEARNING STRATEGY:
        - Track successful interaction patterns
        - Learn from user feedback and behavior
        - Build understanding of effective approaches
        - Optimize for user satisfaction and content quality
        """
        try:
            learning_request = {
                "interaction_type": interaction_type,
                "content": content,
                "success": success,
                "feedback": feedback,
                "quality_score": quality_score,
                "metadata": metadata
            }
            
            response = await self.http_client.post(
                f"{self.rag_service_url}/api/v1/rag/learn",
                json=learning_request
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Interaction learning failed: {str(e)}")
            return False
    
    async def get_generation_insights(
        self,
        content_type: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get insights about content generation patterns and effectiveness
        
        INSIGHTS PROVIDED:
        - Most successful content structures and patterns
        - Quality trends for different content types
        - Subject-specific optimization recommendations
        - User feedback patterns and preferences
        
        Returns:
            Dictionary containing generation insights and recommendations
        """
        try:
            if not await self.is_rag_service_available():
                return {"error": "RAG service unavailable"}
            
            # Query for generation statistics and patterns
            query = f"Successful {content_type} generation patterns"
            if subject:
                query += f" for {subject}"
            
            query_request = {
                "query": query,
                "domain": "content_generation",
                "n_results": 10,
                "metadata_filter": {
                    "content_type": content_type,
                    **({"subject": subject} if subject else {})
                }
            }
            
            response = await self.http_client.post(
                f"{self.rag_service_url}/api/v1/rag/query",
                json=query_request
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "content_type": content_type,
                    "subject": subject,
                    "successful_patterns": result.get("enhanced_context", ""),
                    "n_examples": result.get("n_documents", 0),
                    "insights_timestamp": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {"error": f"Query failed with status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Failed to get generation insights: {str(e)}")
            return {"error": str(e)}
    
    async def close(self):
        """Close HTTP client and cleanup resources"""
        await self.http_client.aclose()
        logger.info("RAG Integration Service closed")

# Global RAG integration service instance
rag_integration = RAGIntegrationService()

async def enhance_prompt_with_rag(
    content_type: str,
    subject: str,
    difficulty_level: str,
    original_prompt: str,
    additional_context: Optional[Dict[str, Any]] = None
) -> RAGEnhancedPrompt:
    """
    Convenience function for prompt enhancement with RAG context
    
    USAGE INTEGRATION:
    This function provides a simple interface for other course generation
    modules to enhance their prompts with RAG-retrieved context.
    """
    return await rag_integration.enhance_content_generation_prompt(
        content_type=content_type,
        subject=subject,
        difficulty_level=difficulty_level,
        original_prompt=original_prompt,
        additional_context=additional_context
    )

async def learn_from_generation(
    content_type: str,
    subject: str,
    difficulty_level: str,
    generated_content: str,
    user_feedback: Optional[str] = None,
    quality_score: float = 0.0,
    generation_metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Convenience function for learning from content generation results
    
    LEARNING INTEGRATION:
    Provides simple interface for course generation modules to contribute
    learning data back to the RAG system for continuous improvement.
    """
    return await rag_integration.learn_from_content_generation(
        content_type=content_type,
        subject=subject,
        difficulty_level=difficulty_level,
        generated_content=generated_content,
        user_feedback=user_feedback,
        quality_score=quality_score,
        generation_metadata=generation_metadata
    )

# Export key components for course generator integration
__all__ = [
    'RAGIntegrationService',
    'RAGEnhancedPrompt', 
    'ContentGenerationResult',
    'enhance_prompt_with_rag',
    'learn_from_generation',
    'rag_integration'
]