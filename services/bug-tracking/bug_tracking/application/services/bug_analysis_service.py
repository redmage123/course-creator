"""
Bug Analysis Service with Claude Integration

BUSINESS CONTEXT:
Analyzes bug reports using Claude API to:
- Identify root cause from bug description
- Suggest fix approach
- Identify affected files in the codebase
- Estimate fix complexity

TECHNICAL CONTEXT:
- Uses Anthropic Python SDK for Claude API
- Gathers codebase context for accurate analysis
- Implements rate limiting and error handling
"""

import logging
import os
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import anthropic

from bug_tracking.domain.entities.bug_report import BugReport
from bug_tracking.domain.entities.bug_analysis import BugAnalysisResult, ComplexityEstimate


logger = logging.getLogger(__name__)


class BugAnalysisService:
    """
    Service for analyzing bugs using Claude API.

    Workflow:
    1. Receive bug report
    2. Gather codebase context (affected files, related code)
    3. Build analysis prompt
    4. Call Claude API
    5. Parse and structure results
    6. Return analysis result

    Example:
        service = BugAnalysisService()
        analysis = await service.analyze_bug(bug_report)
        print(f"Root cause: {analysis.root_cause_analysis}")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        codebase_path: Optional[str] = None
    ):
        """
        Initialize BugAnalysisService.

        Args:
            api_key: Anthropic API key (defaults to env var)
            model: Claude model to use
            codebase_path: Path to the codebase for context gathering
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.codebase_path = codebase_path or os.environ.get("CODEBASE_PATH", "/workspace")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    async def analyze_bug(self, bug: BugReport) -> BugAnalysisResult:
        """
        Analyze a bug report using Claude API.

        Args:
            bug: BugReport to analyze

        Returns:
            BugAnalysisResult: Analysis results from Claude
        """
        start_time = time.time()
        analysis_started = datetime.utcnow()

        try:
            # Gather codebase context
            context = await self._gather_codebase_context(bug)

            # Build analysis prompt
            prompt = self._build_analysis_prompt(bug, context)

            # Call Claude API
            response = await self._call_claude(prompt)

            # Parse response
            analysis_data = self._parse_analysis_response(response)

            duration_ms = int((time.time() - start_time) * 1000)

            # Create analysis result
            return BugAnalysisResult.create(
                bug_report_id=bug.id,
                root_cause_analysis=analysis_data["root_cause"],
                suggested_fix=analysis_data["suggested_fix"],
                affected_files=analysis_data["affected_files"],
                confidence_score=analysis_data["confidence_score"],
                complexity_estimate=analysis_data["complexity"],
                claude_model_used=self.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                analysis_duration_ms=duration_ms
            )

        except Exception as e:
            logger.error(f"Bug analysis failed: {e}")
            raise BugAnalysisError(f"Failed to analyze bug: {str(e)}")

    async def _gather_codebase_context(self, bug: BugReport) -> str:
        """
        Gather relevant codebase context for the bug.

        Args:
            bug: BugReport with affected component info

        Returns:
            str: Relevant code context
        """
        context_parts = []

        # Add affected component code if specified
        if bug.affected_component:
            component_code = await self._get_component_code(bug.affected_component)
            if component_code:
                context_parts.append(f"## Affected Component: {bug.affected_component}\n{component_code}")

        # Search for files mentioned in description or error logs
        if bug.error_logs:
            file_refs = self._extract_file_references(bug.error_logs)
            for file_ref in file_refs[:5]:  # Limit to 5 files
                file_content = await self._read_file(file_ref)
                if file_content:
                    context_parts.append(f"## File: {file_ref}\n```\n{file_content[:2000]}\n```")

        # Add architecture overview
        arch_overview = await self._get_architecture_overview()
        if arch_overview:
            context_parts.append(f"## Architecture Overview\n{arch_overview}")

        return "\n\n".join(context_parts)

    async def _get_component_code(self, component: str) -> Optional[str]:
        """Get code for a specific component/service."""
        # Map component names to directories
        component_map = {
            "frontend-react": "frontend-react/src",
            "user-management": "services/user-management",
            "course-management": "services/course-management",
            "course-generator": "services/course-generator",
            "lab-manager": "services/lab-manager",
            "ai-assistant-service": "services/ai-assistant-service",
            "organization-management": "services/organization-management",
            "analytics": "services/analytics",
            "metadata-service": "services/metadata-service",
        }

        component_dir = component_map.get(component.lower())
        if not component_dir:
            return None

        # Get main files from component
        main_files = ["main.py", "routes.py", "App.tsx", "index.ts"]
        content_parts = []

        import os
        for main_file in main_files:
            full_path = os.path.join(self.codebase_path, component_dir, main_file)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()[:3000]  # Limit content
                        content_parts.append(f"### {main_file}\n```\n{content}\n```")
                except Exception as e:
                    logger.warning(f"Could not read {full_path}: {e}")

        return "\n\n".join(content_parts) if content_parts else None

    async def _get_architecture_overview(self) -> str:
        """Get high-level architecture overview."""
        return """
Course Creator Platform Architecture:
- Frontend: React 18 with TypeScript (port 3000)
- Backend Services:
  - user-management (8000): Authentication, user CRUD
  - course-management (8001): Courses, enrollments
  - course-generator (8002): AI content generation
  - content-management (8003): File uploads, media
  - lab-manager (8005): Docker lab containers
  - ai-assistant-service (8007): RAG chatbot
  - organization-management (8008): Multi-tenant orgs
  - analytics (8009): Usage analytics
- Database: PostgreSQL (5433)
- Cache: Redis (6379)
- All services use HTTPS
        """

    def _extract_file_references(self, text: str) -> List[str]:
        """Extract file paths from error logs."""
        import re
        # Match common file path patterns
        patterns = [
            r'File "([^"]+\.py)"',
            r'at ([^\s]+\.(ts|tsx|js|jsx)):',
            r'(/[^\s]+\.(py|ts|tsx|js|jsx))',
        ]

        files = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    files.append(match[0])
                else:
                    files.append(match)

        return list(set(files))[:10]  # Dedupe and limit

    async def _read_file(self, file_path: str) -> Optional[str]:
        """Read a file from the codebase."""
        import os

        # Handle relative and absolute paths
        if not file_path.startswith('/'):
            full_path = os.path.join(self.codebase_path, file_path)
        else:
            full_path = file_path

        try:
            with open(full_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.debug(f"Could not read {full_path}: {e}")
            return None

    def _build_analysis_prompt(self, bug: BugReport, context: str) -> str:
        """Build the analysis prompt for Claude."""
        return f"""You are an expert software engineer analyzing a bug report for the Course Creator Platform.

## Bug Report

**Title:** {bug.title}
**Severity:** {bug.severity.value}
**Affected Component:** {bug.affected_component or 'Not specified'}

**Description:**
{bug.description}

**Steps to Reproduce:**
{bug.steps_to_reproduce or 'Not provided'}

**Expected Behavior:**
{bug.expected_behavior or 'Not provided'}

**Actual Behavior:**
{bug.actual_behavior or 'Not provided'}

**Error Logs:**
{bug.error_logs or 'None provided'}

**Browser Info:**
{bug.browser_info or 'Not specified'}

## Codebase Context
{context}

## Analysis Instructions

Please analyze this bug and provide:

1. **ROOT CAUSE ANALYSIS**: Explain why this bug is occurring. Be specific about the code path and conditions that cause it.

2. **SUGGESTED FIX**: Provide a detailed fix recommendation with code examples where appropriate.

3. **AFFECTED FILES**: List the specific files that need to be modified to fix this bug.

4. **COMPLEXITY ESTIMATE**: Rate the fix complexity as one of: trivial, simple, moderate, complex, major

5. **CONFIDENCE SCORE**: Rate your confidence in this analysis from 0-100.

Format your response as follows:

### ROOT CAUSE
[Your root cause analysis]

### SUGGESTED FIX
[Your fix recommendation with code examples]

### AFFECTED FILES
- file1.py
- file2.tsx
[etc.]

### COMPLEXITY
[trivial|simple|moderate|complex|major]

### CONFIDENCE
[0-100]
"""

    async def _call_claude(self, prompt: str) -> anthropic.types.Message:
        """Call Claude API with the analysis prompt."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise BugAnalysisError(f"Claude API error: {str(e)}")

    def _parse_analysis_response(self, response: anthropic.types.Message) -> Dict[str, Any]:
        """Parse Claude's response into structured data."""
        content = response.content[0].text

        # Extract sections using markers
        sections = {
            "root_cause": "",
            "suggested_fix": "",
            "affected_files": [],
            "complexity": "moderate",
            "confidence_score": 70.0
        }

        # Parse ROOT CAUSE
        if "### ROOT CAUSE" in content:
            start = content.index("### ROOT CAUSE") + len("### ROOT CAUSE")
            end = content.index("### SUGGESTED FIX") if "### SUGGESTED FIX" in content else len(content)
            sections["root_cause"] = content[start:end].strip()

        # Parse SUGGESTED FIX
        if "### SUGGESTED FIX" in content:
            start = content.index("### SUGGESTED FIX") + len("### SUGGESTED FIX")
            end = content.index("### AFFECTED FILES") if "### AFFECTED FILES" in content else len(content)
            sections["suggested_fix"] = content[start:end].strip()

        # Parse AFFECTED FILES
        if "### AFFECTED FILES" in content:
            start = content.index("### AFFECTED FILES") + len("### AFFECTED FILES")
            end = content.index("### COMPLEXITY") if "### COMPLEXITY" in content else len(content)
            files_section = content[start:end].strip()
            # Extract file paths (lines starting with -)
            import re
            files = re.findall(r'[-*]\s*([^\s]+\.[a-z]+)', files_section)
            sections["affected_files"] = files

        # Parse COMPLEXITY
        if "### COMPLEXITY" in content:
            start = content.index("### COMPLEXITY") + len("### COMPLEXITY")
            end = content.index("### CONFIDENCE") if "### CONFIDENCE" in content else len(content)
            complexity_text = content[start:end].strip().lower()
            valid_complexities = ["trivial", "simple", "moderate", "complex", "major"]
            for c in valid_complexities:
                if c in complexity_text:
                    sections["complexity"] = c
                    break

        # Parse CONFIDENCE
        if "### CONFIDENCE" in content:
            start = content.index("### CONFIDENCE") + len("### CONFIDENCE")
            confidence_text = content[start:].strip()
            import re
            match = re.search(r'(\d+)', confidence_text)
            if match:
                sections["confidence_score"] = min(100.0, max(0.0, float(match.group(1))))

        return sections


class BugAnalysisError(Exception):
    """Exception raised when bug analysis fails."""
    pass
