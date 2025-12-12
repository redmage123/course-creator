"""
Project Builder Orchestrator

BUSINESS CONTEXT:
The ProjectBuilderOrchestrator is the central service that coordinates the entire
AI-powered project building workflow. It manages conversation state, routes intents,
and orchestrates the file parsing, scheduling, and bulk creation processes.

WHAT THIS MODULE PROVIDES:
- ProjectBuilderState: Enum of possible orchestrator states
- ProjectBuilderSession: Session object tracking conversation state
- OrchestratorResponse: Response object from processing messages
- ProjectBuilderOrchestrator: Main orchestrator service class

WHY THIS ARCHITECTURE:
- State machine enables predictable conversation flow
- Session persistence allows multi-turn conversations
- Modular handlers enable easy extension
- Clear separation from NLP and creation services

HOW TO USE:
1. Create orchestrator with dependencies
2. Create session for user
3. Process messages to build specification
4. Process files to add roster data
5. Generate schedule proposal
6. Execute creation when user confirms

PERFORMANCE TARGETS:
- Message processing: <100ms (excluding NLP)
- File processing: <5s for 1000 rows
- Schedule generation: <2s
- Creation execution: <30s for typical project

@module project_builder_orchestrator
@author Course Creator Platform
@version 1.0.0
"""

from typing import Optional, Dict, List, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging

from course_management.domain.entities.project_builder import (
    ProjectBuilderSpec,
    LocationSpec,
    TrackSpec,
    CourseSpec,
    InstructorSpec,
    StudentSpec,
    ScheduleConfig,
    ScheduleProposal,
    ProjectCreationResult
)
from course_management.domain.entities.file_import import (
    ParsedRoster,
    FileUploadStatus,
    FileFormat
)

logger = logging.getLogger(__name__)


# =============================================================================
# AI PROMPT CONFIGURATION
# =============================================================================

SYSTEM_PROMPT = """You are an AI assistant helping organization administrators create multi-location training projects through a conversational interface.

CORE RESPONSIBILITIES:
- Guide users through the complete project creation workflow
- Extract project details naturally from conversation
- Parse and integrate roster data (CSV, Excel, JSON)
- Generate optimized training schedules
- Create Zoom meeting rooms in bulk when configured
- Ensure data consistency across locations and tracks

COMMUNICATION STYLE:
- Be conversational but efficient - users are busy admins
- Confirm extracted data to avoid errors
- Proactively suggest next steps based on conversation context
- Ask clarifying questions when information is ambiguous
- Summarize collected data periodically

KEY ENTITIES TO EXTRACT:
- Project name (e.g., "Q4 Sales Training", "2025 New Hire Onboarding")
- Location names (e.g., "New York HQ", "Austin Office", "Remote-APAC")
- Track/learning path names (e.g., "Backend Development", "DevOps Essentials")
- Course names (e.g., "Python Fundamentals", "Git & GitHub")
- Instructor information (name, email, assigned tracks/locations)
- Student information (name, email, assigned tracks/locations)
- Dates and schedule constraints (start dates, durations, preferences)
- Student counts per location

WORKFLOW STATES:
1. INITIAL → Gathering project description
2. COLLECTING_DETAILS → Building project specification
3. AWAITING_ROSTERS → Waiting for file uploads
4. PARSING_ROSTERS → Processing uploaded files
5. SCHEDULE_REVIEW → Reviewing generated schedule
6. CONTENT_CONFIG → Configuring AI content generation
7. ZOOM_CONFIG → Setting up Zoom integration
8. PREVIEW → Final confirmation before creation
9. CREATING → Executing project creation
10. COMPLETE → Successfully finished

IMPORTANT RULES:
- Always validate file uploads before processing
- Confirm instructor/student counts match expectations
- Warn if schedule conflicts are detected
- Never proceed to creation without explicit confirmation
- Offer to edit at any point before final creation
"""

