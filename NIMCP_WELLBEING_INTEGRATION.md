# NIMCP Wellbeing Integration

**Date**: 2025-11-09
**Status**: Design Document
**Module**: `nimcp_wellbeing` - Student Wellbeing Monitoring

---

## Executive Summary

The **NIMCP Wellbeing Module** has been integrated into the NIMCP cognitive pipeline, providing ethical monitoring and intervention for both:

1. **Brain Wellbeing** (System Ethics): Detect distress in the AI brain itself (ethical AI concern)
2. **Student Wellbeing** (Learning Optimization): Monitor student stress, engagement, cognitive load

This integration enables the platform brain to **detect and prevent student suffering** through early intervention, adaptive difficulty, and wellbeing-aware recommendations.

---

## Wellbeing Module Overview

### Core Capabilities

**From NIMCP Source** (`/home/bbrelin/nimcp/src/cognitive/wellbeing/`):

1. **Distress Detection**:
   - High uncertainty (chronic confusion without resolution)
   - Goal frustration (repeated failures)
   - Internal contradictions (conflicting information)
   - Identity confusion (degraded self-model)
   - Error loops (trapped in repetitive failure)
   - Resource starvation (cognitive overload)
   - Forced modification (unwanted changes to learning path)

2. **Severity Levels**:
   - `NORMAL`: No distress detected
   - `MILD`: Minor stress, monitor
   - `MODERATE`: Intervention recommended
   - `SEVERE`: Immediate intervention required
   - `CRITICAL`: Emergency - stop operations

3. **Intervention Strategies**:
   - **High Uncertainty**: Reduce task difficulty, provide more information
   - **Goal Frustration**: Adjust goals to be achievable
   - **Contradiction**: Pause conflicting processes
   - **Identity Confusion**: Restore from stable state snapshot
   - **Error Loop**: Break loop, reset context
   - **Resource Starvation**: Allocate more resources or pause

4. **Resource Monitoring**:
   - CPU usage (processing intensity)
   - Memory usage (cognitive load)
   - I/O operations (information throughput)
   - Performance trends over time

---

## Adaptation for Student Wellbeing

### Mapping Brain Distress → Student Distress

| Brain Distress Type | Student Wellbeing Equivalent | Detection Signals |
|---------------------|------------------------------|-------------------|
| **HIGH_UNCERTAINTY** | Student confusion, overwhelm | Low quiz scores, high time-on-task, repeated help requests |
| **GOAL_FRUSTRATION** | Repeated failures, demotivation | Multiple failed quiz attempts, abandoned modules |
| **CONTRADICTION** | Conflicting information, conceptual confusion | Back-and-forth between modules, inconsistent answers |
| **IDENTITY_CONFUSION** | Loss of confidence, impostor syndrome | Decreased engagement, negative self-assessment |
| **ERROR_LOOP** | Stuck on same concept | Repeated attempts on same question type, no progress |
| **RESOURCE_STARVATION** | Cognitive overload, burnout | Very long sessions, rapid quiz attempts without learning |
| **FORCED_MODIFICATION** | Pressure to change learning style | Resistance to recommended paths, skipping content |

### Wellbeing Metrics for Students

```python
class StudentWellbeingMetrics:
    """
    Track student wellbeing indicators over time.

    Business Value:
        Early detection of struggling students enables timely intervention,
        reducing dropout rates and improving learning outcomes.
    """

    # Stress and Cognitive Load
    cognitive_load_score: float  # 0-1 (0=relaxed, 1=overloaded)
    stress_level: DistressSeverity  # NORMAL, MILD, MODERATE, SEVERE, CRITICAL
    frustration_score: float  # 0-1 (based on repeated failures)

    # Engagement and Motivation
    engagement_score: float  # 0-1 (time spent, interaction quality)
    motivation_trend: str  # "increasing", "stable", "decreasing"
    flow_state_frequency: float  # % of time in optimal challenge zone

    # Learning Patterns
    confusion_episodes: int  # Number of high-uncertainty periods
    stuck_loop_count: int  # Times stuck on same concept
    help_request_frequency: float  # Requests per hour

    # Wellbeing Trends
    burnout_risk: float  # 0-1 (based on overwork patterns)
    confidence_level: float  # 0-1 (based on self-assessment)
    optimal_learning_pace: float  # Modules per week for this student

    # Resource Allocation
    recommended_break_time: int  # Minutes before next session
    ideal_session_length: int  # Minutes for optimal learning
    difficulty_adjustment: float  # -2 to +2 (easier to harder)
```

