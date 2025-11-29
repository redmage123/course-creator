#!/usr/bin/env python3

"""
Certification Service

WHAT: Application service for certification management including
template management, certificate issuance, verification, and badges.

WHERE: Used by API endpoints for certification operations

WHY: Orchestrates certification workflows with business logic validation,
QR code generation, digital signatures, and PDF rendering.

## Features:
- Certificate template management
- Certificate issuance with unique verification codes
- QR code generation for easy verification
- Digital signature support
- Badge issuance following Open Badges 2.0
- Verification API
- Analytics computation

Author: Course Creator Platform
Version: 1.0.0
"""

import hashlib
import secrets
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
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
    BadgeType,
    VerificationMethod,
    VerificationResult,
    SharePlatform,
    RenewalStatus,
    DesignConfig,
    SkillCertification,
    CompetencyCertification,
    BadgeEvidence
)

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class CertificationServiceError(Exception):
    """Base exception for certification service"""
    pass


class TemplateNotFoundError(CertificationServiceError):
    """Raised when template is not found"""
    pass


class CertificateNotFoundError(CertificationServiceError):
    """Raised when certificate is not found"""
    pass


class InvalidOperationError(CertificationServiceError):
    """Raised when operation is not allowed"""
    pass


class VerificationFailedError(CertificationServiceError):
    """Raised when verification fails"""
    pass


# ============================================================================
# Certification Service
# ============================================================================


