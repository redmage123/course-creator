#!/usr/bin/env python3
"""
Graduate Training Program Simulation
=====================================
Simulates a realistic 6-week multi-location graduate training program for
"Apex Graduate Academy". Creates organization, tracks, courses, instructors,
students, and simulates weekly learning activity with progress, quiz scores,
and lab usage.

Uses API calls (requests library) for data creation and Playwright for
login + screenshot milestones at key phases.

USAGE:
    python3 scripts/simulate_graduate_program.py
    python3 scripts/simulate_graduate_program.py --skip-screenshots
    python3 scripts/simulate_graduate_program.py --skip-simulation
"""

import os
import sys
import json
import time
import random
import string
import argparse
import urllib3
from datetime import datetime, timedelta
from typing import Optional

import requests

# Suppress InsecureRequestWarning for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://localhost:3000"
SCREENSHOT_DIR = "/home/bbrelin/course-creator/reports/simulation-screenshots"
EMAIL_DOMAIN = "apexgrad.training"
DEFAULT_PASSWORD = "ApexGrad2026!"

# Cities for multi-location training
CITIES = ["Toronto", "Vancouver", "Montreal", "Calgary"]

# Performance profile distribution
PERFORMANCE_PROFILES = {
    "star": {"weight": 0.20, "score_range": (88, 98), "progress_mult": 1.15},
    "solid": {"weight": 0.55, "score_range": (68, 87), "progress_mult": 1.00},
    "struggling": {"weight": 0.20, "score_range": (50, 67), "progress_mult": 0.85},
    "at_risk": {"weight": 0.05, "score_range": (35, 49), "progress_mult": 0.65},
}

# Week-by-week target progress ranges (base, before profile multiplier)
WEEKLY_PROGRESS = {
    1: (8, 18),
    2: (22, 38),
    3: (38, 58),
    4: (55, 72),
    5: (70, 88),
    6: (85, 100),
}

# ---------------------------------------------------------------------------
# Tracking / stats
# ---------------------------------------------------------------------------
stats = {
    "api_calls": 0,
    "api_successes": 0,
    "api_failures": 0,
    "entities": {
        "organizations": 0,
        "projects": 0,
        "tracks": 0,
        "courses": 0,
        "instructors": 0,
        "students": 0,
        "enrollments": 0,
    },
    "phase_results": {},
    "start_time": None,
}


