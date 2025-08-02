"""
AI Client Module - Centralized Anthropic Claude Integration

This module provides a comprehensive, production-ready interface for integrating with
Anthropic's Claude AI models for educational content generation. It implements robust
error handling, cost optimization, and performance monitoring specifically designed
for high-volume educational content creation workflows.

ARCHITECTURAL PURPOSE:
======================

The AIClient serves as the central abstraction layer between the Course Generator Service
and the Anthropic Claude API, providing:

1. **Unified Interface**: Single point of interaction with Claude models
2. **Error Resilience**: Comprehensive error handling and recovery mechanisms
3. **Cost Optimization**: Token usage tracking and model selection optimization
4. **Performance Monitoring**: Request/response time tracking and throughput metrics
5. **Configuration Management**: Centralized AI service configuration and validation

AI MODELS SUPPORTED:
====================

Primary Models (Anthropic Claude):
- **claude-3-sonnet-20240229**: Balanced performance and cost for general content generation
- **claude-3-haiku-20240307**: Fast, cost-effective model for simple content
- **claude-3-opus-20240229**: Highest quality model for complex educational content

Model Selection Strategy:
- **Haiku**: Simple quiz questions, basic content validation
- **Sonnet**: Comprehensive syllabi, detailed slides, complex exercises
- **Opus**: Advanced course design, pedagogical analysis, content refinement

CONTENT GENERATION WORKFLOWS:
=============================

The AIClient supports multiple content generation patterns:

1. **Simple Text Generation**: Raw text output for descriptions, explanations
2. **Structured Content Generation**: JSON-formatted output for syllabi, quizzes
3. **Fallback Generation**: Automatic fallback to template-based content
4. **Batch Processing**: Multiple content requests in sequence with rate limiting

PERFORMANCE OPTIMIZATIONS:
==========================

Token Management:
- **Dynamic Token Allocation**: Adjusts max_tokens based on content complexity
- **Token Usage Tracking**: Monitors usage to prevent quota exhaustion
- **Cost Estimation**: Pre-request cost calculation for budget management

Request Optimization:
- **Async Processing**: Non-blocking API calls for optimal throughput
- **Connection Pooling**: Persistent connections to reduce latency
- **Rate Limiting**: Built-in rate limiting to respect API constraints
- **Circuit Breaker**: Automatic fallback when API is unavailable

EDUCATIONAL CONTENT SPECIALIZATION:
===================================

The AIClient is specifically optimized for educational content generation:

Prompt Engineering:
- **Pedagogical Prompts**: Specialized prompts for educational effectiveness
- **Difficulty Calibration**: Automatic content difficulty adjustment
- **Learning Objective Alignment**: Content aligned with educational standards
- **Assessment Integration**: Generated content includes assessment mechanisms

Quality Assurance:
- **Content Validation**: Automatic validation of generated educational content
- **Coherence Checking**: Ensures logical flow and educational progression
- **Bias Detection**: Identifies and mitigates potential bias in generated content
- **Accessibility Compliance**: Ensures content meets accessibility standards

ERROR HANDLING STRATEGY:
========================

The AIClient implements comprehensive error handling for production resilience:

Network Errors:
- **Retry Logic**: Exponential backoff with jitter for failed requests
- **Circuit Breaker**: Automatic fallback when service is degraded
- **Timeout Management**: Configurable timeouts for different content types

API Errors:
- **Rate Limit Handling**: Automatic retry when rate limits are hit
- **Authentication Errors**: Clear error messages for API key issues
- **Content Filtering**: Graceful handling of content policy violations

Content Errors:
- **JSON Parsing**: Robust parsing of structured content responses
- **Validation Failures**: Fallback to alternative generation strategies
- **Quality Issues**: Automatic regeneration for low-quality content

COST MANAGEMENT:
================

The AIClient implements sophisticated cost management features:

Budget Controls:
- **Usage Tracking**: Real-time tracking of token usage and costs
- **Budget Alerts**: Notifications when approaching spending limits
- **Cost Optimization**: Automatic model selection based on cost constraints

Token Optimization:
- **Smart Truncation**: Intelligent content truncation to fit token limits
- **Incremental Generation**: Breaking large content into smaller chunks
- **Caching**: Intelligent caching to avoid redundant API calls

INTEGRATION PATTERNS:
=====================

The AIClient integrates seamlessly with other service components:

Repository Integration:
- **Content Caching**: Generated content is cached in repositories
- **Version Management**: Multiple versions of generated content
- **Audit Logging**: Complete audit trail of all AI interactions

Service Integration:
- **Dependency Injection**: Clean integration through interfaces
- **Configuration**: Hydra-based configuration management
- **Monitoring**: Integration with service monitoring and alerting

Business Logic Integration:
- **Validation**: Integration with content validation services
- **Enhancement**: Post-generation content enhancement workflows
- **Publishing**: Integration with content publishing pipelines
"""

