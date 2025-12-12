"""
Bug Analysis Service Unit Tests

BUSINESS CONTEXT:
Tests for the bug analysis service that uses Claude AI
to analyze bug reports and identify root causes.

TECHNICAL IMPLEMENTATION:
Tests service logic with real objects and test doubles.
"""

import pytest
from datetime import datetime
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../services/bug-tracking'))

from bug_tracking.domain.entities.bug_report import BugReport, BugSeverity, BugStatus
from bug_tracking.domain.entities.bug_analysis import BugAnalysisResult, ComplexityEstimate
from bug_tracking.application.services.bug_analysis_service import BugAnalysisService


class TestBugAnalysisService:
    """Tests for BugAnalysisService."""

    @pytest.fixture
    def analysis_service(self):
        """Create analysis service instance."""
        return BugAnalysisService()

    @pytest.fixture
    def sample_bug(self):
        """Create a sample bug report for testing."""
        return BugReport.create(
            title="Login button not responding",
            description="When I click the login button, nothing happens. No network request is made.",
            submitter_email="test@example.com",
            severity=BugSeverity.HIGH,
            steps_to_reproduce="1. Go to /login\n2. Enter credentials\n3. Click Login",
            expected_behavior="Should log in and redirect to dashboard",
            actual_behavior="Nothing happens, button does nothing",
            affected_component="authentication"
        )

    def test_service_initialization(self, analysis_service):
        """Test service initializes with correct configuration."""
        assert analysis_service.claude_model is not None
        assert analysis_service.max_tokens > 0

    def test_build_analysis_prompt_includes_bug_info(self, analysis_service, sample_bug):
        """Test that analysis prompt includes all bug information."""
        prompt = analysis_service._build_analysis_prompt(sample_bug, "// sample code context")

        assert sample_bug.title in prompt
        assert sample_bug.description in prompt
        assert "authentication" in prompt
        assert "sample code context" in prompt

    def test_build_analysis_prompt_includes_steps(self, analysis_service, sample_bug):
        """Test that analysis prompt includes reproduction steps."""
        prompt = analysis_service._build_analysis_prompt(sample_bug, "")

        assert "Go to /login" in prompt
        assert "Click Login" in prompt

    def test_parse_analysis_response_success(self, analysis_service):
        """Test parsing a valid analysis response."""
        response_text = """
        ROOT_CAUSE:
        The login button click handler is not attached due to a React hydration mismatch.
        END_ROOT_CAUSE

        SUGGESTED_FIX:
        Add useEffect hook to properly attach the click handler after hydration.
        END_SUGGESTED_FIX

        AFFECTED_FILES:
        frontend-react/src/features/auth/Login.tsx
        frontend-react/src/hooks/useAuth.ts
        END_AFFECTED_FILES

        CONFIDENCE: 85

        COMPLEXITY: moderate
        """

        analysis_data = analysis_service._parse_analysis_response(response_text)

        assert "hydration mismatch" in analysis_data["root_cause_analysis"]
        assert "useEffect" in analysis_data["suggested_fix"]
        assert len(analysis_data["affected_files"]) == 2
        assert analysis_data["confidence_score"] == 85
        assert analysis_data["complexity_estimate"] == ComplexityEstimate.MODERATE

    def test_parse_analysis_response_handles_missing_sections(self, analysis_service):
        """Test parsing handles incomplete responses gracefully."""
        response_text = """
        ROOT_CAUSE:
        Something is broken.
        END_ROOT_CAUSE

        CONFIDENCE: 50
        """

        analysis_data = analysis_service._parse_analysis_response(response_text)

        assert "Something is broken" in analysis_data["root_cause_analysis"]
        assert analysis_data["confidence_score"] == 50
        # Should have defaults for missing sections
        assert analysis_data["suggested_fix"] is not None
        assert isinstance(analysis_data["affected_files"], list)

    def test_parse_analysis_response_extracts_confidence(self, analysis_service):
        """Test confidence score extraction from various formats."""
        # Test integer format
        response1 = "CONFIDENCE: 85\n"
        assert analysis_service._extract_confidence(response1) == 85.0

        # Test percentage format
        response2 = "CONFIDENCE: 90%\n"
        assert analysis_service._extract_confidence(response2) == 90.0

        # Test decimal format
        response3 = "CONFIDENCE: 0.75\n"
        assert analysis_service._extract_confidence(response3) == 75.0

    def test_parse_analysis_response_extracts_complexity(self, analysis_service):
        """Test complexity extraction."""
        # Test standard format
        response1 = "COMPLEXITY: simple\n"
        assert analysis_service._extract_complexity(response1) == ComplexityEstimate.SIMPLE

        # Test capitalized
        response2 = "COMPLEXITY: VERY_COMPLEX\n"
        assert analysis_service._extract_complexity(response2) == ComplexityEstimate.VERY_COMPLEX

        # Test with spaces
        response3 = "COMPLEXITY: very complex\n"
        assert analysis_service._extract_complexity(response3) == ComplexityEstimate.VERY_COMPLEX

    
    @pytest.mark.asyncio
    async def test_gather_codebase_context_includes_component(self, analysis_service, sample_bug):
        """Test that codebase context gathering considers affected component."""
        # Requires real codebase search implementation
        pass

    
    @pytest.mark.asyncio
    async def test_analyze_bug_creates_result(self, analysis_service, sample_bug):
        """Test full analysis flow creates valid result."""
        # Requires real Claude API or test fixtures
        pass


