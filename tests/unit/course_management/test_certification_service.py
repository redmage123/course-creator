#!/usr/bin/env python3

"""
Certification Service Unit Tests

WHAT: Unit tests for CertificationService operations
WHERE: Tests service in course_management/application/services/certification_service.py
WHY: Ensures certification business logic works correctly

Author: Course Creator Platform
Version: 1.0.0
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Add service path
service_path = os.path.join(
    os.path.dirname(__file__),
    '../../../services/course-management'
)
sys.path.insert(0, os.path.abspath(service_path))

from course_management.domain.entities.certification import (
    CertificateTemplate,
    IssuedCertificate,
    CertificateVerification,
    DigitalBadge,
    BadgeAssertion,
    CertificateShare,
    CertificateAnalytics,
    TemplateType,
    AchievementType,
    CertificateStatus,
    BadgeType,
    VerificationMethod,
    VerificationResult,
    SharePlatform,
    DesignConfig
)
from course_management.application.services.certification_service import (
    CertificationService,
    CertificationServiceError,
    TemplateNotFoundError,
    CertificateNotFoundError,
    InvalidOperationError,
    VerificationFailedError
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_dao():
    """Creates mock DAO"""
    return AsyncMock()


@pytest.fixture
def service(mock_dao):
    """Creates service with mock DAO"""
    return CertificationService(
        dao=mock_dao,
        config={'base_url': 'https://test.example.com'}
    )


@pytest.fixture
def sample_template():
    """Creates sample template"""
    template = MagicMock()
    template.id = uuid4()
    template.organization_id = uuid4()
    template.name = "Test Template"
    template.template_type = TemplateType.COMPLETION
    template.design_config = DesignConfig()
    template.title_template = "Certificate of {{certificate_type}}"
    template.has_expiration = False
    template.validity_period_months = None
    template.render_title = MagicMock(return_value="Certificate of Completion")
    return template


@pytest.fixture
def sample_certificate():
    """Creates sample certificate"""
    cert = MagicMock()
    cert.id = uuid4()
    cert.certificate_number = "CERT-2025-000001-ABC1"
    cert.verification_code = "ABCD1234-EF56-GH78"
    cert.recipient_id = uuid4()
    cert.recipient_name = "John Doe"
    cert.title = "Certificate of Completion"
    cert.status = CertificateStatus.ACTIVE
    cert.issue_date = date.today()
    cert.expiration_date = None
    cert.digital_signature = None
    cert.is_valid = MagicMock(return_value=True)
    cert.check_expiration = MagicMock(return_value=False)
    return cert


# ============================================================================
# Template Management Tests
# ============================================================================


class TestTemplateManagement:
    """Tests for template CRUD operations"""

    @pytest.mark.asyncio
    async def test_create_template_success(self, service, mock_dao):
        """Tests successful template creation"""
        org_id = uuid4()
        created_template = MagicMock()
        created_template.id = uuid4()
        mock_dao.create_template = AsyncMock(return_value=created_template)

        result = await service.create_template(
            organization_id=org_id,
            name="Course Completion",
            template_type=TemplateType.COMPLETION
        )

        assert result.id == created_template.id
        mock_dao.create_template.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template_success(self, service, mock_dao, sample_template):
        """Tests retrieving template by ID"""
        mock_dao.get_template_by_id = AsyncMock(return_value=sample_template)

        result = await service.get_template(sample_template.id)

        assert result.id == sample_template.id
        mock_dao.get_template_by_id.assert_called_once_with(sample_template.id)

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, service, mock_dao):
        """Tests template not found error"""
        mock_dao.get_template_by_id = AsyncMock(return_value=None)

        with pytest.raises(TemplateNotFoundError):
            await service.get_template(uuid4())

    @pytest.mark.asyncio
    async def test_get_organization_templates(self, service, mock_dao, sample_template):
        """Tests getting templates for organization"""
        mock_dao.get_templates_by_organization = AsyncMock(
            return_value=[sample_template]
        )
        org_id = uuid4()

        result = await service.get_organization_templates(org_id)

        assert len(result) == 1
        mock_dao.get_templates_by_organization.assert_called_once()


# ============================================================================
# Certificate Issuance Tests
# ============================================================================


class TestCertificateIssuance:
    """Tests for certificate issuance"""

    @pytest.mark.asyncio
    async def test_issue_certificate_success(
        self, service, mock_dao, sample_template
    ):
        """Tests successful certificate issuance"""
        mock_dao.get_template_by_id = AsyncMock(return_value=sample_template)
        created_cert = MagicMock()
        created_cert.id = uuid4()
        created_cert.certificate_number = "CERT-2025-000001-XYZ1"
        mock_dao.create_certificate = AsyncMock(return_value=created_cert)

        result = await service.issue_certificate(
            template_id=sample_template.id,
            recipient_id=uuid4(),
            recipient_name="Jane Doe",
            organization_id=sample_template.organization_id
        )

        assert result.id == created_cert.id
        mock_dao.create_certificate.assert_called_once()

    @pytest.mark.asyncio
    async def test_issue_certificate_with_skills(
        self, service, mock_dao, sample_template
    ):
        """Tests issuing certificate with skills"""
        mock_dao.get_template_by_id = AsyncMock(return_value=sample_template)
        created_cert = MagicMock()
        mock_dao.create_certificate = AsyncMock(return_value=created_cert)

        result = await service.issue_certificate(
            template_id=sample_template.id,
            recipient_id=uuid4(),
            recipient_name="Jane Doe",
            organization_id=sample_template.organization_id,
            skills=[
                {"skill_id": str(uuid4()), "skill_name": "Python", "proficiency_level": "Expert"}
            ]
        )

        assert mock_dao.create_certificate.called

    @pytest.mark.asyncio
    async def test_issue_certificate_template_not_found(self, service, mock_dao):
        """Tests error when template not found"""
        mock_dao.get_template_by_id = AsyncMock(return_value=None)

        with pytest.raises(TemplateNotFoundError):
            await service.issue_certificate(
                template_id=uuid4(),
                recipient_id=uuid4(),
                recipient_name="Test",
                organization_id=uuid4()
            )

    @pytest.mark.asyncio
    async def test_get_certificate_success(
        self, service, mock_dao, sample_certificate
    ):
        """Tests retrieving certificate by ID"""
        mock_dao.get_certificate_by_id = AsyncMock(return_value=sample_certificate)

        result = await service.get_certificate(sample_certificate.id)

        assert result.id == sample_certificate.id

    @pytest.mark.asyncio
    async def test_get_certificate_not_found(self, service, mock_dao):
        """Tests certificate not found error"""
        mock_dao.get_certificate_by_id = AsyncMock(return_value=None)

        with pytest.raises(CertificateNotFoundError):
            await service.get_certificate(uuid4())

    @pytest.mark.asyncio
    async def test_get_recipient_certificates(
        self, service, mock_dao, sample_certificate
    ):
        """Tests getting certificates for recipient"""
        mock_dao.get_certificates_by_recipient = AsyncMock(
            return_value=([sample_certificate], 1)
        )

        certs, total = await service.get_recipient_certificates(
            sample_certificate.recipient_id
        )

        assert len(certs) == 1
        assert total == 1


# ============================================================================
# Certificate Revocation Tests
# ============================================================================


class TestCertificateRevocation:
    """Tests for certificate revocation"""

    @pytest.mark.asyncio
    async def test_revoke_certificate_success(
        self, service, mock_dao, sample_certificate
    ):
        """Tests successful certificate revocation"""
        mock_dao.get_certificate_by_id = AsyncMock(return_value=sample_certificate)
        revoked_cert = MagicMock()
        revoked_cert.status = CertificateStatus.REVOKED
        mock_dao.revoke_certificate = AsyncMock(return_value=revoked_cert)

        result = await service.revoke_certificate(
            certificate_id=sample_certificate.id,
            reason="Academic misconduct",
            revoked_by=uuid4()
        )

        assert result.status == CertificateStatus.REVOKED
        mock_dao.revoke_certificate.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_already_revoked_certificate(
        self, service, mock_dao, sample_certificate
    ):
        """Tests error when revoking already revoked certificate"""
        sample_certificate.status = CertificateStatus.REVOKED
        mock_dao.get_certificate_by_id = AsyncMock(return_value=sample_certificate)

        with pytest.raises(InvalidOperationError, match="already revoked"):
            await service.revoke_certificate(
                certificate_id=sample_certificate.id,
                reason="Test",
                revoked_by=uuid4()
            )


# ============================================================================
# Verification Tests
# ============================================================================


class TestVerification:
    """Tests for certificate verification"""

    @pytest.mark.asyncio
    async def test_verify_certificate_valid(
        self, service, mock_dao, sample_certificate
    ):
        """Tests verifying a valid certificate"""
        mock_dao.get_certificate_by_verification_code = AsyncMock(
            return_value=sample_certificate
        )
        mock_dao.log_verification = AsyncMock()

        cert, result = await service.verify_certificate(
            verification_code="ABCD1234-EF56-GH78"
        )

        assert result == VerificationResult.VALID
        assert cert.id == sample_certificate.id

    @pytest.mark.asyncio
    async def test_verify_certificate_not_found(self, service, mock_dao):
        """Tests verification when certificate not found"""
        mock_dao.get_certificate_by_verification_code = AsyncMock(return_value=None)

        cert, result = await service.verify_certificate(
            verification_code="INVALID-CODE"
        )

        assert result == VerificationResult.NOT_FOUND
        assert cert is None

    @pytest.mark.asyncio
    async def test_verify_certificate_revoked(
        self, service, mock_dao, sample_certificate
    ):
        """Tests verifying a revoked certificate"""
        sample_certificate.status = CertificateStatus.REVOKED
        mock_dao.get_certificate_by_verification_code = AsyncMock(
            return_value=sample_certificate
        )
        mock_dao.log_verification = AsyncMock()

        cert, result = await service.verify_certificate(
            verification_code="ABCD1234-EF56-GH78"
        )

        assert result == VerificationResult.REVOKED

    @pytest.mark.asyncio
    async def test_verify_certificate_expired(
        self, service, mock_dao, sample_certificate
    ):
        """Tests verifying an expired certificate"""
        sample_certificate.status = CertificateStatus.EXPIRED
        mock_dao.get_certificate_by_verification_code = AsyncMock(
            return_value=sample_certificate
        )
        mock_dao.log_verification = AsyncMock()

        cert, result = await service.verify_certificate(
            verification_code="ABCD1234-EF56-GH78"
        )

        assert result == VerificationResult.EXPIRED


# ============================================================================
# Badge Management Tests
# ============================================================================


class TestBadgeManagement:
    """Tests for digital badge operations"""

    @pytest.mark.asyncio
    async def test_create_badge_success(self, service, mock_dao):
        """Tests successful badge creation"""
        created_badge = MagicMock()
        created_badge.id = uuid4()
        mock_dao.create_badge = AsyncMock(return_value=created_badge)

        result = await service.create_badge(
            organization_id=uuid4(),
            name="Python Expert",
            description="Expert Python programming",
            image_url="https://example.com/badge.png",
            issuer_name="Test Organization"
        )

        assert result.id == created_badge.id
        mock_dao.create_badge.assert_called_once()

    @pytest.mark.asyncio
    async def test_issue_badge_success(self, service, mock_dao):
        """Tests successful badge issuance"""
        badge = MagicMock()
        badge.id = uuid4()
        mock_dao.get_badge_by_id = AsyncMock(return_value=badge)

        assertion = MagicMock()
        assertion.id = uuid4()
        mock_dao.create_badge_assertion = AsyncMock(return_value=assertion)

        result = await service.issue_badge(
            badge_id=badge.id,
            recipient_id=uuid4(),
            recipient_email="test@example.com"
        )

        assert result.id == assertion.id
        mock_dao.create_badge_assertion.assert_called_once()

    @pytest.mark.asyncio
    async def test_issue_badge_not_found(self, service, mock_dao):
        """Tests badge not found error"""
        mock_dao.get_badge_by_id = AsyncMock(return_value=None)

        with pytest.raises(CertificationServiceError, match="not found"):
            await service.issue_badge(
                badge_id=uuid4(),
                recipient_id=uuid4(),
                recipient_email="test@example.com"
            )

    @pytest.mark.asyncio
    async def test_get_recipient_badges(self, service, mock_dao):
        """Tests getting badges for recipient"""
        badge = MagicMock()
        assertion = MagicMock()
        mock_dao.get_badges_by_recipient = AsyncMock(
            return_value=[(assertion, badge)]
        )

        result = await service.get_recipient_badges(uuid4())

        assert len(result) == 1


# ============================================================================
# Sharing Tests
# ============================================================================


class TestSharing:
    """Tests for certificate sharing"""

    @pytest.mark.asyncio
    async def test_share_certificate_linkedin(
        self, service, mock_dao, sample_certificate
    ):
        """Tests sharing certificate to LinkedIn"""
        mock_dao.get_certificate_by_id = AsyncMock(return_value=sample_certificate)
        share = MagicMock()
        share.share_platform = SharePlatform.LINKEDIN
        mock_dao.create_share = AsyncMock(return_value=share)

        result = await service.share_certificate(
            certificate_id=sample_certificate.id,
            platform=SharePlatform.LINKEDIN
        )

        assert result.share_platform == SharePlatform.LINKEDIN
        mock_dao.create_share.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_certificate_email(
        self, service, mock_dao, sample_certificate
    ):
        """Tests sharing certificate via email"""
        mock_dao.get_certificate_by_id = AsyncMock(return_value=sample_certificate)
        share = MagicMock()
        share.share_platform = SharePlatform.EMAIL
        mock_dao.create_share = AsyncMock(return_value=share)

        result = await service.share_certificate(
            certificate_id=sample_certificate.id,
            platform=SharePlatform.EMAIL,
            recipient_email="hr@company.com",
            recipient_name="HR Manager"
        )

        assert result.share_platform == SharePlatform.EMAIL


# ============================================================================
# Analytics Tests
# ============================================================================


class TestAnalytics:
    """Tests for certification analytics"""

    @pytest.mark.asyncio
    async def test_get_analytics(self, service, mock_dao):
        """Tests getting organization analytics"""
        analytics = MagicMock()
        analytics.certificates_issued = 100
        analytics.total_verifications = 500
        mock_dao.get_organization_analytics = AsyncMock(return_value=analytics)

        result = await service.get_analytics(
            organization_id=uuid4(),
            period_start=date.today() - timedelta(days=30),
            period_end=date.today()
        )

        assert result.certificates_issued == 100
        assert result.total_verifications == 500


# ============================================================================
# Helper Method Tests
# ============================================================================


class TestHelperMethods:
    """Tests for service helper methods"""

    def test_generate_certificate_number(self, service):
        """Tests certificate number generation"""
        number = service._generate_certificate_number()

        assert number.startswith("CERT-")
        assert str(datetime.now().year) in number

    def test_generate_verification_code(self, service):
        """Tests verification code generation"""
        code = service._generate_verification_code()

        assert "-" in code
        assert len(code.split("-")) == 3

    def test_hash_email(self, service):
        """Tests email hashing for Open Badges"""
        hashed = service._hash_email("test@example.com")

        assert hashed.startswith("sha256$")
        assert len(hashed) > 64

    def test_generate_linkedin_share_url(self, service):
        """Tests LinkedIn share URL generation"""
        cert_id = uuid4()
        url = service._generate_linkedin_share_url(cert_id)

        assert "linkedin.com" in url
        assert str(cert_id) in url


# ============================================================================
# Integration Tests
# ============================================================================


class TestCertificationWorkflow:
    """Integration tests for certification workflows"""

    @pytest.mark.asyncio
    async def test_complete_certification_workflow(self, service, mock_dao):
        """Tests complete workflow: create template -> issue -> verify"""
        # Setup mocks
        template = MagicMock()
        template.id = uuid4()
        template.render_title = MagicMock(return_value="Certificate of Completion")
        template.has_expiration = False
        mock_dao.create_template = AsyncMock(return_value=template)
        mock_dao.get_template_by_id = AsyncMock(return_value=template)

        cert = MagicMock()
        cert.id = uuid4()
        cert.certificate_number = "CERT-2025-000001"
        cert.verification_code = "TEST-CODE-1234"
        cert.status = CertificateStatus.ACTIVE
        cert.is_valid = MagicMock(return_value=True)
        cert.check_expiration = MagicMock(return_value=False)
        cert.digital_signature = None
        mock_dao.create_certificate = AsyncMock(return_value=cert)
        mock_dao.get_certificate_by_verification_code = AsyncMock(return_value=cert)
        mock_dao.log_verification = AsyncMock()

        # 1. Create template
        created_template = await service.create_template(
            organization_id=uuid4(),
            name="Test Template"
        )
        assert created_template.id == template.id

        # 2. Issue certificate
        issued_cert = await service.issue_certificate(
            template_id=template.id,
            recipient_id=uuid4(),
            recipient_name="John Doe",
            organization_id=uuid4()
        )
        assert issued_cert.certificate_number == cert.certificate_number

        # 3. Verify certificate
        verified_cert, result = await service.verify_certificate(
            verification_code=cert.verification_code
        )
        assert result == VerificationResult.VALID
