"""
Linguistic Transformer - Morphological Rule Engine

BUSINESS CONTEXT:
Provides linguistic transformations for role names to track/discipline names.
Used in project creation wizard to generate appropriate track names based on
target audience selection.

TECHNICAL IMPLEMENTATION:
- Morphological transformation rules (plurals to singulars, professions to fields)
- Handles special cases (QA, DevOps, etc.)
- Title-case formatting with proper capitalization
- Extensible rule-based system

EXAMPLES:
- application_developers → Application Development
- business_analysts → Business Analysis
- qa_engineers → QA Engineering
- devops_engineers → DevOps Engineering

@module linguistic_transformer
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class LinguisticTransformer:
    """
    Applies linguistic transformation rules to convert role identifiers
    to appropriate discipline/field names.

    BUSINESS VALUE:
    - Consistent naming across the platform
    - Professional, concise track names
    - Automated name generation reduces manual work
    """

    def __init__(self):
        """Initialize transformation rules"""

        # Profession → Field/Discipline transformation rules
        # Based on morphological patterns in English
        self.profession_to_field: Dict[str, str] = {
            # Plural forms
            'developers': 'Development',
            'analysts': 'Analysis',
            'engineers': 'Engineering',
            'scientists': 'Science',
            'administrators': 'Administration',
            'architects': 'Architecture',
            'consultants': 'Consulting',
            'designers': 'Design',
            'managers': 'Management',
            'specialists': 'Specialization',
            'technicians': 'Technology',
            'coordinators': 'Coordination',
            'directors': 'Direction',
            'leads': 'Leadership',

            # Singular forms (fallback)
            'developer': 'Development',
            'analyst': 'Analysis',
            'engineer': 'Engineering',
            'scientist': 'Science',
            'administrator': 'Administration',
            'architect': 'Architecture',
            'consultant': 'Consulting',
            'designer': 'Design',
            'manager': 'Management',
            'specialist': 'Specialization',
            'technician': 'Technology',
            'coordinator': 'Coordination',
            'director': 'Direction',
            'lead': 'Leadership',

            # Special executive roles
            'cto': 'Technology Leadership'
        }

        # Special case handling for acronyms and compound words
        self.special_cases: Dict[str, str] = {
            'qa': 'QA',
            'devops': 'DevOps',
            'cicd': 'CI/CD',
            'mlops': 'MLOps',
            'devsecops': 'DevSecOps',
            'ui': 'UI',
            'ux': 'UX',
            'api': 'API',
            'fullstack': 'Full-Stack',
            'fullstack': 'Full Stack'
        }

        logger.info(f"Initialized LinguisticTransformer with {len(self.profession_to_field)} transformation rules")

    def generate_track_name(self, role_identifier: str) -> str:
        """
        Generate professional track name from role identifier.

        ALGORITHM:
        1. Split underscore-separated identifier
        2. Extract profession (last word)
        3. Transform profession to field using morphological rules
        4. Capitalize prefix words (handling special cases)
        5. Combine into final track name

        Args:
            role_identifier: Underscore-separated role (e.g., "application_developers")

        Returns:
            Properly formatted track name (e.g., "Application Development")

        Examples:
            >>> transformer = LinguisticTransformer()
            >>> transformer.generate_track_name("application_developers")
            "Application Development"
            >>> transformer.generate_track_name("qa_engineers")
            "QA Engineering"
            >>> transformer.generate_track_name("devops_engineers")
            "DevOps Engineering"
        """
        if not role_identifier or not isinstance(role_identifier, str):
            logger.warning(f"Invalid role identifier: {role_identifier}")
            return "Unknown Track"

        # Split into words
        words = role_identifier.lower().strip().split('_')

        if len(words) == 0:
            logger.warning(f"Empty role identifier after splitting")
            return "Unknown Track"

        # Extract profession (last word) and prefix words
        profession = words[-1]
        prefix_words = words[:-1]

        # Transform profession using morphological rules
        field_name = self.profession_to_field.get(profession)

        if not field_name:
            # Fallback: capitalize profession if no rule found
            field_name = profession.capitalize()
            logger.info(f"No transformation rule for profession '{profession}', using capitalized form")

        # Capitalize prefix words with special case handling
        capitalized_prefix = []
        for word in prefix_words:
            # Check for special cases (acronyms, compound words)
            if word in self.special_cases:
                capitalized_prefix.append(self.special_cases[word])
            else:
                # Standard title-case capitalization
                capitalized_prefix.append(word.capitalize())

        # Combine prefix + field name
        track_name = ' '.join(capitalized_prefix + [field_name])

        logger.info(f"Transformed '{role_identifier}' → '{track_name}'")

        return track_name

    def batch_generate_track_names(self, role_identifiers: List[str]) -> Dict[str, str]:
        """
        Generate track names for multiple role identifiers in batch.

        Args:
            role_identifiers: List of role identifiers

        Returns:
            Dictionary mapping role identifiers to track names

        Example:
            >>> transformer = LinguisticTransformer()
            >>> roles = ["application_developers", "qa_engineers"]
            >>> transformer.batch_generate_track_names(roles)
            {
                "application_developers": "Application Development",
                "qa_engineers": "QA Engineering"
            }
        """
        results = {}

        for role_id in role_identifiers:
            try:
                results[role_id] = self.generate_track_name(role_id)
            except Exception as e:
                logger.error(f"Error transforming role '{role_id}': {e}")
                results[role_id] = "Unknown Track"

        logger.info(f"Batch transformed {len(results)} role identifiers")

        return results

    def add_transformation_rule(self, profession: str, field: str):
        """
        Add or update a transformation rule.

        Allows runtime extension of transformation rules.

        Args:
            profession: Profession noun (e.g., "developers")
            field: Field noun (e.g., "Development")
        """
        self.profession_to_field[profession.lower()] = field
        logger.info(f"Added transformation rule: '{profession}' → '{field}'")

    def add_special_case(self, word: str, formatted: str):
        """
        Add or update a special case formatting rule.

        Args:
            word: Lowercase word (e.g., "qa")
            formatted: Properly formatted version (e.g., "QA")
        """
        self.special_cases[word.lower()] = formatted
        logger.info(f"Added special case: '{word}' → '{formatted}'")
