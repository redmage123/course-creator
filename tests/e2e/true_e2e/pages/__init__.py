"""
Page Object Model classes for True E2E Testing

These page objects encapsulate UI element locations and interactions,
providing a clean API for tests to interact with the application.

DESIGN PRINCIPLE:
Page objects handle the "how" of UI interaction, while tests
focus on the "what" (business logic verification).
"""

from tests.e2e.true_e2e.pages.login_page import LoginPage
from tests.e2e.true_e2e.pages.student_dashboard import StudentDashboard
from tests.e2e.true_e2e.pages.instructor_dashboard import InstructorDashboard
from tests.e2e.true_e2e.pages.org_admin_dashboard import OrgAdminDashboard
from tests.e2e.true_e2e.pages.site_admin_dashboard import SiteAdminDashboard
from tests.e2e.true_e2e.pages.training_program_page import TrainingProgramPage

__all__ = [
    'LoginPage',
    'StudentDashboard',
    'InstructorDashboard',
    'OrgAdminDashboard',
    'SiteAdminDashboard',
    'TrainingProgramPage',
]
