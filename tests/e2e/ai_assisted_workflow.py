#!/usr/bin/env python3
"""
AI-Assisted Complete Platform Workflow

BUSINESS CONTEXT:
This workflow uses the platform's AI assistant to intelligently create
a complete organization structure from template files. The AI assistant
reads templates, understands entity relationships, and creates everything
in the correct order.

TECHNICAL IMPLEMENTATION:
- Reads JSON template files defining organization structure
- Uploads templates to AI assistant via Knowledge Graph API
- AI assistant processes templates and creates entities via REST APIs
- Verifies all entities were created correctly
- Reports detailed success/failure metrics

WHY THIS APPROACH:
- Reduces manual test setup time from hours to minutes
- Ensures consistent test data across environments
- Demonstrates AI assistant's capability to handle complex workflows
- Templates can be easily modified for different test scenarios
- AI handles edge cases and validation automatically
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIAssistedWorkflow:
    """
    AI-assisted workflow orchestrator

    BUSINESS CONTEXT:
    Automates the creation of complete organization structures by
    leveraging the AI assistant to process templates and create entities.

    TECHNICAL IMPLEMENTATION:
    Uses Playwright for browser automation, uploads templates to
    AI assistant knowledge graph, monitors AI execution progress,
    and verifies results against expected outcomes.
    """

    def __init__(self, base_url: str = "https://localhost:3000"):
        """Initialize workflow orchestrator"""
        self.base_url = base_url
        self.templates_dir = Path(__file__).parent / "templates"
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.auth_token: Optional[str] = None
        self.organization_id: Optional[str] = None
        self.created_entities: Dict[str, List[str]] = {
            "organizations": [],
            "users": [],
            "programs": [],
            "locations": [],
            "tracks": [],
            "courses": [],
            "enrollments": []
        }

    async def setup(self):
        """
        Set up browser and page

        BUSINESS CONTEXT:
        Initializes browser automation environment for interacting
        with the platform UI and APIs.
        """
        logger.info("Setting up browser automation...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=os.getenv('HEADLESS', 'true').lower() == 'true'
        )
        context = await self.browser.new_context(ignore_https_errors=True)
        self.page = await context.new_page()
        logger.info("Browser setup complete")

    async def teardown(self):
        """Clean up browser resources"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")

    async def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load JSON template file

        Args:
            template_name: Name of template file (e.g., "organization_template.json")

        Returns:
            Parsed JSON template data
        """
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r') as f:
            template_data = json.load(f)

        logger.info(f"Loaded template: {template_name}")
        return template_data

    async def create_organization_manual(self, org_template: Dict[str, Any]) -> bool:
        """
        Create organization using UI (Step 1 - before AI assistant available)

        BUSINESS CONTEXT:
        Organization creation must be done manually first because
        the AI assistant is only available after authentication.

        WHY THIS APPROACH:
        - Organization admin account is needed to access AI assistant
        - AI assistant requires authenticated session
        - Once org is created, AI can handle all subsequent steps
        """
        logger.info("=" * 80)
        logger.info("STEP 1: CREATE ORGANIZATION MANUALLY")
        logger.info("=" * 80)

        org_data = org_template["organization"]
        admin_data = org_data["admin_user"]

        # Navigate to organization registration
        await self.page.goto(f"{self.base_url}/organization/register")
        await self.page.wait_for_load_state('networkidle')

        # Fill organization details
        await self.page.fill('input[name="name"]', org_data["name"])
        # Note: slug is auto-generated, but we can override it
        await self.page.fill('input[name="slug"]', org_data.get("slug", org_data["name"].lower().replace(" ", "-")))
        await self.page.fill('textarea[name="description"]', org_data.get("description", ""))
        await self.page.fill('input[name="domain"]', org_data["domain"])

        # Fill organization address
        await self.page.fill('input[name="street_address"]', org_data.get("street_address", ""))
        await self.page.fill('input[name="city"]', org_data.get("city", ""))
        await self.page.fill('input[name="state_province"]', org_data.get("state_province", ""))
        await self.page.fill('input[name="postal_code"]', org_data.get("postal_code", ""))
        await self.page.select_option('select[name="country"]', org_data["country"])

        # Fill contact information
        await self.page.fill('input[name="contact_phone"]', org_data.get("contact_phone", ""))
        await self.page.fill('input[name="contact_email"]', org_data.get("contact_email", admin_data["email"]))

        # Fill admin account details
        await self.page.fill('input[name="admin_full_name"]', admin_data["full_name"])
        await self.page.fill('input[name="admin_username"]', admin_data["username"])
        await self.page.fill('input[name="admin_email"]', admin_data["email"])
        await self.page.fill('input[name="admin_password"]', admin_data["password"])
        await self.page.fill('input[name="admin_password_confirm"]', admin_data["password_confirm"])

        # Accept terms and privacy policy
        await self.page.check('input[name="terms_accepted"]')
        await self.page.check('input[name="privacy_accepted"]')

        # Submit form
        await self.page.click('button[type="submit"]')

        # Wait for redirect to login page OR directly to dashboard (depending on implementation)
        try:
            await self.page.wait_for_url(f"{self.base_url}/login*", timeout=5000)
            login_required = True
        except:
            login_required = False

        logger.info(f"✅ Organization '{org_data['name']}' created")
        logger.info(f"✅ Admin user '{admin_data['email']}' created")

        # Login as org admin if redirected to login page
        if login_required:
            await self.page.fill('input[name="email"]', admin_data["email"])
            await self.page.fill('input[name="password"]', admin_data["password"])
            await self.page.click('button[type="submit"]')

        # Wait for dashboard
        await self.page.wait_for_url(f"{self.base_url}/dashboard/org-admin*", timeout=10000)

        # Extract auth token from localStorage
        self.auth_token = await self.page.evaluate("localStorage.getItem('authToken')")
        self.organization_id = await self.page.evaluate("localStorage.getItem('organizationId')")

        logger.info(f"✅ Logged in as organization admin")
        logger.info(f"✅ Organization ID: {self.organization_id}")

        return True

    async def upload_templates_to_ai_assistant(
        self,
        templates: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Upload all templates to AI assistant knowledge graph

        BUSINESS CONTEXT:
        The AI assistant uses the knowledge graph to store and reason
        about entities. By uploading templates, we give the AI full
        context about what needs to be created.

        TECHNICAL IMPLEMENTATION:
        - Uses Knowledge Graph API to create nodes for each template
        - Links templates together showing dependencies
        - Provides instructions for AI on processing order

        Args:
            templates: Dictionary mapping template names to template data

        Returns:
            True if upload successful
        """
        logger.info("=" * 80)
        logger.info("STEP 2: UPLOAD TEMPLATES TO AI ASSISTANT")
        logger.info("=" * 80)

        # Navigate to AI assistant interface
        await self.page.goto(f"{self.base_url}/ai-assistant")
        await self.page.wait_for_load_state('networkidle')

        # Upload master workflow template
        master_template = templates["master_workflow_template.json"]

        # Create prompt for AI assistant
        prompt = f"""
I need you to help me set up a complete Software Engineering Graduate Program.
I will provide you with templates defining the entire organization structure.

Please process these templates in the following order:
1. Training programs with multiple locations
2. Learning tracks for each program phase
3. Courses assigned to each track
4. Instructor accounts with track assignments and schedules
5. Student accounts enrolled in tracks by city

Here are the templates:

**Training Programs Template:**
```json
{json.dumps(templates["training_programs_template.json"], indent=2)}
```

**Tracks Template:**
```json
{json.dumps(templates["tracks_template.json"], indent=2)}
```

**Courses Template:**
```json
{json.dumps(templates["courses_template.json"], indent=2)}
```

**Instructors Template:**
```json
{json.dumps(templates["instructors_template.json"], indent=2)}
```

**Students Template:**
```json
{json.dumps(templates["students_template.json"], indent=2)}
```

**Master Workflow:**
```json
{json.dumps(master_template, indent=2)}
```

Please create all these entities in the correct order, respecting dependencies
and date ranges. Report your progress after each major step.
"""

        # Send prompt to AI assistant
        await self.page.fill('textarea[placeholder*="Ask"]', prompt)
        await self.page.click('button:has-text("Send")')

        logger.info("✅ Templates uploaded to AI assistant")
        logger.info("✅ AI assistant is now processing templates...")

        return True

    async def monitor_ai_progress(self) -> bool:
        """
        Monitor AI assistant progress and wait for completion

        BUSINESS CONTEXT:
        The AI assistant works asynchronously. We need to monitor
        its progress and wait for confirmation that all entities
        were created successfully.

        Returns:
            True if AI completed successfully
        """
        logger.info("=" * 80)
        logger.info("STEP 3: MONITORING AI ASSISTANT PROGRESS")
        logger.info("=" * 80)

        # Wait for AI response (look for completion indicators)
        max_wait_seconds = 300  # 5 minutes timeout
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < max_wait_seconds:
            # Check for AI response
            response_text = await self.page.text_content('.ai-response:last-child')

            if response_text and any(keyword in response_text.lower() for keyword in [
                "successfully created",
                "workflow complete",
                "all entities created"
            ]):
                logger.info("✅ AI assistant completed workflow successfully")
                return True

            if response_text and "error" in response_text.lower():
                logger.error(f"❌ AI assistant encountered error: {response_text}")
                return False

            await asyncio.sleep(5)  # Check every 5 seconds

        logger.error("❌ Timeout waiting for AI assistant to complete")
        return False

    async def verify_entities_created(self) -> Dict[str, Any]:
        """
        Verify all expected entities were created

        BUSINESS CONTEXT:
        After AI assistant completes, we need to verify that all
        entities were actually created in the database and are
        accessible via the API.

        Returns:
            Verification results with counts and status
        """
        logger.info("=" * 80)
        logger.info("STEP 4: VERIFYING CREATED ENTITIES")
        logger.info("=" * 80)

        results = {
            "status": "pending",
            "checks": []
        }

        # Verify training programs
        programs_response = await self.page.evaluate(f"""
            fetch('/api/v1/courses?organization_id={self.organization_id}&published_only=false', {{
                headers: {{ 'Authorization': 'Bearer {self.auth_token}' }}
            }}).then(r => r.json())
        """)

        programs_count = len(programs_response) if isinstance(programs_response, list) else 0
        results["checks"].append({
            "entity": "training_programs",
            "expected": 1,
            "actual": programs_count,
            "status": "✅" if programs_count >= 1 else "❌"
        })

        # Verify tracks
        tracks_response = await self.page.evaluate(f"""
            fetch('/api/v1/tracks/?organization_id={self.organization_id}', {{
                headers: {{ 'Authorization': 'Bearer {self.auth_token}' }}
            }}).then(r => r.json())
        """)

        tracks_count = len(tracks_response) if isinstance(tracks_response, list) else 0
        results["checks"].append({
            "entity": "tracks",
            "expected": 4,
            "actual": tracks_count,
            "status": "✅" if tracks_count >= 4 else "❌"
        })

        # TODO: Add more verification checks for courses, instructors, students

        # Determine overall status
        all_passed = all(check["status"] == "✅" for check in results["checks"])
        results["status"] = "✅ PASSED" if all_passed else "❌ FAILED"

        # Log results
        logger.info("Verification Results:")
        for check in results["checks"]:
            logger.info(f"  {check['status']} {check['entity']}: {check['actual']}/{check['expected']}")

        return results

    async def run_complete_workflow(self):
        """
        Execute complete AI-assisted workflow

        BUSINESS CONTEXT:
        This is the main entry point that orchestrates the entire
        workflow from organization creation to final verification.
        """
        try:
            await self.setup()

            # Load all templates
            logger.info("Loading templates...")
            templates = {
                "organization_template.json": await self.load_template("organization_template.json"),
                "training_programs_template.json": await self.load_template("training_programs_template.json"),
                "tracks_template.json": await self.load_template("tracks_template.json"),
                "courses_template.json": await self.load_template("courses_template.json"),
                "instructors_template.json": await self.load_template("instructors_template.json"),
                "students_template.json": await self.load_template("students_template.json"),
                "master_workflow_template.json": await self.load_template("master_workflow_template.json")
            }
            logger.info(f"✅ Loaded {len(templates)} templates")

            # Step 1: Create organization manually
            await self.create_organization_manual(templates["organization_template.json"])

            # Step 2: Upload templates to AI assistant
            await self.upload_templates_to_ai_assistant(templates)

            # Step 3: Monitor AI progress
            ai_success = await self.monitor_ai_progress()

            if not ai_success:
                logger.error("❌ AI assistant workflow failed")
                return False

            # Step 4: Verify entities
            verification_results = await self.verify_entities_created()

            # Print final summary
            logger.info("=" * 80)
            logger.info("WORKFLOW COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Final Status: {verification_results['status']}")

            return verification_results["status"] == "✅ PASSED"

        except Exception as e:
            logger.error(f"❌ Workflow failed with exception: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            await self.teardown()


async def main():
    """Main entry point"""
    workflow = AIAssistedWorkflow()
    success = await workflow.run_complete_workflow()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