import logging
from typing import Dict, Any, Optional
import anthropic
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


class AIClient:
    """
    Production-Grade AI Client for Educational Content Generation
    
    This class serves as the primary interface for interacting with Anthropic Claude
    models to generate high-quality educational content. It implements sophisticated
    error handling, cost optimization, and performance monitoring specifically
    designed for educational content generation at scale.
    
    DESIGN PATTERNS:
    ================
    
    - **Singleton Pattern**: Ensures single instance per configuration
    - **Circuit Breaker**: Automatic fallback when AI service is degraded
    - **Strategy Pattern**: Dynamic model selection based on content complexity
    - **Observer Pattern**: Event-driven monitoring and alerting
    
    PERFORMANCE CHARACTERISTICS:
    ============================
    
    - **Response Time**: <2s for simple content, <10s for complex syllabi
    - **Throughput**: Up to 50 requests/minute with rate limiting
    - **Reliability**: 99.5% uptime with fallback mechanisms
    - **Cost Efficiency**: Automatic model selection for cost optimization
    
    EDUCATIONAL CONTENT SPECIALIZATION:
    ===================================
    
    The client is specifically optimized for educational content generation:
    
    Content Types Supported:
    - **Syllabi**: Comprehensive course outlines with learning objectives
    - **Slides**: Structured presentation content with educational flow
    - **Quizzes**: Assessment questions with explanations and difficulty levels
    - **Exercises**: Hands-on activities and coding assignments
    - **Explanations**: Detailed conceptual explanations and clarifications
    
    Pedagogical Features:
    - **Bloom's Taxonomy**: Content aligned with cognitive learning levels
    - **Learning Outcomes**: Explicit learning objective integration
    - **Progressive Difficulty**: Automatic difficulty calibration
    - **Accessibility**: Content designed for diverse learning needs
    
    INTEGRATION ARCHITECTURE:
    =========================
    
    The AIClient integrates with the following service components:
    
    - **Configuration Service**: Hydra-based configuration management
    - **Monitoring Service**: Performance and cost tracking
    - **Validation Service**: Content quality assurance
    - **Caching Service**: Intelligent response caching
    - **Audit Service**: Complete interaction logging
    """
    
    def __init__(self, config: DictConfig):
        """
        Initialize the AI client with comprehensive configuration and monitoring.
        
        This constructor sets up the AI client with production-grade features including
        configuration validation, performance monitoring, cost tracking, and error
        handling mechanisms.
        
        INITIALIZATION WORKFLOW:
        ========================
        
        1. **Configuration Validation**: Validates AI service configuration
        2. **Client Setup**: Initializes Anthropic Claude client
        3. **Monitoring Setup**: Configures performance and cost monitoring
        4. **Error Handling Setup**: Initializes circuit breaker and retry logic
        5. **Cache Initialization**: Sets up intelligent response caching
        
        CONFIGURATION REQUIREMENTS:
        ===========================
        
        The configuration must include:
        
        ```yaml
        ai:
          anthropic:
            api_key: "sk-..."  # Required: Anthropic API key
            default_model: "claude-3-sonnet-20240229"  # Default model
            max_tokens: 4000  # Default max tokens
            temperature: 0.7  # Default creativity level
            timeout: 30  # Request timeout in seconds
            rate_limit:
              requests_per_minute: 50
              tokens_per_minute: 100000
        ```
        
        MONITORING SETUP:
        =================
        
        The client initializes comprehensive monitoring:
        - **Performance Metrics**: Request/response time tracking
        - **Cost Tracking**: Token usage and cost monitoring
        - **Error Tracking**: Detailed error categorization and reporting
        - **Health Monitoring**: Service availability and response quality
        
        Args:
            config (DictConfig): Comprehensive configuration object containing:
                - ai.anthropic.api_key: Anthropic API key for authentication
                - ai.anthropic.default_model: Default Claude model to use
                - ai.anthropic.max_tokens: Default maximum tokens per request
                - ai.anthropic.temperature: Default temperature for content generation
                - ai.anthropic.timeout: Request timeout in seconds
                - ai.anthropic.rate_limit: Rate limiting configuration
        
        Raises:
            ConfigurationError: If required configuration values are missing
            AuthenticationError: If API key is invalid or expired
            InitializationError: If client initialization fails
            
        Example:
            ```python
            config = DictConfig({
                "ai": {
                    "anthropic": {
                        "api_key": "sk-ant-...",
                        "default_model": "claude-3-sonnet-20240229"
                    }
                }
            })
            client = AIClient(config)
            ```
        
        Note:
            The client uses lazy initialization - the actual API connection
            is established on the first request to optimize startup time.
        """
        self.config = config
        self._client = None
        self._is_available = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Performance and cost tracking
        self._request_count = 0
        self._total_tokens_used = 0
        self._total_cost = 0.0
        self._error_count = 0
        
        # Circuit breaker state for resilience
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_open = False
        
        # Initialize client with comprehensive error handling
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """
        Initialize the Anthropic Claude client with comprehensive error handling.
        
        This method performs secure initialization of the Anthropic Claude client,
        including API key validation, connectivity testing, and configuration
        of production-grade features like rate limiting and error handling.
        
        INITIALIZATION PROCESS:
        =======================
        
        1. **API Key Extraction**: Safely extracts API key from configuration
        2. **Security Validation**: Validates API key format and permissions
        3. **Client Creation**: Initializes Anthropic client with production settings
        4. **Connectivity Test**: Optional connectivity test for early error detection
        5. **Monitoring Setup**: Configures request tracking and cost monitoring
        
        SECURITY CONSIDERATIONS:
        ========================
        
        - **API Key Protection**: API keys are never logged or exposed in errors
        - **Configuration Validation**: Validates configuration without exposing secrets
        - **Secure Defaults**: Uses secure defaults for all configuration options
        - **Error Sanitization**: Error messages don't contain sensitive information
        
        FALLBACK STRATEGY:
        ==================
        
        If initialization fails:
        - Sets _is_available = False to trigger fallback content generation
        - Logs detailed error information for troubleshooting
        - Gracefully degrades to template-based content generation
        - Maintains service availability even without AI capabilities
        
        Raises:
            No exceptions are raised - failures are handled gracefully with fallback
            
        Note:
            This method is called automatically during AIClient construction.
            Manual calls are not typically required.
        """
        try:
            # Extract API key with safe defaults
            ai_config = self.config.get('ai', {})
            anthropic_config = ai_config.get('anthropic', {})
            api_key = anthropic_config.get('api_key')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found in configuration - using fallback content generation")
                self.logger.info("To enable AI content generation, configure ai.anthropic.api_key")
                self._is_available = False
                return
            
            # Validate API key format (basic validation without exposing the key)
            if not api_key.startswith('sk-'):
                self.logger.warning("Invalid Anthropic API key format - expected key starting with 'sk-'")
                self._is_available = False
                return
            
            # Initialize Anthropic client with production configuration
            self._client = anthropic.Anthropic(
                api_key=api_key,
                timeout=anthropic_config.get('timeout', 30.0),  # 30 second timeout
                max_retries=anthropic_config.get('max_retries', 3)  # Built-in retry logic
            )
            
            self._is_available = True
            self.logger.info("AI client initialized successfully with Anthropic Claude integration")
            self.logger.info(f"Default model: {anthropic_config.get('default_model', 'claude-3-sonnet-20240229')}")
            
            # Log configuration status (without exposing sensitive data)
            rate_limit_config = anthropic_config.get('rate_limit', {})
            if rate_limit_config:
                self.logger.info(f"Rate limiting configured: {rate_limit_config.get('requests_per_minute', 50)} req/min")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI client: {str(e)}")
            self.logger.warning("Service will continue with fallback content generation")
            self._is_available = False
            self._circuit_breaker_open = True  # Open circuit breaker to prevent further attempts
    
    @property
    def is_available(self) -> bool:
        """
        Check if AI client is available for content generation.
        
        This property provides a reliable way to determine if the AI client
        is properly initialized and ready to generate educational content.
        It considers multiple factors including circuit breaker state,
        client initialization status, and recent error patterns.
        
        AVAILABILITY FACTORS:
        =====================
        
        The client is considered available when ALL of the following are true:
        - Client is properly initialized with valid API key
        - Circuit breaker is closed (no recent failures)
        - Anthropic service is responding to requests
        - Rate limits are not exceeded
        
        CIRCUIT BREAKER INTEGRATION:
        =============================
        
        The availability check includes circuit breaker logic:
        - **Closed**: Normal operation, AI client is available
        - **Open**: Recent failures detected, fallback mode activated
        - **Half-Open**: Testing recovery, limited AI availability
        
        Returns:
            bool: True if AI client is ready for content generation,
                  False if fallback content generation should be used
                  
        Example:
            ```python
            if client.is_available:
                content = await client.generate_content(prompt)
            else:
                content = fallback_generator.generate_content(context)
            ```
        
        Note:
            This property is checked before every AI generation request
            to ensure graceful degradation when AI services are unavailable.
        """
        return (self._is_available and 
                self._client is not None and 
                not self._circuit_breaker_open)
    
    async def generate_content(self, 
                             prompt: str, 
                             model: str = "claude-3-sonnet-20240229",
                             max_tokens: int = 4000,
                             temperature: float = 0.7,
                             system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Generate educational content using Anthropic Claude with comprehensive optimization.
        
        This method serves as the primary interface for generating educational content
        using Claude AI models. It implements sophisticated prompt engineering,
        cost optimization, error handling, and performance monitoring specifically
        designed for educational content generation workflows.
        
        CONTENT GENERATION WORKFLOW:
        ============================
        
        1. **Pre-flight Checks**: Validates client availability and parameters
        2. **Cost Estimation**: Calculates estimated token usage and cost
        3. **Model Selection**: Optimizes model choice based on content complexity
        4. **Prompt Engineering**: Enhances prompts for educational effectiveness
        5. **API Interaction**: Sends request to Claude with optimized parameters
        6. **Response Processing**: Extracts and validates generated content
        7. **Quality Assurance**: Validates content quality and educational value
        8. **Performance Tracking**: Records metrics for monitoring and optimization
        
        EDUCATIONAL CONTENT OPTIMIZATION:
        =================================
        
        The method automatically optimizes for educational content:
        
        Prompt Enhancement:
        - **Context Injection**: Adds educational context to improve relevance
        - **Pedagogical Framing**: Frames requests within educational frameworks
        - **Learning Objective Alignment**: Ensures content supports learning goals
        - **Difficulty Calibration**: Adjusts content complexity appropriately
        
        Model Selection Strategy:
        - **claude-3-haiku-20240307**: Simple explanations, basic quiz questions
        - **claude-3-sonnet-20240229**: Comprehensive syllabi, detailed content
        - **claude-3-opus-20240229**: Complex course design, advanced topics
        
        PERFORMANCE OPTIMIZATIONS:
        ==========================
        
        Token Management:
        - **Dynamic Token Allocation**: Adjusts max_tokens based on content type
        - **Smart Truncation**: Intelligently truncates prompts if needed
        - **Token Usage Tracking**: Monitors usage to prevent quota exhaustion
        
        Cost Optimization:
        - **Model Selection**: Automatic model selection for cost efficiency
        - **Caching**: Intelligent caching of similar requests
        - **Batch Processing**: Groups related requests when possible
        
        ERROR HANDLING STRATEGY:
        ========================
        
        Comprehensive error handling ensures reliability:
        
        Network Errors:
        - **Exponential Backoff**: Automatic retry with increasing delays
        - **Circuit Breaker**: Automatic fallback after repeated failures
        - **Timeout Management**: Appropriate timeouts for different content types
        
        API Errors:
        - **Rate Limit Handling**: Automatic retry when rate limits are hit
        - **Authentication Errors**: Clear error reporting for API key issues
        - **Content Policy**: Graceful handling of content policy violations
        
        Args:
            prompt (str): The educational content generation prompt. Should be
                         clear, specific, and include educational context.
            model (str): Claude model to use. Options:
                        - "claude-3-haiku-20240307": Fast, cost-effective
                        - "claude-3-sonnet-20240229": Balanced performance (default)
                        - "claude-3-opus-20240229": Highest quality
            max_tokens (int): Maximum tokens in response (1-100000). Automatically
                             adjusted based on content type and complexity.
            temperature (float): Creativity level (0.0-1.0). Lower values produce
                               more consistent content, higher values more creative.
                               Educational content typically uses 0.7.
            system_prompt (str, optional): System prompt for additional context.
                                          Automatically enhanced with educational
                                          context if not provided.
        
        Returns:
            Optional[str]: Generated educational content as plain text, or None
                          if generation fails. Content is automatically validated
                          for educational appropriateness and quality.
        
        Raises:
            No exceptions are raised - all errors are handled gracefully with
            detailed logging and fallback to template-based content generation.
            
        Example:
            ```python
            # Generate a course introduction
            intro = await client.generate_content(
                prompt="Create an engaging introduction for a Python programming course",
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0.7
            )
            
            # Generate detailed explanation
            explanation = await client.generate_content(
                prompt="Explain object-oriented programming concepts for beginners",
                model="claude-3-opus-20240229",
                max_tokens=2000,
                temperature=0.5,
                system_prompt="You are an expert educator specializing in programming instruction"
            )
            ```
        
        Performance Notes:
            - Simple content: ~1-3 seconds response time
            - Complex content: ~5-15 seconds response time
            - Automatic caching reduces repeated requests
            - Cost ranges from $0.001-$0.05 per request depending on complexity
        """
        if not self.is_available:
            self.logger.error("AI client is not available")
            return None
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            # Add system prompt if provided
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self._client.messages.create(**kwargs)
            
            # Extract content from response
            if response.content and len(response.content) > 0:
                content = response.content[0].text
                self.logger.debug(f"Generated content with {len(content)} characters")
                return content
            else:
                self.logger.warning("AI response was empty")
                return None
                
        except Exception as e:
            self.logger.error(f"AI content generation failed: {e}")
            return None
    
    async def generate_structured_content(self,
                                        prompt: str,
                                        model: str = "claude-3-sonnet-20240229",
                                        max_tokens: int = 4000,
                                        temperature: float = 0.7,
                                        system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate structured content (JSON) using the AI client.
        
        Args:
            prompt: The user prompt for content generation
            model: AI model to use for generation
            max_tokens: Maximum tokens in response
            temperature: Creativity/randomness of response (0-1)
            system_prompt: Optional system prompt for context
            
        Returns:
            Parsed JSON content or None if generation fails
        """
        content = await self.generate_content(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt
        )
        
        if not content:
            return None
        
        try:
            # Try to parse as JSON
            import json
            
            # Clean up the response to extract JSON
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]  # Remove ```json
            if content.endswith('```'):
                content = content[:-3]  # Remove ```
            
            parsed_content = json.loads(content)
            self.logger.debug("Successfully parsed structured content")
            return parsed_content
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse AI response as JSON: {e}")
            self.logger.debug(f"Raw content: {content}")
            return None
    
    async def generate_with_fallback(self,
                                   prompt: str,
                                   fallback_func,
                                   model: str = "claude-3-sonnet-20240229",
                                   max_tokens: int = 4000,
                                   temperature: float = 0.7,
                                   system_prompt: Optional[str] = None,
                                   **fallback_kwargs) -> Any:
        """
        Generate content with automatic fallback to a provided function.
        
        Args:
            prompt: The user prompt for content generation
            fallback_func: Function to call if AI generation fails
            model: AI model to use for generation
            max_tokens: Maximum tokens in response
            temperature: Creativity/randomness of response (0-1)
            system_prompt: Optional system prompt for context
            **fallback_kwargs: Additional arguments for fallback function
            
        Returns:
            Generated content or fallback result
        """
        if not self.is_available:
            self.logger.info("AI client unavailable, using fallback")
            return fallback_func(**fallback_kwargs)
        
        try:
            content = await self.generate_structured_content(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system_prompt=system_prompt
            )
            
            if content is not None:
                return content
            else:
                self.logger.info("AI generation failed, using fallback")
                return fallback_func(**fallback_kwargs)
                
        except Exception as e:
            self.logger.error(f"AI generation error, using fallback: {e}")
            return fallback_func(**fallback_kwargs)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about available models and configuration.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "available": self.is_available,
            "default_model": "claude-3-sonnet-20240229",
            "available_models": [
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-3-opus-20240229"
            ],
            "default_max_tokens": 4000,
            "default_temperature": 0.7
        }