"""
AI Client

Centralized AI client for Anthropic Claude integration.
Handles client initialization, configuration, and common AI operations.
"""

import logging
from typing import Dict, Any, Optional
import anthropic
from omegaconf import DictConfig

logger = logging.getLogger(__name__)


class AIClient:
    """
    Centralized AI client for Anthropic Claude integration.
    
    This class provides a singleton-like interface for AI operations
    with proper error handling and configuration management.
    """
    
    def __init__(self, config: DictConfig):
        """
        Initialize the AI client with configuration.
        
        Args:
            config: Application configuration containing AI settings
        """
        self.config = config
        self._client = None
        self._is_available = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize client
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the Anthropic client with API key."""
        try:
            api_key = self.config.get('ai', {}).get('anthropic', {}).get('api_key')
            
            if not api_key:
                self.logger.warning("No Anthropic API key found in configuration")
                self._is_available = False
                return
            
            self._client = anthropic.Anthropic(api_key=api_key)
            self._is_available = True
            self.logger.info("AI client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AI client: {e}")
            self._is_available = False
    
    @property
    def is_available(self) -> bool:
        """Check if AI client is available for use."""
        return self._is_available and self._client is not None
    
    async def generate_content(self, 
                             prompt: str, 
                             model: str = "claude-3-sonnet-20240229",
                             max_tokens: int = 4000,
                             temperature: float = 0.7,
                             system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Generate content using the AI client.
        
        Args:
            prompt: The user prompt for content generation
            model: AI model to use for generation
            max_tokens: Maximum tokens in response
            temperature: Creativity/randomness of response (0-1)
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated content or None if generation fails
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