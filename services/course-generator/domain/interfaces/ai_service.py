"""
AI Service Interface
Single Responsibility: Define AI interaction operations
Dependency Inversion: Abstract interface for AI providers
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from enum import Enum

class AIProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    MOCK = "mock"

class AIModel(Enum):
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    MOCK_MODEL = "mock-model"

class ContentGenerationType(Enum):
    SYLLABUS = "syllabus"
    SLIDES = "slides"
    EXERCISE = "exercise"
    QUIZ = "quiz"
    CHAT_RESPONSE = "chat_response"
    EXPLANATION = "explanation"

class IAIService(ABC):
    """Interface for AI service operations"""

    @abstractmethod
    async def generate_content(self, content_type: ContentGenerationType, 
                              prompt: str, context: Dict[str, Any] = None, 
                              model: Optional[AIModel] = None) -> str:
        """Generate content using AI"""
        pass

    @abstractmethod
    async def generate_structured_content(self, content_type: ContentGenerationType, 
                                         prompt: str, schema: Dict[str, Any], 
                                         context: Dict[str, Any] = None,
                                         model: Optional[AIModel] = None) -> Dict[str, Any]:
        """Generate structured content that matches a specific schema"""
        pass

    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]], 
                             context: Dict[str, Any] = None,
                             model: Optional[AIModel] = None) -> str:
        """Generate chat completion response"""
        pass

    @abstractmethod
    async def analyze_text(self, text: str, analysis_type: str, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze text content (sentiment, topics, etc.)"""
        pass

    @abstractmethod
    async def validate_content(self, content: str, content_type: ContentGenerationType, 
                              validation_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate generated content quality and appropriateness"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[AIModel]:
        """Get list of available AI models"""
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the AI provider"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to AI service"""
        pass

class IPromptTemplateService(ABC):
    """Interface for prompt template management"""

    @abstractmethod
    def get_prompt_template(self, content_type: ContentGenerationType, 
                           template_name: str = "default") -> str:
        """Get prompt template for content generation"""
        pass

    @abstractmethod
    def render_prompt(self, template: str, variables: Dict[str, Any]) -> str:
        """Render prompt template with variables"""
        pass

    @abstractmethod
    def validate_template_variables(self, template: str, variables: Dict[str, Any]) -> bool:
        """Validate that all required template variables are provided"""
        pass

    @abstractmethod
    def get_available_templates(self, content_type: ContentGenerationType) -> List[str]:
        """Get list of available templates for a content type"""
        pass

class IAIFallbackService(ABC):
    """Interface for AI fallback service when primary AI is unavailable"""

    @abstractmethod
    async def generate_fallback_content(self, content_type: ContentGenerationType, 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback content when AI service is unavailable"""
        pass

    @abstractmethod
    async def is_primary_service_available(self) -> bool:
        """Check if primary AI service is available"""
        pass

    @abstractmethod
    def get_fallback_quality_score(self, content_type: ContentGenerationType) -> float:
        """Get quality score for fallback content (0.0 to 1.0)"""
        pass

class IContentValidationService(ABC):
    """Interface for validating AI-generated content"""

    @abstractmethod
    async def validate_educational_content(self, content: str, 
                                          subject: str, difficulty_level: str) -> Dict[str, Any]:
        """Validate educational content for accuracy and appropriateness"""
        pass

    @abstractmethod
    async def check_content_safety(self, content: str) -> Dict[str, Any]:
        """Check content for safety and appropriateness"""
        pass

    @abstractmethod
    async def evaluate_content_quality(self, content: str, 
                                      content_type: ContentGenerationType) -> Dict[str, Any]:
        """Evaluate overall content quality"""
        pass

    @abstractmethod
    async def suggest_content_improvements(self, content: str, 
                                          validation_results: Dict[str, Any]) -> List[str]:
        """Suggest improvements based on validation results"""
        pass

class IAIConfigurationService(ABC):
    """Interface for AI service configuration management"""

    @abstractmethod
    def get_model_configuration(self, model: AIModel) -> Dict[str, Any]:
        """Get configuration for a specific AI model"""
        pass

    @abstractmethod
    def update_model_parameters(self, model: AIModel, parameters: Dict[str, Any]) -> None:
        """Update parameters for a specific model"""
        pass

    @abstractmethod
    def get_rate_limits(self, provider: AIProvider) -> Dict[str, Any]:
        """Get rate limits for an AI provider"""
        pass

    @abstractmethod
    def get_usage_statistics(self, provider: AIProvider, 
                            time_period_days: int = 30) -> Dict[str, Any]:
        """Get usage statistics for an AI provider"""
        pass

    @abstractmethod
    def estimate_generation_cost(self, content_type: ContentGenerationType, 
                                model: AIModel, estimated_tokens: int) -> float:
        """Estimate cost for content generation"""
        pass