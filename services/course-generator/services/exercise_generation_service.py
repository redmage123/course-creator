"""
ExerciseGenerationService implementation following SOLID principles.
Handles AI-powered exercise generation with interactive lab environments.
"""
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ExerciseGenerationService:
    """
    Service for generating AI-powered exercises with interactive lab environments.
    Follows Single Responsibility Principle and replaces default fallback exercises.
    """
    
    def __init__(self, db, ai_service, syllabus_service, lab_service):
        """
        Initialize ExerciseGenerationService with dependencies.
        
        Args:
            db: Database connection/pool
            ai_service: AI service for exercise generation
            syllabus_service: Service for syllabus operations
            lab_service: Service for lab environment management
        """
        self.db = db
        self.ai_service = ai_service
        self.syllabus_service = syllabus_service
        self.lab_service = lab_service
        self._memory_cache = {}  # In-memory cache for exercises
        
        # Exercise types and their characteristics
        self.exercise_types = {
            'interactive_lab': {
                'description': 'Hands-on coding lab with real-time feedback',
                'duration_range': (20, 45),
                'requires_lab_env': True
            },
            'design_challenge': {
                'description': 'Design and implementation challenge',
                'duration_range': (30, 60),
                'requires_lab_env': True
            },
            'data_analysis': {
                'description': 'Data analysis and visualization project',
                'duration_range': (45, 90),
                'requires_lab_env': True
            },
            'simulation': {
                'description': 'Simulation and modeling exercise',
                'duration_range': (30, 60),
                'requires_lab_env': True
            },
            'case_study': {
                'description': 'Real-world case study analysis',
                'duration_range': (60, 120),
                'requires_lab_env': False
            }
        }
        
        # Difficulty progression mapping
        self.difficulty_progression = {
            1: 'beginner',
            2: 'beginner',
            3: 'intermediate',
            4: 'advanced',
            5: 'advanced'
        }
    
    async def generate_ai_powered_exercises(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Generate AI-powered exercises to replace default fallback exercises.
        
        Args:
            course_id: The course ID to generate exercises for
            
        Returns:
            List of AI-generated exercise dictionaries
        """
        try:
            # Get syllabus data
            syllabus = await self.syllabus_service.get_syllabus(course_id)
            if not syllabus:
                raise ValueError(f"No syllabus found for course {course_id}")
            
            # Generate exercises using AI service
            try:
                ai_response = await self.ai_service.generate_interactive_exercises(syllabus)
                
                if ai_response and 'exercises' in ai_response:
                    exercises = ai_response['exercises']
                    
                    # Process and validate each exercise
                    processed_exercises = []
                    for exercise_data in exercises:
                        # Add metadata
                        exercise_data['id'] = str(uuid.uuid4())
                        exercise_data['course_id'] = course_id
                        exercise_data['created_at'] = datetime.now().isoformat()
                        exercise_data['source'] = 'ai_generated'
                        
                        # Validate exercise quality
                        if self.validate_exercise_quality(exercise_data):
                            # Generate interactive lab environment if needed
                            if exercise_data.get('type') in self.exercise_types and \
                               self.exercise_types[exercise_data['type']]['requires_lab_env']:
                                lab_env = await self.generate_interactive_lab_environment(course_id, exercise_data)
                                exercise_data['lab_environment'] = lab_env
                            
                            processed_exercises.append(exercise_data)
                            
                            # Save to database
                            try:
                                await self.save_exercise_to_database(exercise_data)
                            except Exception as e:
                                logger.error(f"Failed to save exercise to database: {e}")
                                self._add_to_memory_cache(course_id, exercise_data)
                        else:
                            logger.warning(f"Invalid exercise data generated for course {course_id}")
                    
                    return processed_exercises
                else:
                    logger.warning("Invalid AI response, falling back to enhanced exercises")
                    
            except Exception as e:
                logger.error(f"AI service failed: {e}, falling back to enhanced exercises")
            
            # Fallback to enhanced exercises (not the old default ones)
            return await self.generate_enhanced_fallback_exercises(course_id, syllabus)
            
        except Exception as e:
            logger.error(f"Error generating AI-powered exercises for course {course_id}: {e}")
            raise
    
    async def generate_enhanced_fallback_exercises(self, course_id: str, syllabus: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate enhanced fallback exercises when AI fails.
        These are much better than the original default exercises.
        """
        try:
            exercises = []
            
            for module_idx, module in enumerate(syllabus.get("modules", [])):
                module_number = module.get('module_number', module_idx + 1)
                module_title = module.get('title', f'Module {module_number}')
                topics = module.get("topics", [module_title])
                
                # Determine exercise type based on module content
                exercise_type = self._determine_exercise_type(module_title, topics)
                
                # Generate exercise with proper lab environment
                exercise_data = {
                    'id': str(uuid.uuid4()),
                    'course_id': course_id,
                    'title': f'{module_title} - Interactive Lab',
                    'description': f'Hands-on interactive lab for {module_title}. Apply concepts through practical exercises with real-time feedback.',
                    'type': exercise_type,
                    'difficulty': self._get_progressive_difficulty(module_number),
                    'module_number': module_number,
                    'topics_covered': topics,
                    'estimated_time': f"{self.exercise_types[exercise_type]['duration_range'][0]}-{self.exercise_types[exercise_type]['duration_range'][1]} minutes",
                    'learning_objectives': [
                        f"Apply {module_title} concepts in practical scenarios",
                        f"Develop hands-on skills with {', '.join(topics[:3])}",
                        "Gain experience with real-world problem solving"
                    ],
                    'source': 'enhanced_fallback',
                    'created_at': datetime.now().isoformat(),
                    'exercises': await self._generate_step_by_step_exercises(module_title, topics, exercise_type)
                }
                
                # Add lab environment for interactive exercises
                if self.exercise_types[exercise_type]['requires_lab_env']:
                    lab_env = await self.generate_interactive_lab_environment(course_id, exercise_data)
                    exercise_data['lab_environment'] = lab_env
                
                exercises.append(exercise_data)
            
            return exercises
            
        except Exception as e:
            logger.error(f"Error generating enhanced fallback exercises: {e}")
            raise
    
    def _determine_exercise_type(self, module_title: str, topics: List[str]) -> str:
        """Determine the best exercise type based on module content."""
        title_lower = module_title.lower()
        topics_str = ' '.join(topics).lower()
        
        if any(keyword in title_lower or keyword in topics_str for keyword in ['data', 'analysis', 'visualization', 'statistics']):
            return 'data_analysis'
        elif any(keyword in title_lower or keyword in topics_str for keyword in ['design', 'architecture', 'pattern', 'system']):
            return 'design_challenge'
        elif any(keyword in title_lower or keyword in topics_str for keyword in ['simulation', 'model', 'algorithm']):
            return 'simulation'
        elif any(keyword in title_lower or keyword in topics_str for keyword in ['case', 'study', 'research', 'analysis']):
            return 'case_study'
        else:
            return 'interactive_lab'
    
    def _get_progressive_difficulty(self, module_number: int) -> str:
        """Get progressive difficulty based on module number."""
        return self.difficulty_progression.get(module_number, 'intermediate')
    
    async def _generate_step_by_step_exercises(self, module_title: str, topics: List[str], exercise_type: str) -> List[Dict[str, Any]]:
        """Generate step-by-step exercises for the module."""
        exercises = []
        
        for idx, topic in enumerate(topics[:3]):  # Limit to 3 main topics
            step_exercise = {
                'step': idx + 1,
                'title': f'{topic} Practice',
                'description': f'Interactive practice with {topic} concepts',
                'starter_code': self._generate_starter_code(topic, exercise_type),
                'solution': self._generate_solution_code(topic, exercise_type),
                'validation': self._generate_validation_code(topic, exercise_type),
                'hints': [
                    f'Focus on {topic} fundamentals',
                    f'Apply {module_title} principles',
                    'Test your solution incrementally'
                ]
            }
            exercises.append(step_exercise)
        
        return exercises
    
    def _generate_starter_code(self, topic: str, exercise_type: str) -> str:
        """Generate appropriate starter code based on topic and exercise type."""
        if exercise_type == 'data_analysis':
            return f"""
# {topic} Data Analysis Exercise
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load your data here
data = pd.DataFrame()

# Your analysis code here
"""
        elif exercise_type == 'design_challenge':
            return f"""
# {topic} Design Challenge
class {topic.replace(' ', '')}:
    def __init__(self):
        # Your initialization code here
        pass
    
    def implement_solution(self):
        # Your implementation here
        pass
"""
        else:
            return f"""
# {topic} Interactive Lab
# Complete the following exercises

def solve_{topic.lower().replace(' ', '_')}():
    # Your solution here
    pass

# Test your solution
if __name__ == "__main__":
    result = solve_{topic.lower().replace(' ', '_')}()
    print(f"Result: {{result}}")
"""
    
    def _generate_solution_code(self, topic: str, exercise_type: str) -> str:
        """Generate solution code for the exercise."""
        if exercise_type == 'data_analysis':
            return f"""
# {topic} Data Analysis Solution
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sample solution for {topic}
data = pd.DataFrame({{'values': np.random.randn(100)}})
result = data.describe()
plt.figure(figsize=(10, 6))
plt.plot(data['values'])
plt.title('{topic} Analysis')
plt.show()
"""
        elif exercise_type == 'design_challenge':
            return f"""
# {topic} Design Solution
class {topic.replace(' ', '')}:
    def __init__(self):
        self.initialized = True
    
    def implement_solution(self):
        return f"Solution for {topic}"
"""
        else:
            return f"""
# {topic} Solution
def solve_{topic.lower().replace(' ', '_')}():
    return "{topic} successfully implemented"

if __name__ == "__main__":
    result = solve_{topic.lower().replace(' ', '_')}()
    print(f"Result: {{result}}")
"""
    
    def _generate_validation_code(self, topic: str, exercise_type: str) -> str:
        """Generate validation code for the exercise."""
        if exercise_type == 'data_analysis':
            return f"assert data is not None and len(data) > 0, '{topic} data should not be empty'"
        elif exercise_type == 'design_challenge':
            return f"assert hasattr({topic.replace(' ', '')}, 'implement_solution'), '{topic} class should have implement_solution method'"
        else:
            return f"assert solve_{topic.lower().replace(' ', '_')}() is not None, '{topic} function should return a result'"
    
    async def generate_interactive_lab_environment(self, course_id: str, exercise_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate interactive lab environment for an exercise.
        
        Args:
            course_id: The course ID
            exercise_data: Exercise data dictionary
            
        Returns:
            Lab environment dictionary
        """
        try:
            # Determine environment type based on exercise
            env_type = self._determine_environment_type(exercise_data)
            
            # Create lab environment configuration
            lab_config = {
                'course_id': course_id,
                'name': f"{exercise_data['title']} Environment",
                'description': f"Interactive lab environment for {exercise_data['title']}",
                'environment_type': env_type,
                'config': self._get_environment_config(env_type, exercise_data),
                'exercises': exercise_data.get('exercises', []),
                'is_active': True
            }
            
            # Use lab service to create environment
            lab_env = await self.lab_service.create_lab_environment(lab_config)
            
            return lab_env
            
        except Exception as e:
            logger.error(f"Error generating interactive lab environment: {e}")
            # Return a basic environment configuration
            return {
                'id': str(uuid.uuid4()),
                'name': f"{exercise_data['title']} Environment",
                'environment_type': 'basic',
                'config': {'language': 'python', 'version': '3.9'},
                'exercises': exercise_data.get('exercises', [])
            }
    
    def _determine_environment_type(self, exercise_data: Dict[str, Any]) -> str:
        """Determine the appropriate environment type for the exercise."""
        exercise_type = exercise_data.get('type', 'interactive_lab')
        topics = exercise_data.get('topics_covered', [])
        title = exercise_data.get('title', '').lower()
        
        if exercise_type == 'data_analysis' or any('data' in topic.lower() for topic in topics):
            return 'data'
        elif 'web' in title or any('web' in topic.lower() for topic in topics):
            return 'web'
        elif 'java' in title or any('java' in topic.lower() for topic in topics):
            return 'java'
        elif 'security' in title or any('security' in topic.lower() for topic in topics):
            return 'security'
        else:
            return 'python'
    
    def _get_environment_config(self, env_type: str, exercise_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get environment configuration based on type."""
        base_configs = {
            'python': {
                'language': 'python',
                'version': '3.9',
                'packages': ['numpy', 'pandas', 'matplotlib']
            },
            'data': {
                'language': 'python',
                'version': '3.9',
                'packages': ['pandas', 'numpy', 'matplotlib', 'scikit-learn', 'seaborn']
            },
            'web': {
                'language': 'html',
                'version': 'html5',
                'frameworks': ['bootstrap', 'jquery']
            },
            'java': {
                'language': 'java',
                'version': '11',
                'build_tool': 'maven'
            },
            'security': {
                'language': 'linux',
                'version': 'ubuntu20',
                'tools': ['nmap', 'wireshark', 'metasploit']
            }
        }
        
        return base_configs.get(env_type, base_configs['python'])
    
    async def save_exercise_to_database(self, exercise_data: Dict[str, Any]) -> None:
        """
        Save exercise to database with proper schema mapping.
        
        Args:
            exercise_data: Exercise data dictionary
        """
        if not self.db:
            raise Exception("Database not available")
        
        try:
            # Map exercise data to database schema
            query = """
                INSERT INTO exercises (
                    id, course_id, title, description, type, difficulty, 
                    module_number, estimated_time, learning_objectives, 
                    exercise_data, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    type = EXCLUDED.type,
                    difficulty = EXCLUDED.difficulty,
                    module_number = EXCLUDED.module_number,
                    estimated_time = EXCLUDED.estimated_time,
                    learning_objectives = EXCLUDED.learning_objectives,
                    exercise_data = EXCLUDED.exercise_data,
                    updated_at = EXCLUDED.updated_at
            """
            
            # Create a serializable copy of exercise_data
            serializable_data = {}
            for key, value in exercise_data.items():
                try:
                    json.dumps(value)  # Test if value is serializable
                    serializable_data[key] = value
                except (TypeError, ValueError):
                    # Skip non-serializable values (like AsyncMock objects)
                    logger.warning(f"Skipping non-serializable field {key} in exercise data")
            
            values = (
                exercise_data['id'],
                exercise_data['course_id'],
                exercise_data['title'],
                exercise_data['description'],
                exercise_data['type'],
                exercise_data['difficulty'],
                exercise_data.get('module_number', 1),
                exercise_data.get('estimated_time', '30 minutes'),
                json.dumps(exercise_data.get('learning_objectives', [])),
                json.dumps(serializable_data),
                exercise_data.get('created_at', datetime.now().isoformat()),
                datetime.now().isoformat()
            )
            
            await self.db.execute(query, values)
            logger.info(f"Exercise {exercise_data['id']} saved to database")
            
        except Exception as e:
            logger.error(f"Error saving exercise to database: {e}")
            raise
    
    def validate_exercise_quality(self, exercise_data: Dict[str, Any]) -> bool:
        """
        Validate exercise quality and completeness.
        
        Args:
            exercise_data: Exercise data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            required_fields = ['title', 'description', 'type']
            for field in required_fields:
                if not exercise_data.get(field) or str(exercise_data[field]).strip() == '':
                    logger.warning(f"Exercise missing required field: {field}")
                    return False
            
            # Check exercise type is valid
            if exercise_data['type'] not in self.exercise_types:
                logger.warning(f"Invalid exercise type: {exercise_data['type']}")
                return False
            
            # Check exercises structure if present
            exercises = exercise_data.get('exercises', [])
            if exercises and not isinstance(exercises, list):
                logger.warning("Exercises must be a list")
                return False
            
            # Validate individual exercises
            for exercise in exercises:
                if not self._validate_individual_exercise(exercise):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating exercise quality: {e}")
            return False
    
    def _validate_individual_exercise(self, exercise: Dict[str, Any]) -> bool:
        """Validate individual exercise within the exercise set."""
        required_fields = ['title', 'description']
        for field in required_fields:
            if not exercise.get(field) or exercise[field].strip() == '':
                return False
        return True
    
    def _add_to_memory_cache(self, course_id: str, exercise_data: Dict[str, Any]) -> None:
        """Add exercise to memory cache."""
        if course_id not in self._memory_cache:
            self._memory_cache[course_id] = []
        self._memory_cache[course_id].append(exercise_data)
    
    async def personalize_exercises_for_course(self, course_context: Dict[str, Any], syllabus: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Personalize exercises based on course context.
        
        Args:
            course_context: Course context information
            syllabus: Syllabus data
            
        Returns:
            List of personalized exercises
        """
        try:
            exercises = []
            
            for module in syllabus.get("modules", []):
                # Create personalized exercise based on course context
                exercise_data = {
                    'id': str(uuid.uuid4()),
                    'course_id': course_context['id'],
                    'title': f"{module['title']} - {course_context['category']} Lab",
                    'description': f"Specialized {course_context['category']} lab for {module['title']}. Designed for {course_context['target_audience']}.",
                    'type': 'interactive_lab',
                    'difficulty': course_context['difficulty_level'],
                    'module_number': module.get('module_number', 1),
                    'topics_covered': module.get('topics', []),
                    'estimated_time': '45 minutes',
                    'learning_objectives': [
                        f"Apply {module['title']} in {course_context['category']} context",
                        f"Develop professional {course_context['category']} skills"
                    ],
                    'lab_environment': {
                        'type': self._determine_environment_type({'title': course_context['title']}),
                        'packages': self._get_specialized_packages(course_context['category'])
                    },
                    'source': 'personalized',
                    'created_at': datetime.now().isoformat()
                }
                
                exercises.append(exercise_data)
            
            return exercises
            
        except Exception as e:
            logger.error(f"Error personalizing exercises: {e}")
            raise
    
    def _get_specialized_packages(self, category: str) -> List[str]:
        """Get specialized packages based on course category."""
        package_mapping = {
            'Data Science': ['pandas', 'numpy', 'matplotlib', 'scikit-learn', 'seaborn'],
            'Web Development': ['flask', 'django', 'requests', 'beautifulsoup4'],
            'Machine Learning': ['tensorflow', 'pytorch', 'scikit-learn', 'numpy'],
            'Cybersecurity': ['scapy', 'cryptography', 'hashlib'],
            'DevOps': ['docker', 'kubernetes', 'ansible']
        }
        
        return package_mapping.get(category, ['numpy', 'pandas'])
    
    async def generate_progressive_exercises(self, course_id: str) -> List[Dict[str, Any]]:
        """
        Generate exercises with progressive difficulty.
        
        Args:
            course_id: The course ID
            
        Returns:
            List of exercises with progressive difficulty
        """
        try:
            syllabus = await self.syllabus_service.get_syllabus(course_id)
            exercises = []
            
            for module in syllabus.get("modules", []):
                module_number = module.get('module_number', 1)
                difficulty = self._get_progressive_difficulty(module_number)
                
                exercise_data = {
                    'id': str(uuid.uuid4()),
                    'course_id': course_id,
                    'title': f"{module['title']} - Progressive Lab",
                    'description': f"Progressive difficulty lab for {module['title']}",
                    'type': 'interactive_lab',
                    'difficulty': difficulty,
                    'module_number': module_number,
                    'topics_covered': module.get('topics', []),
                    'estimated_time': f"{30 + (module_number * 10)} minutes",
                    'learning_objectives': [
                        f"Master {module['title']} at {difficulty} level"
                    ],
                    'source': 'progressive',
                    'created_at': datetime.now().isoformat()
                }
                
                exercises.append(exercise_data)
            
            return exercises
            
        except Exception as e:
            logger.error(f"Error generating progressive exercises: {e}")
            raise