class CertificationService:
    """
    WHAT: Application service for certification management

    WHERE: Called by API layer for all certification operations

    WHY: Encapsulates business logic for certificate issuance,
    verification, and management with proper validation.

    ## Capabilities:
    - Template CRUD with design configuration
    - Certificate issuance with auto-generated numbers
    - QR code generation for verification
    - Digital signature creation and verification
    - Badge management (Open Badges 2.0)
    - Public verification API
    - Analytics computation
    """

    def __init__(self, dao, config: Optional[Dict[str, Any]] = None):
        """
        WHAT: Initializes certification service

        WHERE: Called by dependency injection container

        WHY: Sets up service with required dependencies

        Args:
            dao: CertificationDAO instance
            config: Optional configuration
        """
        self.dao = dao
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'https://example.com')
        logger.info("CertificationService initialized")

    # =========================================================================
    # Template Management
    # =========================================================================

    async def create_template(
        self,
        organization_id: UUID,
        name: str,
        template_type: TemplateType = TemplateType.COMPLETION,
        description: Optional[str] = None,
        design_config: Optional[Dict[str, Any]] = None,
        title_template: str = "Certificate of {{certificate_type}}",
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> CertificateTemplate:
        """
        WHAT: Creates a new certificate template

        WHERE: Called when organization configures templates

        WHY: Enables customized certificate generation

        Args:
            organization_id: UUID of organization
            name: Template name
            template_type: Type of certificate
            description: Template description
            design_config: Visual design configuration
            title_template: Title with placeholders
            created_by: User creating template
            **kwargs: Additional template settings

        Returns:
            Created CertificateTemplate

        Raises:
            CertificationServiceError: If creation fails
        """
        try:
            config = DesignConfig(**design_config) if design_config else DesignConfig()

            template = CertificateTemplate(
                id=uuid4(),
                organization_id=organization_id,
                name=name,
                template_type=template_type,
                description=description,
                design_config=config,
                title_template=title_template,
                created_by=created_by,
                **kwargs
            )

            created = await self.dao.create_template(template)
            logger.info(f"Created template {created.id} for org {organization_id}")
            return created

        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            raise CertificationServiceError(f"Failed to create template: {e}") from e

    async def get_template(self, template_id: UUID) -> CertificateTemplate:
        """
        WHAT: Retrieves a template by ID

        WHERE: Called when issuing certificates or updating templates

        WHY: Fetches template configuration

        Args:
            template_id: UUID of template

        Returns:
            CertificateTemplate

        Raises:
            TemplateNotFoundError: If template doesn't exist
        """
        template = await self.dao.get_template_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(f"Template {template_id} not found")
        return template

    async def get_organization_templates(
        self,
        organization_id: UUID,
        template_type: Optional[TemplateType] = None,
        active_only: bool = True
    ) -> List[CertificateTemplate]:
        """
        WHAT: Gets templates for an organization

        WHERE: Called when listing available templates

        WHY: Shows organization's template options

        Args:
            organization_id: UUID of organization
            template_type: Optional type filter
            active_only: Whether to return only active

        Returns:
            List of matching templates
        """
        return await self.dao.get_templates_by_organization(
            organization_id, template_type, active_only
        )

    async def update_template(
        self,
        template_id: UUID,
        updated_by: UUID,
        **updates
    ) -> CertificateTemplate:
        """
        WHAT: Updates an existing template

        WHERE: Called when modifying template settings

        WHY: Enables template customization

        Args:
            template_id: UUID of template to update
            updated_by: User making changes
            **updates: Fields to update

        Returns:
            Updated template

        Raises:
            TemplateNotFoundError: If template doesn't exist
        """
        template = await self.get_template(template_id)

        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        template.updated_by = updated_by
        template.updated_at = datetime.utcnow()

        return await self.dao.update_template(template)

    # =========================================================================
    # Certificate Issuance
    # =========================================================================

    async def issue_certificate(
        self,
        template_id: UUID,
        recipient_id: UUID,
        recipient_name: str,
        organization_id: UUID,
        course_id: Optional[UUID] = None,
        program_id: Optional[UUID] = None,
        achievement_type: AchievementType = AchievementType.COMPLETION,
        grade: Optional[str] = None,
        score: Optional[Decimal] = None,
        credits_earned: Optional[Decimal] = None,
        skills: Optional[List[Dict[str, Any]]] = None,
        competencies: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> IssuedCertificate:
        """
        WHAT: Issues a new certificate to a recipient

        WHERE: Called when user completes requirements

        WHY: Creates official verifiable credential

        Args:
            template_id: UUID of template to use
            recipient_id: UUID of recipient
            recipient_name: Name to appear on certificate
            organization_id: UUID of issuing organization
            course_id: Optional course ID
            program_id: Optional program ID
            achievement_type: Type of achievement
            grade: Optional grade
            score: Optional numeric score
            credits_earned: Optional credits
            skills: Optional skills certified
            competencies: Optional competencies certified
            metadata: Additional metadata

        Returns:
            Issued certificate with verification code

        Raises:
            TemplateNotFoundError: If template doesn't exist
            CertificationServiceError: If issuance fails
        """
        try:
            # Get template
            template = await self.get_template(template_id)

            # Generate unique identifiers
            certificate_number = self._generate_certificate_number()
            verification_code = self._generate_verification_code()

            # Calculate expiration if template requires it
            expiration_date = None
            if template.has_expiration and template.validity_period_months:
                expiration_date = date.today() + timedelta(
                    days=template.validity_period_months * 30
                )

            # Build skills list
            skills_certified = []
            if skills:
                for s in skills:
                    skills_certified.append(SkillCertification(
                        skill_id=UUID(s['skill_id']),
                        skill_name=s['skill_name'],
                        proficiency_level=s.get('proficiency_level', 'Proficient')
                    ))

            # Build competencies list
            competencies_certified = []
            if competencies:
                for c in competencies:
                    competencies_certified.append(CompetencyCertification(
                        competency_id=UUID(c['competency_id']),
                        competency_name=c['competency_name'],
                        proficiency_level=c.get('proficiency_level', 'Competent')
                    ))

            # Render title
            title = template.render_title({
                "certificate_type": achievement_type.value.title(),
                "course_name": metadata.get('course_name', '') if metadata else ''
            })

            # Create certificate
            certificate = IssuedCertificate(
                id=uuid4(),
                certificate_number=certificate_number,
                verification_code=verification_code,
                template_id=template_id,
                recipient_id=recipient_id,
                recipient_name=recipient_name,
                organization_id=organization_id,
                course_id=course_id,
                program_id=program_id,
                title=title,
                achievement_type=achievement_type,
                grade=grade,
                score=score,
                credits_earned=credits_earned,
                skills_certified=skills_certified,
                competencies_certified=competencies_certified,
                issue_date=date.today(),
                completion_date=date.today(),
                expiration_date=expiration_date,
                verification_url=f"{self.base_url}/verify/{verification_code}",
                metadata=metadata or {}
            )

            # Generate QR code data
            certificate.qr_code_data = self._generate_qr_data(verification_code)

            # Generate digital signature
            certificate.digital_signature = self._generate_signature(certificate)

            # Save certificate
            created = await self.dao.create_certificate(certificate)
            logger.info(f"Issued certificate {certificate_number} to {recipient_name}")

            return created

        except TemplateNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to issue certificate: {e}")
            raise CertificationServiceError(f"Failed to issue certificate: {e}") from e

    async def get_certificate(self, certificate_id: UUID) -> IssuedCertificate:
        """
        WHAT: Retrieves certificate by ID

        WHERE: Called when viewing certificate details

        WHY: Fetches complete certificate data

        Args:
            certificate_id: UUID of certificate

        Returns:
            IssuedCertificate

        Raises:
            CertificateNotFoundError: If not found
        """
        certificate = await self.dao.get_certificate_by_id(certificate_id)
        if not certificate:
            raise CertificateNotFoundError(f"Certificate {certificate_id} not found")
        return certificate

    async def get_recipient_certificates(
        self,
        recipient_id: UUID,
        status_filter: Optional[CertificateStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[IssuedCertificate], int]:
        """
        WHAT: Gets all certificates for a recipient

        WHERE: Called when viewing user's credentials

        WHY: Shows user's earned certificates

        Args:
            recipient_id: UUID of recipient
            status_filter: Optional status filter
            limit: Max results
            offset: Pagination offset

        Returns:
            Tuple of (certificates, total_count)
        """
        return await self.dao.get_certificates_by_recipient(
            recipient_id, status_filter, limit, offset
        )

    async def revoke_certificate(
        self,
        certificate_id: UUID,
        reason: str,
        revoked_by: UUID
    ) -> IssuedCertificate:
        """
        WHAT: Revokes an issued certificate

        WHERE: Called for administrative action

        WHY: Invalidates certificate due to misconduct/error

        Args:
            certificate_id: UUID of certificate
            reason: Reason for revocation
            revoked_by: User performing revocation

        Returns:
            Updated certificate

        Raises:
            CertificateNotFoundError: If not found
            InvalidOperationError: If already revoked
        """
        certificate = await self.get_certificate(certificate_id)

        if certificate.status == CertificateStatus.REVOKED:
            raise InvalidOperationError("Certificate is already revoked")

        revoked = await self.dao.revoke_certificate(
            certificate_id, reason, revoked_by
        )
        logger.info(f"Revoked certificate {certificate_id}: {reason}")
        return revoked

    # =========================================================================
    # Verification
    # =========================================================================

    async def verify_certificate(
        self,
        verification_code: str,
        method: VerificationMethod = VerificationMethod.CODE,
        verifier_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[IssuedCertificate, VerificationResult]:
        """
        WHAT: Verifies a certificate by code

        WHERE: Called by public verification API

        WHY: Enables third parties to validate credentials

        Args:
            verification_code: Unique verification code
            method: How verification was initiated
            verifier_info: Optional verifier information

        Returns:
            Tuple of (certificate, verification_result)
        """
        try:
            certificate = await self.dao.get_certificate_by_verification_code(
                verification_code
            )

            if not certificate:
                result = VerificationResult.NOT_FOUND
                # Log failed verification
                await self._log_verification(
                    None, method, result, verifier_info
                )
                return (None, result)

            # Check status
            if certificate.status == CertificateStatus.REVOKED:
                result = VerificationResult.REVOKED
            elif certificate.status == CertificateStatus.EXPIRED:
                result = VerificationResult.EXPIRED
            elif not certificate.is_valid():
                # Check expiration
                if certificate.check_expiration():
                    result = VerificationResult.EXPIRED
                else:
                    result = VerificationResult.INVALID
            else:
                # Verify digital signature
                if self._verify_signature(certificate):
                    result = VerificationResult.VALID
                else:
                    result = VerificationResult.INVALID

            # Log verification
            await self._log_verification(
                certificate.id, method, result, verifier_info
            )

            logger.info(f"Verified certificate {certificate.certificate_number}: {result.value}")
            return (certificate, result)

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            raise VerificationFailedError(f"Verification failed: {e}") from e

    async def _log_verification(
        self,
        certificate_id: Optional[UUID],
        method: VerificationMethod,
        result: VerificationResult,
        verifier_info: Optional[Dict[str, Any]]
    ) -> None:
        """Logs a verification attempt"""
        if not certificate_id:
            return

        verification = CertificateVerification(
            id=uuid4(),
            certificate_id=certificate_id,
            verification_method=method,
            verification_result=result,
            verifier_ip=verifier_info.get('ip') if verifier_info else None,
            verifier_user_agent=verifier_info.get('user_agent') if verifier_info else None,
            verifier_organization=verifier_info.get('organization') if verifier_info else None,
            verifier_email=verifier_info.get('email') if verifier_info else None,
            country_code=verifier_info.get('country') if verifier_info else None
        )
        await self.dao.log_verification(verification)

    # =========================================================================
    # Badge Management
    # =========================================================================

    async def create_badge(
        self,
        organization_id: UUID,
        name: str,
        description: str,
        image_url: str,
        issuer_name: str,
        badge_type: BadgeType = BadgeType.ACHIEVEMENT,
        criteria_narrative: Optional[str] = None,
        tags: Optional[List[str]] = None,
        requirements: Optional[Dict[str, Any]] = None
    ) -> DigitalBadge:
        """
        WHAT: Creates a digital badge definition

        WHERE: Called when organization defines badges

        WHY: Establishes badge criteria and appearance

        Args:
            organization_id: UUID of organization
            name: Badge name
            description: What badge represents
            image_url: Badge image URL
            issuer_name: Name of issuing organization
            badge_type: Type of badge
            criteria_narrative: How to earn badge
            tags: Discovery tags
            requirements: Badge requirements

        Returns:
            Created DigitalBadge
        """
        try:
            badge = DigitalBadge(
                id=uuid4(),
                organization_id=organization_id,
                name=name,
                description=description,
                image_url=image_url,
                issuer_name=issuer_name,
                badge_type=badge_type,
                criteria_narrative=criteria_narrative,
                tags=tags or [],
                requirements=requirements or {}
            )

            created = await self.dao.create_badge(badge)
            logger.info(f"Created badge {created.id}: {name}")
            return created

        except Exception as e:
            logger.error(f"Failed to create badge: {e}")
            raise CertificationServiceError(f"Failed to create badge: {e}") from e

    async def issue_badge(
        self,
        badge_id: UUID,
        recipient_id: UUID,
        recipient_email: str,
        evidence: Optional[List[Dict[str, Any]]] = None
    ) -> BadgeAssertion:
        """
        WHAT: Issues a badge to a recipient

        WHERE: Called when user earns badge

        WHY: Creates verifiable badge assertion

        Args:
            badge_id: UUID of badge to issue
            recipient_id: UUID of recipient
            recipient_email: Email for hashing
            evidence: Optional evidence of achievement

        Returns:
            BadgeAssertion

        Raises:
            BadgeNotFoundError: If badge doesn't exist
        """
        try:
            badge = await self.dao.get_badge_by_id(badge_id)
            if not badge:
                raise CertificationServiceError(f"Badge {badge_id} not found")

            # Hash recipient email for privacy
            hashed_identity = self._hash_email(recipient_email)

            # Build evidence list
            badge_evidence = []
            if evidence:
                for e in evidence:
                    badge_evidence.append(BadgeEvidence(
                        evidence_id=e.get('id', str(uuid4())),
                        narrative=e['narrative'],
                        name=e.get('name'),
                        description=e.get('description')
                    ))

            assertion = BadgeAssertion(
                id=uuid4(),
                badge_id=badge_id,
                recipient_id=recipient_id,
                recipient_identity=hashed_identity,
                recipient_hashed=True,
                evidence=badge_evidence,
                verification_url=f"{self.base_url}/badges/{badge_id}/assertions"
            )

            created = await self.dao.create_badge_assertion(assertion)
            logger.info(f"Issued badge {badge_id} to {recipient_id}")
            return created

        except Exception as e:
            logger.error(f"Failed to issue badge: {e}")
            raise CertificationServiceError(f"Failed to issue badge: {e}") from e

    async def get_recipient_badges(
        self,
        recipient_id: UUID,
        active_only: bool = True
    ) -> List[Tuple[BadgeAssertion, DigitalBadge]]:
        """
        WHAT: Gets badges earned by a recipient

        WHERE: Called when viewing user's badges

        WHY: Shows badge portfolio

        Args:
            recipient_id: UUID of recipient
            active_only: Exclude revoked badges

        Returns:
            List of (assertion, badge) tuples
        """
        return await self.dao.get_badges_by_recipient(recipient_id, active_only)

    # =========================================================================
    # Sharing
    # =========================================================================

    async def share_certificate(
        self,
        certificate_id: UUID,
        platform: SharePlatform,
        recipient_email: Optional[str] = None,
        recipient_name: Optional[str] = None
    ) -> CertificateShare:
        """
        WHAT: Records certificate sharing

        WHERE: Called when user shares certificate

        WHY: Tracks sharing for analytics

        Args:
            certificate_id: UUID of certificate
            platform: Where being shared
            recipient_email: For email shares
            recipient_name: For email shares

        Returns:
            CertificateShare record
        """
        try:
            # Verify certificate exists
            await self.get_certificate(certificate_id)

            share = CertificateShare(
                id=uuid4(),
                certificate_id=certificate_id,
                share_platform=platform,
                recipient_email=recipient_email,
                recipient_name=recipient_name
            )

            # Generate share URL based on platform
            if platform == SharePlatform.LINKEDIN:
                share.share_url = self._generate_linkedin_share_url(certificate_id)
            elif platform == SharePlatform.LINK:
                share.share_url = f"{self.base_url}/certificates/{certificate_id}"

            created = await self.dao.create_share(share)
            logger.info(f"Shared certificate {certificate_id} on {platform.value}")
            return created

        except CertificateNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to share certificate: {e}")
            raise CertificationServiceError(f"Failed to share certificate: {e}") from e

    # =========================================================================
    # Analytics
    # =========================================================================

    async def get_analytics(
        self,
        organization_id: UUID,
        period_start: date,
        period_end: date
    ) -> CertificateAnalytics:
        """
        WHAT: Gets certification analytics for organization

        WHERE: Called for analytics dashboards

        WHY: Provides insights into certification activity

        Args:
            organization_id: UUID of organization
            period_start: Start of period
            period_end: End of period

        Returns:
            CertificateAnalytics with computed metrics
        """
        return await self.dao.get_organization_analytics(
            organization_id, period_start, period_end
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _generate_certificate_number(self) -> str:
        """Generates unique certificate number"""
        year = datetime.now().year
        random_part = secrets.token_hex(3).upper()
        seq = secrets.randbelow(999999)
        return f"CERT-{year}-{seq:06d}-{random_part}"

    def _generate_verification_code(self) -> str:
        """Generates unique verification code"""
        parts = [secrets.token_hex(4).upper() for _ in range(3)]
        return "-".join(parts)

    def _generate_qr_data(self, verification_code: str) -> str:
        """Generates QR code data for verification URL"""
        # In production, generate actual QR code image
        return f"{self.base_url}/verify/{verification_code}"

    def _generate_signature(self, certificate: IssuedCertificate) -> str:
        """Generates digital signature for certificate"""
        # In production, use proper cryptographic signing
        data = f"{certificate.certificate_number}:{certificate.recipient_id}:{certificate.issue_date}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _verify_signature(self, certificate: IssuedCertificate) -> bool:
        """Verifies certificate digital signature"""
        if not certificate.digital_signature:
            return True  # No signature to verify

        expected = self._generate_signature(certificate)
        return certificate.digital_signature == expected

    def _hash_email(self, email: str) -> str:
        """Hashes email for Open Badges recipient identity"""
        return f"sha256${hashlib.sha256(email.lower().encode()).hexdigest()}"

    def _generate_linkedin_share_url(self, certificate_id: UUID) -> str:
        """Generates LinkedIn share URL"""
        cert_url = f"{self.base_url}/certificates/{certificate_id}"
        return f"https://www.linkedin.com/sharing/share-offsite/?url={cert_url}"