# ---------------------------------------------------------------------------
# HTTP helper with retry
# ---------------------------------------------------------------------------
class APIClient:
    """Thin wrapper around requests with retry, token management, and stats."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = False

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def request(self, method: str, path: str, retries: int = 3, **kwargs) -> requests.Response:
        """Make an HTTP request with retry logic and 429 handling."""
        url = f"{self.base_url}{path}"
        # For file uploads, don't set Content-Type (let requests handle multipart boundary)
        if kwargs.pop("use_json_headers", True) and "files" not in kwargs:
            kwargs.setdefault("headers", self._headers())
        else:
            h = {"Accept": "application/json"}
            if self.token:
                h["Authorization"] = f"Bearer {self.token}"
            kwargs.setdefault("headers", h)
        kwargs.setdefault("timeout", 30)

        last_exc = None
        for attempt in range(retries):
            stats["api_calls"] += 1
            try:
                resp = self.session.request(method, url, **kwargs)

                # Handle rate limiting (429) — wait and retry
                if resp.status_code == 429:
                    retry_after = 60
                    try:
                        retry_after = int(resp.json().get("retry_after", 60))
                    except Exception:
                        pass
                    wait_time = min(retry_after + 2, 65)
                    print(f"    Rate limited (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                if resp.status_code < 500:
                    if resp.status_code < 400 or resp.status_code == 409:
                        stats["api_successes"] += 1
                    else:
                        stats["api_failures"] += 1
                    return resp
                # 5xx — retry with backoff
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
            except requests.exceptions.RequestException as e:
                last_exc = e
                stats["api_failures"] += 1
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)

        # All retries exhausted
        if last_exc:
            raise last_exc
        stats["api_failures"] += 1
        return resp  # type: ignore[possibly-undefined]

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def patch(self, path, **kw):
        return self.request("PATCH", path, **kw)

    def login(self, email: str, password: str) -> bool:
        """Login and store JWT token. Returns True on success.

        The login endpoint expects {"username": ..., "password": ...}
        where "username" can be either email or username.
        """
        resp = self.post("/api/v1/auth/login", json={"username": email, "password": password})
        if resp.status_code == 200:
            data = resp.json()
            self.token = data.get("access_token") or data.get("token")
            self.current_user = data.get("user", {})
            return bool(self.token)
        return False


api = APIClient(BASE_URL)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    return text.lower().replace(" ", "-").replace("&", "and").replace(",", "").replace(".", "")


def _clean_name_part(name: str) -> str:
    """Remove apostrophes and non-alphanumeric characters from a name part."""
    return "".join(c for c in name.lower() if c.isalnum())


def make_username(full_name: str) -> str:
    """Generate username from full name (alphanumeric + underscores only)."""
    parts = full_name.split()
    first = _clean_name_part(parts[0])
    last = _clean_name_part(parts[-1])
    return f"{first}_{last}"


def make_email(full_name: str, domain: str = EMAIL_DOMAIN) -> str:
    """Generate email from full name (using dots for readability)."""
    parts = full_name.split()
    first = _clean_name_part(parts[0])
    last = _clean_name_part(parts[-1])
    return f"{first}.{last}@{domain}"


def phase_header(name: str):
    """Print a phase header."""
    print(f"\n{'=' * 70}")
    print(f"  PHASE: {name}")
    print(f"{'=' * 70}")


def phase_result(name: str, success: bool, details: str = ""):
    """Record phase outcome."""
    status = "SUCCESS" if success else "FAILED"
    stats["phase_results"][name] = {"status": status, "details": details}
    icon = "OK" if success else "FAIL"
    print(f"  [{icon}] Phase result: {details or status}")


def assign_performance_profile() -> str:
    """Randomly assign a performance profile based on weights."""
    r = random.random()
    cumulative = 0.0
    for profile, cfg in PERFORMANCE_PROFILES.items():
        cumulative += cfg["weight"]
        if r <= cumulative:
            return profile
    return "solid"


# ---------------------------------------------------------------------------
# Phase 1: Organization Registration
# ---------------------------------------------------------------------------
def phase_1_create_organization() -> Optional[dict]:
    """Register Apex Graduate Academy with admin user Victoria Chen."""
    phase_header("1 — Organization Registration")

    org_data = {
        "name": "Apex Graduate Academy",
        "slug": "apex-graduate-academy",
        "description": "Multi-city graduate training program specializing in technology career development across Application Development, Data Analytics, and Systems Engineering tracks.",
        "address": "100 Innovation Drive, Toronto, ON M5V 3C6",
        "contact_phone": "14165551234",
        "contact_email": f"info@{EMAIL_DOMAIN}",
        "domain": EMAIL_DOMAIN,
        "admin_full_name": "Victoria Chen",
        "admin_email": f"victoria.chen@{EMAIL_DOMAIN}",
        "admin_password": DEFAULT_PASSWORD,
        "admin_role": "organization_admin",
    }

    print(f"  Creating organization: {org_data['name']}")
    print(f"  Admin: {org_data['admin_full_name']} ({org_data['admin_email']})")

    resp = api.post("/api/v1/organizations", json=org_data)

    if resp.status_code in (200, 201):
        result = resp.json()
        org_id = result.get("id") or result.get("organization_id") or result.get("organization", {}).get("id")
        print(f"  Organization created: ID={org_id}")
        stats["entities"]["organizations"] += 1

        # Login as org admin to get JWT token for subsequent requests
        if api.login(org_data["admin_email"], DEFAULT_PASSWORD):
            print(f"  Logged in as org admin: {org_data['admin_email']}")
        else:
            print(f"  Warning: Could not login as org admin")

        phase_result("Organization Registration", True, f"Org ID: {org_id}")
        return {
            "org_id": str(org_id),
            "admin_email": org_data["admin_email"],
            "admin_name": org_data["admin_full_name"],
        }

    elif resp.status_code in (409, 500, 422):
        # Org may already exist — try to login with admin credentials
        print(f"  Organization may already exist (HTTP {resp.status_code}), attempting login...")

        # Login via direct API to get org_id from user profile
        login_resp = api.post("/api/v1/auth/login",
                              json={"username": org_data["admin_email"],
                                    "password": DEFAULT_PASSWORD})
        if login_resp.status_code == 200:
            login_data = login_resp.json()
            api.token = login_data.get("access_token")
            user_info = login_data.get("user", {})
            org_id = user_info.get("organization_id")
            print(f"  Logged in as existing org admin. Org ID from profile: {org_id}")

            if not org_id:
                org_id = "existing"
            phase_result("Organization Registration", True, f"Already exists, ID: {org_id}")
            return {
                "org_id": str(org_id),
                "admin_email": org_data["admin_email"],
                "admin_name": org_data["admin_full_name"],
            }
        # Login failed
        print(f"  Login failed: HTTP {login_resp.status_code}")
        phase_result("Organization Registration", False,
                     f"HTTP {resp.status_code} and login failed")
        return None
    else:
        body = ""
        try:
            body = resp.text[:300]
        except Exception:
            pass
        print(f"  Failed: HTTP {resp.status_code} — {body}")
        phase_result("Organization Registration", False, f"HTTP {resp.status_code}")
        return None


# ---------------------------------------------------------------------------
# Phase 2: Program Setup (creates a "course" that serves as the training program container)
# ---------------------------------------------------------------------------
def phase_2_create_program(org_id: str) -> Optional[str]:
    """Create the Graduate Training Program 2026.

    In this platform, "projects" for track association are stored in the courses table.
    The track API's project_id references courses.id. So we create a course entry that
    acts as the training program container.
    """
    phase_header("2 — Program Setup")

    program_data = {
        "title": "Graduate Training Program 2026",
        "description": "6-week intensive graduate training program across 4 Canadian cities. Covers Application Development, Data Analytics, and Systems Engineering career tracks with 80 graduates.",
        "category": "Training Program",
        "difficulty_level": "intermediate",
        "estimated_duration": 6,
        "organization_id": org_id,
    }

    print(f"  Creating program: {program_data['title']}")
    resp = api.post("/api/v1/courses", json=program_data)

    if resp.status_code in (200, 201):
        result = resp.json()
        program_id = result.get("id") or result.get("course_id")
        print(f"  Program created: ID={program_id}")
        stats["entities"]["projects"] += 1
        phase_result("Program Setup", True, f"Program ID: {program_id}")
        return str(program_id)

    elif resp.status_code == 409:
        print(f"  Program already exists (409)")
        phase_result("Program Setup", True, "Already exists")
        return "existing"
    else:
        print(f"  Failed: HTTP {resp.status_code} — {resp.text[:200]}")
        # Try to find existing program
        print(f"  Looking for existing program...")
        courses_resp = api.get("/api/v1/courses")
        if courses_resp.status_code == 200:
            courses = courses_resp.json()
            if isinstance(courses, list):
                for c in courses:
                    if "Graduate Training" in c.get("title", ""):
                        pid = c.get("id")
                        print(f"  Found existing program: {pid}")
                        phase_result("Program Setup", True, f"Found existing: {pid}")
                        return str(pid)
            elif isinstance(courses, dict) and courses.get("courses"):
                for c in courses["courses"]:
                    if "Graduate Training" in c.get("title", ""):
                        pid = c.get("id")
                        print(f"  Found existing program: {pid}")
                        phase_result("Program Setup", True, f"Found existing: {pid}")
                        return str(pid)
        phase_result("Program Setup", False, f"HTTP {resp.status_code}")
        return None


# ---------------------------------------------------------------------------
# Phase 3: Track Creation
# ---------------------------------------------------------------------------
TRACKS = [
    {
        "name": "Application Developers",
        "description": "Full-stack application development covering React, Node.js, TypeScript, and modern web architecture. Graduates will be ready for junior developer roles.",
        "duration_weeks": 6,
        "difficulty_level": "intermediate",
    },
    {
        "name": "Data Analysts",
        "description": "Data analysis pipeline from SQL fundamentals through Python analytics to dashboard creation. Graduates will be equipped for data analyst positions.",
        "duration_weeks": 6,
        "difficulty_level": "intermediate",
    },
    {
        "name": "Systems Engineering",
        "description": "Infrastructure and operations covering Linux administration, AWS cloud services, and Kubernetes container orchestration for DevOps/SRE career paths.",
        "duration_weeks": 6,
        "difficulty_level": "intermediate",
    },
]


def phase_3_create_tracks(project_id: str) -> list[dict]:
    """Create 3 career tracks linked to the project."""
    phase_header("3 — Track Creation")

    created_tracks = []

    for track_def in TRACKS:
        track_data = {
            "name": track_def["name"],
            "description": track_def["description"],
            "project_id": project_id,
        }
        print(f"  Creating track: {track_def['name']}")
        resp = api.post("/api/v1/tracks/", json=track_data)

        if resp.status_code in (200, 201):
            result = resp.json()
            track_id = result.get("id") or result.get("track_id")
            print(f"    Track created: ID={track_id}")
            stats["entities"]["tracks"] += 1
            created_tracks.append({
                "id": str(track_id),
                "name": track_def["name"],
                "description": track_def["description"],
            })
        elif resp.status_code == 409:
            print(f"    Track already exists (409)")
            created_tracks.append({
                "id": "existing",
                "name": track_def["name"],
                "description": track_def["description"],
            })
        else:
            print(f"    Failed: HTTP {resp.status_code} — {resp.text[:200]}")
            created_tracks.append({
                "id": None,
                "name": track_def["name"],
                "description": track_def["description"],
            })

    success_count = sum(1 for t in created_tracks if t["id"])
    phase_result("Track Creation", success_count > 0, f"{success_count}/{len(TRACKS)} tracks created")
    return created_tracks


# ---------------------------------------------------------------------------
# Phase 4: User Registration
# ---------------------------------------------------------------------------
INSTRUCTOR_DEFS = [
    # App Dev track — one per city
    {"name": "David Park", "city": "Toronto", "track": "Application Developers", "bio": "Senior React developer, 8 years experience in full-stack web applications"},
    {"name": "Rachel Morrison", "city": "Vancouver", "track": "Application Developers", "bio": "Node.js architect, previously led engineering at a fintech startup"},
    {"name": "Antoine Dubois", "city": "Montreal", "track": "Application Developers", "bio": "TypeScript expert, open-source contributor and conference speaker"},
    {"name": "Priya Sharma", "city": "Calgary", "track": "Application Developers", "bio": "Full-stack lead specializing in modern JavaScript frameworks and API design"},
    # Data Analysts track
    {"name": "Maria Santos", "city": "Toronto", "track": "Data Analysts", "bio": "Data science manager with 10 years of analytics and visualization experience"},
    {"name": "James Liu", "city": "Vancouver", "track": "Data Analysts", "bio": "Senior data analyst, expert in Python pandas and SQL optimization"},
    {"name": "Sophie Tremblay", "city": "Montreal", "track": "Data Analysts", "bio": "Business intelligence specialist with expertise in dashboard design"},
    {"name": "Amir Hassan", "city": "Calgary", "track": "Data Analysts", "bio": "Statistician and Python instructor, PhD in Applied Mathematics"},
    # Systems Engineering track
    {"name": "Karen O'Brien", "city": "Toronto", "track": "Systems Engineering", "bio": "AWS Solutions Architect, 12 years in cloud infrastructure"},
    {"name": "Raj Patel", "city": "Vancouver", "track": "Systems Engineering", "bio": "Kubernetes specialist, SRE lead at a major cloud provider"},
    {"name": "Marc Gagnon", "city": "Montreal", "track": "Systems Engineering", "bio": "Linux systems administrator, RHCE certified with DevOps expertise"},
    {"name": "Yuki Tanaka", "city": "Calgary", "track": "Systems Engineering", "bio": "Infrastructure automation engineer, Terraform and Ansible expert"},
]

# Student names — 60 total, 20 per city (distributed across tracks)
STUDENT_NAMES_BY_CITY = {
    "Toronto": [
        "Aiden Mitchell", "Sophia Nguyen", "Marcus Johnson", "Emma Kowalski",
        "Liam Okafor", "Olivia Fitzgerald", "Noah Yamamoto", "Ava Petrova",
        "Ethan Rossi", "Isabella Chandra", "Lucas Hoffman", "Mia Johansson",
        "Benjamin Abubakar", "Charlotte Kim", "Alexander Reyes", "Amelia Zheng",
        "Daniel Moreau", "Harper Sullivan", "William Andersen", "Ella Mbeki",
    ],
    "Vancouver": [
        "Jackson Lee", "Scarlett Wong", "Sebastian Cruz", "Aria Nakamura",
        "Henry Gill", "Chloe Prasad", "Owen Robertson", "Layla Khoury",
        "Samuel Fraser", "Zoe Tremblay", "Caleb Singh", "Penelope Olsen",
        "Theodore Huang", "Riley Bergeron", "Nathan Osei", "Lily Dubois",
        "Ryan McAllister", "Aurora Joshi", "Dylan Fernandez", "Hannah Choi",
    ],
    "Montreal": [
        "Gabriel Lemieux", "Camille Bouchard", "Felix Lapointe", "Juliette Roy",
        "Mathis Gagnon", "Lea Belanger", "Raphael Cote", "Emilie Fortin",
        "Thomas Pelletier", "Clara Morin", "Louis Gauthier", "Maeve O'Sullivan",
        "Hugo Bergeron", "Nora Hassan", "Alexis Levesque", "Zara Rousseau",
        "Victor Tran", "Simone Perreault", "Maxime Dube", "Florence Diallo",
    ],
    "Calgary": [
        "Wyatt Makenzie", "Sadie Blackwood", "Hudson Rempel", "Nadia Fehr",
        "Chase Oliphant", "Piper Thiessen", "Colton Driedger", "Ivy Brandt",
        "Beckett Fonseca", "Stella Mukherjee", "Asher Parikh", "Ruby Takahashi",
        "Rowan Chicklis", "Violet Agarwal", "Miles Henriksen", "Hazel Ramirez",
        "Leo Gustafson", "Willow Siddiqui", "Ezra Mahmood", "Luna Svenson",
    ],
}


def _get_db_connection():
    """Get a psycopg2 database connection for direct inserts."""
    import psycopg2
    # Try common password locations
    passwords = ["bY9QwaxIoTFo705wxqT8jd0UnTsejDNW", "postgres_password", "postgres"]
    last_err = None
    for pw in passwords:
        try:
            return psycopg2.connect(
                host="localhost",
                port=5433,
                database="course_creator",
                user="postgres",
                password=pw,
            )
        except psycopg2.OperationalError as e:
            last_err = e
            continue
    raise last_err  # type: ignore


def _get_password_hash() -> str:
    """Get bcrypt hash of the default password."""
    import bcrypt
    return bcrypt.hashpw(DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _bulk_create_users_db(user_defs: list[dict], org_id: str) -> list[dict]:
    """Create users directly in the database (bypasses API rate limits).

    Each user_def should have: full_name, role, city, track, and optionally bio.
    Returns list of user dicts with id, email, username, full_name.
    """
    import psycopg2
    import psycopg2.extras
    import uuid

    conn = None
    created_users = []
    pw_hash = _get_password_hash()

    try:
        conn = _get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        for udef in user_defs:
            full_name = udef["full_name"]
            email = make_email(full_name)
            username = make_username(full_name)
            role = udef["role"]
            user_id = str(uuid.uuid4())

            try:
                cur.execute("""
                    INSERT INTO course_creator.users (
                        id, email, username, full_name, hashed_password,
                        is_active, role, bio, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        role = EXCLUDED.role,
                        updated_at = NOW()
                    RETURNING id
                """, (
                    user_id, email, username, full_name, pw_hash,
                    True, role, udef.get("bio", ""), "active",
                ))
                result = cur.fetchone()
                actual_id = str(result["id"])

                created_users.append({
                    "id": actual_id,
                    "email": email,
                    "username": username,
                    "full_name": full_name,
                    "city": udef.get("city"),
                    "track": udef.get("track"),
                    "track_id": udef.get("track_id"),
                    "bio": udef.get("bio"),
                    "profile": udef.get("profile"),
                })

            except psycopg2.Error as e:
                # If username conflict, try with a suffix
                try:
                    username2 = f"{username}_{random.randint(10, 99)}"
                    cur.execute("""
                        INSERT INTO course_creator.users (
                            id, email, username, full_name, hashed_password,
                            is_active, role, bio, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (email) DO UPDATE SET
                            full_name = EXCLUDED.full_name,
                            updated_at = NOW()
                        RETURNING id
                    """, (
                        user_id, email, username2, full_name, pw_hash,
                        True, role, udef.get("bio", ""), "active",
                    ))
                    result = cur.fetchone()
                    actual_id = str(result["id"])
                    created_users.append({
                        "id": actual_id,
                        "email": email,
                        "username": username2,
                        "full_name": full_name,
                        "city": udef.get("city"),
                        "track": udef.get("track"),
                        "track_id": udef.get("track_id"),
                        "bio": udef.get("bio"),
                        "profile": udef.get("profile"),
                    })
                except psycopg2.Error:
                    conn.rollback()
                    print(f"    Could not create user {full_name}: {e}")
                    continue

        conn.commit()

        # Create organization memberships
        for user in created_users:
            try:
                role_name = "instructor" if user.get("bio") else "student"
                cur.execute("""
                    INSERT INTO course_creator.organization_memberships (
                        user_id, organization_id, role, is_active, joined_at
                    ) VALUES (%s, %s, %s, true, NOW())
                    ON CONFLICT (user_id, organization_id) DO UPDATE SET
                        role = EXCLUDED.role, is_active = true
                """, (user["id"], org_id, role_name))
            except psycopg2.Error:
                conn.rollback()
                conn.commit()

        conn.commit()
        cur.close()

    except Exception as e:
        print(f"    Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    return created_users


def phase_4_register_users(org_id: str, tracks: list[dict]) -> dict:
    """Register 12 instructors and 80 students via direct DB inserts (fast)."""
    phase_header("4 — User Registration (Direct DB)")

    # Build track name→id map
    track_map = {t["name"]: t["id"] for t in tracks}
    track_names = [t["name"] for t in tracks]

    # --- Build instructor defs ---
    instructor_defs = []
    for idef in INSTRUCTOR_DEFS:
        instructor_defs.append({
            "full_name": idef["name"],
            "role": "instructor",
            "city": idef["city"],
            "track": idef["track"],
            "track_id": track_map.get(idef["track"]),
            "bio": idef["bio"],
        })

    # --- Build student defs ---
    student_defs = []
    for city, names in STUDENT_NAMES_BY_CITY.items():
        for idx, name in enumerate(names):
            if idx < 7:
                track_idx = 0
            elif idx < 14:
                track_idx = 1
            else:
                track_idx = 2
            assigned_track = track_names[track_idx] if track_idx < len(track_names) else track_names[0]

            student_defs.append({
                "full_name": name,
                "role": "student",
                "city": city,
                "track": assigned_track,
                "track_id": track_map.get(assigned_track),
                "profile": assign_performance_profile(),
            })

    # --- Bulk create via DB ---
    print(f"\n  Creating {len(instructor_defs)} instructors via DB...")
    instructors = _bulk_create_users_db(instructor_defs, org_id)
    stats["entities"]["instructors"] += len(instructors)
    print(f"  Instructors created: {len(instructors)}/{len(instructor_defs)}")

    print(f"\n  Creating {len(student_defs)} students via DB...")
    students = _bulk_create_users_db(student_defs, org_id)
    stats["entities"]["students"] += len(students)
    print(f"  Students created: {len(students)}/{len(student_defs)}")

    # Print city breakdown
    for city in CITIES:
        city_count = sum(1 for s in students if s.get("city") == city)
        print(f"    {city}: {city_count} students")

    # Profile distribution
    profile_counts = {}
    for s in students:
        p = s.get("profile", "unknown")
        profile_counts[p] = profile_counts.get(p, 0) + 1
    print(f"  Performance profiles: {profile_counts}")

    success = len(instructors) > 0 and len(students) > 0
    phase_result("User Registration", success,
                 f"{len(instructors)} instructors, {len(students)} students")

    return {"instructors": instructors, "students": students}


# ---------------------------------------------------------------------------
# Phase 5: Course Creation
# ---------------------------------------------------------------------------
COURSE_DEFS = [
    # App Dev Track (4 courses)
    {
        "title": "Modern JavaScript & TypeScript",
        "description": "Master ES2024+ features, TypeScript type system, async patterns, and module architecture. Covers variables, functions, closures, promises, generics, and decorators.",
        "track": "Application Developers",
        "category": "Programming",
        "difficulty_level": "beginner",
        "estimated_duration": 2,
        "weeks": "1-2",
    },
    {
        "title": "React Application Development",
        "description": "Build production-grade React applications with hooks, context, routing, state management (Redux Toolkit), and testing with React Testing Library.",
        "track": "Application Developers",
        "category": "Web Development",
        "difficulty_level": "intermediate",
        "estimated_duration": 3,
        "weeks": "2-4",
    },
    {
        "title": "Node.js Backend Services",
        "description": "Design and implement RESTful APIs with Express.js, authentication with JWT, database integration with PostgreSQL, and deployment with Docker.",
        "track": "Application Developers",
        "category": "Backend Development",
        "difficulty_level": "intermediate",
        "estimated_duration": 3,
        "weeks": "3-5",
    },
    {
        "title": "Full-Stack Capstone Project",
        "description": "Integrate frontend and backend skills in a team-based capstone project. Covers CI/CD, code review, agile ceremonies, and presentation skills.",
        "track": "Application Developers",
        "category": "Project",
        "difficulty_level": "advanced",
        "estimated_duration": 2,
        "weeks": "5-6",
    },
    # Data Analysts Track (3 courses)
    {
        "title": "SQL & Database Fundamentals",
        "description": "Master relational databases from schema design through complex queries, joins, window functions, CTEs, indexing strategies, and query optimization.",
        "track": "Data Analysts",
        "category": "Data & Databases",
        "difficulty_level": "beginner",
        "estimated_duration": 2,
        "weeks": "1-2",
    },
    {
        "title": "Python for Data Analysis",
        "description": "Data manipulation with pandas, numerical computing with NumPy, statistical analysis with SciPy, and exploratory data analysis workflows.",
        "track": "Data Analysts",
        "category": "Data Science",
        "difficulty_level": "intermediate",
        "estimated_duration": 3,
        "weeks": "2-4",
    },
    {
        "title": "Data Visualization & Dashboards",
        "description": "Create compelling visualizations with Matplotlib, Seaborn, and Plotly. Build interactive dashboards and learn data storytelling techniques.",
        "track": "Data Analysts",
        "category": "Data Science",
        "difficulty_level": "intermediate",
        "estimated_duration": 3,
        "weeks": "4-6",
    },
    # Systems Engineering Track (3 courses)
    {
        "title": "Linux Systems Administration",
        "description": "Linux fundamentals including file systems, user management, networking, shell scripting, systemd services, security hardening, and troubleshooting.",
        "track": "Systems Engineering",
        "category": "DevOps",
        "difficulty_level": "beginner",
        "estimated_duration": 2,
        "weeks": "1-2",
    },
    {
        "title": "Cloud Infrastructure with AWS",
        "description": "Core AWS services — EC2, S3, RDS, VPC, IAM, Lambda, CloudFormation. Infrastructure as Code with Terraform. Cost optimization and security best practices.",
        "track": "Systems Engineering",
        "category": "Cloud Computing",
        "difficulty_level": "intermediate",
        "estimated_duration": 3,
        "weeks": "2-4",
    },
    {
        "title": "Containerization & Kubernetes",
        "description": "Docker container lifecycle, multi-stage builds, Kubernetes architecture, deployments, services, ingress, Helm charts, monitoring with Prometheus/Grafana.",
        "track": "Systems Engineering",
        "category": "DevOps",
        "difficulty_level": "advanced",
        "estimated_duration": 3,
        "weeks": "4-6",
    },
]


def phase_5_create_courses(org_id: str, tracks: list[dict], instructors: list[dict]) -> list[dict]:
    """Create 10 courses, one per course definition, assigned to tracks and instructors."""
    phase_header("5 — Course Creation")

    track_map = {t["name"]: t["id"] for t in tracks}

    # Map track→instructor (pick the first instructor for each track as primary)
    track_instructors = {}
    for inst in instructors:
        track_name = inst.get("track")
        if track_name and track_name not in track_instructors:
            track_instructors[track_name] = inst

    created_courses = []

    for cdef in COURSE_DEFS:
        track_id = track_map.get(cdef["track"])
        instructor = track_instructors.get(cdef["track"], {})
        instructor_id = instructor.get("id")

        course_data = {
            "title": cdef["title"],
            "description": cdef["description"],
            "category": cdef.get("category", "General"),
            "difficulty_level": cdef.get("difficulty_level", "intermediate"),
            "estimated_duration": cdef.get("estimated_duration", 2),
            "organization_id": org_id,
        }

        # Only add track_id if it's a real UUID (not "existing" placeholder)
        if track_id and track_id != "existing" and track_id != "None":
            course_data["track_id"] = track_id

        print(f"  Creating course: {cdef['title']} ({cdef['track']}, Weeks {cdef['weeks']})")

        # We need to be logged in as an instructor or org admin to create courses
        resp = api.post("/api/v1/courses", json=course_data)

        if resp.status_code in (200, 201):
            result = resp.json()
            course_id = result.get("id") or result.get("course_id")
            print(f"    Created: ID={course_id}")
            stats["entities"]["courses"] += 1

            course_info = {
                "id": str(course_id),
                "title": cdef["title"],
                "track": cdef["track"],
                "track_id": track_id,
                "weeks": cdef["weeks"],
                "instructor_id": instructor_id,
                "difficulty": cdef.get("difficulty_level"),
            }

            # Try to publish the course
            publish_resp = api.post(f"/api/v1/courses/{course_id}/publish")
            if publish_resp.status_code in (200, 201):
                print(f"    Published successfully")
            else:
                # Try PATCH to set status
                patch_resp = api.patch(f"/api/v1/courses/{course_id}",
                                       json={"status": "published", "is_published": True})
                if patch_resp.status_code in (200, 201):
                    print(f"    Published via PATCH")
                else:
                    print(f"    Could not publish (non-critical): {publish_resp.status_code}")

            created_courses.append(course_info)
        elif resp.status_code == 409:
            print(f"    Already exists (409)")
            created_courses.append({
                "id": "existing",
                "title": cdef["title"],
                "track": cdef["track"],
                "track_id": track_id,
                "weeks": cdef["weeks"],
                "instructor_id": instructor_id,
                "difficulty": cdef.get("difficulty_level"),
            })
        else:
            print(f"    Failed: HTTP {resp.status_code} — {resp.text[:200]}")
            created_courses.append({
                "id": None,
                "title": cdef["title"],
                "track": cdef["track"],
                "track_id": track_id,
                "weeks": cdef["weeks"],
                "instructor_id": instructor_id,
                "difficulty": cdef.get("difficulty_level"),
            })

    success_count = sum(1 for c in created_courses if c.get("id"))
    phase_result("Course Creation", success_count > 0, f"{success_count}/{len(COURSE_DEFS)} courses created")
    return created_courses


# ---------------------------------------------------------------------------
# Phase 6: Content Generation (optional, non-critical)
# ---------------------------------------------------------------------------
def phase_6_content_generation(courses: list[dict]):
    """Attempt to generate quizzes for each course via AI service. Non-critical."""
    phase_header("6 — Content Generation (Optional)")

    generated = 0
    for course in courses:
        course_id = course.get("id")
        if not course_id or course_id in ("existing", "None"):
            continue

        try:
            print(f"  Generating quiz for: {course['title']}")
            resp = api.post("/api/v1/course-generator/quiz/generate", json={
                "course_id": course_id,
                "course_title": course["title"],
                "num_questions": 5,
                "difficulty": course.get("difficulty", "intermediate"),
            }, retries=1)

            if resp.status_code in (200, 201):
                print(f"    Quiz generated successfully")
                generated += 1
            else:
                print(f"    Quiz generation skipped (HTTP {resp.status_code}) — non-critical")
        except Exception as e:
            print(f"    Quiz generation failed ({e}) — non-critical, continuing")

    phase_result("Content Generation", True, f"{generated}/{len(courses)} quizzes generated (optional phase)")


# ---------------------------------------------------------------------------
# Phase 7: Student Enrollment (Direct DB)
# ---------------------------------------------------------------------------
def phase_7_enroll_students(courses: list[dict], students: list[dict],
                            tracks: list[dict], org_id: str) -> list[dict]:
    """Enroll students via direct DB inserts into track_enrollments and
    student_course_enrollments tables.

    DB schema requires:
    - track_enrollments: user_id (uuid FK users), track_id (uuid FK tracks)
    - student_course_enrollments: student_id (uuid FK users),
      course_instance_id (uuid FK course_instances)
    - course_instances: course_id (uuid FK course_outlines), organization_id, instructor_id
    - course_outlines: must exist first for FK from course_instances

    Strategy:
    1. Create course_outlines records (mirror of courses table)
    2. Create course_instances for each course
    3. Insert track_enrollments for each student
    4. Insert student_course_enrollments for each student × course in their track
    """
    import psycopg2
    import psycopg2.extras

    phase_header("7 — Student Enrollment (Direct DB)")

    enrollments = []
    track_enrollment_count = 0
    course_enrollment_count = 0

    # Group courses by track
    track_courses = {}
    for c in courses:
        track = c.get("track")
        if track:
            track_courses.setdefault(track, []).append(c)

    # Group students by track
    track_students = {}
    for s in students:
        track = s.get("track")
        if track:
            track_students.setdefault(track, []).append(s)

    # Build track_id lookup from track name
    track_id_map = {}
    for t in tracks:
        track_id_map[t["name"]] = t["id"]

    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Step 1: Create course_outlines for FK from course_instances
        print("\n  Creating course outlines and instances...")
        course_instance_map = {}  # course_id -> instance_id
        for course in courses:
            course_id = course.get("id")
            if not course_id or course_id in ("existing", "None"):
                continue

            outline_id = course_id  # Use same UUID for simplicity

            # Insert course_outline if not exists (required FK for course_instances)
            course_track_id = track_id_map.get(course.get("track"))
            try:
                cur.execute("""
                    INSERT INTO course_creator.course_outlines
                        (id, title, description, organization_id, track_id, created_at)
                    VALUES (%s, %s, %s, %s::uuid, %s::uuid, NOW())
                    ON CONFLICT (id) DO NOTHING
                """, (outline_id, course["title"], course.get("description", ""),
                      org_id, course_track_id))
            except psycopg2.Error:
                conn.rollback()
                # Outline might already exist
                pass

            # Create course_instance
            import uuid as _uuid
            instance_id = str(_uuid.uuid4())
            try:
                cur.execute("""
                    INSERT INTO course_creator.course_instances
                        (id, course_id, organization_id, instance_name, is_active, created_at)
                    VALUES (%s, %s, %s, %s, true, NOW())
                    ON CONFLICT DO NOTHING
                """, (instance_id, outline_id, org_id, f"{course['title']} - 2026 Cohort"))
                conn.commit()
                course_instance_map[course_id] = instance_id
            except psycopg2.Error as e:
                conn.rollback()
                print(f"    Warning: Could not create instance for {course['title']}: {str(e)[:80]}")

        print(f"    Course instances created: {len(course_instance_map)}/{len(courses)}")

        # Step 2: Insert track enrollments
        print("\n  Enrolling students in tracks...")
        for track_name, student_list in track_students.items():
            track_id = track_id_map.get(track_name)
            if not track_id:
                print(f"    Warning: No track ID for '{track_name}'")
                continue

            for s in student_list:
                try:
                    cur.execute("""
                        INSERT INTO course_creator.track_enrollments
                            (user_id, track_id, enrollment_date, is_active)
                        VALUES (%s::uuid, %s::uuid, NOW(), true)
                        ON CONFLICT (user_id, track_id) DO NOTHING
                    """, (s["id"], track_id))
                    track_enrollment_count += 1
                except psycopg2.Error:
                    conn.rollback()

            conn.commit()
            print(f"    Track '{track_name}': {len(student_list)} students enrolled")

        # Step 3: Insert course enrollments
        print("\n  Enrolling students in courses...")
        for track_name, track_course_list in track_courses.items():
            student_list = track_students.get(track_name, [])
            if not student_list:
                continue

            print(f"\n  Track: {track_name}")
            print(f"    Courses: {len(track_course_list)}, Students: {len(student_list)}")

            for course in track_course_list:
                course_id = course.get("id")
                instance_id = course_instance_map.get(course_id)
                if not instance_id:
                    print(f"    Skipping {course['title']} — no course instance")
                    continue

                enrolled_in_course = 0
                for s in student_list:
                    try:
                        cur.execute("""
                            INSERT INTO course_creator.student_course_enrollments
                                (student_id, course_instance_id, enrollment_date, status,
                                 progress_percentage)
                            VALUES (%s::uuid, %s::uuid, NOW(), 'enrolled', 0.00)
                            ON CONFLICT (student_id, course_instance_id) DO NOTHING
                        """, (s["id"], instance_id))
                        enrolled_in_course += 1
                        course_enrollment_count += 1
                    except psycopg2.Error:
                        conn.rollback()

                    # Build enrollment record for simulation phases
                    enrollments.append({
                        "student_id": s["id"],
                        "student_email": s["email"],
                        "student_name": s["full_name"],
                        "course_id": course_id,
                        "course_instance_id": instance_id,
                        "course_title": course["title"],
                        "track": track_name,
                        "city": s.get("city"),
                        "profile": s.get("profile"),
                    })
                    stats["entities"]["enrollments"] += 1

                conn.commit()
                print(f"    Enrolled {enrolled_in_course}/{len(student_list)} in: {course['title']}")

        conn.commit()

    except Exception as e:
        print(f"  DB enrollment error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

    print(f"\n  Summary: {track_enrollment_count} track enrollments, "
          f"{course_enrollment_count} course enrollments")

    phase_result("Student Enrollment", course_enrollment_count > 0,
                 f"{track_enrollment_count} track + {course_enrollment_count} course enrollments")
    return enrollments


# ---------------------------------------------------------------------------
# Phase 8: Week-by-Week Simulation
# ---------------------------------------------------------------------------
def phase_8_simulate_weeks(students: list[dict], courses: list[dict],
                           enrollments: list[dict]) -> dict:
    """Simulate 6 weeks of learning activity."""
    phase_header("8 — Week-by-Week Simulation (6 Weeks)")

    simulation_data = {
        "weekly_summaries": [],
        "student_records": {},
        "quiz_scores": [],
        "lab_sessions": [],
    }

    # Build per-student enrollment map
    student_enrollments = {}
    for enr in enrollments:
        sid = enr["student_email"]
        student_enrollments.setdefault(sid, []).append(enr)

    # Initialize student records
    for s in students:
        simulation_data["student_records"][s["email"]] = {
            "name": s["full_name"],
            "city": s.get("city"),
            "track": s.get("track"),
            "profile": s.get("profile", "solid"),
            "weekly_progress": [],
            "quiz_scores": [],
            "lab_hours": [],
            "final_progress": 0,
            "completed": False,
        }

    for week in range(1, 7):
        print(f"\n  --- Week {week} ---")
        week_stats = {
            "week": week,
            "activities": 0,
            "avg_progress": 0,
            "quiz_attempts": 0,
            "lab_sessions": 0,
        }

        progress_values = []

        for s in students:
            record = simulation_data["student_records"][s["email"]]
            profile = record["profile"]
            profile_cfg = PERFORMANCE_PROFILES.get(profile, PERFORMANCE_PROFILES["solid"])

            # Calculate progress for this week
            base_low, base_high = WEEKLY_PROGRESS[week]
            mult = profile_cfg["progress_mult"]
            progress = random.uniform(base_low * mult, min(base_high * mult, 100))
            progress = round(min(progress, 100), 1)
            record["weekly_progress"].append(progress)
            record["final_progress"] = progress
            progress_values.append(progress)

            # Quiz score for this week
            score_low, score_high = profile_cfg["score_range"]
            # Add some weekly variance
            week_variance = random.uniform(-5, 5)
            quiz_score = round(min(max(random.uniform(score_low, score_high) + week_variance, 0), 100), 1)
            record["quiz_scores"].append(quiz_score)

            simulation_data["quiz_scores"].append({
                "student": s["email"],
                "week": week,
                "score": quiz_score,
                "track": s.get("track"),
                "city": s.get("city"),
            })

            # Lab hours (more in later weeks)
            base_lab_hours = week * 1.5 + random.uniform(0, 3)
            lab_hours = round(base_lab_hours * mult, 1)
            record["lab_hours"].append(lab_hours)

            simulation_data["lab_sessions"].append({
                "student": s["email"],
                "week": week,
                "hours": lab_hours,
                "track": s.get("track"),
                "city": s.get("city"),
            })

            week_stats["activities"] += 1
            week_stats["quiz_attempts"] += 1
            week_stats["lab_sessions"] += 1

            # Try to record progress via API (non-critical)
            my_enrollments = student_enrollments.get(s["email"], [])
            for enr in my_enrollments:
                cid = enr.get("course_id")
                if cid and cid not in ("existing", "None"):
                    try:
                        api.put(f"/api/v1/courses/{cid}/progress", json={
                            "student_email": s["email"],
                            "progress_percentage": progress,
                            "week": week,
                        }, retries=1)
                    except Exception:
                        pass  # Non-critical

        avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
        week_stats["avg_progress"] = round(avg_progress, 1)

        avg_quiz = sum(q["score"] for q in simulation_data["quiz_scores"] if q["week"] == week) / max(
            sum(1 for q in simulation_data["quiz_scores"] if q["week"] == week), 1
        )

        print(f"    Students active: {len(students)}")
        print(f"    Avg progress: {week_stats['avg_progress']}%")
        print(f"    Avg quiz score: {round(avg_quiz, 1)}%")
        print(f"    Lab sessions: {week_stats['lab_sessions']}")

        simulation_data["weekly_summaries"].append(week_stats)

    # Mark completions (week 6 progress >= 85%)
    completed = 0
    for email, record in simulation_data["student_records"].items():
        if record["final_progress"] >= 85:
            record["completed"] = True
            completed += 1

    print(f"\n  --- Simulation Summary ---")
    print(f"  Students completing program: {completed}/{len(students)} ({round(100*completed/max(len(students),1), 1)}%)")

    phase_result("Weekly Simulation", True,
                 f"6 weeks simulated, {completed}/{len(students)} completions")

    return simulation_data


# ---------------------------------------------------------------------------
# Phase 9: Playwright Screenshot Milestones
# ---------------------------------------------------------------------------
def phase_9_screenshots(org_admin_email: str, instructors: list[dict],
                        students: list[dict]):
    """Take screenshots at milestone pages using Playwright."""
    phase_header("9 — Playwright Screenshot Milestones")

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError:
        print("  Playwright not installed. Skipping screenshots.")
        phase_result("Screenshots", False, "Playwright not available")
        return

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    def take_screenshot(page, filename):
        path = os.path.join(SCREENSHOT_DIR, filename)
        page.screenshot(path=path, full_page=False)
        print(f"    Screenshot saved: {filename}")
        return path

    def spa_navigate(page, url):
        """Use SPA navigation to preserve in-memory auth tokens."""
        page.evaluate("""(url) => {
            window.history.pushState({}, '', url);
            window.dispatchEvent(new PopStateEvent('popstate'));
        }""", url)
        time.sleep(3)  # Allow time for API calls and rendering

    def login_via_form(page, email, password):
        """Login using Playwright keyboard typing (properly triggers React controlled inputs).

        Uses keyboard.type() for character-by-character input which correctly updates
        React state. Checks login success via JavaScript window.location (page.url is
        stale after React Router navigation).
        """
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)

            # Wait for form inputs to render
            page.wait_for_selector('input[type="password"]', timeout=8000)

            # Click and type into identifier field (character by character for React)
            id_input = page.locator('input[autocomplete="username"]')
            id_input.click()
            time.sleep(0.1)
            id_input.press("Control+a")
            id_input.press("Delete")
            page.keyboard.type(email, delay=10)
            time.sleep(0.2)

            # Click and type into password field
            pw_input = page.locator('input[type="password"]')
            pw_input.click()
            time.sleep(0.1)
            page.keyboard.type(password, delay=10)
            time.sleep(0.2)

            # Click submit button
            page.locator('button[type="submit"]').first.click()

            # Wait for navigation (React Router uses pushState, so page.url may be stale)
            time.sleep(5)

            # Check actual URL via JavaScript (page.url can be stale after SPA navigation)
            current_path = page.evaluate("() => window.location.pathname")
            has_dashboard = page.evaluate(
                '() => document.body.innerText.includes("Dashboard") && '
                '!document.body.innerText.includes("Sign In")'
            )

            if "/login" not in current_path or has_dashboard:
                print(f"    Logged in as {email.split('@')[0]}. Path: {current_path}")
                return True

            # Check for error banner
            error_text = page.evaluate(
                '() => { const el = document.querySelector("[role=alert]"); '
                'return el ? el.textContent : null; }'
            )
            if error_text:
                print(f"    Login error: {error_text}")
            else:
                print(f"    Login failed: still on {current_path}")

        except Exception as e:
            print(f"    Login error: {str(e)[:200]}")

        return False

    def logout(page):
        """Logout and clear state."""
        try:
            page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=10000)
            page.evaluate("localStorage.clear(); sessionStorage.clear();")
            time.sleep(1)
        except Exception:
            pass

    # ---- Navbar link validation ----
    # Every navbar path for each role, mapped to the role that uses it.
    # These MUST match the paths in Navbar.tsx getNavLinks().
    NAVBAR_ROUTES = {
        "organization_admin": [
            "/dashboard",
            "/organization/members",
            "/organization/courses",
            "/organization/analytics",
        ],
        "instructor": [
            "/dashboard",
            "/instructor/programs",
            "/instructor/students",
            "/instructor/analytics",
        ],
        "student": [
            "/dashboard",
            "/courses/my-courses",
            "/labs",
            "/progress",
        ],
        "site_admin": [
            "/dashboard",
            "/admin/organizations",
            "/admin/users",
            "/admin/analytics",
        ],
    }

    screenshots_taken = 0
    nav_errors = []

    def validate_navbar_links(page, role, routes):
        """Navigate to every navbar link for a role and flag 404s / error pages."""
        errors = []
        for route in routes:
            spa_navigate(page, route)
            current_path = page.evaluate("() => window.location.pathname")
            body_text = page.evaluate("() => document.body.innerText.substring(0, 600)")
            is_404 = (
                "404" in body_text
                or "not found" in body_text.lower()
                or "page not found" in body_text.lower()
            )
            redirected_to_login = "/login" in current_path and "/login" not in route
            if is_404 or redirected_to_login:
                reason = "404 page" if is_404 else f"redirected to {current_path}"
                errors.append(f"{role} nav '{route}' → {reason}")
                print(f"    FAIL: {role} navbar link {route} → {reason}")
            else:
                print(f"    OK:   {role} navbar link {route} → {current_path}")
        return errors

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--ignore-certificate-errors", "--no-sandbox"]
            )
            context = browser.new_context(
                ignore_https_errors=True,
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            # ── Org Admin session ──────────────────────────────────
            print("\n  [1/10] Org Admin Dashboard")
            if login_via_form(page, org_admin_email, DEFAULT_PASSWORD):
                # Validate every org-admin navbar link
                print("  Validating org-admin navbar links …")
                nav_errors.extend(
                    validate_navbar_links(page, "organization_admin",
                                          NAVBAR_ROUTES["organization_admin"])
                )

                spa_navigate(page, "/dashboard/org-admin")
                take_screenshot(page, "01_org_dashboard.png")
                screenshots_taken += 1

                print("  [2/10] Tracks Page")
                spa_navigate(page, "/organization/tracks")
                take_screenshot(page, "02_tracks.png")
                screenshots_taken += 1

                print("  [3/10] Training Programs")
                spa_navigate(page, "/organization/courses")
                take_screenshot(page, "03_programs.png")
                screenshots_taken += 1

                print("  [4/10] Organization Members")
                spa_navigate(page, "/organization/members")
                take_screenshot(page, "04_members.png")
                screenshots_taken += 1

                print("  [5/10] Week 2 Analytics")
                spa_navigate(page, "/organization/analytics")
                take_screenshot(page, "05_week2_analytics.png")
                screenshots_taken += 1

                logout(page)
            else:
                print("    Failed to login as org admin")

            # ── Instructor session ─────────────────────────────────
            print("  [6/10] Instructor Insights")
            first_instructor = next((i for i in instructors if i.get("email")), None)
            if first_instructor and login_via_form(page, first_instructor["email"], DEFAULT_PASSWORD):
                # Validate every instructor navbar link
                print("  Validating instructor navbar links …")
                nav_errors.extend(
                    validate_navbar_links(page, "instructor",
                                          NAVBAR_ROUTES["instructor"])
                )

                spa_navigate(page, "/instructor/insights")
                take_screenshot(page, "06_instructor_insights.png")
                screenshots_taken += 1
                logout(page)
            else:
                print("    Failed to login as instructor")

            # ── Student session ────────────────────────────────────
            print("  [7/10] Student Analytics")
            first_student = next((s for s in students if s.get("email")), None)
            if first_student and login_via_form(page, first_student["email"], DEFAULT_PASSWORD):
                # Validate every student navbar link
                print("  Validating student navbar links …")
                nav_errors.extend(
                    validate_navbar_links(page, "student",
                                          NAVBAR_ROUTES["student"])
                )

                spa_navigate(page, "/learning-analytics")
                take_screenshot(page, "07_student_analytics.png")
                screenshots_taken += 1

                print("  [8/10] Student Certificates")
                spa_navigate(page, "/certificates")
                take_screenshot(page, "08_certificates.png")
                screenshots_taken += 1
                logout(page)
            else:
                print("    Failed to login as student")

            # ── Org Admin again for final analytics ────────────────
            print("  [9/10] Final Org Analytics")
            if login_via_form(page, org_admin_email, DEFAULT_PASSWORD):
                spa_navigate(page, "/organization/analytics")
                take_screenshot(page, "09_final_analytics.png")
                screenshots_taken += 1
                logout(page)

            # ── Site Admin session ─────────────────────────────────
            print("  [10/10] Platform Analytics (Site Admin)")
            if login_via_form(page, "admin@example.com", "password123"):
                # Validate every site-admin navbar link
                print("  Validating site-admin navbar links …")
                nav_errors.extend(
                    validate_navbar_links(page, "site_admin",
                                          NAVBAR_ROUTES["site_admin"])
                )

                spa_navigate(page, "/admin/analytics")
                take_screenshot(page, "10_platform_analytics.png")
                screenshots_taken += 1
                logout(page)
            else:
                print("    Failed to login as site admin")

            browser.close()

    except Exception as e:
        print(f"  Playwright error: {e}")

    # Report navbar validation results
    if nav_errors:
        print(f"\n  NAVBAR VALIDATION FAILURES ({len(nav_errors)}):")
        for err in nav_errors:
            print(f"    ✗ {err}")
    else:
        print(f"\n  Navbar validation: all links OK across all roles")

    phase_result("Screenshots", screenshots_taken > 0,
                 f"{screenshots_taken}/10 screenshots taken, "
                 f"{len(nav_errors)} navbar errors")


# ---------------------------------------------------------------------------
# Phase 10: Summary Report
# ---------------------------------------------------------------------------
def phase_10_summary(simulation_data: dict, students: list[dict],
                     courses: list[dict], tracks: list[dict]):
    """Print comprehensive statistics and save report."""
    phase_header("10 — Summary Report")

    elapsed = time.time() - stats["start_time"]

    print(f"\n  {'=' * 60}")
    print(f"  APEX GRADUATE ACADEMY — Simulation Report")
    print(f"  {'=' * 60}")

    # Entity counts
    print(f"\n  Entities Created:")
    for entity, count in stats["entities"].items():
        print(f"    {entity.capitalize():20} {count}")

    # API stats
    total_calls = stats["api_calls"]
    success_rate = (stats["api_successes"] / total_calls * 100) if total_calls > 0 else 0
    print(f"\n  API Statistics:")
    print(f"    Total calls:       {total_calls}")
    print(f"    Successes:         {stats['api_successes']}")
    print(f"    Failures:          {stats['api_failures']}")
    print(f"    Success rate:      {success_rate:.1f}%")

    # Quiz scores by track
    if simulation_data and simulation_data.get("quiz_scores"):
        print(f"\n  Average Quiz Scores by Track:")
        track_scores = {}
        for qs in simulation_data["quiz_scores"]:
            track = qs.get("track", "Unknown")
            track_scores.setdefault(track, []).append(qs["score"])
        for track, scores in sorted(track_scores.items()):
            avg = sum(scores) / len(scores) if scores else 0
            print(f"    {track:30} {avg:.1f}%")

    # Quiz scores by city
    if simulation_data and simulation_data.get("quiz_scores"):
        print(f"\n  Average Quiz Scores by City:")
        city_scores = {}
        for qs in simulation_data["quiz_scores"]:
            city = qs.get("city", "Unknown")
            city_scores.setdefault(city, []).append(qs["score"])
        for city, scores in sorted(city_scores.items()):
            avg = sum(scores) / len(scores) if scores else 0
            print(f"    {city:30} {avg:.1f}%")

    # Completion rates by track
    if simulation_data and simulation_data.get("student_records"):
        print(f"\n  Completion Rates by Track:")
        track_completion = {}
        for email, record in simulation_data["student_records"].items():
            track = record.get("track", "Unknown")
            track_completion.setdefault(track, {"total": 0, "completed": 0})
            track_completion[track]["total"] += 1
            if record.get("completed"):
                track_completion[track]["completed"] += 1
        for track, data in sorted(track_completion.items()):
            rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
            print(f"    {track:30} {data['completed']}/{data['total']} ({rate:.0f}%)")

    # Completion rates by city
    if simulation_data and simulation_data.get("student_records"):
        print(f"\n  Completion Rates by City:")
        city_completion = {}
        for email, record in simulation_data["student_records"].items():
            city = record.get("city", "Unknown")
            city_completion.setdefault(city, {"total": 0, "completed": 0})
            city_completion[city]["total"] += 1
            if record.get("completed"):
                city_completion[city]["completed"] += 1
        for city, data in sorted(city_completion.items()):
            rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
            print(f"    {city:30} {data['completed']}/{data['total']} ({rate:.0f}%)")

    # Performance profile outcomes
    if simulation_data and simulation_data.get("student_records"):
        print(f"\n  Outcomes by Performance Profile:")
        profile_outcomes = {}
        for email, record in simulation_data["student_records"].items():
            prof = record.get("profile", "unknown")
            profile_outcomes.setdefault(prof, {"total": 0, "completed": 0, "avg_score": []})
            profile_outcomes[prof]["total"] += 1
            if record.get("completed"):
                profile_outcomes[prof]["completed"] += 1
            if record.get("quiz_scores"):
                profile_outcomes[prof]["avg_score"].extend(record["quiz_scores"])
        for prof, data in sorted(profile_outcomes.items()):
            rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0
            avg_s = sum(data["avg_score"]) / len(data["avg_score"]) if data["avg_score"] else 0
            print(f"    {prof.capitalize():15} {data['completed']}/{data['total']} completed ({rate:.0f}%), avg score {avg_s:.1f}%")

    # Phase results
    print(f"\n  Phase Results:")
    for phase_name, result in stats["phase_results"].items():
        icon = "OK" if result["status"] == "SUCCESS" else "!!"
        print(f"    [{icon}] {phase_name:35} {result['details']}")

    # Timing
    print(f"\n  Total simulation time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")

    # Save report to file
    report_path = os.path.join(SCREENSHOT_DIR, "simulation_report.json")
    report = {
        "timestamp": datetime.now().isoformat(),
        "organization": "Apex Graduate Academy",
        "program": "Graduate Training Program 2026",
        "cities": CITIES,
        "stats": stats,
        "simulation_summary": {
            "weekly_summaries": simulation_data.get("weekly_summaries", []) if simulation_data else [],
        },
        "elapsed_seconds": elapsed,
    }

    # Add per-track quiz averages
    if simulation_data and simulation_data.get("quiz_scores"):
        track_avgs = {}
        for qs in simulation_data["quiz_scores"]:
            t = qs.get("track", "Unknown")
            track_avgs.setdefault(t, []).append(qs["score"])
        report["quiz_averages_by_track"] = {
            t: round(sum(s) / len(s), 1) for t, s in track_avgs.items()
        }

    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Report saved: {report_path}")
    except Exception as e:
        print(f"\n  Could not save report: {e}")

    # Save human-readable report
    txt_path = os.path.join(SCREENSHOT_DIR, "simulation_report.txt")
    try:
        with open(txt_path, "w") as f:
            f.write("Apex Graduate Academy — Simulation Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'=' * 60}\n\n")
            f.write("Entities Created:\n")
            for entity, count in stats["entities"].items():
                f.write(f"  {entity.capitalize():20} {count}\n")
            f.write(f"\nAPI Calls: {total_calls} (success rate: {success_rate:.1f}%)\n")
            f.write(f"Simulation Time: {elapsed:.1f}s\n\n")

            if simulation_data and simulation_data.get("student_records"):
                f.write("Student Records:\n")
                f.write(f"{'Name':30} {'City':12} {'Track':25} {'Profile':12} {'Progress':10} {'Completed':10}\n")
                f.write("-" * 100 + "\n")
                for email, record in sorted(simulation_data["student_records"].items(),
                                            key=lambda x: x[1].get("track", "")):
                    f.write(f"{record['name']:30} {record.get('city', ''):12} "
                            f"{record.get('track', ''):25} {record.get('profile', ''):12} "
                            f"{record['final_progress']:8.1f}% "
                            f"{'Yes' if record['completed'] else 'No':10}\n")
        print(f"  Text report saved: {txt_path}")
    except Exception as e:
        print(f"  Could not save text report: {e}")

    print(f"\n  {'=' * 60}")
    print(f"  Simulation complete.")
    print(f"  {'=' * 60}")


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Simulate graduate training program")
    parser.add_argument("--skip-screenshots", action="store_true",
                        help="Skip Playwright screenshot phase")
    parser.add_argument("--skip-simulation", action="store_true",
                        help="Skip week-by-week simulation (create entities only)")
    parser.add_argument("--skip-content", action="store_true",
                        help="Skip content generation phase")
    args = parser.parse_args()

    stats["start_time"] = time.time()
    random.seed(42)  # Reproducible results

    print("=" * 70)
    print("  APEX GRADUATE ACADEMY — Training Program Simulation")
    print("=" * 70)
    print(f"  Base URL:      {BASE_URL}")
    print(f"  Screenshots:   {SCREENSHOT_DIR}")
    print(f"  Cities:        {', '.join(CITIES)}")
    print(f"  Tracks:        3 career tracks")
    print(f"  Instructors:   12 (4 per track)")
    print(f"  Students:      80 (20 per city x 4 cities)")
    print(f"  Courses:       10")
    print(f"  Duration:      6 weeks simulated")
    print(f"  Started:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Pre-flight: check API health
    print(f"\n  Pre-flight health check...")
    try:
        health = api.get("/api/v1/auth/health", retries=1)
        print(f"    User Management: HTTP {health.status_code}")
    except Exception as e:
        print(f"    User Management: UNREACHABLE ({e})")

    try:
        health = api.get("/api/v1/organizations/health", retries=1)
        print(f"    Organization Mgmt: HTTP {health.status_code}")
    except Exception as e:
        print(f"    Organization Mgmt: UNREACHABLE ({e})")

    try:
        health = api.get("/health", retries=1)
        print(f"    Nginx Frontend: HTTP {health.status_code}")
    except Exception as e:
        print(f"    Nginx Frontend: UNREACHABLE ({e})")

    # Phase 1: Create Organization
    org_result = phase_1_create_organization()
    if not org_result:
        print("\n  FATAL: Could not create or access organization. Aborting.")
        sys.exit(1)

    org_id = org_result["org_id"]
    admin_email = org_result["admin_email"]

    # Phase 2: Create Program (course entry that acts as training program container)
    program_id = phase_2_create_program(org_id)
    if not program_id:
        print("\n  WARNING: Program creation failed, using placeholder.")
        program_id = "placeholder"

    # Phase 3: Create Tracks (linked to the program via project_id)
    tracks = phase_3_create_tracks(program_id)

    # Phase 4: Register Users
    users = phase_4_register_users(org_id, tracks)
    instructors = users["instructors"]
    students = users["students"]

    # Phase 5: Create Courses
    courses = phase_5_create_courses(org_id, tracks, instructors)

    # Phase 6: Content Generation (optional)
    if not args.skip_content:
        phase_6_content_generation(courses)
    else:
        print("\n  Skipping content generation (--skip-content)")
        stats["phase_results"]["Content Generation"] = {"status": "SKIPPED", "details": "User skipped"}

    # Phase 7: Student Enrollment
    enrollments = phase_7_enroll_students(courses, students, tracks, org_id)

    # Phase 8: Weekly Simulation
    simulation_data = None
    if not args.skip_simulation:
        simulation_data = phase_8_simulate_weeks(students, courses, enrollments)
    else:
        print("\n  Skipping weekly simulation (--skip-simulation)")
        stats["phase_results"]["Weekly Simulation"] = {"status": "SKIPPED", "details": "User skipped"}

    # Phase 9: Playwright Screenshots
    if not args.skip_screenshots:
        phase_9_screenshots(admin_email, instructors, students)
    else:
        print("\n  Skipping screenshots (--skip-screenshots)")
        stats["phase_results"]["Screenshots"] = {"status": "SKIPPED", "details": "User skipped"}

    # Phase 10: Summary
    phase_10_summary(simulation_data or {}, students, courses, tracks)


if __name__ == "__main__":
    main()
