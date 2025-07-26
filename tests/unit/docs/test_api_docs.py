import pytest
from docs.api_validator import validate_api_docs

def test_api_docs_structure():
    """Test API documentation structure and required sections"""
    errors = validate_api_docs("docs/api")
    assert not errors, f"API docs validation failed: {errors}"

def test_api_examples():
    """Test API examples are valid and match schemas"""
    examples = collect_api_examples("docs/api")
    for example in examples:
        assert validate_example(example)

def test_architecture_diagrams():
    """Test architecture diagrams are valid"""
    diagrams = collect_diagrams("docs/architecture/diagrams")
    for diagram in diagrams:
        assert validate_diagram(diagram)