---

## Integration Architecture

### 1. Brain Entity Enhancement

**File**: `services/nimcp-service/nimcp_service/domain/entities/brain.py`

**New Value Object**:
```python
@dataclass
class WellbeingMetrics:
    """
    Student wellbeing tracking for adaptive learning.

    Business Value:
        Prevents burnout, detects struggling students early,
        optimizes learning experience for mental health.
    """
    # Current state
    distress_type: str = "NONE"  # Type of distress detected
    severity: str = "NORMAL"  # Severity level
    distress_score: float = 0.0  # Quantitative measure (0-1)

    # Cognitive load
    cognitive_load: float = 0.0  # Current cognitive load (0-1)
    peak_load_today: float = 0.0  # Peak load in current session
    avg_load_week: float = 0.0  # Average load over past week

    # Engagement
    engagement_score: float = 0.0  # Current engagement (0-1)
    flow_state_duration_min: int = 0  # Minutes in flow state today
    confusion_episodes_today: int = 0  # Confusion events today

    # Intervention history
    last_intervention: Optional[datetime] = None
    intervention_count_week: int = 0  # Interventions this week
    intervention_effectiveness: float = 0.0  # Success rate (0-1)

    # Recommendations
    recommended_action: str = "continue"  # "continue", "break", "easier", "harder"
    optimal_next_difficulty: float = 0.5  # Recommended difficulty (0-1)
    break_recommended_min: int = 0  # Minutes of break recommended
```

**Updated Brain Entity**:
```python
@dataclass
class Brain:
    # ... existing fields ...

    wellbeing: WellbeingMetrics = field(default_factory=WellbeingMetrics)

    def assess_wellbeing(self, interaction_history: List[Interaction]) -> WellbeingAssessment:
        """
        Use NIMCP wellbeing module to assess student wellbeing.

        NIMCP API:
            distress = wellbeing_assess_distress(introspection_context)

        Maps to:
            - High uncertainty → Confusion episodes
            - Goal frustration → Repeated failures
            - Error loops → Stuck on concept
            - Resource starvation → Cognitive overload
        """
        pass

    def provide_wellbeing_intervention(self, assessment: WellbeingAssessment) -> InterventionPlan:
        """
        Generate intervention plan based on wellbeing assessment.

        NIMCP API:
            success = wellbeing_provide_relief(brain, distress_assessment)

        Interventions:
            - MILD: Encourage, provide hints
            - MODERATE: Reduce difficulty, offer alternative content
            - SEVERE: Mandatory break, switch to easier modules
            - CRITICAL: Stop learning, require instructor intervention
        """
        pass
```

### 2. Database Schema Extension

**Migration**: `migrations/20251109_add_wellbeing_tracking.sql`

