"""
AI Service wrapper for exercise generation.
Wraps the Anthropic Claude client to provide exercise generation capabilities.
"""
import json
import logging
from typing import Dict, Any, Optional, List
import anthropic

logger = logging.getLogger(__name__)

class AIService:
    """
    AI Service wrapper for exercise generation following SOLID principles.
    """
    
    def __init__(self, claude_client: anthropic.Anthropic):
        """
        Initialize AIService with Claude client.
        
        Args:
            claude_client: Anthropic Claude client instance
        """
        self.claude_client = claude_client
    
    async def generate_interactive_exercises(self, syllabus: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate interactive exercises from syllabus using Claude.
        
        Args:
            syllabus: Course syllabus dictionary
            
        Returns:
            Dictionary containing exercises or None if failed
        """
        try:
            # Build comprehensive prompt using syllabus structure
            exercises_prompt = f"""
            You are an expert educator creating comprehensive, practical lab exercises for this course syllabus.
            
            Course Overview: {syllabus.get('overview', '')}
            
            Full Syllabus Modules:
            {json.dumps(syllabus.get('modules', []), indent=2)}
            
            CRITICAL REQUIREMENTS FOR EXERCISES:
            1. Create ONE meaningful lab exercise per major topic/module that demonstrates real-world applications
            2. Each lab must solve a practical problem or complete a useful task relevant to the subject matter
            3. Include specific, actionable steps with actual commands, code examples, or procedures
            4. Labs should build practical skills students can use beyond the course
            5. Focus on problem-solving and applied learning, not just theory or memorization
            6. Include realistic data, scenarios, and contexts appropriate to the subject
            7. Each lab should have a clear purpose that students can understand and relate to
            
            EXERCISE STRUCTURE REQUIREMENTS:
            - Each exercise should have: title, description, type, difficulty, module_number, estimated_time
            - Include step-by-step instructions with code examples
            - Provide starter code, solution code, and validation logic
            - Add hints and learning objectives
            - Support interactive lab environments
            
            EXERCISE TYPES:
            - interactive_lab: Hands-on coding with real-time feedback
            - design_challenge: Design and implementation tasks
            - data_analysis: Data processing and visualization
            - simulation: Modeling and simulation exercises
            - case_study: Real-world case analysis
            
            For each module, create a comprehensive exercise that students can work through interactively.
            Include practical code examples, realistic scenarios, and clear learning objectives.
            
            Return ONLY valid JSON with this structure:
            {{
                "exercises": [
                    {{
                        "title": "Module Name - Interactive Lab",
                        "description": "Comprehensive description of the lab exercise",
                        "type": "interactive_lab",
                        "difficulty": "beginner|intermediate|advanced",
                        "module_number": 1,
                        "estimated_time": "30-45 minutes",
                        "learning_objectives": ["Objective 1", "Objective 2"],
                        "exercises": [
                            {{
                                "step": 1,
                                "title": "Step Title",
                                "description": "Step description",
                                "starter_code": "# Code template",
                                "solution": "# Solution code",
                                "validation": "# Validation logic",
                                "hints": ["Hint 1", "Hint 2"]
                            }}
                        ]
                    }}
                ]
            }}
            """
            
            logger.info(f"Generating interactive exercises for course with {len(syllabus.get('modules', []))} modules")
            
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=6000,
                messages=[
                    {"role": "user", "content": exercises_prompt}
                ]
            )
            
            try:
                exercises_data = json.loads(response.content[0].text)
                logger.info(f"Generated {len(exercises_data.get('exercises', []))} exercises from syllabus using AI")
                return exercises_data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = response.content[0].text
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != 0:
                    try:
                        exercises_data = json.loads(text[start:end])
                        logger.info(f"Extracted {len(exercises_data.get('exercises', []))} exercises from AI response")
                        return exercises_data
                    except json.JSONDecodeError:
                        logger.error("Failed to parse AI response as JSON")
                        return None
                
                logger.error("Failed to extract valid JSON from AI response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating interactive exercises with AI: {e}")
            return None
    
    async def generate_lab_environment(self, course_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate lab environment from course data using AI.
        
        Args:
            course_data: Course data dictionary
            
        Returns:
            Dictionary containing lab environment or None if failed
        """
        try:
            # Build lab environment prompt
            lab_prompt = f"""
            You are an expert educator creating interactive lab environments for this course.
            
            Course Data:
            {json.dumps(course_data, indent=2)}
            
            Create a comprehensive lab environment that supports the course objectives.
            Include appropriate tools, packages, and configuration for the course content.
            
            Return ONLY valid JSON with this structure:
            {{
                "lab_environment": {{
                    "name": "Course Lab Environment",
                    "description": "Description of the lab environment",
                    "environment_type": "python|javascript|java|web|data|security",
                    "config": {{
                        "language": "python",
                        "version": "3.9",
                        "packages": ["numpy", "pandas", "matplotlib"]
                    }},
                    "exercises": []
                }}
            }}
            """
            
            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=3000,
                messages=[
                    {"role": "user", "content": lab_prompt}
                ]
            )
            
            try:
                lab_data = json.loads(response.content[0].text)
                logger.info(f"Generated lab environment for course {course_data.get('id', 'unknown')}")
                return lab_data
            except json.JSONDecodeError:
                # Try to extract JSON from response
                text = response.content[0].text
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != 0:
                    try:
                        lab_data = json.loads(text[start:end])
                        logger.info(f"Extracted lab environment from AI response")
                        return lab_data
                    except json.JSONDecodeError:
                        logger.error("Failed to parse lab environment response as JSON")
                        return None
                
                logger.error("Failed to extract valid JSON from lab environment response")
                return None
                
        except Exception as e:
            logger.error(f"Error generating lab environment with AI: {e}")
            return None