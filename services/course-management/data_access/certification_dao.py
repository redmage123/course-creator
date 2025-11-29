#!/usr/bin/env python3

"""
Certification Data Access Object (DAO)

WHAT: Data access layer for certification system including templates,
issued certificates, digital badges, and verification.

WHERE: Used by CertificationService for database operations

WHY: Provides clean separation between business logic and data persistence,
supporting multiple database backends and transaction management.

## Operations:
- Certificate template CRUD
- Certificate issuance and retrieval
- Digital badge management
- Verification logging
- Analytics aggregation

Author: Course Creator Platform
Version: 1.0.0
"""

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import logging

from course_management.domain.entities.certification import (
    CertificateTemplate,
    CertificateSignatory,
    IssuedCertificate,
    CertificateVerification,
    DigitalBadge,
    BadgeAssertion,
    CertificateShare,
    CertificateRenewal,
    CertificateAnalytics,
    TemplateType,
    AchievementType,
    CertificateStatus,
    SignatureStyle,
    BadgeType,
    VerificationMethod,
    VerificationResult,
    SharePlatform,
    RenewalStatus,
    DesignConfig,
    SkillCertification,
    CompetencyCertification,
    BadgeAlignment,
    BadgeEvidence
)

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class CertificationDAOError(Exception):
    """
    WHAT: Base exception for certification DAO operations
    WHERE: Raised when database operations fail
    WHY: Provides specific exception type for error handling
    """
    pass


class TemplateNotFoundError(CertificationDAOError):
    """Raised when certificate template is not found"""
    pass


class CertificateNotFoundError(CertificationDAOError):
    """Raised when issued certificate is not found"""
    pass


class BadgeNotFoundError(CertificationDAOError):
    """Raised when digital badge is not found"""
    pass


class DuplicateCertificateError(CertificationDAOError):
    """Raised when certificate number already exists"""
    pass


class DuplicateVerificationCodeError(CertificationDAOError):
    """Raised when verification code already exists"""
    pass


# ============================================================================
# Certification DAO
# ============================================================================


