#!/usr/bin/env python3
"""
API-Based Template Workflow

BUSINESS CONTEXT:
Creates complete organization structure from templates using direct REST API calls.
Bypasses UI automation issues by using backend APIs directly. Faster and more reliable
than browser automation.

TECHNICAL IMPLEMENTATION:
- Uses requests library for HTTP calls
- Authenticates via JWT tokens
- Creates entities in correct dependency order
- Validates API responses
- Provides detailed logging

WHY THIS APPROACH:
- No UI automation flakiness
- Faster execution (seconds vs minutes)
- More reliable (direct database operations)
- Easier to debug (direct API responses)
- Can run in CI/CD pipelines
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIWorkflow:
    """
    API-based workflow orchestrator

    BUSINESS CONTEXT:
    Automates the creation of complete organization structures by
    making direct API calls to backend services. No browser required.

    TECHNICAL IMPLEMENTATION:
    Uses requests library to make authenticated HTTP calls to
    platform REST APIs in the correct dependency order.
    """

    def __init__(self, base_url: str = "https://localhost:3000"):
        """Initialize API workflow orchestrator"""
        self.base_url = base_url
        self.templates_dir = Path(__file__).parent / "templates"
        self.session = requests.Session()
        self.session.verify = False  # For self-signed certs
        self.auth_token: Optional[str] = None
        self.organization_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self.created_entities: Dict[str, List[str]] = {
            "organizations": [],
            "users": [],
            "programs": [],
            "locations": [],
            "tracks": [],
            "courses": [],
            "enrollments": [],
            "assignments": []
        }

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load JSON template file

        Args:
            template_name: Name of template file

        Returns:
            Parsed JSON template data
        """
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r') as f:
            template_data = json.load(f)

        logger.info(f"✅ Loaded template: {template_name}")
        return template_data

    def create_organization(self, org_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create organization via API

        BUSINESS CONTEXT:
        Creates organization and admin user in single transaction.
        Returns organization ID and auto-logs in admin user.

        Args:
            org_template: Organization template data

        Returns:
            Created organization data including ID
        """
        logger.info("=" * 80)
        logger.info("STEP 1: CREATE ORGANIZATION VIA API")
        logger.info("=" * 80)

        org_data = org_template["organization"]
        admin_data = org_data["admin_user"]

        # Prepare organization creation payload
        # API expects flat structure with admin_ prefixed fields
        # Add timestamp to slug and domain to ensure uniqueness across test runs
        import time
        timestamp = int(time.time())
        base_slug = org_data.get("slug", org_data["name"].lower().replace(" ", "-"))
        unique_slug = f"{base_slug}-{timestamp}"

        # Make domain unique by adding timestamp
        base_domain = org_data.get("domain", "example.edu")
        unique_domain = f"test{timestamp}.{base_domain}"

        # Make admin email unique by using the unique domain
        admin_email_local = admin_data["email"].split("@")[0]
        unique_admin_email = f"{admin_email_local}@{unique_domain}"

        # Make username unique by adding timestamp
        base_username = admin_data.get("username", admin_email_local)
        unique_username = f"{base_username}{timestamp}"

        payload = {
            "name": org_data["name"],
            "slug": unique_slug,
            "description": org_data.get("description", ""),
            "domain": unique_domain,
            "street_address": org_data.get("street_address", ""),
            "city": org_data.get("city", ""),
            "state_province": org_data.get("state_province", ""),
            "postal_code": org_data.get("postal_code", ""),
            "country": org_data.get("country", "US"),
            "contact_phone": org_data.get("contact_phone", ""),
            "contact_email": org_data.get("contact_email", unique_admin_email),
            # Admin user fields (flat structure, not nested)
            "admin_full_name": admin_data["full_name"],
            "admin_username": unique_username,
            "admin_email": unique_admin_email,
            "admin_password": admin_data["password"],
            "admin_role": admin_data.get("role", "organization_admin")
        }

        # Create organization
        response = self.session.post(
            f"{self.base_url}/api/v1/organizations",
            json=payload,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code in [200, 201]:
            result = response.json()
            self.organization_id = result.get("organization_id") or result.get("id")
            self.created_entities["organizations"].append(self.organization_id)
            logger.info(f"✅ Organization created: {org_data['name']} (ID: {self.organization_id})")

            # Login to get auth token with the unique email and username we created
            self.login(unique_admin_email, admin_data["password"], unique_username)

            return result
        else:
            logger.error(f"❌ Failed to create organization: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"Organization creation failed: {response.text}")

    def login(self, email: str, password: str, username: str = None) -> str:
        """
        Login and get auth token

        Args:
            email: User email
            password: User password
            username: Username (optional, defaults to email local part)

        Returns:
            JWT auth token
        """
        logger.info(f"Logging in as {email}...")

        # Use username if provided, otherwise extract from email
        if not username:
            username = email.split("@")[0]

        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            self.auth_token = result.get("token") or result.get("access_token")
            self.user_id = result.get("user_id")

            # Set auth header for all future requests
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })

            logger.info(f"✅ Logged in successfully (Token: {self.auth_token[:20]}...)")
            return self.auth_token
        else:
            logger.error(f"❌ Login failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"Login failed: {response.text}")

    def create_training_program(self, program_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create training program (course) via API

        BUSINESS CONTEXT:
        Training programs are represented as courses in the database.
        Each program can have multiple locations and tracks.

        Args:
            program_data: Program template data

        Returns:
            Created program data including ID
        """
        logger.info("=" * 80)
        logger.info("STEP 2: CREATE TRAINING PROGRAM")
        logger.info("=" * 80)

        payload = {
            "title": program_data["name"],
            "description": program_data["description"],
            "category": program_data.get("category", "Software Engineering"),
            "difficulty_level": program_data.get("difficulty_level", "intermediate"),
            "estimated_duration": program_data.get("estimated_duration", 18),
            "duration_unit": program_data.get("duration_unit", "months"),
            "price": program_data.get("price", 0),
            "is_published": program_data.get("is_published", False),
            "organization_id": self.organization_id
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/courses",
            json=payload
        )

        if response.status_code in [200, 201]:
            result = response.json()
            program_id = result.get("id")
            self.created_entities["programs"].append(program_id)
            logger.info(f"✅ Training program created: {program_data['name']} (ID: {program_id})")
            return result
        else:
            logger.error(f"❌ Failed to create training program: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"Training program creation failed: {response.text}")

    def create_track(self, track_data: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """
        Create learning track via API

        BUSINESS CONTEXT:
        Tracks organize courses into structured learning paths.
        Each track belongs to a project (training program).

        Args:
            track_data: Track template data
            project_id: ID of parent project

        Returns:
            Created track data including ID
        """
        payload = {
            "name": track_data["name"],
            "description": track_data.get("description", ""),
            "project_id": project_id,
            "target_audience": track_data.get("target_audience", []),
            "prerequisites": track_data.get("prerequisites", []),
            "learning_objectives": track_data.get("learning_objectives", []),
            "duration_weeks": track_data.get("duration_weeks"),
            "difficulty_level": track_data.get("difficulty_level", "beginner"),
            "max_students": track_data.get("max_students", 50)
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/tracks/",
            json=payload
        )

        if response.status_code in [200, 201]:
            result = response.json()
            track_id = result.get("id")
            self.created_entities["tracks"].append(track_id)
            logger.info(f"✅ Track created: {track_data['name']} (ID: {track_id})")
            return result
        else:
            logger.error(f"❌ Failed to create track: {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"Track creation failed: {response.text}")

    def create_course(self, course_data: Dict[str, Any], track_id: str) -> Dict[str, Any]:
        """
        Create individual course via API

        BUSINESS CONTEXT:
        Courses are individual learning modules within a track.
        Each course has specific learning outcomes.

        Args:
            course_data: Course template data
            track_id: ID of parent track

        Returns:
            Created course data including ID
        """
        payload = {
            "title": course_data["title"],
            "description": course_data["description"],
            "category": "Software Engineering",
            "difficulty_level": course_data.get("difficulty_level", "intermediate"),
            "estimated_duration": course_data.get("duration_weeks", 4),
            "duration_unit": "weeks",
            "price": 0,
            "is_published": False,
            "organization_id": self.organization_id,
            "track_id": track_id
        }

        response = self.session.post(
            f"{self.base_url}/api/v1/courses",
            json=payload
        )

        if response.status_code in [200, 201]:
            result = response.json()
            course_id = result.get("id")
            self.created_entities["courses"].append(course_id)
            logger.info(f"  ✅ Course created: {course_data['title']}")
            return result
        else:
            logger.warning(f"  ⚠️  Failed to create course: {course_data['title']}")
            logger.warning(f"  Response: {response.status_code} - {response.text}")
            return None

    def create_user(self, user_data: Dict[str, Any], role: str) -> Optional[Dict[str, Any]]:
        """
        Create user (instructor or student) via API

        BUSINESS CONTEXT:
        Users can be instructors or students with different permissions.
        All users belong to the organization and are created as organization members.

        Args:
            user_data: User template data
            role: User role (instructor or student)

        Returns:
            Created user data including ID
        """
        # Get full name from template
        full_name = user_data.get("full_name", f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}")

        # Generate username from email, replacing dots with underscores to match pattern ^[a-zA-Z0-9_]+$
        base_username = user_data.get("username", user_data["email"].split("@")[0])
        username = base_username.replace(".", "_")

        payload = {
            "email": user_data["email"],
            "password": user_data.get("password", "TempPass123!"),
            "full_name": full_name,
            "username": username,
            "role_name": role
        }

        # Use organization members endpoint instead of users endpoint
        response = self.session.post(
            f"{self.base_url}/api/v1/organizations/{self.organization_id}/members",
            json=payload
        )

        if response.status_code in [200, 201]:
            result = response.json()
            user_id = result.get("id") or result.get("user_id")
            self.created_entities["users"].append(user_id)
            logger.info(f"  ✅ {role.title()} created: {user_data.get('first_name', full_name)}")
            return result
        else:
            logger.warning(f"  ⚠️  Failed to create {role}: {user_data['email']}")
            logger.warning(f"  Response: {response.status_code} - {response.text}")
            return None

    def run_workflow(self):
        """
        Execute complete API workflow

        BUSINESS CONTEXT:
        Orchestrates the creation of all entities from templates
        in the correct dependency order.
        """
        try:
            logger.info("=" * 80)
            logger.info("API-BASED WORKFLOW STARTING")
            logger.info("=" * 80)

            # Load all templates
            logger.info("\nLoading templates...")
            org_template = self.load_template("organization_template.json")
            programs_template = self.load_template("training_programs_template.json")
            tracks_template = self.load_template("tracks_template.json")
            courses_template = self.load_template("courses_template.json")
            instructors_template = self.load_template("instructors_template.json")
            students_template = self.load_template("students_template.json")

            # Step 1: Create organization
            self.create_organization(org_template)

            # Step 2: Create training programs
            program_ids = []
            for program in programs_template["programs"]:
                result = self.create_training_program(program)
                program_ids.append(result["id"])

            # Step 3: Create tracks
            logger.info("=" * 80)
            logger.info("STEP 3: CREATE TRACKS")
            logger.info("=" * 80)

            track_map = {}  # Map track name to track ID
            for track in tracks_template["tracks"]:
                # Use first program for all tracks
                result = self.create_track(track, program_ids[0])
                if result:
                    track_map[track["name"]] = result["id"]

            # Step 4: Create courses and assign to tracks
            logger.info("=" * 80)
            logger.info("STEP 4: CREATE COURSES")
            logger.info("=" * 80)

            for course_group in courses_template["courses"]:
                track_name = course_group["track"]
                track_id = track_map.get(track_name)

                if not track_id:
                    logger.warning(f"⚠️  Track not found: {track_name}, skipping courses")
                    continue

                logger.info(f"\nCreating courses for track: {track_name}")
                for course in course_group["courses"]:
                    self.create_course(course, track_id)

            # Step 5: Create instructors
            logger.info("=" * 80)
            logger.info("STEP 5: CREATE INSTRUCTORS")
            logger.info("=" * 80)

            instructor_map = {}
            for instructor in instructors_template["instructors"]:
                result = self.create_user(instructor, "instructor")
                if result:
                    instructor_map[instructor["email"]] = result.get("id") or result.get("user_id")

            # Step 6: Create students
            logger.info("=" * 80)
            logger.info("STEP 6: CREATE STUDENTS")
            logger.info("=" * 80)

            student_map = {}
            for student in students_template["students"]:
                result = self.create_user(student, "student")
                if result:
                    student_map[student["email"]] = result.get("id") or result.get("user_id")

            # Step 7: Print summary
            logger.info("=" * 80)
            logger.info("WORKFLOW COMPLETE - SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Organizations created: {len(self.created_entities['organizations'])}")
            logger.info(f"Training programs created: {len(self.created_entities['programs'])}")
            logger.info(f"Tracks created: {len(self.created_entities['tracks'])}")
            logger.info(f"Courses created: {len(self.created_entities['courses'])}")
            logger.info(f"Users created: {len(self.created_entities['users'])}")
            logger.info("=" * 80)

            return True

        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    workflow = APIWorkflow()
    success = workflow.run_workflow()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