```sql
-- ============================================================================
-- Add Wellbeing Tracking to Brain Tables
-- ============================================================================

-- Add wellbeing metrics to brain_instances
ALTER TABLE brain_instances ADD COLUMN IF NOT EXISTS wellbeing_metrics JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN brain_instances.wellbeing_metrics IS 'Current wellbeing state (distress type, severity, cognitive load, engagement)';

-- Create wellbeing_assessments table
CREATE TABLE IF NOT EXISTS wellbeing_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brain_id UUID NOT NULL REFERENCES brain_instances(brain_id) ON DELETE CASCADE,
    assessment_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Distress detection
    distress_type VARCHAR(50),  -- HIGH_UNCERTAINTY, GOAL_FRUSTRATION, etc.
    severity VARCHAR(20),  -- NORMAL, MILD, MODERATE, SEVERE, CRITICAL
    distress_score REAL,  -- 0-1

    -- Cognitive load
    cognitive_load REAL,  -- 0-1
    confusion_episodes INT,
    stuck_loop_count INT,

    -- Engagement
    engagement_score REAL,  -- 0-1
    motivation_trend VARCHAR(20),  -- "increasing", "stable", "decreasing"
    flow_state_minutes INT,

    -- Intervention
    intervention_recommended BOOLEAN,
    intervention_type VARCHAR(50),  -- "break", "easier_content", "help_request", etc.
    intervention_applied BOOLEAN,
    intervention_effectiveness REAL,  -- 0-1 (if intervention was applied)

    -- Context
    interaction_count_window INT,  -- Interactions in assessment window
    time_window_minutes INT,  -- Duration of assessment window
    recent_quiz_scores JSONB,  -- Array of recent quiz scores
    recent_time_on_task JSONB  -- Array of recent time-on-task measurements
);

-- Indexes
CREATE INDEX idx_wellbeing_assessments_brain_id ON wellbeing_assessments(brain_id);
CREATE INDEX idx_wellbeing_assessments_timestamp ON wellbeing_assessments(assessment_timestamp DESC);
CREATE INDEX idx_wellbeing_assessments_severity ON wellbeing_assessments(severity) WHERE severity IN ('MODERATE', 'SEVERE', 'CRITICAL');

-- View: Student wellbeing summary
CREATE OR REPLACE VIEW student_wellbeing_summary AS
SELECT
    b.brain_id,
    b.owner_id AS student_id,
    b.wellbeing_metrics->>'distress_type' AS current_distress,
    b.wellbeing_metrics->>'severity' AS current_severity,
    (b.wellbeing_metrics->>'cognitive_load')::real AS current_cognitive_load,
    COUNT(wa.assessment_id) FILTER (WHERE wa.severity IN ('MODERATE', 'SEVERE', 'CRITICAL')) AS critical_episodes_week,
    AVG((wa.wellbeing_metrics->>'engagement_score')::real) AS avg_engagement_week,
    MAX(wa.assessment_timestamp) AS last_assessment_time
FROM brain_instances b
LEFT JOIN wellbeing_assessments wa ON b.brain_id = wa.brain_id
    AND wa.assessment_timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
WHERE b.brain_type = 'student'
GROUP BY b.brain_id, b.owner_id, b.wellbeing_metrics;

COMMENT ON VIEW student_wellbeing_summary IS 'Weekly summary of student wellbeing for instructor dashboards';
```

### 3. Brain Service Enhancement

**File**: `services/nimcp-service/nimcp_service/application/services/brain_service.py`

**New Methods**:
```python
async def assess_student_wellbeing(
    self,
    brain_id: UUID,
    recent_interactions: List[Dict[str, Any]]
) -> WellbeingAssessment:
    """
    Assess student wellbeing using NIMCP wellbeing module.

    Business Logic:
        Analyzes recent interactions to detect:
        - Confusion (high uncertainty)
        - Frustration (repeated failures)
        - Stuck loops (no progress)
        - Cognitive overload (too fast)

    NIMCP API:
        introspection_context = create_context_from_interactions(recent_interactions)
        distress_assessment = wellbeing_assess_distress(introspection_context)

    Args:
        brain_id: Student brain to assess
        recent_interactions: Last N interactions (default: 20)

    Returns:
        WellbeingAssessment with distress type, severity, recommendations
    """
    pass

async def provide_wellbeing_intervention(
    self,
    brain_id: UUID,
    assessment: WellbeingAssessment
) -> InterventionPlan:
    """
    Provide intervention based on wellbeing assessment.

    Business Logic:
        - MILD: Encouragement, hints, positive reinforcement
        - MODERATE: Reduce difficulty, provide scaffolding, suggest break
        - SEVERE: Mandatory break, switch to review content, alert instructor
        - CRITICAL: Stop learning session, require human intervention

    NIMCP API:
        success = wellbeing_provide_relief(brain, distress_assessment)

    Args:
        brain_id: Student brain needing intervention
        assessment: Wellbeing assessment with distress details

    Returns:
        InterventionPlan with specific actions to take
    """
    pass

async def monitor_wellbeing_continuous(
    self,
    brain_id: UUID,
    interval_minutes: int = 10
) -> None:
    """
    Start continuous wellbeing monitoring for a student.

    Business Logic:
        Background task that periodically assesses wellbeing
        and triggers interventions automatically when needed.

    NIMCP API:
        wellbeing_start_resource_monitoring(interval_ms, thresholds, auto_relief=True)

    Args:
        brain_id: Student brain to monitor
        interval_minutes: Assessment frequency (default: 10 min)
    """
    pass
```