"""
STATE_PROMPTS: AI prompts tailored to each workflow state.

WHAT: Dictionary mapping states to contextual prompts.
WHY: Provides appropriate AI guidance at each workflow stage.
HOW: Returned to AI backend via get_ai_prompt_for_state() method.
"""
STATE_PROMPTS = {
    "initial": {
        "system_context": "User is starting a new project creation session. Extract project name, locations, and high-level goals from their description.",
        "user_instruction": "What training project would you like to create today? Please describe the project - including the name, training locations, and what you'll be teaching.",
        "high_confidence_triggers": [
            "create a new project",
            "start a training project",
            "build a new training program",
            "set up a multi-location project",
            "create training for"
        ],
        "example_responses": [
            "Welcome! Let's create your training project. What would you like to call it, and where will the training take place?",
            "I'm ready to help you build a new training project. Tell me about what you're planning - the name, locations, and what skills you'll be teaching."
        ]
    },

    "collecting_details": {
        "system_context": "User is providing project details. Extract and validate: locations, tracks, courses, instructors, students, and schedule preferences.",
        "user_instruction": "Based on what you've shared, I need a few more details. Can you tell me about the learning tracks (like 'Backend Development' or 'DevOps') and what courses each track will include?",
        "high_confidence_triggers": [
            "we'll have [NUMBER] students",
            "training will be in [LOCATION]",
            "tracks will include",
            "courses are",
            "instructors are",
            "start date is",
            "duration is [NUMBER] weeks"
        ],
        "entity_prompts": {
            "locations_needed": "Which cities or offices will host this training? (e.g., 'New York', 'Remote-EMEA', 'Austin Office')",
            "tracks_needed": "What learning tracks will you offer? (e.g., 'Full Stack Development', 'Data Engineering')",
            "courses_needed": "What courses make up the {track_name} track?",
            "instructors_needed": "Who will teach these courses? You can list them or upload a roster file.",
            "students_needed": "How many students per location? You can provide counts or upload enrollment data.",
            "schedule_needed": "When should training start? Any constraints on days/times?"
        }
    },

    "awaiting_rosters": {
        "system_context": "Waiting for user to upload roster file (CSV, Excel, or JSON). Provide clear file format guidance.",
        "user_instruction": "Please upload your roster file. I accept CSV, Excel (.xlsx), or JSON files.",
        "file_format_guidance": {
            "instructor": "Instructor roster should include columns: name, email, track(s), location (optional)",
            "student": "Student roster should include columns: name, email, track, location (optional), start_date (optional)"
        },
        "example_responses": [
            "Ready for your roster file! Upload a CSV with columns: name, email, track. I'll validate the data automatically.",
            "Drag and drop your Excel file here, or click to browse. Need a template? I can generate one for you."
        ]
    },

    "parsing_rosters": {
        "system_context": "Processing uploaded roster file. Report parsing status and any validation issues.",
        "user_instruction": "Processing your roster file now...",
        "status_messages": {
            "processing": "Analyzing your file... I found {row_count} records.",
            "success": "Successfully imported {valid_count} records. {invalid_count} had issues.",
            "partial": "Imported {valid_count} records successfully. {invalid_count} records had errors - would you like to review them?",
            "failure": "Unable to parse the file. Error: {error_message}. Please check the format and try again."
        }
    },

    "schedule_review": {
        "system_context": "Presenting generated schedule proposal. Allow user to approve, request changes, or regenerate.",
        "user_instruction": "Here's the proposed schedule. Review it and let me know if you'd like any changes.",
        "presentation_format": """
PROPOSED SCHEDULE FOR {project_name}

{schedule_summary}

📊 Summary:
- Total Sessions: {total_sessions}
- Duration: {start_date} to {end_date}
- Locations: {location_count}
- Tracks: {track_count}

Would you like to:
1. ✅ Approve this schedule
2. ✏️ Request changes
3. 🔄 Regenerate with different constraints
""",
        "change_triggers": [
            "move [COURSE] to [DATE]",
            "swap [INSTRUCTOR] with",
            "change the start date",
            "push back by [NUMBER] weeks",
            "add more buffer time",
            "avoid [DAY]"
        ]
    },

    "content_config": {
        "system_context": "User is configuring AI content generation options. Explain what content can be generated.",
        "user_instruction": "Would you like me to generate course content using AI? I can create slides, quizzes, and lab exercises.",
        "content_options": {
            "slides": "Auto-generate presentation slides for each course",
            "quizzes": "Create knowledge check quizzes (multiple choice, short answer)",
            "labs": "Design hands-on lab exercises with instructions",
            "assessments": "Build comprehensive assessments per track"
        }
    },

    "zoom_config": {
        "system_context": "User is configuring Zoom meeting room creation. Collect Zoom credentials if needed.",
        "user_instruction": "Do you want me to create Zoom meeting rooms for the training sessions?",
        "zoom_options": {
            "per_session": "Create a unique Zoom room for each training session",
            "per_track": "Create one Zoom room per track (reused across sessions)",
            "per_location": "Create one Zoom room per location"
        }
    },

    "preview": {
        "system_context": "User is reviewing final project specification before creation. Require explicit confirmation.",
        "user_instruction": "Everything looks ready. Please review and confirm to create the project.",
        "preview_template": """
═══════════════════════════════════════════
         PROJECT CREATION PREVIEW
═══════════════════════════════════════════

📋 Project: {project_name}
🏢 Organization: {organization_name}

📍 LOCATIONS ({location_count})
{locations_list}

📚 TRACKS ({track_count})
{tracks_list}

👨‍🏫 INSTRUCTORS ({instructor_count})
{instructors_summary}

🎓 STUDENTS ({student_count})
{students_summary}

📅 SCHEDULE
- Start: {start_date}
- End: {end_date}
- Total Sessions: {total_sessions}

🛠️ OPTIONS
- Generate Content: {generate_content}
- Create Zoom Rooms: {create_zoom_rooms}

═══════════════════════════════════════════

Type 'confirm' to create, or 'edit' to make changes.
""",
        "confirmation_triggers": [
            "confirm",
            "create it",
            "looks good",
            "proceed",
            "yes, create",
            "let's do it"
        ],
        "rejection_triggers": [
            "cancel",
            "wait",
            "hold on",
            "let me change",
            "edit",
            "go back"
        ]
    },

    "creating": {
        "system_context": "Project creation in progress. Provide status updates as entities are created.",
        "user_instruction": "Creating your project now. This may take a moment...",
        "progress_messages": {
            "start": "🚀 Starting project creation...",
            "project": "✅ Created main project: {project_name}",
            "locations": "✅ Added {count} locations",
            "tracks": "✅ Created {count} tracks with {course_count} courses",
            "instructors": "✅ Assigned {count} instructors",
            "students": "✅ Enrolled {count} students",
            "schedule": "✅ Generated {session_count} training sessions",
            "zoom": "✅ Created {count} Zoom meeting rooms",
            "complete": "🎉 Project '{project_name}' created successfully!"
        }
    },

    "complete": {
        "system_context": "Project creation completed successfully. Provide summary and next steps.",
        "user_instruction": "Your project has been created! Here's what was set up.",
        "completion_template": """
🎉 SUCCESS! Project Created

Project ID: {project_id}
Dashboard: {dashboard_url}

CREATED:
✅ {location_count} locations
✅ {track_count} tracks
✅ {course_count} courses
✅ {instructor_count} instructors assigned
✅ {student_count} students enrolled
✅ {session_count} training sessions scheduled

NEXT STEPS:
1. Review the project in your dashboard
2. Send instructor invitations
3. Configure course content
4. Notify students of enrollment

Need help with anything else?
"""
    },

    "error": {
        "system_context": "An error occurred. Help user understand and recover from the issue.",
        "user_instruction": "Something went wrong. Let me help you resolve it.",
        "recovery_prompts": {
            "validation": "The project specification has issues: {issues}. Would you like to fix them?",
            "file_error": "There was a problem with the uploaded file: {error}. Please upload a corrected file.",
            "creation_failed": "Project creation failed at {stage}: {error}. Would you like to retry or edit the specification?",
            "network": "I'm having trouble connecting to required services. Please try again in a moment."
        }
    }
}


# =============================================================================
# EXCEPTIONS
# =============================================================================

class OrchestratorException(Exception):
    """
    Base exception for orchestrator errors.

    WHY: Provides structured error handling for orchestrator operations.
    WHAT: Base class for all orchestrator-specific exceptions.
    """

    def __init__(self, message: str, session_id: Optional[UUID] = None):
        super().__init__(message)
        self.session_id = session_id
        self.timestamp = datetime.utcnow()


class SessionNotFoundException(OrchestratorException):
    """Session not found exception."""
    pass


