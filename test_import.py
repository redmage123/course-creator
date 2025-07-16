#!/usr/bin/env python3
"""Test script to verify imports work correctly."""

import sys
import os
sys.path.insert(0, '/home/bbrelin/course-creator/services/course-generator')

try:
    from services.exercise_generation_service import ExerciseGenerationService
    print("✓ ExerciseGenerationService imported successfully")
except ImportError as e:
    print(f"✗ Error importing ExerciseGenerationService: {e}")

try:
    from services.lab_environment_service import LabEnvironmentService
    print("✓ LabEnvironmentService imported successfully")
except ImportError as e:
    print(f"✗ Error importing LabEnvironmentService: {e}")

try:
    from services.ai_service import AIService
    print("✓ AIService imported successfully")
except ImportError as e:
    print(f"✗ Error importing AIService: {e}")

try:
    from services.syllabus_service import SyllabusService
    print("✓ SyllabusService imported successfully")
except ImportError as e:
    print(f"✗ Error importing SyllabusService: {e}")