#!/usr/bin/env python3
"""Test script to verify imports work correctly."""

import sys
import os
sys.path.insert(0, '/home/bbrelin/course-creator/services/course-generator')

# Test import of ExerciseGenerationService standalone
try:
    from services.exercise_generation_service import ExerciseGenerationService
    print("✓ ExerciseGenerationService imported successfully")
    
    # Test instantiation
    from unittest.mock import Mock
    mock_db = Mock()
    mock_ai_service = Mock()
    mock_syllabus_service = Mock()
    mock_lab_service = Mock()
    
    service = ExerciseGenerationService(
        db=mock_db,
        ai_service=mock_ai_service,
        syllabus_service=mock_syllabus_service,
        lab_service=mock_lab_service
    )
    print("✓ ExerciseGenerationService instantiated successfully")
    
except Exception as e:
    print(f"✗ Error with ExerciseGenerationService: {e}")
    import traceback
    traceback.print_exc()