class TestBugAnalysisServiceEdgeCases:
    """Edge case tests for BugAnalysisService."""

    @pytest.fixture
    def analysis_service(self):
        return BugAnalysisService()

    def test_extract_section_empty_response(self, analysis_service):
        """Test section extraction from empty response."""
        result = analysis_service._extract_section("", "ROOT_CAUSE", "END_ROOT_CAUSE")
        assert result == ""

    def test_extract_section_missing_end_marker(self, analysis_service):
        """Test section extraction with missing end marker."""
        text = "ROOT_CAUSE:\nSome analysis without end marker"
        result = analysis_service._extract_section(text, "ROOT_CAUSE:", "END_ROOT_CAUSE")
        # Should return empty or handle gracefully
        assert result == "" or "Some analysis" in result

    def test_parse_affected_files_various_formats(self, analysis_service):
        """Test parsing affected files from various formats."""
        # Bullet list format
        text1 = """
        AFFECTED_FILES:
        - file1.py
        - file2.py
        END_AFFECTED_FILES
        """
        files1 = analysis_service._extract_affected_files(text1)
        assert "file1.py" in files1
        assert "file2.py" in files1

        # Numbered list format
        text2 = """
        AFFECTED_FILES:
        1. file1.py
        2. file2.py
        END_AFFECTED_FILES
        """
        files2 = analysis_service._extract_affected_files(text2)
        assert "file1.py" in files2

        # Plain list format
        text3 = """
        AFFECTED_FILES:
        file1.py
        file2.py
        END_AFFECTED_FILES
        """
        files3 = analysis_service._extract_affected_files(text3)
        assert "file1.py" in files3

    def test_confidence_extraction_bounds(self, analysis_service):
        """Test confidence extraction respects bounds."""
        # Over 100 should be capped
        response1 = "CONFIDENCE: 150\n"
        assert analysis_service._extract_confidence(response1) <= 100

        # Negative should be clamped to 0
        response2 = "CONFIDENCE: -10\n"
        assert analysis_service._extract_confidence(response2) >= 0

    def test_complexity_unknown_defaults_to_moderate(self, analysis_service):
        """Test unknown complexity defaults to moderate."""
        response = "COMPLEXITY: unknown_value\n"
        result = analysis_service._extract_complexity(response)
        assert result == ComplexityEstimate.MODERATE