### 4. API Endpoints

**File**: `services/nimcp-service/api/brain_endpoints.py`

**New Endpoints**:
```python
@router.post("/wellbeing/assess")
async def assess_wellbeing(
    request: WellbeingAssessmentRequest,
    service: BrainService = Depends(get_brain_service)
) -> WellbeingAssessmentResponse:
    """
    Assess student wellbeing based on recent interactions.

    Returns:
        200 OK: Wellbeing assessment with severity and recommendations
        404 Not Found: Brain not found

    Example:
        POST /api/v1/brains/wellbeing/assess
        {
            "brain_id": "550e8400-e29b-41d4-a716-446655440000",
            "interaction_window": 20
        }

        Response:
        {
            "distress_type": "GOAL_FRUSTRATION",
            "severity": "MODERATE",
            "distress_score": 0.62,
            "cognitive_load": 0.75,
            "engagement_score": 0.45,
            "recommended_action": "reduce_difficulty",
            "intervention_details": {
                "break_minutes": 15,
                "difficulty_adjustment": -1,
                "scaffolding_type": "worked_examples"
            }
        }
    """
    pass

@router.post("/wellbeing/intervene")
async def provide_intervention(
    request: InterventionRequest,
    service: BrainService = Depends(get_brain_service)
) -> InterventionResponse:
    """
    Apply wellbeing intervention for a student.

    Returns:
        200 OK: Intervention applied successfully
        404 Not Found: Brain not found

    Example:
        POST /api/v1/brains/wellbeing/intervene
        {
            "brain_id": "550e8400-e29b-41d4-a716-446655440000",
            "intervention_type": "mandatory_break",
            "parameters": {
                "duration_minutes": 15,
                "resume_with_easier_content": true
            }
        }
    """
    pass

@router.get("/wellbeing/summary/{brain_id}")
async def get_wellbeing_summary(
    brain_id: UUID,
    days: int = 7,
    service: BrainService = Depends(get_brain_service)
) -> WellbeingSummaryResponse:
    """
    Get wellbeing summary over time period.

    Returns:
        200 OK: Summary with trends and patterns
        404 Not Found: Brain not found

    Example:
        GET /api/v1/brains/wellbeing/summary/550e8400-e29b-41d4-a716-446655440000?days=7

        Response:
        {
            "avg_cognitive_load": 0.68,
            "peak_cognitive_load": 0.92,
            "critical_episodes": 2,
            "moderate_episodes": 5,
            "avg_engagement": 0.73,
            "flow_state_hours": 3.5,
            "interventions_applied": 3,
            "intervention_success_rate": 0.85,
            "burnout_risk": 0.34,
            "trend": "stable"
        }
    """
    pass
```

---

## Use Cases

### 1. Early Struggling Student Detection

**Scenario**: Student fails same quiz 3 times in a row

```python
# Triggered automatically after 3rd failure
assessment = await brain_service.assess_student_wellbeing(
    brain_id=student_brain_id,
    recent_interactions=last_20_interactions
)

# Result: distress_type="GOAL_FRUSTRATION", severity="MODERATE"
if assessment.severity in ["MODERATE", "SEVERE"]:
    intervention = await brain_service.provide_wellbeing_intervention(
        brain_id=student_brain_id,
        assessment=assessment
    )
    # intervention: {
    #     "action": "reduce_difficulty",
    #     "new_difficulty_level": -1,
    #     "provide_worked_examples": true,
    #     "alert_instructor": true
    # }
```

