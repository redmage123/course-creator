"""
Prerequisite Service - Course Prerequisite Checking

BUSINESS REQUIREMENT:
Validate student readiness for courses by checking prerequisite
completion and recommending preparation courses.

BUSINESS VALUE:
- Prevents students from enrolling in courses they're not ready for
- Reduces course dropout rates
- Provides clear learning path guidance
- Improves student success rates

TECHNICAL IMPLEMENTATION:
- Traverses prerequisite graph
- Checks student completion status
- Handles alternative prerequisites (OR logic)
- Provides actionable recommendations

WHY:
Students need to know if they're ready for a course BEFORE enrolling.
Clear prerequisite checking reduces frustration and improves outcomes.
"""

import logging
from typing import List, Optional, Dict, Any, Set
from uuid import UUID
from decimal import Decimal

from knowledge_graph_service.domain.entities.node import Node, NodeType
from knowledge_graph_service.domain.entities.edge import Edge, EdgeType
from data_access.graph_dao import GraphDAO

logger = logging.getLogger(__name__)


class PrerequisiteService:
    """
    Course Prerequisite Validation Service

    BUSINESS VALUE:
    Ensures students are adequately prepared for courses
    """

    def __init__(self, dao: GraphDAO):
        """
        Initialize prerequisite service

        Args:
            dao: GraphDAO instance for data access
        """
        self.dao = dao

    async def check_prerequisites(
        self,
        course_id: UUID,
        student_id: UUID,
        completed_course_ids: Optional[List[UUID]] = None
    ) -> Dict[str, Any]:
        """
        Check if student meets all prerequisites for a course

        BUSINESS USE CASE:
        Before allowing enrollment, verify student has completed
        all required prerequisite courses.

        Args:
            course_id: Target course UUID
            student_id: Student UUID
            completed_course_ids: Optional list of completed course UUIDs
                                 (if not provided, will be fetched)

        Returns:
            Dict with:
            - ready: bool (can student enroll?)
            - prerequisites: List of all prerequisites with status
            - missing_prerequisites: List of courses student needs to complete
            - recommended_courses: Suggested courses to take first
            - alternative_paths: Alternative ways to meet prerequisites
        """
        # Get graph node for course
        course_node = await self.dao.get_node_by_entity(
            course_id,
            NodeType.COURSE
        )

        if not course_node:
            return {
                'ready': False,
                'error': f'Course {course_id} not found in knowledge graph',
                'prerequisites': [],
                'missing_prerequisites': [],
                'recommended_courses': []
            }

        # Get student's completed courses if not provided
        if completed_course_ids is None:
            # TODO: Integrate with student progress service
            # For now, return empty list
            completed_course_ids = []

        # Get all prerequisites using database function
        prerequisite_data = await self.dao.get_all_prerequisites(
            course_node.id,
            max_depth=5
        )

        # Process prerequisites
        prerequisites = []
        missing = []
        completed_set = set(completed_course_ids)

        for prereq in prerequisite_data:
            prereq_node_id = prereq['prerequisite_node_id']
            prereq_node = await self.dao.get_node_by_id(prereq_node_id)

            if not prereq_node:
                continue

            prereq_course_id = prereq_node.entity_id
            is_completed = prereq_course_id in completed_set

            # Get edge properties to check if mandatory
            edge_id = prereq.get('edge_id')
            is_mandatory = True
            alternatives = []

            if edge_id:
                edge = await self.dao.get_edge_by_id(UUID(edge_id))
                if edge:
                    is_mandatory = edge.is_mandatory_prerequisite()
                    alternatives = await self._get_alternative_prerequisites(
                        prereq_node.id
                    )

            prereq_info = {
                'course_id': str(prereq_course_id),
                'course_name': prereq_node.label,
                'depth': prereq['depth'],
                'completed': is_completed,
                'mandatory': is_mandatory,
                'alternatives': alternatives
            }

            prerequisites.append(prereq_info)

            if not is_completed and is_mandatory:
                # Check if student completed any alternatives
                alt_completed = any(
                    alt['course_id'] in [str(cid) for cid in completed_set]
                    for alt in alternatives
                )
                if not alt_completed:
                    missing.append(prereq_info)

        # Determine readiness
        ready = len(missing) == 0

        # Get recommended courses (nearest prerequisites to complete)
        recommended = await self._get_recommended_prerequisite_order(
            missing,
            completed_set
        )

        result = {
            'ready': ready,
            'course_id': str(course_id),
            'course_name': course_node.label,
            'prerequisites': prerequisites,
            'missing_prerequisites': missing,
            'recommended_courses': recommended,
            'total_prerequisites': len(prerequisites),
            'completed_prerequisites': len(prerequisites) - len(missing)
        }

        logger.info(
            f"Prerequisite check for course {course_id}: "
            f"ready={ready}, missing={len(missing)}"
        )

        return result

    async def get_prerequisite_chain(
        self,
        course_id: UUID,
        max_depth: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get complete prerequisite chain for a course

        BUSINESS USE CASE:
        Show students the full dependency tree for a course

        Args:
            course_id: Target course UUID
            max_depth: Maximum chain depth

        Returns:
            List of prerequisite courses organized by depth
        """
        # Get graph node for course
        course_node = await self.dao.get_node_by_entity(
            course_id,
            NodeType.COURSE
        )

        if not course_node:
            return []

        # Get all prerequisites
        prerequisite_data = await self.dao.get_all_prerequisites(
            course_node.id,
            max_depth=max_depth
        )

        # Organize by depth
        chain = []
        for prereq in prerequisite_data:
            prereq_node_id = UUID(prereq['prerequisite_id'])
            prereq_node = await self.dao.get_node_by_id(prereq_node_id)

            if prereq_node:
                chain.append({
                    'course_id': str(prereq_node.entity_id),
                    'course_name': prereq_node.label,
                    'depth': prereq['depth'],
                    'difficulty': prereq_node.properties.get('difficulty', 'intermediate'),
                    'duration': prereq_node.properties.get('duration', 0)
                })

        # Sort by depth (foundation courses first)
        chain.sort(key=lambda x: -x['depth'])

        return chain

    async def validate_course_sequence(
        self,
        course_sequence: List[UUID],
        student_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Validate if a course sequence respects prerequisites

        BUSINESS USE CASE:
        Student plans to take courses A, B, C in that order.
        Verify this sequence is valid.

        Args:
            course_sequence: List of course UUIDs in planned order
            student_id: Optional student UUID

        Returns:
            Dict with validation results and suggestions
        """
        if not course_sequence:
            return {
                'valid': True,
                'issues': [],
                'suggestions': []
            }

        issues = []
        suggestions = []
        completed_in_sequence = set()

        for i, course_id in enumerate(course_sequence):
            # Check prerequisites for this course
            prereq_check = await self.check_prerequisites(
                course_id,
                student_id or UUID('00000000-0000-0000-0000-000000000000'),
                completed_course_ids=list(completed_in_sequence)
            )

            if not prereq_check['ready']:
                # Find which prerequisites are missing
                missing = prereq_check['missing_prerequisites']

                for missing_prereq in missing:
                    prereq_course_id = UUID(missing_prereq['course_id'])

                    # Check if it's later in the sequence
                    if prereq_course_id in course_sequence[i+1:]:
                        issues.append({
                            'course_index': i,
                            'course_id': str(course_id),
                            'issue': 'prerequisite_not_met',
                            'message': f"{missing_prereq['course_name']} must be taken before this course"
                        })

                        # Suggest reordering
                        prereq_index = course_sequence.index(prereq_course_id)
                        suggestions.append({
                            'type': 'reorder',
                            'message': f"Move '{missing_prereq['course_name']}' (index {prereq_index}) before index {i}"
                        })
                    else:
                        # Prerequisite not in sequence at all
                        suggestions.append({
                            'type': 'add_course',
                            'course_id': str(prereq_course_id),
                            'course_name': missing_prereq['course_name'],
                            'message': f"Add '{missing_prereq['course_name']}' before '{prereq_check['course_name']}'"
                        })

            # Mark this course as completed for next iterations
            completed_in_sequence.add(course_id)

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'suggestions': suggestions,
            'total_courses': len(course_sequence)
        }

    async def get_enrollment_readiness(
        self,
        student_id: UUID,
        course_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Check student's readiness for multiple courses

        BUSINESS USE CASE:
        Student browsing course catalog. Show which courses
        they're ready for and which need prerequisites.

        Args:
            student_id: Student UUID
            course_ids: List of course UUIDs to check

        Returns:
            Dict with readiness status for each course
        """
        # TODO: Get student's completed courses from progress service
        completed_course_ids = []

        readiness = {
            'ready': [],
            'not_ready': [],
            'partial': []  # Some prerequisites met
        }

        for course_id in course_ids:
            check = await self.check_prerequisites(
                course_id,
                student_id,
                completed_course_ids
            )

            course_info = {
                'course_id': str(course_id),
                'course_name': check.get('course_name', 'Unknown'),
                'missing_count': len(check['missing_prerequisites']),
                'total_prerequisites': check['total_prerequisites']
            }

            if check['ready']:
                readiness['ready'].append(course_info)
            elif check['completed_prerequisites'] > 0:
                readiness['partial'].append(course_info)
            else:
                readiness['not_ready'].append(course_info)

        return readiness

    # ========================================
    # HELPER METHODS
    # ========================================

    async def _get_alternative_prerequisites(
        self,
        prereq_node_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get alternative prerequisites (OR logic)

        BUSINESS LOGIC:
        Some courses accept alternative prerequisites.
        E.g., "Intro to Python" OR "Intro to Programming"

        Args:
            prereq_node_id: Prerequisite node UUID

        Returns:
            List of alternative prerequisite courses
        """
        # Get edges with "alternative_to" relationship
        edges = await self.dao.get_edges_from_node(
            prereq_node_id,
            edge_types=[EdgeType.ALTERNATIVE_TO]
        )

        alternatives = []
        for edge in edges:
            alt_node = await self.dao.get_node_by_id(edge.target_node_id)
            if alt_node and alt_node.node_type == NodeType.COURSE:
                alternatives.append({
                    'course_id': str(alt_node.entity_id),
                    'course_name': alt_node.label,
                    'difficulty': alt_node.properties.get('difficulty', 'intermediate')
                })

        return alternatives

    async def _get_recommended_prerequisite_order(
        self,
        missing_prerequisites: List[Dict[str, Any]],
        completed_course_ids: Set[UUID]
    ) -> List[Dict[str, Any]]:
        """
        Determine optimal order to complete missing prerequisites

        BUSINESS LOGIC:
        Recommend prerequisites in dependency order (foundation first)

        Args:
            missing_prerequisites: List of missing prerequisites
            completed_course_ids: Set of completed course UUIDs

        Returns:
            List of recommended courses in optimal order
        """
        # Sort by depth (deeper = more foundational)
        sorted_prereqs = sorted(
            missing_prerequisites,
            key=lambda x: -x.get('depth', 0)
        )

        recommended = []
        for prereq in sorted_prereqs:
            # Check if this prerequisite's own prerequisites are met
            prereq_course_id = UUID(prereq['course_id'])

            # Get prerequisites for this prerequisite
            sub_check = await self.check_prerequisites(
                prereq_course_id,
                UUID('00000000-0000-0000-0000-000000000000'),  # Dummy student ID
                completed_course_ids=list(completed_course_ids)
            )

            recommended.append({
                **prereq,
                'sub_prerequisites_count': len(sub_check['missing_prerequisites']),
                'ready_to_take': sub_check['ready']
            })

        # Sort: ready courses first, then by depth
        recommended.sort(
            key=lambda x: (not x['ready_to_take'], -x.get('depth', 0))
        )

        return recommended

    async def get_prerequisite_statistics(
        self,
        course_id: UUID
    ) -> Dict[str, Any]:
        """
        Get statistics about course prerequisites

        BUSINESS USE CASE:
        For instructors/admins to understand prerequisite complexity

        Args:
            course_id: Course UUID

        Returns:
            Dict with prerequisite statistics
        """
        course_node = await self.dao.get_node_by_entity(
            course_id,
            NodeType.COURSE
        )

        if not course_node:
            return {}

        # Get all prerequisites
        prereq_data = await self.dao.get_all_prerequisites(
            course_node.id,
            max_depth=10
        )

        # Calculate statistics
        total_prereqs = len(prereq_data)
        max_depth = max([p['depth'] for p in prereq_data]) if prereq_data else 0

        # Count mandatory vs optional
        mandatory_count = 0
        for prereq in prereq_data:
            edge_id = prereq.get('edge_id')
            if edge_id:
                edge = await self.dao.get_edge_by_id(UUID(edge_id))
                if edge and edge.is_mandatory_prerequisite():
                    mandatory_count += 1

        return {
            'course_id': str(course_id),
            'course_name': course_node.label,
            'total_prerequisites': total_prereqs,
            'mandatory_prerequisites': mandatory_count,
            'optional_prerequisites': total_prereqs - mandatory_count,
            'max_depth': max_depth,
            'complexity': 'high' if total_prereqs > 5 else 'medium' if total_prereqs > 2 else 'low'
        }