class CertificationDAO:
    """
    WHAT: Data Access Object for certification system

    WHERE: Used by CertificationService for all database operations

    WHY: Encapsulates database access, enabling clean architecture
    and supporting different database backends.

    ## Database Operations:
    - Template management (CRUD)
    - Certificate issuance and retrieval
    - Badge management
    - Verification logging
    - Analytics computation
    """

    def __init__(self, db_connection):
        """
        WHAT: Initializes DAO with database connection
        WHERE: Called by service layer during initialization
        WHY: Enables database operations with connection pooling

        Args:
            db_connection: Database connection or pool
        """
        self.db = db_connection
        logger.info("CertificationDAO initialized")

    # =========================================================================
    # Certificate Template Operations
    # =========================================================================

    async def create_template(self, template: CertificateTemplate) -> CertificateTemplate:
        """
        WHAT: Creates a new certificate template

        WHERE: Called when organization creates template

        WHY: Persists template configuration for certificate generation

        Args:
            template: CertificateTemplate entity to create

        Returns:
            Created template with generated ID

        Raises:
            CertificationDAOError: If creation fails
        """
        try:
            query = """
                INSERT INTO certificate_templates (
                    id, organization_id, name, description, template_type,
                    design_config, title_template, subtitle_template,
                    body_template, footer_template,
                    primary_color, secondary_color, accent_color, font_family,
                    include_qr_code, include_verification_url,
                    include_skills_list, include_competencies,
                    include_credits, include_grade,
                    has_expiration, validity_period_months, renewal_allowed,
                    is_active, is_default, created_by
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                    $21, $22, $23, $24, $25, $26
                )
                RETURNING id, created_at
            """
            result = await self.db.fetchrow(
                query,
                template.id, template.organization_id, template.name,
                template.description, template.template_type.value,
                template.design_config.to_dict() if template.design_config else {},
                template.title_template, template.subtitle_template,
                template.body_template, template.footer_template,
                template.primary_color, template.secondary_color,
                template.accent_color, template.font_family,
                template.include_qr_code, template.include_verification_url,
                template.include_skills_list, template.include_competencies,
                template.include_credits, template.include_grade,
                template.has_expiration, template.validity_period_months,
                template.renewal_allowed, template.is_active, template.is_default,
                template.created_by
            )
            template.created_at = result['created_at']
            logger.info(f"Created certificate template: {template.id}")
            return template

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            raise CertificationDAOError(f"Failed to create template: {e}") from e

    async def get_template_by_id(self, template_id: UUID) -> Optional[CertificateTemplate]:
        """
        WHAT: Retrieves template by ID

        WHERE: Called when issuing certificates or updating templates

        WHY: Fetches template configuration for certificate generation

        Args:
            template_id: UUID of template to retrieve

        Returns:
            CertificateTemplate if found, None otherwise
        """
        try:
            query = """
                SELECT * FROM certificate_templates
                WHERE id = $1
            """
            row = await self.db.fetchrow(query, template_id)
            if not row:
                return None
            return self._row_to_template(row)

        except Exception as e:
            logger.error(f"Failed to get template {template_id}: {e}")
            raise CertificationDAOError(f"Failed to get template: {e}") from e

    async def get_templates_by_organization(
        self,
        organization_id: UUID,
        template_type: Optional[TemplateType] = None,
        active_only: bool = True
    ) -> List[CertificateTemplate]:
        """
        WHAT: Retrieves templates for an organization

        WHERE: Called when listing available templates

        WHY: Enables organizations to manage their templates

        Args:
            organization_id: UUID of organization
            template_type: Optional filter by type
            active_only: Whether to return only active templates

        Returns:
            List of matching templates
        """
        try:
            conditions = ["organization_id = $1"]
            params = [organization_id]

            if template_type:
                conditions.append(f"template_type = ${len(params) + 1}")
                params.append(template_type.value)

            if active_only:
                conditions.append("is_active = true")

            query = f"""
                SELECT * FROM certificate_templates
                WHERE {' AND '.join(conditions)}
                ORDER BY is_default DESC, name ASC
            """
            rows = await self.db.fetch(query, *params)
            return [self._row_to_template(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get templates for org {organization_id}: {e}")
            raise CertificationDAOError(f"Failed to get templates: {e}") from e

    async def update_template(self, template: CertificateTemplate) -> CertificateTemplate:
        """
        WHAT: Updates an existing template

        WHERE: Called when modifying template configuration

        WHY: Enables template customization over time

        Args:
            template: Template with updated values

        Returns:
            Updated template

        Raises:
            TemplateNotFoundError: If template doesn't exist
        """
        try:
            query = """
                UPDATE certificate_templates SET
                    name = $2, description = $3,
                    design_config = $4, title_template = $5,
                    subtitle_template = $6, body_template = $7,
                    footer_template = $8, primary_color = $9,
                    secondary_color = $10, accent_color = $11,
                    font_family = $12, include_qr_code = $13,
                    include_verification_url = $14, include_skills_list = $15,
                    include_competencies = $16, include_credits = $17,
                    include_grade = $18, has_expiration = $19,
                    validity_period_months = $20, renewal_allowed = $21,
                    is_active = $22, is_default = $23,
                    updated_at = NOW(), updated_by = $24
                WHERE id = $1
                RETURNING updated_at
            """
            result = await self.db.fetchrow(
                query, template.id, template.name, template.description,
                template.design_config.to_dict() if template.design_config else {},
                template.title_template, template.subtitle_template,
                template.body_template, template.footer_template,
                template.primary_color, template.secondary_color,
                template.accent_color, template.font_family,
                template.include_qr_code, template.include_verification_url,
                template.include_skills_list, template.include_competencies,
                template.include_credits, template.include_grade,
                template.has_expiration, template.validity_period_months,
                template.renewal_allowed, template.is_active, template.is_default,
                template.updated_by
            )
            if not result:
                raise TemplateNotFoundError(f"Template {template.id} not found")

            template.updated_at = result['updated_at']
            logger.info(f"Updated template: {template.id}")
            return template

        except TemplateNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            raise CertificationDAOError(f"Failed to update template: {e}") from e

    # =========================================================================
    # Issued Certificate Operations
    # =========================================================================

    async def create_certificate(
        self,
        certificate: IssuedCertificate
    ) -> IssuedCertificate:
        """
        WHAT: Creates/issues a new certificate

        WHERE: Called when user earns a certificate

        WHY: Persists the official credential record

        Args:
            certificate: IssuedCertificate entity to create

        Returns:
            Created certificate with timestamps

        Raises:
            DuplicateCertificateError: If certificate number exists
            DuplicateVerificationCodeError: If verification code exists
        """
        try:
            query = """
                INSERT INTO issued_certificates (
                    id, certificate_number, verification_code,
                    template_id, recipient_id, course_id, program_id,
                    organization_id, title, recipient_name, description,
                    achievement_type, grade, score, credits_earned,
                    completion_percentage, skills_certified, competencies_certified,
                    issue_date, completion_date, expiration_date,
                    verification_url, qr_code_data, digital_signature,
                    signature_algorithm, pdf_url, image_url, thumbnail_url,
                    status, is_public, metadata
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                    $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31
                )
                RETURNING id, created_at
            """
            skills_json = [
                {"skill_id": str(s.skill_id), "skill_name": s.skill_name,
                 "proficiency_level": s.proficiency_level}
                for s in certificate.skills_certified
            ]
            competencies_json = [
                {"competency_id": str(c.competency_id), "competency_name": c.competency_name,
                 "proficiency_level": c.proficiency_level}
                for c in certificate.competencies_certified
            ]

            result = await self.db.fetchrow(
                query,
                certificate.id, certificate.certificate_number,
                certificate.verification_code, certificate.template_id,
                certificate.recipient_id, certificate.course_id,
                certificate.program_id, certificate.organization_id,
                certificate.title, certificate.recipient_name,
                certificate.description, certificate.achievement_type.value,
                certificate.grade, certificate.score, certificate.credits_earned,
                certificate.completion_percentage, skills_json, competencies_json,
                certificate.issue_date, certificate.completion_date,
                certificate.expiration_date, certificate.verification_url,
                certificate.qr_code_data, certificate.digital_signature,
                certificate.signature_algorithm, certificate.pdf_url,
                certificate.image_url, certificate.thumbnail_url,
                certificate.status.value, certificate.is_public,
                certificate.metadata
            )
            certificate.created_at = result['created_at']
            logger.info(f"Created certificate: {certificate.certificate_number}")
            return certificate

        except Exception as e:
            if "certificate_number" in str(e):
                raise DuplicateCertificateError(
                    f"Certificate number {certificate.certificate_number} already exists"
                )
            if "verification_code" in str(e):
                raise DuplicateVerificationCodeError(
                    f"Verification code already exists"
                )
            logger.error(f"Failed to create certificate: {e}")
            raise CertificationDAOError(f"Failed to create certificate: {e}") from e

    async def get_certificate_by_id(
        self,
        certificate_id: UUID
    ) -> Optional[IssuedCertificate]:
        """
        WHAT: Retrieves certificate by ID

        WHERE: Called when viewing or verifying certificates

        WHY: Fetches complete certificate data

        Args:
            certificate_id: UUID of certificate

        Returns:
            IssuedCertificate if found, None otherwise
        """
        try:
            query = "SELECT * FROM issued_certificates WHERE id = $1"
            row = await self.db.fetchrow(query, certificate_id)
            if not row:
                return None
            return self._row_to_certificate(row)

        except Exception as e:
            logger.error(f"Failed to get certificate {certificate_id}: {e}")
            raise CertificationDAOError(f"Failed to get certificate: {e}") from e

    async def get_certificate_by_verification_code(
        self,
        verification_code: str
    ) -> Optional[IssuedCertificate]:
        """
        WHAT: Retrieves certificate by verification code

        WHERE: Called during certificate verification

        WHY: Enables public verification without exposing internal IDs

        Args:
            verification_code: Unique verification code

        Returns:
            IssuedCertificate if found, None otherwise
        """
        try:
            query = "SELECT * FROM issued_certificates WHERE verification_code = $1"
            row = await self.db.fetchrow(query, verification_code)
            if not row:
                return None
            return self._row_to_certificate(row)

        except Exception as e:
            logger.error(f"Failed to get certificate by code: {e}")
            raise CertificationDAOError(f"Failed to get certificate: {e}") from e

    async def get_certificates_by_recipient(
        self,
        recipient_id: UUID,
        status_filter: Optional[CertificateStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[IssuedCertificate], int]:
        """
        WHAT: Retrieves certificates for a recipient

        WHERE: Called when viewing user's certificates

        WHY: Enables users to see all their earned credentials

        Args:
            recipient_id: UUID of recipient
            status_filter: Optional status filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            Tuple of (certificates list, total count)
        """
        try:
            conditions = ["recipient_id = $1"]
            params = [recipient_id]

            if status_filter:
                conditions.append(f"status = ${len(params) + 1}")
                params.append(status_filter.value)

            where_clause = " AND ".join(conditions)

            count_query = f"""
                SELECT COUNT(*) FROM issued_certificates WHERE {where_clause}
            """
            total = await self.db.fetchval(count_query, *params)

            query = f"""
                SELECT * FROM issued_certificates
                WHERE {where_clause}
                ORDER BY issue_date DESC
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
            """
            rows = await self.db.fetch(query, *params, limit, offset)

            return ([self._row_to_certificate(row) for row in rows], total)

        except Exception as e:
            logger.error(f"Failed to get certificates for recipient: {e}")
            raise CertificationDAOError(f"Failed to get certificates: {e}") from e

    async def revoke_certificate(
        self,
        certificate_id: UUID,
        reason: str,
        revoked_by: UUID
    ) -> IssuedCertificate:
        """
        WHAT: Revokes an issued certificate

        WHERE: Called when certificate needs to be invalidated

        WHY: Enables administrative action for misconduct or errors

        Args:
            certificate_id: UUID of certificate to revoke
            reason: Reason for revocation
            revoked_by: UUID of user performing revocation

        Returns:
            Updated certificate with revoked status

        Raises:
            CertificateNotFoundError: If certificate doesn't exist
        """
        try:
            query = """
                UPDATE issued_certificates SET
                    status = 'revoked',
                    revocation_reason = $2,
                    revoked_by = $3,
                    revoked_at = NOW(),
                    updated_at = NOW()
                WHERE id = $1
                RETURNING *
            """
            row = await self.db.fetchrow(query, certificate_id, reason, revoked_by)
            if not row:
                raise CertificateNotFoundError(f"Certificate {certificate_id} not found")

            logger.info(f"Revoked certificate: {certificate_id}")
            return self._row_to_certificate(row)

        except CertificateNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to revoke certificate: {e}")
            raise CertificationDAOError(f"Failed to revoke certificate: {e}") from e

    # =========================================================================
    # Verification Operations
    # =========================================================================

    async def log_verification(
        self,
        verification: CertificateVerification
    ) -> CertificateVerification:
        """
        WHAT: Logs a certificate verification attempt

        WHERE: Called during verification process

        WHY: Creates audit trail and enables analytics

        Args:
            verification: Verification record to log

        Returns:
            Created verification record
        """
        try:
            query = """
                INSERT INTO certificate_verifications (
                    id, certificate_id, verification_method,
                    verifier_ip, verifier_user_agent,
                    verifier_organization, verifier_email,
                    verification_result, country_code, region
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING verified_at
            """
            result = await self.db.fetchrow(
                query,
                verification.id, verification.certificate_id,
                verification.verification_method.value,
                verification.verifier_ip, verification.verifier_user_agent,
                verification.verifier_organization, verification.verifier_email,
                verification.verification_result.value,
                verification.country_code, verification.region
            )
            verification.verified_at = result['verified_at']
            return verification

        except Exception as e:
            logger.error(f"Failed to log verification: {e}")
            raise CertificationDAOError(f"Failed to log verification: {e}") from e

    async def get_verification_count(
        self,
        certificate_id: UUID,
        since: Optional[datetime] = None
    ) -> int:
        """
        WHAT: Gets verification count for a certificate

        WHERE: Called for certificate analytics

        WHY: Shows how often certificate is being verified

        Args:
            certificate_id: UUID of certificate
            since: Optional start date filter

        Returns:
            Number of verifications
        """
        try:
            if since:
                query = """
                    SELECT COUNT(*) FROM certificate_verifications
                    WHERE certificate_id = $1 AND verified_at >= $2
                """
                return await self.db.fetchval(query, certificate_id, since)
            else:
                query = """
                    SELECT COUNT(*) FROM certificate_verifications
                    WHERE certificate_id = $1
                """
                return await self.db.fetchval(query, certificate_id)

        except Exception as e:
            logger.error(f"Failed to get verification count: {e}")
            raise CertificationDAOError(f"Failed to get verification count: {e}") from e

    # =========================================================================
    # Digital Badge Operations
    # =========================================================================

    async def create_badge(self, badge: DigitalBadge) -> DigitalBadge:
        """
        WHAT: Creates a new digital badge definition

        WHERE: Called when organization creates a badge

        WHY: Defines badge criteria and appearance

        Args:
            badge: DigitalBadge entity to create

        Returns:
            Created badge with timestamps
        """
        try:
            query = """
                INSERT INTO digital_badges (
                    id, organization_id, name, description,
                    image_url, criteria_url, criteria_narrative,
                    badge_type, issuer_name, issuer_url,
                    issuer_email, issuer_image_url,
                    alignment, tags, requirements,
                    is_active, is_stackable
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, $15, $16, $17
                )
                RETURNING id, created_at
            """
            alignment_json = [a.to_dict() for a in badge.alignment]

            result = await self.db.fetchrow(
                query,
                badge.id, badge.organization_id, badge.name,
                badge.description, badge.image_url, badge.criteria_url,
                badge.criteria_narrative, badge.badge_type.value,
                badge.issuer_name, badge.issuer_url, badge.issuer_email,
                badge.issuer_image_url, alignment_json, badge.tags,
                badge.requirements, badge.is_active, badge.is_stackable
            )
            badge.created_at = result['created_at']
            logger.info(f"Created badge: {badge.id}")
            return badge

        except Exception as e:
            logger.error(f"Failed to create badge: {e}")
            raise CertificationDAOError(f"Failed to create badge: {e}") from e

    async def get_badge_by_id(self, badge_id: UUID) -> Optional[DigitalBadge]:
        """
        WHAT: Retrieves badge by ID

        WHERE: Called when issuing or viewing badges

        WHY: Fetches badge configuration

        Args:
            badge_id: UUID of badge

        Returns:
            DigitalBadge if found, None otherwise
        """
        try:
            query = "SELECT * FROM digital_badges WHERE id = $1"
            row = await self.db.fetchrow(query, badge_id)
            if not row:
                return None
            return self._row_to_badge(row)

        except Exception as e:
            logger.error(f"Failed to get badge {badge_id}: {e}")
            raise CertificationDAOError(f"Failed to get badge: {e}") from e

    async def create_badge_assertion(
        self,
        assertion: BadgeAssertion
    ) -> BadgeAssertion:
        """
        WHAT: Creates a badge assertion (issues badge)

        WHERE: Called when user earns a badge

        WHY: Records the badge award

        Args:
            assertion: BadgeAssertion entity to create

        Returns:
            Created assertion with timestamps
        """
        try:
            query = """
                INSERT INTO badge_assertions (
                    id, badge_id, recipient_id, recipient_type,
                    recipient_identity, recipient_hashed, recipient_salt,
                    evidence, verification_type, verification_url,
                    issued_on, expires_at, status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                RETURNING id, created_at
            """
            evidence_json = [e.to_dict() for e in assertion.evidence]

            result = await self.db.fetchrow(
                query,
                assertion.id, assertion.badge_id, assertion.recipient_id,
                assertion.recipient_type, assertion.recipient_identity,
                assertion.recipient_hashed, assertion.recipient_salt,
                evidence_json, assertion.verification_type,
                assertion.verification_url, assertion.issued_on,
                assertion.expires_at, assertion.status
            )
            assertion.created_at = result['created_at']
            logger.info(f"Created badge assertion: {assertion.id}")
            return assertion

        except Exception as e:
            logger.error(f"Failed to create badge assertion: {e}")
            raise CertificationDAOError(f"Failed to create badge assertion: {e}") from e

    async def get_badges_by_recipient(
        self,
        recipient_id: UUID,
        active_only: bool = True
    ) -> List[Tuple[BadgeAssertion, DigitalBadge]]:
        """
        WHAT: Retrieves badges earned by a recipient

        WHERE: Called when viewing user's badges

        WHY: Shows all badges a user has earned

        Args:
            recipient_id: UUID of recipient
            active_only: Whether to exclude revoked badges

        Returns:
            List of (assertion, badge) tuples
        """
        try:
            conditions = ["ba.recipient_id = $1"]
            if active_only:
                conditions.append("ba.revoked = false")

            query = f"""
                SELECT ba.*, db.*,
                       ba.id as assertion_id, db.id as badge_id
                FROM badge_assertions ba
                JOIN digital_badges db ON ba.badge_id = db.id
                WHERE {' AND '.join(conditions)}
                ORDER BY ba.issued_on DESC
            """
            rows = await self.db.fetch(query, recipient_id)

            results = []
            for row in rows:
                assertion = self._row_to_assertion(row)
                badge = self._row_to_badge(row)
                results.append((assertion, badge))

            return results

        except Exception as e:
            logger.error(f"Failed to get badges for recipient: {e}")
            raise CertificationDAOError(f"Failed to get badges: {e}") from e

    # =========================================================================
    # Share Operations
    # =========================================================================

    async def create_share(self, share: CertificateShare) -> CertificateShare:
        """
        WHAT: Records a certificate share action

        WHERE: Called when user shares certificate

        WHY: Tracks sharing for analytics

        Args:
            share: CertificateShare entity to create

        Returns:
            Created share record
        """
        try:
            query = """
                INSERT INTO certificate_shares (
                    id, certificate_id, share_platform,
                    share_url, external_id,
                    recipient_email, recipient_name
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, shared_at
            """
            result = await self.db.fetchrow(
                query,
                share.id, share.certificate_id, share.share_platform.value,
                share.share_url, share.external_id,
                share.recipient_email, share.recipient_name
            )
            share.shared_at = result['shared_at']
            return share

        except Exception as e:
            logger.error(f"Failed to create share: {e}")
            raise CertificationDAOError(f"Failed to create share: {e}") from e

    async def update_share_click(self, share_id: UUID) -> None:
        """
        WHAT: Updates share click count

        WHERE: Called when shared link is clicked

        WHY: Tracks engagement with shared certificates

        Args:
            share_id: UUID of share to update
        """
        try:
            query = """
                UPDATE certificate_shares SET
                    clicked_count = clicked_count + 1,
                    last_clicked_at = NOW()
                WHERE id = $1
            """
            await self.db.execute(query, share_id)

        except Exception as e:
            logger.error(f"Failed to update share click: {e}")
            raise CertificationDAOError(f"Failed to update share: {e}") from e

    # =========================================================================
    # Analytics Operations
    # =========================================================================

    async def get_organization_analytics(
        self,
        organization_id: UUID,
        period_start: date,
        period_end: date
    ) -> CertificateAnalytics:
        """
        WHAT: Computes certificate analytics for organization

        WHERE: Called for analytics dashboards

        WHY: Provides insights into certification activity

        Args:
            organization_id: UUID of organization
            period_start: Start of period
            period_end: End of period

        Returns:
            CertificateAnalytics with computed metrics
        """
        try:
            # Get certificate counts
            cert_query = """
                SELECT
                    COUNT(*) FILTER (WHERE issue_date BETWEEN $2 AND $3) as issued,
                    COUNT(*) FILTER (WHERE status = 'revoked' AND revoked_at BETWEEN $2 AND $3) as revoked,
                    COUNT(*) FILTER (WHERE status = 'expired' AND expiration_date BETWEEN $2 AND $3) as expired,
                    COUNT(*) FILTER (WHERE achievement_type = 'completion') as completion,
                    COUNT(*) FILTER (WHERE achievement_type = 'competency') as competency,
                    COUNT(*) FILTER (WHERE achievement_type = 'skill') as skill,
                    COUNT(*) FILTER (WHERE achievement_type = 'program') as program
                FROM issued_certificates
                WHERE organization_id = $1
            """
            cert_stats = await self.db.fetchrow(
                cert_query, organization_id, period_start, period_end
            )

            # Get verification counts
            verify_query = """
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT verifier_ip) as unique_verifiers,
                    COUNT(*) FILTER (WHERE verification_result = 'valid') as valid,
                    COUNT(*) FILTER (WHERE verification_result != 'valid') as failed
                FROM certificate_verifications cv
                JOIN issued_certificates ic ON cv.certificate_id = ic.id
                WHERE ic.organization_id = $1
                  AND cv.verified_at BETWEEN $2 AND $3
            """
            verify_stats = await self.db.fetchrow(
                verify_query, organization_id, period_start, period_end
            )

            # Get share counts
            share_query = """
                SELECT
                    COUNT(*) FILTER (WHERE share_platform = 'linkedin') as linkedin,
                    COUNT(*) FILTER (WHERE share_platform = 'email') as email,
                    COUNT(*) FILTER (WHERE share_platform = 'download') as downloads
                FROM certificate_shares cs
                JOIN issued_certificates ic ON cs.certificate_id = ic.id
                WHERE ic.organization_id = $1
                  AND cs.shared_at BETWEEN $2 AND $3
            """
            share_stats = await self.db.fetchrow(
                share_query, organization_id, period_start, period_end
            )

            return CertificateAnalytics(
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
                certificates_issued=cert_stats['issued'] or 0,
                certificates_revoked=cert_stats['revoked'] or 0,
                certificates_expired=cert_stats['expired'] or 0,
                total_verifications=verify_stats['total'] or 0,
                unique_verifiers=verify_stats['unique_verifiers'] or 0,
                valid_verifications=verify_stats['valid'] or 0,
                failed_verifications=verify_stats['failed'] or 0,
                linkedin_shares=share_stats['linkedin'] or 0,
                email_shares=share_stats['email'] or 0,
                download_count=share_stats['downloads'] or 0,
                completion_certificates=cert_stats['completion'] or 0,
                competency_certificates=cert_stats['competency'] or 0,
                skill_badges=cert_stats['skill'] or 0,
                program_certificates=cert_stats['program'] or 0
            )

        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            raise CertificationDAOError(f"Failed to get analytics: {e}") from e

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _row_to_template(self, row: Dict[str, Any]) -> CertificateTemplate:
        """Converts database row to CertificateTemplate entity"""
        design_config = DesignConfig(**row.get('design_config', {})) if row.get('design_config') else DesignConfig()

        return CertificateTemplate(
            id=row['id'],
            organization_id=row['organization_id'],
            name=row['name'],
            description=row.get('description'),
            template_type=TemplateType(row['template_type']),
            design_config=design_config,
            title_template=row['title_template'],
            subtitle_template=row.get('subtitle_template'),
            body_template=row.get('body_template'),
            footer_template=row.get('footer_template'),
            primary_color=row['primary_color'],
            secondary_color=row['secondary_color'],
            accent_color=row['accent_color'],
            font_family=row['font_family'],
            include_qr_code=row['include_qr_code'],
            include_verification_url=row['include_verification_url'],
            include_skills_list=row['include_skills_list'],
            include_competencies=row['include_competencies'],
            include_credits=row['include_credits'],
            include_grade=row['include_grade'],
            has_expiration=row['has_expiration'],
            validity_period_months=row.get('validity_period_months'),
            renewal_allowed=row['renewal_allowed'],
            is_active=row['is_active'],
            is_default=row['is_default'],
            created_at=row['created_at'],
            updated_at=row.get('updated_at'),
            created_by=row.get('created_by'),
            updated_by=row.get('updated_by')
        )

    def _row_to_certificate(self, row: Dict[str, Any]) -> IssuedCertificate:
        """Converts database row to IssuedCertificate entity"""
        skills = []
        for s in (row.get('skills_certified') or []):
            skills.append(SkillCertification(
                skill_id=UUID(s['skill_id']),
                skill_name=s['skill_name'],
                proficiency_level=s['proficiency_level']
            ))

        competencies = []
        for c in (row.get('competencies_certified') or []):
            competencies.append(CompetencyCertification(
                competency_id=UUID(c['competency_id']),
                competency_name=c['competency_name'],
                proficiency_level=c['proficiency_level']
            ))

        return IssuedCertificate(
            id=row['id'],
            certificate_number=row['certificate_number'],
            verification_code=row['verification_code'],
            template_id=row['template_id'],
            recipient_id=row['recipient_id'],
            course_id=row.get('course_id'),
            program_id=row.get('program_id'),
            organization_id=row['organization_id'],
            title=row['title'],
            recipient_name=row['recipient_name'],
            description=row.get('description'),
            achievement_type=AchievementType(row['achievement_type']),
            grade=row.get('grade'),
            score=row.get('score'),
            credits_earned=row.get('credits_earned'),
            completion_percentage=row.get('completion_percentage', Decimal("100.00")),
            skills_certified=skills,
            competencies_certified=competencies,
            issue_date=row['issue_date'],
            completion_date=row.get('completion_date'),
            expiration_date=row.get('expiration_date'),
            verification_url=row.get('verification_url'),
            qr_code_data=row.get('qr_code_data'),
            digital_signature=row.get('digital_signature'),
            signature_algorithm=row.get('signature_algorithm', 'SHA256withRSA'),
            pdf_url=row.get('pdf_url'),
            image_url=row.get('image_url'),
            thumbnail_url=row.get('thumbnail_url'),
            status=CertificateStatus(row['status']),
            revocation_reason=row.get('revocation_reason'),
            revoked_at=row.get('revoked_at'),
            revoked_by=row.get('revoked_by'),
            is_public=row.get('is_public', False),
            linkedin_shared=row.get('linkedin_shared', False),
            linkedin_share_id=row.get('linkedin_share_id'),
            metadata=row.get('metadata', {}),
            created_at=row['created_at'],
            updated_at=row.get('updated_at')
        )

    def _row_to_badge(self, row: Dict[str, Any]) -> DigitalBadge:
        """Converts database row to DigitalBadge entity"""
        alignment = []
        for a in (row.get('alignment') or []):
            alignment.append(BadgeAlignment(
                target_name=a['targetName'],
                target_url=a.get('targetUrl'),
                target_description=a.get('targetDescription'),
                target_framework=a.get('targetFramework'),
                target_code=a.get('targetCode')
            ))

        return DigitalBadge(
            id=row.get('badge_id', row['id']),
            organization_id=row['organization_id'],
            name=row['name'],
            description=row['description'],
            image_url=row['image_url'],
            criteria_url=row.get('criteria_url'),
            criteria_narrative=row.get('criteria_narrative'),
            badge_type=BadgeType(row['badge_type']),
            issuer_name=row['issuer_name'],
            issuer_url=row.get('issuer_url'),
            issuer_email=row.get('issuer_email'),
            issuer_image_url=row.get('issuer_image_url'),
            alignment=alignment,
            tags=row.get('tags', []),
            requirements=row.get('requirements', {}),
            is_active=row.get('is_active', True),
            is_stackable=row.get('is_stackable', False),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at')
        )

    def _row_to_assertion(self, row: Dict[str, Any]) -> BadgeAssertion:
        """Converts database row to BadgeAssertion entity"""
        evidence = []
        for e in (row.get('evidence') or []):
            evidence.append(BadgeEvidence(
                evidence_id=e['id'],
                narrative=e['narrative'],
                name=e.get('name'),
                description=e.get('description'),
                genre=e.get('genre'),
                audience=e.get('audience')
            ))

        return BadgeAssertion(
            id=row.get('assertion_id', row['id']),
            badge_id=row['badge_id'],
            recipient_id=row['recipient_id'],
            recipient_type=row.get('recipient_type', 'email'),
            recipient_identity=row['recipient_identity'],
            recipient_hashed=row.get('recipient_hashed', True),
            recipient_salt=row.get('recipient_salt'),
            evidence=evidence,
            verification_type=row.get('verification_type', 'hosted'),
            verification_url=row.get('verification_url'),
            issued_on=row.get('issued_on'),
            expires_at=row.get('expires_at'),
            status=row.get('status', 'active'),
            revoked=row.get('revoked', False),
            revocation_reason=row.get('revocation_reason'),
            created_at=row.get('created_at')
        )