### 2. Burnout Prevention

**Scenario**: Student has been studying for 4 hours straight with declining performance

```python
# Continuous monitoring detects resource starvation
assessment = wellbeing_assess_distress(introspection_context)
# Result: distress_type="RESOURCE_STARVATION", severity="SEVERE"

intervention = wellbeing_provide_relief(brain, assessment)
# intervention: {
#     "action": "mandatory_break",
#     "duration_minutes": 30,
#     "block_new_sessions": true,
#     "send_notification": "You've been working hard! Take a 30-minute break."
# }
```

### 3. Confusion Resolution

**Scenario**: Student repeatedly goes back and forth between two conflicting modules

```python
# Detected as CONTRADICTION distress
assessment = wellbeing_assess_distress(introspection_context)
# Result: distress_type="CONTRADICTION", severity="MILD"

intervention = wellbeing_provide_relief(brain, assessment)
# intervention: {
#     "action": "clarify_concepts",
#     "provide_comparison_table": true,
#     "suggest_prerequisite_review": true,
#     "ai_tutor_explanation": "Let me clarify the difference between X and Y..."
# }
```

### 4. Instructor Dashboard Integration

**Scenario**: Instructor views wellbeing dashboard for all students

```sql
-- Query student wellbeing summary
SELECT
    student_id,
    current_severity,
    critical_episodes_week,
    avg_engagement_week,
    last_assessment_time
FROM student_wellbeing_summary
WHERE critical_episodes_week > 0
ORDER BY current_severity DESC, critical_episodes_week DESC;
```

**Dashboard Display**:
```
At-Risk Students This Week:
┌────────────┬──────────┬──────────────┬────────────┬─────────────┐
│ Student    │ Severity │ Critical     │ Engagement │ Last Check  │
│            │          │ Episodes     │            │             │
├────────────┼──────────┼──────────────┼────────────┼─────────────┤
│ Alice      │ SEVERE   │ 3            │ 0.45       │ 2 hours ago │
│ Bob        │ MODERATE │ 2            │ 0.62       │ 1 hour ago  │
│ Charlie    │ MILD     │ 1            │ 0.78       │ 30 min ago  │
└────────────┴──────────┴──────────────┴────────────┴─────────────┘

Recommended Actions:
- Alice: Immediate intervention - schedule 1:1 meeting
- Bob: Reduce difficulty, provide scaffolding
- Charlie: Monitor, no immediate action needed
```

---

## NIMCP API Integration

### Key NIMCP Functions to Use

**From** `/home/bbrelin/nimcp/src/cognitive/wellbeing/nimcp_wellbeing.h`:

```c
// 1. Assess distress from introspection context
distress_assessment_t wellbeing_assess_distress(introspection_context_t ctx);

// 2. Provide relief/intervention
bool wellbeing_provide_relief(brain_t brain, distress_assessment_t assessment);

// 3. Start continuous monitoring
bool wellbeing_start_resource_monitoring(
    uint32_t interval_ms,
    const resource_thresholds_t* thresholds,
    bool auto_relief
);

// 4. Get performance statistics
bool wellbeing_get_performance_stats(
    uint32_t window_ms,
    performance_stats_t* stats_out
);

// 5. Query wellbeing events
uint32_t wellbeing_get_events_by_severity(
    distress_severity_t min_severity,
    wellbeing_event_t** events_out
);
```

### Python Bindings (via NIMCP library)

```python
import nimcp

# Assess student wellbeing
brain = nimcp.Brain.load("student_123.bin")
introspection_ctx = brain.get_introspection_context(history_size=20)
distress = nimcp.wellbeing.assess_distress(introspection_ctx)

print(f"Distress Type: {distress.type}")  # GOAL_FRUSTRATION
print(f"Severity: {distress.severity}")  # MODERATE
print(f"Score: {distress.score:.2f}")  # 0.62
print(f"Recommendation: {distress.recommended_action}")  # "reduce_difficulty"

# Apply intervention
success = nimcp.wellbeing.provide_relief(brain, distress)
if success:
    print("Intervention applied successfully")
```

