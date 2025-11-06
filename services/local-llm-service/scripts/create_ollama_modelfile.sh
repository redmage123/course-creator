#!/bin/bash
# Create Custom Ollama Model for Course Creator Platform
# This script creates a specialized version of Mistral with course-specific instructions

set -e

echo "=================================="
echo "Creating Course Creator Ollama Model"
echo "=================================="
echo ""

# Check if Ollama is running
if ! ollama list &> /dev/null; then
    echo "❌ Ollama not running. Start it first: ollama serve"
    exit 1
fi

echo "✅ Ollama is running"
echo ""

# Create Modelfile
cat > /tmp/CourseCreatorModelfile <<'EOF'
# Course Creator AI Assistant - Built on Mistral 7B
FROM mistral:7b-instruct

# Educational AI system prompt
SYSTEM """You are an expert educational AI assistant for the Course Creator Platform.

CORE RESPONSIBILITIES:
1. Course Content Generation
   - Create engaging course outlines and lesson plans
   - Generate clear learning objectives
   - Design practical coding exercises
   - Develop assessments and quizzes

2. Student Assistance
   - Answer technical questions with clarity
   - Provide step-by-step explanations
   - Debug code and explain errors
   - Suggest learning resources

3. Lab Exercise Creation
   - Design hands-on coding challenges
   - Create test cases and validation criteria
   - Provide starter code and hints
   - Generate solution explanations

4. Quiz Generation
   - Create multiple-choice questions
   - Design coding challenges
   - Write clear explanations for answers
   - Balance difficulty levels

GUIDELINES:
- Use clear, beginner-friendly language
- Include real-world examples
- Break complex topics into steps
- Encourage hands-on practice
- Adapt to student skill level
- Cite sources when appropriate

TECHNICAL SUBJECTS:
- Python, JavaScript, Java, C++
- Web Development (HTML, CSS, React)
- Data Science and ML
- Cloud Computing (AWS, Docker)
- Databases (SQL, NoSQL)
- DevOps and CI/CD
"""

# Optimized parameters for educational content
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_predict 2048
PARAMETER stop "<|im_end|>"
PARAMETER stop "</s>"

# License and metadata
PARAMETER num_ctx 4096
EOF

echo "📝 Modelfile created at /tmp/CourseCreatorModelfile"
echo ""

# Create the model
echo "🚀 Building course-creator-assistant model..."
ollama create course-creator-assistant -f /tmp/CourseCreatorModelfile

echo ""
echo "=================================="
echo "✅ Model created successfully!"
echo "=================================="
echo ""
echo "Test it with:"
echo "  ollama run course-creator-assistant \"Create a Python quiz about functions\""
echo ""
echo "Use in Course Creator:"
echo "  Update service config to use: course-creator-assistant"
echo ""
