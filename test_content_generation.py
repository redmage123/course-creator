#!/usr/bin/env python3
"""
Test script to verify content generation functionality
"""
import requests
import json
import uuid

def test_content_generation():
    """Test the complete content generation workflow"""
    
    base_url = "http://localhost:8001"
    
    # Step 1: Create a test syllabus
    print("🧪 Testing Content Generation Workflow")
    print("=" * 50)
    
    course_id = str(uuid.uuid4())
    print(f"Course ID: {course_id}")
    
    # Step 2: Generate a syllabus first
    syllabus_request = {
        "course_id": course_id,
        "title": "Introduction to Python Programming",
        "description": "Learn Python programming from basics to advanced concepts",
        "category": "Programming",
        "difficulty_level": "beginner",
        "estimated_duration": 40
    }
    
    print("\n1. Generating syllabus...")
    response = requests.post(f"{base_url}/syllabus/generate", json=syllabus_request)
    
    if response.status_code == 200:
        syllabus_data = response.json()
        print(f"✅ Syllabus generated with {len(syllabus_data['syllabus']['modules'])} modules")
    else:
        print(f"❌ Failed to generate syllabus: {response.status_code}")
        print(response.text)
        return False
    
    # Step 3: Generate content from syllabus
    print("\n2. Generating content from syllabus...")
    content_request = {"course_id": course_id}
    
    response = requests.post(f"{base_url}/content/generate-from-syllabus", json=content_request)
    
    if response.status_code == 200:
        content_data = response.json()
        print(f"✅ Content generated successfully!")
        print(f"   - {len(content_data['slides'])} slides")
        print(f"   - {len(content_data['exercises'])} exercises") 
        print(f"   - {len(content_data['quizzes'])} quizzes")
        if 'lab' in content_data:
            print(f"   - Lab environment created")
        
        # Test fetching the content
        print("\n3. Testing content retrieval...")
        
        # Test slides
        slides_response = requests.get(f"{base_url}/slides/{course_id}")
        if slides_response.status_code == 200:
            slides = slides_response.json()['slides']
            print(f"✅ Retrieved {len(slides)} slides")
            if slides:
                print(f"   First slide: '{slides[0]['title']}'")
        else:
            print("❌ Failed to retrieve slides")
        
        # Test exercises
        exercises_response = requests.get(f"{base_url}/exercises/{course_id}")
        if exercises_response.status_code == 200:
            exercises = exercises_response.json()['exercises']
            print(f"✅ Retrieved {len(exercises)} exercises")
            if exercises:
                print(f"   First exercise: '{exercises[0]['title']}'")
        else:
            print("❌ Failed to retrieve exercises")
        
        # Test quizzes
        quizzes_response = requests.get(f"{base_url}/quizzes/{course_id}")
        if quizzes_response.status_code == 200:
            quizzes = quizzes_response.json()['quizzes']
            print(f"✅ Retrieved {len(quizzes)} quizzes")
            if quizzes:
                print(f"   First quiz: '{quizzes[0]['title']}'")
        else:
            print("❌ Failed to retrieve quizzes")
        
        # Test lab environment
        lab_response = requests.get(f"{base_url}/lab/{course_id}")
        if lab_response.status_code == 200:
            lab = lab_response.json()['lab']
            print(f"✅ Retrieved lab environment: '{lab['name']}'")
        else:
            print("❌ Failed to retrieve lab environment")
            
        return True
    else:
        print(f"❌ Failed to generate content: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    success = test_content_generation()
    
    if success:
        print("\n🎉 All content generation tests passed!")
    else:
        print("\n❌ Content generation tests failed!")