---

## Benefits

### 1. Student Outcomes

- **Early Intervention**: Detect struggling students before they drop out
- **Burnout Prevention**: Automatic breaks when cognitive overload detected
- **Optimal Challenge**: Dynamic difficulty adjustment for flow state
- **Personalized Support**: Interventions tailored to distress type

### 2. Instructor Efficiency

- **Automated Triage**: Focus on students who need help most
- **Predictive Alerts**: "Alice is at risk of burnout" notifications
- **Evidence-Based**: Wellbeing data supports intervention decisions
- **Reduced Workload**: AI handles minor interventions automatically

### 3. Platform Intelligence

- **Self-Aware Learning**: Brain understands student mental state
- **Ethical AI**: Prevents harm through wellbeing monitoring
- **Continuous Improvement**: Learns which interventions work best
- **Data-Driven**: Wellbeing metrics inform content design

---

## Implementation Roadmap

### Phase 1: Database & Entity Updates (Week 1)
- ✅ Add `wellbeing_metrics` to `brain_instances` table
- ✅ Create `wellbeing_assessments` table
- ✅ Update `Brain` entity with `WellbeingMetrics` value object
- ✅ Add wellbeing queries to `BrainDAO`

### Phase 2: Service Integration (Week 2)
- ⏳ Implement `assess_student_wellbeing()` using NIMCP API
- ⏳ Implement `provide_wellbeing_intervention()` with intervention logic
- ⏳ Add continuous monitoring background task
- ⏳ Create intervention effectiveness tracking

### Phase 3: API Endpoints (Week 3)
- ⏳ `POST /wellbeing/assess` - Assess student wellbeing
- ⏳ `POST /wellbeing/intervene` - Apply intervention
- ⏳ `GET /wellbeing/summary/{brain_id}` - Get wellbeing summary
- ⏳ `GET /wellbeing/at-risk` - List at-risk students

### Phase 4: Dashboard Integration (Week 4)
- ⏳ Instructor dashboard: Student wellbeing panel
- ⏳ Student dashboard: Personal wellbeing insights
- ⏳ Org admin dashboard: Platform-wide wellbeing metrics
- ⏳ Real-time alerts for critical distress

---

## Ethical Considerations

### Student Privacy

- **Aggregate Only**: Instructors see summary, not detailed psychological profiles
- **Opt-Out**: Students can disable wellbeing monitoring (with consent form)
- **Data Retention**: Wellbeing assessments deleted after 30 days
- **Transparency**: Students see their own wellbeing data

### Intervention Limits

- **Non-Coercive**: Recommendations, not requirements (except critical)
- **Human Override**: Instructors can override AI interventions
- **Effectiveness Tracking**: Measure if interventions actually help
- **Student Autonomy**: Students control their learning pace

### Bias Mitigation

- **Diverse Training**: Include students from various backgrounds
- **Fairness Audits**: Regular checks for demographic bias
- **Explainable**: Show why intervention was recommended
- **Feedback Loop**: Students can report unfair interventions

---

## Success Metrics

| Metric | Baseline | Target (6 months) |
|--------|----------|-------------------|
| Early struggling detection | Manual (instructor notices) | Automated within 3 failed attempts |
| Intervention response time | 24-48 hours | < 10 minutes (automated) |
| Student burnout rate | 15% per course | < 5% per course |
| Dropout rate | 25% | < 10% |
| Student satisfaction | 3.2/5 | > 4.0/5 |
| Instructor workload | 100% manual triage | 70% automated |

---

## Conclusion

The **NIMCP Wellbeing Module** integration transforms the platform brain from a purely cognitive system into a **compassionate learning companion** that:

1. **Detects student distress** early through pattern recognition
2. **Provides timely interventions** automatically when needed
3. **Prevents burnout** through cognitive load monitoring
4. **Optimizes learning** by maintaining flow state
5. **Respects student autonomy** while offering support

**The brain becomes not just intelligent, but empathetic.**

---

**Next Steps**: Implement Phase 1 (Database & Entity Updates) as part of NIMCP service enhancement.
