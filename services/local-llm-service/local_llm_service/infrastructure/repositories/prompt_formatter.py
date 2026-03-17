"""
Prompt Formatter for Llama 3.1 Models

This module handles formatting prompts in the specific format expected by Llama 3.1 models.

Llama 3.1 Prompt Format:
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>

{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

This format ensures optimal performance and instruction following for Llama 3.1 models.
"""

from typing import Dict, Any, List


class PromptFormatter:
    """
    Formats prompts for Llama 3.1 instruction-tuned models.

    Llama 3.1 uses special tokens to delimit different parts of the conversation:
    - <|begin_of_text|> - Start of conversation
    - <|start_header_id|>role<|end_header_id|> - Role indicator
    - <|eot_id|> - End of turn

    This formatter ensures prompts are correctly structured for optimal model performance.
    """

    def __init__(self):
        """Initialize the prompt formatter with Llama 3.1 special tokens"""
        self.begin_of_text = "<|begin_of_text|>"
        self.start_header_id = "<|start_header_id|>"
        self.end_header_id = "<|end_header_id|>"
        self.eot_id = "<|eot_id|>"

    def format_llama_prompt(
        self,
        user_message: str,
        system_prompt: str = "You are a helpful AI assistant.",
        assistant_prefix: str = ""
    ) -> str:
        """
        Format a simple user message in Llama 3.1 format.

        Args:
            user_message: The user's query or message
            system_prompt: System instruction for the model
            assistant_prefix: Optional prefix for assistant response

        Returns:
            Formatted prompt string ready for Llama 3.1 inference

        Example:
            formatter = PromptFormatter()
            prompt = formatter.format_llama_prompt(
                user_message="What is Python?",
                system_prompt="You are a programming tutor."
            )
        """
        prompt = f"{self.begin_of_text}"

        # Add system message
        prompt += f"{self.start_header_id}system{self.end_header_id}\n\n"
        prompt += f"{system_prompt}{self.eot_id}"

        # Add user message
        prompt += f"{self.start_header_id}user{self.end_header_id}\n\n"
        prompt += f"{user_message}{self.eot_id}"

        # Add assistant header
        prompt += f"{self.start_header_id}assistant{self.end_header_id}\n\n"

        # Add optional assistant prefix
        if assistant_prefix:
            prompt += assistant_prefix

        return prompt

    def format_conversation(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "You are a helpful AI assistant."
    ) -> str:
        """
        Format a multi-turn conversation in Llama 3.1 format.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: System instruction for the model

        Returns:
            Formatted conversation string ready for Llama 3.1 inference

        Example:
            formatter = PromptFormatter()
            messages = [
                {"role": "user", "content": "What is Python?"},
                {"role": "assistant", "content": "Python is a programming language."},
                {"role": "user", "content": "What are its features?"}
            ]
            prompt = formatter.format_conversation(messages=messages)
        """
        prompt = f"{self.begin_of_text}"

        # Add system message
        prompt += f"{self.start_header_id}system{self.end_header_id}\n\n"
        prompt += f"{system_prompt}{self.eot_id}"

        # Add conversation turns
        for message in messages:
            role = message["role"]
            content = message["content"]

            prompt += f"{self.start_header_id}{role}{self.end_header_id}\n\n"
            prompt += f"{content}{self.eot_id}"

        # If last message was from user, add assistant header
        if messages and messages[-1]["role"] == "user":
            prompt += f"{self.start_header_id}assistant{self.end_header_id}\n\n"

        return prompt

    def format_function_calling_prompt(
        self,
        user_message: str,
        functions: List[Dict[str, Any]],
        system_prompt: str = None
    ) -> str:
        """
        Format a prompt for function calling / structured output.

        Instructs the model to extract function parameters from the user message
        and return them as JSON.

        Args:
            user_message: The user's query or command
            functions: List of function schemas with name, description, parameters
            system_prompt: Optional custom system prompt

        Returns:
            Formatted prompt for function parameter extraction

        Example:
            formatter = PromptFormatter()
            functions = [{
                "name": "create_course",
                "description": "Create a new course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "organization_id": {"type": "integer"}
                    },
                    "required": ["title", "organization_id"]
                }
            }]
            prompt = formatter.format_function_calling_prompt(
                user_message="Create a Python course for org 5",
                functions=functions
            )
        """
        if system_prompt is None:
            system_prompt = (
                "You are a function parameter extraction assistant. "
                "Extract the function name and parameters from the user message. "
                "Return ONLY a JSON object with 'function_name' and 'parameters' keys. "
                "Do not include any explanation or additional text."
            )

        # Build function documentation
        function_docs = "\n\nAvailable functions:\n"
        for func in functions:
            function_docs += f"\n{func['name']}: {func['description']}\n"
            function_docs += f"Parameters: {func['parameters']}\n"

        full_system_prompt = system_prompt + function_docs

        # Format the prompt
        prompt = self.format_llama_prompt(
            user_message=user_message,
            system_prompt=full_system_prompt
        )

        return prompt

    def format_summarization_prompt(
        self,
        text_to_summarize: str,
        max_words: int = 100,
        focus: str = None
    ) -> str:
        """
        Format a prompt for text summarization.

        Args:
            text_to_summarize: The text content to summarize
            max_words: Maximum words in the summary
            focus: Optional focus area for the summary

        Returns:
            Formatted summarization prompt

        Example:
            formatter = PromptFormatter()
            prompt = formatter.format_summarization_prompt(
                text_to_summarize=long_rag_context,
                max_words=50,
                focus="API endpoints"
            )
        """
        system_prompt = (
            f"You are a concise summarization assistant. "
            f"Summarize the following text in {max_words} words or less. "
            f"Focus on the most important information."
        )

        if focus:
            system_prompt += f" Pay special attention to information about {focus}."

        user_message = f"Summarize this text:\n\n{text_to_summarize}"

        return self.format_llama_prompt(
            user_message=user_message,
            system_prompt=system_prompt
        )

    def format_compression_prompt(
        self,
        conversation_history: List[Dict[str, str]],
        target_length: int = 200
    ) -> str:
        """
        Format a prompt for conversation history compression.

        Args:
            conversation_history: List of conversation messages
            target_length: Target length in words for compressed version

        Returns:
            Formatted compression prompt

        Example:
            formatter = PromptFormatter()
            prompt = formatter.format_compression_prompt(
                conversation_history=long_conversation,
                target_length=100
            )
        """
        system_prompt = (
            f"You are a conversation compression assistant. "
            f"Compress the following conversation into approximately {target_length} words "
            f"while preserving key information and context. "
            f"Maintain the logical flow and important details."
        )

        # Convert conversation to readable text
        conversation_text = ""
        for msg in conversation_history:
            role = msg["role"].capitalize()
            content = msg["content"]
            conversation_text += f"{role}: {content}\n"

        user_message = f"Compress this conversation:\n\n{conversation_text}"

        return self.format_llama_prompt(
            user_message=user_message,
            system_prompt=system_prompt
        )

    def format_json_extraction_prompt(
        self,
        text: str,
        json_schema: Dict[str, Any]
    ) -> str:
        """
        Format a prompt for structured JSON extraction.

        Args:
            text: The text to extract information from
            json_schema: JSON schema defining the expected output structure

        Returns:
            Formatted JSON extraction prompt

        Example:
            formatter = PromptFormatter()
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "date": {"type": "string"}
                }
            }
            prompt = formatter.format_json_extraction_prompt(
                text="John enrolled on 2024-01-15",
                json_schema=schema
            )
        """
        system_prompt = (
            "You are a structured data extraction assistant. "
            "Extract information from the text according to the provided schema. "
            "Return ONLY a valid JSON object matching the schema. "
            "Do not include any explanation or additional text."
        )

        user_message = (
            f"Extract information matching this schema:\n{json_schema}\n\n"
            f"From this text:\n{text}"
        )

        return self.format_llama_prompt(
            user_message=user_message,
            system_prompt=system_prompt
        )