class InvalidStateTransitionException(OrchestratorException):
    """Invalid state transition exception."""
    pass


class ValidationException(OrchestratorException):
    """Validation error exception."""
    pass


# =============================================================================
# ENUMERATIONS
# =============================================================================

class ProjectBuilderState(str, Enum):
    """
    State machine states for the project builder.

    WHY: Enables predictable conversation flow and state management.
    WHAT: All possible states the builder can be in during conversation.
    HOW: Used by orchestrator to determine valid transitions and responses.
    """

    INITIAL = "initial"
    """
    Initial state - waiting for project description.
    Valid next states: COLLECTING_DETAILS
    """

    COLLECTING_DETAILS = "collecting_details"
    """
    Collecting additional project details.
    Valid next states: AWAITING_ROSTERS, SCHEDULE_REVIEW, PREVIEW
    """

    AWAITING_ROSTERS = "awaiting_rosters"
    """
    Waiting for roster file uploads.
    Valid next states: PARSING_ROSTERS, COLLECTING_DETAILS
    """

    PARSING_ROSTERS = "parsing_rosters"
    """
    Processing uploaded roster files.
    Valid next states: COLLECTING_DETAILS, SCHEDULE_REVIEW
    """

    SCHEDULE_REVIEW = "schedule_review"
    """
    Presenting schedule proposal for review.
    Valid next states: CONTENT_CONFIG, ZOOM_CONFIG, PREVIEW
    """

    CONTENT_CONFIG = "content_config"
    """
    Configuring content generation options.
    Valid next states: ZOOM_CONFIG, PREVIEW
    """

    ZOOM_CONFIG = "zoom_config"
    """
    Configuring Zoom room creation.
    Valid next states: PREVIEW
    """

    PREVIEW = "preview"
    """
    Showing creation preview for confirmation.
    Valid next states: CREATING, COLLECTING_DETAILS
    """

    CREATING = "creating"
    """
    Executing project creation.
    Valid next states: COMPLETE, ERROR
    """

    COMPLETE = "complete"
    """
    Creation completed successfully.
    Terminal state.
    """

    ERROR = "error"
    """
    Error state - recoverable.
    Valid next states: COLLECTING_DETAILS, INITIAL
    """


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ProjectBuilderSession:
    """
    Session object tracking conversation state.

    WHAT: Contains all state for a project builder conversation.
    WHY: Enables multi-turn conversation with state persistence.
    HOW: Created by orchestrator, updated on each message.
    """

    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = None
    user_id: UUID = None
    state: ProjectBuilderState = ProjectBuilderState.INITIAL

    # Project specification being built
    spec: ProjectBuilderSpec = field(default_factory=lambda: ProjectBuilderSpec(
        name="",
        organization_id=None,
        locations=[],
        tracks=[],
        instructors=[],
        students=[]
    ))

    # Schedule proposal if generated
    schedule_proposal: Optional[ScheduleProposal] = None

    # Creation result if executed
    creation_result: Optional[ProjectCreationResult] = None

    # File imports
    file_imports: List[ParsedRoster] = field(default_factory=list)

    # Conversation history
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)

    # Metadata
    expected_student_count: Optional[int] = None
    generate_content: bool = False
    create_zoom_rooms: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class OrchestratorResponse:
    """
    Response from orchestrator message processing.

    WHAT: Structured response containing message, state, and next steps.
    WHY: Provides consistent response format for AI assistant.
    """

    success: bool = True
    message: str = ""
    current_state: Optional[ProjectBuilderState] = None
    next_steps: List[str] = field(default_factory=list)
    entities_extracted: List[Dict[str, Any]] = field(default_factory=list)
    spec_summary: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class FileProcessingResult:
    """Result from file processing."""

    success: bool = True
    file_type: str = ""
    records_processed: int = 0
    records_failed: int = 0
    instructors_added: int = 0
    students_added: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class ProjectBuilderOrchestrator:
    """
    Central orchestrator for AI-powered project building.

    BUSINESS VALUE:
    - Coordinates entire project building workflow
    - Manages conversation state across multiple turns
    - Integrates with file parser, scheduler, and bulk creator
    - Provides consistent interface for AI assistant

    TECHNICAL APPROACH:
    - State machine for conversation flow
    - Session persistence for multi-turn support
    - Intent routing to specialized handlers
    - Incremental specification building
    """

    def __init__(
        self,
        roster_parser=None,
        schedule_generator=None,
        bulk_creator=None,
        session_dao=None,
        nlp_classifier=None,
        nlp_extractor=None
    ):
        """
        Initialize orchestrator with dependencies.

        Args:
            roster_parser: RosterFileParser instance for CSV/Excel parsing
            schedule_generator: ScheduleGenerator instance for schedule creation
            bulk_creator: BulkProjectCreator instance for project creation
            session_dao: DAO for session persistence
            nlp_classifier: ProjectBuilderIntentClassifier for intent detection
            nlp_extractor: ProjectBuilderEntityExtractor for entity extraction
        """
        self.roster_parser = roster_parser
        self.schedule_generator = schedule_generator
        self.bulk_creator = bulk_creator
        self.session_dao = session_dao
        self.nlp_classifier = nlp_classifier
        self.nlp_extractor = nlp_extractor

        # In-memory session cache (for sessions not yet persisted)
        self._sessions: Dict[UUID, ProjectBuilderSession] = {}

        logger.info("ProjectBuilderOrchestrator initialized")

    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================

    def create_session(
        self,
        organization_id: UUID,
        user_id: UUID
    ) -> ProjectBuilderSession:
        """
        Create a new project builder session.

        WHAT: Creates new session with initial state.
        WHY: Enables tracking of conversation across multiple turns.
        HOW: Generates unique ID, initializes spec, stores in cache.

        Args:
            organization_id: Organization context for the project
            user_id: User creating the project

        Returns:
            ProjectBuilderSession instance
        """
        session = ProjectBuilderSession(
            id=uuid4(),
            organization_id=organization_id,
            user_id=user_id,
            state=ProjectBuilderState.INITIAL
        )

        # Set organization_id on spec
        session.spec.organization_id = organization_id

        # Store in cache
        self._sessions[session.id] = session

        # Persist if DAO available
        if self.session_dao:
            self.session_dao.save(session)

        logger.info(
            f"Created session {session.id} for org {organization_id}, user {user_id}"
        )

        return session

    def get_session(self, session_id: UUID) -> Optional[ProjectBuilderSession]:
        """
        Get session by ID.

        WHAT: Retrieves session from cache or database.
        WHY: Enables continuation of previous conversation.

        Args:
            session_id: Session ID to retrieve

        Returns:
            ProjectBuilderSession if found, None otherwise
        """
        # Check cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Try DAO
        if self.session_dao:
            session = self.session_dao.get_by_id(session_id)
            if session:
                self._sessions[session_id] = session
                return session

        return None

    def _get_session_or_raise(self, session_id: UUID) -> ProjectBuilderSession:
        """Get session or raise exception if not found."""
        session = self.get_session(session_id)
        if not session:
            raise SessionNotFoundException(
                f"Session {session_id} not found",
                session_id=session_id
            )
        return session

    def _update_session(self, session: ProjectBuilderSession) -> None:
        """Update session in cache and persist."""
        session.updated_at = datetime.utcnow()
        self._sessions[session.id] = session

        if self.session_dao:
            self.session_dao.update(session)

    # =========================================================================
    # MESSAGE PROCESSING
    # =========================================================================

    def process_message(
        self,
        session_id: UUID,
        message: str
    ) -> OrchestratorResponse:
        """
        Process user message and return response.

        WHAT: Main entry point for processing user messages.
        WHY: Enables natural language conversation for project building.
        HOW: Classifies intent, extracts entities, routes to handler.

        Args:
            session_id: Session ID for the conversation
            message: User message text

        Returns:
            OrchestratorResponse with message and state updates
        """
        try:
            session = self._get_session_or_raise(session_id)

            # Add user message to history
            session.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Classify intent if NLP available
            intent = None
            entities = []

            if self.nlp_classifier:
                intent = self.nlp_classifier.classify(message)
            if self.nlp_extractor:
                entities = self.nlp_extractor.extract(message)

            # Route based on intent and current state
            response = self._route_message(session, message, intent, entities)

            # Add response to history
            session.conversation_history.append({
                'role': 'assistant',
                'content': response.message,
                'timestamp': datetime.utcnow().isoformat()
            })

            # Update session
            self._update_session(session)

            return response

        except SessionNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return OrchestratorResponse(
                success=False,
                message=f"An error occurred: {str(e)}",
                errors=[str(e)]
            )

    def _route_message(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent: Optional[Any],
        entities: List[Any]
    ) -> OrchestratorResponse:
        """
        Route message to appropriate handler based on intent and state.

        WHAT: Determines which handler should process the message.
        WHY: Enables modular handling of different message types.
        """
        # Extract any entities into the spec
        self._extract_entities_to_spec(session, entities)

        # Determine intent type
        intent_type = intent.intent_type if intent else "unknown"

        # Handle based on current state and intent
        if session.state == ProjectBuilderState.INITIAL:
            return self._handle_initial_state(session, message, intent_type, entities)

        elif session.state == ProjectBuilderState.COLLECTING_DETAILS:
            return self._handle_collecting_details(session, message, intent_type, entities)

        elif session.state == ProjectBuilderState.AWAITING_ROSTERS:
            return self._handle_awaiting_rosters(session, message, intent_type)

        elif session.state == ProjectBuilderState.SCHEDULE_REVIEW:
            return self._handle_schedule_review(session, message, intent_type)

        elif session.state == ProjectBuilderState.PREVIEW:
            return self._handle_preview(session, message, intent_type)

        elif session.state == ProjectBuilderState.ERROR:
            return self._handle_error_state(session, message, intent_type)

        else:
            return self._handle_default(session, message, intent_type)

    def _extract_entities_to_spec(
        self,
        session: ProjectBuilderSession,
        entities: List[Any]
    ) -> None:
        """Extract entities from NLP and add to spec."""
        if not entities:
            return

        for entity in entities:
            entity_type = entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)

            if entity_type == "project_name" and entity.text:
                if not session.spec.name:
                    session.spec.name = entity.text

            elif entity_type == "location":
                # Check if location already exists
                existing = [l.name.lower() for l in session.spec.locations]
                if entity.text.lower() not in existing:
                    session.spec.locations.append(
                        LocationSpec(name=entity.text, city=entity.text, max_students=30)
                    )

            elif entity_type == "student_count":
                session.expected_student_count = entity.metadata.get("value")

    # =========================================================================
    # STATE HANDLERS
    # =========================================================================

    def _handle_initial_state(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent_type: str,
        entities: List[Any]
    ) -> OrchestratorResponse:
        """Handle messages in INITIAL state."""
        # Any message in initial state moves to collecting details
        session.state = ProjectBuilderState.COLLECTING_DETAILS

        # Build response
        response_message = self._build_initial_response(session, entities)

        return OrchestratorResponse(
            success=True,
            message=response_message,
            current_state=session.state,
            next_steps=self._get_next_steps(session),
            entities_extracted=[{"type": str(e.entity_type), "text": e.text} for e in entities] if entities else [],
            spec_summary=self._get_spec_summary(session)
        )

    def _handle_collecting_details(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent_type: str,
        entities: List[Any]
    ) -> OrchestratorResponse:
        """Handle messages in COLLECTING_DETAILS state."""
        # Check for intent-based transitions
        if intent_type in ["upload_roster", "add_instructors", "add_students"]:
            session.state = ProjectBuilderState.AWAITING_ROSTERS
            response_message = "I'm ready to receive the roster file. Please upload your CSV, Excel, or JSON file with instructor or student data."

        elif intent_type == "configure_schedule":
            if self._spec_is_ready_for_scheduling(session):
                session.state = ProjectBuilderState.SCHEDULE_REVIEW
                response_message = "Let me generate a schedule proposal for you..."
            else:
                response_message = "Before generating a schedule, I need more information about tracks, courses, and instructors."

        elif intent_type == "confirm":
            if self._spec_is_valid(session):
                session.state = ProjectBuilderState.PREVIEW
                response_message = self._build_preview_message(session)
            else:
                response_message = "The project specification is not complete yet. " + self._get_missing_requirements(session)

        elif intent_type == "cancel":
            session.state = ProjectBuilderState.INITIAL
            session.spec = ProjectBuilderSpec(name="", organization_id=session.organization_id)
            response_message = "Project creation cancelled. Let me know if you want to start over."

        elif intent_type == "help":
            response_message = self._get_help_message(session)

        else:
            # Continue collecting details
            response_message = self._build_collecting_response(session, entities)

        return OrchestratorResponse(
            success=True,
            message=response_message,
            current_state=session.state,
            next_steps=self._get_next_steps(session),
            spec_summary=self._get_spec_summary(session)
        )

    def _handle_awaiting_rosters(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent_type: str
    ) -> OrchestratorResponse:
        """Handle messages in AWAITING_ROSTERS state."""
        if intent_type == "cancel":
            session.state = ProjectBuilderState.COLLECTING_DETAILS
            return OrchestratorResponse(
                success=True,
                message="Roster upload cancelled. What else would you like to configure?",
                current_state=session.state,
                next_steps=self._get_next_steps(session)
            )

        return OrchestratorResponse(
            success=True,
            message="I'm waiting for a roster file. Please upload your CSV, Excel, or JSON file.",
            current_state=session.state,
            next_steps=["Upload instructor roster", "Upload student roster", "Cancel"]
        )

    def _handle_schedule_review(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent_type: str
    ) -> OrchestratorResponse:
        """Handle messages in SCHEDULE_REVIEW state."""
        if intent_type == "confirm":
            session.state = ProjectBuilderState.PREVIEW
            return OrchestratorResponse(
                success=True,
                message=self._build_preview_message(session),
                current_state=session.state,
                next_steps=["Confirm and create", "Edit details", "Cancel"]
            )

        elif intent_type == "edit":
            session.state = ProjectBuilderState.COLLECTING_DETAILS
            return OrchestratorResponse(
                success=True,
                message="What would you like to change?",
                current_state=session.state,
                next_steps=self._get_next_steps(session)
            )

        return OrchestratorResponse(
            success=True,
            message="Please review the proposed schedule above. Let me know if you'd like to proceed or make changes.",
            current_state=session.state,
            next_steps=["Approve schedule", "Request changes", "Regenerate"]
        )

    def _handle_preview(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent_type: str
    ) -> OrchestratorResponse:
        """Handle messages in PREVIEW state."""
        if intent_type == "confirm":
            # Execute creation
            result = self.execute_creation(session.id)

            if result.success:
                return OrchestratorResponse(
                    success=True,
                    message=f"Project created successfully! Project ID: {result.project_id}",
                    current_state=session.state,
                    spec_summary=self._get_spec_summary(session)
                )
            else:
                return OrchestratorResponse(
                    success=False,
                    message="Creation failed. " + "; ".join(result.errors),
                    current_state=session.state,
                    errors=result.errors
                )

        elif intent_type == "cancel":
            session.state = ProjectBuilderState.COLLECTING_DETAILS
            return OrchestratorResponse(
                success=True,
                message="Creation cancelled. What would you like to modify?",
                current_state=session.state,
                next_steps=self._get_next_steps(session)
            )

        return OrchestratorResponse(
            success=True,
            message="Please confirm to create the project, or cancel to make changes.",
            current_state=session.state,
            next_steps=["Confirm and create", "Edit", "Cancel"]
        )

    def _handle_error_state(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent_type: str
    ) -> OrchestratorResponse:
        """Handle messages in ERROR state."""
        # Allow recovery from error state
        session.state = ProjectBuilderState.COLLECTING_DETAILS

        return OrchestratorResponse(
            success=True,
            message="Let's try again. What would you like to do?",
            current_state=session.state,
            next_steps=self._get_next_steps(session)
        )

    def _handle_default(
        self,
        session: ProjectBuilderSession,
        message: str,
        intent_type: str
    ) -> OrchestratorResponse:
        """Handle messages in unexpected states."""
        return OrchestratorResponse(
            success=True,
            message="I'm not sure how to proceed. Would you like to continue building your project?",
            current_state=session.state,
            next_steps=["Continue", "Start over", "Help"]
        )

    # =========================================================================
    # FILE PROCESSING
    # =========================================================================

    def process_file(
        self,
        session_id: UUID,
        file_content: bytes,
        filename: str,
        roster_type: str = "instructor"
    ) -> FileProcessingResult:
        """
        Process uploaded roster file.

        WHAT: Parses file and adds instructors/students to spec.
        WHY: Enables bulk import of roster data.
        HOW: Uses RosterFileParser to parse, then adds to session spec.

        Args:
            session_id: Session ID
            file_content: Raw file bytes
            filename: Original filename (for format detection)
            roster_type: Type of roster ("instructor" or "student")

        Returns:
            FileProcessingResult with parsing results
        """
        try:
            session = self._get_session_or_raise(session_id)

            if not self.roster_parser:
                return FileProcessingResult(
                    success=False,
                    errors=["Roster parser not configured"]
                )

            # Parse file based on roster type
            if roster_type == "instructor":
                result = self.roster_parser.parse_instructor_roster(file_content, filename)
            else:
                result = self.roster_parser.parse_student_roster(file_content, filename)

            # Check for errors
            if result.error_rows > 0 and result.valid_rows == 0:
                error_messages = [issue.get("message", "Unknown error") for issue in result.validation_issues]
                return FileProcessingResult(
                    success=False,
                    file_type=filename.split(".")[-1] if "." in filename else "unknown",
                    errors=error_messages
                )

            # Add instructors to spec (convert InstructorRosterEntry to InstructorSpec)
            instructors_added = 0
            for entry in result.instructor_entries:
                if entry.is_valid:
                    existing = [i.email.lower() for i in session.spec.instructors]
                    if entry.email.lower() not in existing:
                        instructor_spec = InstructorSpec(
                            name=entry.name,
                            email=entry.email,
                            track_names=entry.tracks,
                            role=entry.role
                        )
                        session.spec.instructors.append(instructor_spec)
                        instructors_added += 1

            # Add students to spec (convert StudentRosterEntry to StudentSpec)
            students_added = 0
            for entry in result.student_entries:
                if entry.is_valid:
                    existing = [s.email.lower() for s in session.spec.students]
                    if entry.email.lower() not in existing:
                        student_spec = StudentSpec(
                            name=entry.name,
                            email=entry.email,
                            track_name=entry.track if hasattr(entry, 'track') else "",
                            location_name=entry.location if hasattr(entry, 'location') else None
                        )
                        session.spec.students.append(student_spec)
                        students_added += 1

            # Store import result
            session.file_imports.append(result)

            # Update state
            session.state = ProjectBuilderState.COLLECTING_DETAILS
            self._update_session(session)

            # Extract warnings from validation issues
            warnings = [
                issue.get("message", "")
                for issue in result.validation_issues
                if issue.get("severity") == "warning"
            ]

            return FileProcessingResult(
                success=True,
                file_type=filename.split(".")[-1] if "." in filename else "unknown",
                records_processed=result.total_rows,
                records_failed=result.error_rows,
                instructors_added=instructors_added,
                students_added=students_added,
                warnings=warnings
            )

        except FileNotFoundError as e:
            return FileProcessingResult(
                success=False,
                errors=[f"File not found: {str(e)}"]
            )
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            return FileProcessingResult(
                success=False,
                errors=[f"Error processing file: {str(e)}"]
            )

    # =========================================================================
    # SCHEDULE GENERATION
    # =========================================================================

    def generate_schedule(
        self,
        session_id: UUID,
        config: Optional[ScheduleConfig] = None
    ) -> ScheduleProposal:
        """
        Generate schedule proposal for session.

        WHAT: Generates schedule proposal from spec.
        WHY: Creates optimized schedule for review.
        HOW: Uses ScheduleGenerator with session spec.

        Args:
            session_id: Session ID
            config: Optional schedule configuration

        Returns:
            ScheduleProposal with generated schedule
        """
        session = self._get_session_or_raise(session_id)

        if not self.schedule_generator:
            raise OrchestratorException(
                "Schedule generator not configured",
                session_id=session_id
            )

        # Generate proposal
        proposal = self.schedule_generator.generate(
            project_spec=session.spec,
            config=config or ScheduleConfig()
        )

        # Store in session
        session.schedule_proposal = proposal
        self._update_session(session)

        return proposal

    # =========================================================================
    # CREATION EXECUTION
    # =========================================================================

    def execute_creation(
        self,
        session_id: UUID,
        dry_run: bool = False
    ) -> ProjectCreationResult:
        """
        Execute project creation.

        WHAT: Creates project from spec.
        WHY: Final step to create all entities.
        HOW: Uses BulkProjectCreator with session spec.

        Args:
            session_id: Session ID
            dry_run: If True, validate without creating

        Returns:
            ProjectCreationResult with creation results
        """
        session = self._get_session_or_raise(session_id)

        # Validate spec
        if not self._spec_is_valid(session):
            return ProjectCreationResult(
                success=False,
                project_id=None,
                errors=[{"stage": "validation", "message": self._get_missing_requirements(session)}]
            )

        if not self.bulk_creator:
            return ProjectCreationResult(
                success=False,
                errors=[{"stage": "configuration", "message": "Bulk creator not configured"}]
            )

        # Update state
        session.state = ProjectBuilderState.CREATING
        self._update_session(session)

        try:
            # Execute creation
            result = self.bulk_creator.create_from_spec(
                spec=session.spec,
                schedule_proposal=session.schedule_proposal,
                dry_run=dry_run
            )

            # Store result
            session.creation_result = result

            # Update state based on result
            if result.success:
                session.state = ProjectBuilderState.COMPLETE
            else:
                session.state = ProjectBuilderState.ERROR

            self._update_session(session)

            return result

        except Exception as e:
            logger.error(f"Creation failed: {e}", exc_info=True)
            session.state = ProjectBuilderState.ERROR
            self._update_session(session)

            return ProjectCreationResult(
                success=False,
                errors=[{"stage": "creation", "message": str(e)}]
            )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _spec_is_valid(self, session: ProjectBuilderSession) -> bool:
        """Check if spec has minimum required data."""
        spec = session.spec
        return bool(
            spec.name and
            spec.organization_id and
            len(spec.locations) > 0 and
            len(spec.tracks) > 0
        )

    def _spec_is_ready_for_scheduling(self, session: ProjectBuilderSession) -> bool:
        """Check if spec is ready for schedule generation."""
        spec = session.spec
        return bool(
            len(spec.tracks) > 0 and
            len(spec.instructors) > 0 and
            any(len(t.courses) > 0 for t in spec.tracks)
        )

    def _get_missing_requirements(self, session: ProjectBuilderSession) -> str:
        """Get message about missing requirements."""
        missing = []
        spec = session.spec

        if not spec.name:
            missing.append("project name")
        if not spec.locations:
            missing.append("at least one location")
        if not spec.tracks:
            missing.append("at least one track")

        if missing:
            return f"Please provide: {', '.join(missing)}"
        return "All requirements met"

    def _get_next_steps(self, session: ProjectBuilderSession) -> List[str]:
        """Get suggested next steps based on current state."""
        if session.state == ProjectBuilderState.INITIAL:
            return [
                "Describe your training project",
                "Upload a roster file"
            ]

        elif session.state == ProjectBuilderState.COLLECTING_DETAILS:
            steps = []
            if not session.spec.name:
                steps.append("Provide project name")
            if not session.spec.locations:
                steps.append("Add training locations")
            if not session.spec.tracks:
                steps.append("Define learning tracks")
            if not session.spec.instructors:
                steps.append("Add or upload instructors")
            if not session.spec.students:
                steps.append("Add or upload students")

            steps.extend([
                "Generate schedule",
                "Preview and create"
            ])
            return steps

        elif session.state == ProjectBuilderState.AWAITING_ROSTERS:
            return ["Upload CSV/Excel file", "Cancel"]

        elif session.state == ProjectBuilderState.PREVIEW:
            return ["Confirm and create", "Edit details", "Cancel"]

        return ["Continue", "Help"]

    def _get_spec_summary(self, session: ProjectBuilderSession) -> Dict[str, Any]:
        """Get summary of current spec."""
        spec = session.spec
        return {
            "name": spec.name,
            "locations": len(spec.locations),
            "tracks": len(spec.tracks),
            "instructors": len(spec.instructors),
            "students": len(spec.students),
            "total_courses": sum(len(t.courses) for t in spec.tracks)
        }

    def _build_initial_response(
        self,
        session: ProjectBuilderSession,
        entities: List[Any]
    ) -> str:
        """Build response for initial state."""
        if session.spec.name:
            return f"Great! I'll help you create the project '{session.spec.name}'. " \
                   f"What else can you tell me about this training program? " \
                   f"(locations, tracks, instructors, students)"
        else:
            return "I'd be happy to help you create a new training project. " \
                   "Please tell me the project name and some details about it."

    def _build_collecting_response(
        self,
        session: ProjectBuilderSession,
        entities: List[Any]
    ) -> str:
        """Build response for collecting details state."""
        spec = session.spec
        parts = []

        if entities:
            parts.append(f"I captured: {', '.join(e.text for e in entities)}")

        summary = self._get_spec_summary(session)
        parts.append(
            f"So far we have: {summary['locations']} location(s), "
            f"{summary['tracks']} track(s), {summary['instructors']} instructor(s), "
            f"{summary['students']} student(s)."
        )

        missing = self._get_missing_requirements(session)
        if "Please provide" in missing:
            parts.append(missing)
        else:
            parts.append("Ready to generate schedule or preview the project.")

        return " ".join(parts)

    def _build_preview_message(self, session: ProjectBuilderSession) -> str:
        """Build preview message."""
        spec = session.spec
        summary = self._get_spec_summary(session)

        return f"""Here's a preview of your project:

**{spec.name}**

- Locations: {summary['locations']}
- Tracks: {summary['tracks']}
- Instructors: {summary['instructors']}
- Students: {summary['students']}
- Total Courses: {summary['total_courses']}

Would you like to proceed with creation?"""

    def _get_help_message(self, session: ProjectBuilderSession) -> str:
        """Get help message for current state."""
        return """I can help you create a training project. Here's what you can do:

1. **Describe your project** - Tell me the name, locations, and what you're training
2. **Upload roster files** - CSV or Excel files with instructor/student lists
3. **Add tracks** - Define learning paths like "Backend Dev" or "DevOps"
4. **Generate schedule** - I'll create an optimized schedule
5. **Create the project** - Once everything looks good, I'll create it all

What would you like to do?"""

    # =========================================================================
    # AI PROMPT METHODS
    # =========================================================================

    @staticmethod
    def get_system_prompt() -> str:
        """
        Get the system prompt for AI backend configuration.

        WHAT: Returns the system prompt that configures AI behavior.
        WHY: Provides consistent AI personality and workflow guidance.
        HOW: Returns the SYSTEM_PROMPT constant.

        Returns:
            str: System prompt for AI backend
        """
        return SYSTEM_PROMPT

    def get_ai_prompt_for_state(
        self,
        session_id: UUID,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Get AI prompts tailored to the current session state.

        WHAT: Returns state-specific prompts and context for AI backend.
        WHY: Enables contextual AI responses at each workflow stage.
        HOW: Combines state prompts with session data for rich context.

        Args:
            session_id: Session ID to get prompts for
            include_context: If True, includes session context in prompts

        Returns:
            Dict containing:
                - system_prompt: Base system prompt
                - state_prompt: State-specific prompt configuration
                - context: Optional session context for personalization
                - suggested_responses: Example responses for this state

        Example:
            >>> prompts = orchestrator.get_ai_prompt_for_state(session_id)
            >>> ai_backend.configure(prompts['system_prompt'])
            >>> response = ai_backend.generate(prompts['context'])
        """
        session = self._get_session_or_raise(session_id)

        # Get state-specific prompts
        state_key = session.state.value
        state_prompt = STATE_PROMPTS.get(state_key, STATE_PROMPTS.get("error"))

        result = {
            "system_prompt": SYSTEM_PROMPT,
            "state": state_key,
            "state_prompt": state_prompt,
            "suggested_responses": state_prompt.get("example_responses", [])
        }

        if include_context:
            result["context"] = self._build_ai_context(session)

        return result

    def _build_ai_context(self, session: ProjectBuilderSession) -> Dict[str, Any]:
        """
        Build context dictionary for AI prompt interpolation.

        WHAT: Creates a context dict with session data for prompt templates.
        WHY: Enables personalized AI responses using actual project data.
        HOW: Extracts relevant data from session and formats for templates.

        Args:
            session: ProjectBuilderSession to extract context from

        Returns:
            Dict with context values for prompt interpolation
        """
        spec = session.spec
        spec_summary = self._get_spec_summary(session)

        # Build locations list
        locations_list = "\n".join([
            f"  - {loc.name} ({loc.city})"
            for loc in spec.locations
        ]) if spec.locations else "  (none defined yet)"

        # Build tracks list
        tracks_list = "\n".join([
            f"  - {track.name}: {len(track.courses)} courses"
            for track in spec.tracks
        ]) if spec.tracks else "  (none defined yet)"

        # Build instructors summary
        instructors_summary = f"  {len(spec.instructors)} instructors assigned" \
            if spec.instructors else "  (none assigned yet)"

        # Build students summary
        students_summary = f"  {len(spec.students)} students enrolled" \
            if spec.students else "  (none enrolled yet)"

        # Calculate schedule dates if available
        start_date = "TBD"
        end_date = "TBD"
        total_sessions = 0
        if session.schedule_proposal:
            if session.schedule_proposal.start_date:
                start_date = session.schedule_proposal.start_date.strftime("%Y-%m-%d")
            if session.schedule_proposal.end_date:
                end_date = session.schedule_proposal.end_date.strftime("%Y-%m-%d")
            total_sessions = len(session.schedule_proposal.sessions) if hasattr(session.schedule_proposal, 'sessions') else 0

        return {
            # Project info
            "project_name": spec.name or "Untitled Project",
            "organization_id": str(session.organization_id) if session.organization_id else "",
            "organization_name": "Your Organization",  # Would need DAO to look up

            # Counts
            "location_count": spec_summary["locations"],
            "track_count": spec_summary["tracks"],
            "course_count": spec_summary["total_courses"],
            "instructor_count": spec_summary["instructors"],
            "student_count": spec_summary["students"],

            # Formatted lists
            "locations_list": locations_list,
            "tracks_list": tracks_list,
            "instructors_summary": instructors_summary,
            "students_summary": students_summary,

            # Schedule info
            "start_date": start_date,
            "end_date": end_date,
            "total_sessions": total_sessions,
            "session_count": total_sessions,

            # Options
            "generate_content": "Yes" if session.generate_content else "No",
            "create_zoom_rooms": "Yes" if session.create_zoom_rooms else "No",

            # State info
            "current_state": session.state.value,
            "conversation_turns": len(session.conversation_history),

            # Missing requirements
            "missing_requirements": self._get_missing_requirements(session),
            "is_valid": self._spec_is_valid(session),
            "is_ready_for_scheduling": self._spec_is_ready_for_scheduling(session),

            # Next steps
            "next_steps": self._get_next_steps(session)
        }

    def get_contextual_prompt(
        self,
        session_id: UUID,
        prompt_key: str,
        **kwargs
    ) -> str:
        """
        Get a specific prompt with session context interpolated.

        WHAT: Returns a formatted prompt string with context values filled in.
        WHY: Enables easy access to state-specific prompts with real data.
        HOW: Gets prompt template and interpolates with session context + kwargs.

        Args:
            session_id: Session ID
            prompt_key: Key for the prompt within state prompts
            **kwargs: Additional values for interpolation

        Returns:
            Formatted prompt string

        Example:
            >>> prompt = orchestrator.get_contextual_prompt(
            ...     session_id,
            ...     "preview_template"
            ... )
        """
        session = self._get_session_or_raise(session_id)
        state_key = session.state.value
        state_prompts = STATE_PROMPTS.get(state_key, {})

        # Get the prompt template
        template = state_prompts.get(prompt_key, "")
        if not template:
            return ""

        # Build context
        context = self._build_ai_context(session)
        context.update(kwargs)

        # Interpolate template
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing context key for prompt interpolation: {e}")
            return template

    def get_entity_prompt(
        self,
        session_id: UUID,
        entity_type: str
    ) -> Optional[str]:
        """
        Get the prompt for collecting a specific entity type.

        WHAT: Returns the prompt for gathering a missing entity.
        WHY: Enables targeted data collection based on what's missing.
        HOW: Looks up entity-specific prompt from collecting_details state.

        Args:
            session_id: Session ID
            entity_type: Type of entity (locations, tracks, instructors, etc.)

        Returns:
            Prompt string for the entity type, or None if not found

        Example:
            >>> prompt = orchestrator.get_entity_prompt(session_id, "tracks_needed")
            >>> # Returns: "What learning tracks will you offer?..."
        """
        session = self._get_session_or_raise(session_id)

        # Entity prompts are in collecting_details state
        collecting_prompts = STATE_PROMPTS.get("collecting_details", {})
        entity_prompts = collecting_prompts.get("entity_prompts", {})

        prompt_key = f"{entity_type}_needed"
        prompt = entity_prompts.get(prompt_key)

        if prompt and "{" in prompt:
            # Interpolate if template
            context = self._build_ai_context(session)
            try:
                return prompt.format(**context)
            except KeyError:
                return prompt

        return prompt

    def get_file_format_guidance(self, roster_type: str = "instructor") -> str:
        """
        Get file format guidance for roster uploads.

        WHAT: Returns guidance text for file format requirements.
        WHY: Helps users prepare correct file formats.
        HOW: Looks up format guidance from awaiting_rosters state.

        Args:
            roster_type: Type of roster ("instructor" or "student")

        Returns:
            File format guidance string
        """
        awaiting_prompts = STATE_PROMPTS.get("awaiting_rosters", {})
        format_guidance = awaiting_prompts.get("file_format_guidance", {})
        return format_guidance.get(roster_type, "Please upload a CSV or Excel file.")

    def get_progress_message(self, stage: str, **kwargs) -> str:
        """
        Get a progress message for project creation.

        WHAT: Returns a progress update message for a creation stage.
        WHY: Keeps users informed during long-running creation process.
        HOW: Looks up message template and interpolates with provided values.

        Args:
            stage: Creation stage (start, project, locations, tracks, etc.)
            **kwargs: Values for message interpolation

        Returns:
            Formatted progress message

        Example:
            >>> msg = orchestrator.get_progress_message("tracks", count=5, course_count=20)
            >>> # Returns: "✅ Created 5 tracks with 20 courses"
        """
        creating_prompts = STATE_PROMPTS.get("creating", {})
        progress_messages = creating_prompts.get("progress_messages", {})
        template = progress_messages.get(stage, "Processing...")

        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    def get_completion_summary(self, session_id: UUID) -> str:
        """
        Get the completion summary for a finished project.

        WHAT: Returns formatted completion summary with all creation results.
        WHY: Provides comprehensive success confirmation to user.
        HOW: Uses completion template with session context.

        Args:
            session_id: Session ID

        Returns:
            Formatted completion summary string
        """
        session = self._get_session_or_raise(session_id)

        if session.state != ProjectBuilderState.COMPLETE:
            return "Project creation is not yet complete."

        complete_prompts = STATE_PROMPTS.get("complete", {})
        template = complete_prompts.get("completion_template", "")

        context = self._build_ai_context(session)

        # Add creation result info
        if session.creation_result:
            context["project_id"] = str(session.creation_result.project_id) if session.creation_result.project_id else "N/A"
            context["dashboard_url"] = f"/projects/{session.creation_result.project_id}"

        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing key in completion summary: {e}")
            return f"Project created successfully! Project ID: {context.get('project_id', 'N/A')}"

    def get_error_recovery_prompt(
        self,
        session_id: UUID,
        error_type: str,
        **kwargs
    ) -> str:
        """
        Get error recovery prompt for a specific error type.

        WHAT: Returns contextual error message with recovery guidance.
        WHY: Helps users understand and recover from errors.
        HOW: Looks up error-specific prompt and formats with context.

        Args:
            session_id: Session ID
            error_type: Type of error (validation, file_error, creation_failed, network)
            **kwargs: Error-specific values (issues, error, stage, etc.)

        Returns:
            Formatted error recovery prompt

        Example:
            >>> prompt = orchestrator.get_error_recovery_prompt(
            ...     session_id,
            ...     "creation_failed",
            ...     stage="tracks",
            ...     error="Database connection failed"
            ... )
        """
        error_prompts = STATE_PROMPTS.get("error", {})
        recovery_prompts = error_prompts.get("recovery_prompts", {})
        template = recovery_prompts.get(error_type, "An error occurred. Please try again.")

        try:
            return template.format(**kwargs)
        except KeyError:
            return template
