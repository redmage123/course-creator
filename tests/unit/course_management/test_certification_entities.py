#!/usr/bin/env python3

"""
Certification Domain Entity Tests

WHAT: Unit tests for certification domain entities including templates,
issued certificates, digital badges, and verification.

WHERE: Tests entities in course_management/domain/entities/certification.py

WHY: Ensures certification entities correctly handle validation,
business logic, and data transformations.

Author: Course Creator Platform
Version: 1.0.0
"""

import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4
import pytest

# Add service path
service_path = os.path.join(
    os.path.dirname(__file__),
    '../../../services/course-management'
)
sys.path.insert(0, os.path.abspath(service_path))

from course_management.domain.entities.certification import (
    # Enums
    TemplateType,
    AchievementType,
    CertificateStatus,
    SignatureStyle,
    BadgeType,
    VerificationMethod,
    VerificationResult,
    SharePlatform,
    RenewalStatus,
    # Value Objects
    DesignConfig,
    SkillCertification,
    CompetencyCertification,
    BadgeAlignment,
    BadgeEvidence,
    # Entities
    CertificateTemplate,
    CertificateSignatory,
    IssuedCertificate,
    CertificateVerification,
    DigitalBadge,
    BadgeAssertion,
    CertificateShare,
    CertificateRenewal,
    CertificateAnalytics
)


# ============================================================================
# Enumeration Tests
# ============================================================================


class TestTemplateType:
    """Tests for TemplateType enumeration"""

    def test_all_template_types_defined(self):
        """Verifies all expected template types exist"""
        expected = ['COMPLETION', 'COMPETENCY', 'SKILL', 'PROGRAM', 'PROFESSIONAL']
        actual = [t.name for t in TemplateType]
        assert set(actual) == set(expected)

    def test_template_type_values(self):
        """Verifies template type values are lowercase"""
        assert TemplateType.COMPLETION.value == "completion"
        assert TemplateType.PROFESSIONAL.value == "professional"


class TestAchievementType:
    """Tests for AchievementType enumeration"""

    def test_all_achievement_types_defined(self):
        """Verifies all expected achievement types exist"""
        expected = ['COMPLETION', 'COMPETENCY', 'SKILL', 'PROGRAM', 'HONOR', 'DISTINCTION']
        actual = [t.name for t in AchievementType]
        assert set(actual) == set(expected)

    def test_honor_and_distinction_for_high_performers(self):
        """Verifies honor and distinction types for high performers"""
        assert AchievementType.HONOR.value == "honor"
        assert AchievementType.DISTINCTION.value == "distinction"


class TestCertificateStatus:
    """Tests for CertificateStatus enumeration"""

    def test_all_statuses_defined(self):
        """Verifies all certificate statuses exist"""
        expected = ['ACTIVE', 'REVOKED', 'EXPIRED', 'SUPERSEDED', 'PENDING']
        actual = [s.name for s in CertificateStatus]
        assert set(actual) == set(expected)


class TestVerificationResult:
    """Tests for VerificationResult enumeration"""

    def test_all_verification_results_defined(self):
        """Verifies all verification results exist"""
        expected = ['VALID', 'REVOKED', 'EXPIRED', 'NOT_FOUND', 'INVALID']
        actual = [r.name for r in VerificationResult]
        assert set(actual) == set(expected)


# ============================================================================
# Value Object Tests
# ============================================================================


class TestDesignConfig:
    """Tests for DesignConfig value object"""

    def test_default_design_config(self):
        """Tests default design configuration"""
        config = DesignConfig()
        assert config.background_image is None
        assert "x" in config.logo_position
        assert "font" in config.title_style
        assert config.border_style["type"] == "double"

    def test_design_config_to_dict(self):
        """Tests conversion to dictionary"""
        config = DesignConfig(
            background_image="https://example.com/bg.png"
        )
        result = config.to_dict()
        assert result["background_image"] == "https://example.com/bg.png"
        assert "logo_position" in result
        assert "title_style" in result

    def test_design_config_immutable(self):
        """Verifies design config is immutable (frozen)"""
        config = DesignConfig()
        with pytest.raises(AttributeError):
            config.background_image = "new_value"


class TestSkillCertification:
    """Tests for SkillCertification value object"""

    def test_skill_certification_creation(self):
        """Tests creating a skill certification record"""
        skill = SkillCertification(
            skill_id=uuid4(),
            skill_name="Python Programming",
            proficiency_level="Expert"
        )
        assert skill.skill_name == "Python Programming"
        assert skill.proficiency_level == "Expert"

    def test_skill_certification_immutable(self):
        """Verifies skill certification is immutable"""
        skill = SkillCertification(
            skill_id=uuid4(),
            skill_name="Test",
            proficiency_level="Basic"
        )
        with pytest.raises(AttributeError):
            skill.skill_name = "Changed"


class TestBadgeAlignment:
    """Tests for BadgeAlignment value object"""

    def test_badge_alignment_to_dict(self):
        """Tests conversion to Open Badges format"""
        alignment = BadgeAlignment(
            target_name="Python Fundamentals",
            target_url="https://example.com/standards/python",
            target_framework="Internal Skills Framework",
            target_code="PY-001"
        )
        result = alignment.to_dict()
        assert result["targetName"] == "Python Fundamentals"
        assert result["targetCode"] == "PY-001"


class TestBadgeEvidence:
    """Tests for BadgeEvidence value object"""

    def test_badge_evidence_to_dict(self):
        """Tests conversion to Open Badges format"""
        evidence = BadgeEvidence(
            evidence_id="ev-123",
            narrative="Completed final project with 95% score",
            name="Final Project",
            genre="project"
        )
        result = evidence.to_dict()
        assert result["id"] == "ev-123"
        assert result["narrative"].startswith("Completed")


# ============================================================================
# Certificate Template Tests
# ============================================================================


class TestCertificateTemplate:
    """Tests for CertificateTemplate entity"""

    def test_template_creation_success(self):
        """Tests successful template creation"""
        template = CertificateTemplate(
            name="Course Completion Certificate",
            organization_id=uuid4(),
            template_type=TemplateType.COMPLETION
        )
        assert template.name == "Course Completion Certificate"
        assert template.template_type == TemplateType.COMPLETION
        assert template.is_active is True

    def test_template_requires_name(self):
        """Tests that template name is required"""
        with pytest.raises(ValueError, match="name is required"):
            CertificateTemplate(name="")

    def test_template_name_max_length(self):
        """Tests template name maximum length"""
        with pytest.raises(ValueError, match="255 characters"):
            CertificateTemplate(name="x" * 256)

    def test_template_validates_primary_color(self):
        """Tests primary color validation"""
        with pytest.raises(ValueError, match="Invalid primary color"):
            CertificateTemplate(
                name="Test",
                primary_color="invalid"
            )

    def test_template_accepts_valid_colors(self):
        """Tests valid hex color acceptance"""
        template = CertificateTemplate(
            name="Test",
            primary_color="#FF5733",
            secondary_color="#33FF57",
            accent_color="#5733FF"
        )
        assert template.primary_color == "#FF5733"

    def test_template_default_settings(self):
        """Tests default template settings"""
        template = CertificateTemplate(name="Test")
        assert template.include_qr_code is True
        assert template.include_verification_url is True
        assert template.has_expiration is False
        assert template.renewal_allowed is True

    def test_template_render_title(self):
        """Tests title rendering with variables"""
        template = CertificateTemplate(
            name="Test",
            title_template="Certificate of {{certificate_type}} in {{course_name}}"
        )
        result = template.render_title({
            "certificate_type": "Completion",
            "course_name": "Python 101"
        })
        assert result == "Certificate of Completion in Python 101"

    def test_template_design_config_default(self):
        """Tests default design configuration"""
        template = CertificateTemplate(name="Test")
        assert isinstance(template.design_config, DesignConfig)


# ============================================================================
# Certificate Signatory Tests
# ============================================================================


class TestCertificateSignatory:
    """Tests for CertificateSignatory entity"""

    def test_signatory_creation_success(self):
        """Tests successful signatory creation"""
        signatory = CertificateSignatory(
            name="Dr. Jane Smith",
            title="Director of Education",
            organization_id=uuid4()
        )
        assert signatory.name == "Dr. Jane Smith"
        assert signatory.title == "Director of Education"

    def test_signatory_requires_name(self):
        """Tests that signatory name is required"""
        with pytest.raises(ValueError, match="name is required"):
            CertificateSignatory(name="", title="Director")

    def test_signatory_requires_title(self):
        """Tests that signatory title is required"""
        with pytest.raises(ValueError, match="title is required"):
            CertificateSignatory(name="Jane Smith", title="")

    def test_signatory_display_name_override(self):
        """Tests display name override"""
        signatory = CertificateSignatory(
            name="Dr. Jane Elizabeth Smith",
            title="Director",
            display_name="Dr. Jane Smith"
        )
        assert signatory.get_display_name() == "Dr. Jane Smith"

    def test_signatory_display_name_default(self):
        """Tests default display name"""
        signatory = CertificateSignatory(
            name="Jane Smith",
            title="Director"
        )
        assert signatory.get_display_name() == "Jane Smith"

    def test_signatory_signature_styles(self):
        """Tests different signature styles"""
        for style in SignatureStyle:
            signatory = CertificateSignatory(
                name="Test",
                title="Test",
                signature_style=style
            )
            assert signatory.signature_style == style


# ============================================================================
# Issued Certificate Tests
# ============================================================================


class TestIssuedCertificate:
    """Tests for IssuedCertificate entity"""

    @pytest.fixture
    def valid_certificate(self):
        """Creates a valid certificate for testing"""
        return IssuedCertificate(
            certificate_number="CERT-2025-000001-ABC1",
            verification_code="ABC12345-DEF4-GHI5",
            title="Certificate of Completion",
            recipient_name="John Doe",
            recipient_id=uuid4(),
            organization_id=uuid4(),
            template_id=uuid4()
        )

    def test_certificate_creation_success(self, valid_certificate):
        """Tests successful certificate creation"""
        assert valid_certificate.title == "Certificate of Completion"
        assert valid_certificate.recipient_name == "John Doe"
        assert valid_certificate.status == CertificateStatus.ACTIVE

    def test_certificate_requires_title(self):
        """Tests that certificate title is required"""
        with pytest.raises(ValueError, match="title is required"):
            IssuedCertificate(
                title="",
                recipient_name="John Doe"
            )

    def test_certificate_requires_recipient_name(self):
        """Tests that recipient name is required"""
        with pytest.raises(ValueError, match="Recipient name is required"):
            IssuedCertificate(
                title="Certificate",
                recipient_name=""
            )

    def test_certificate_is_valid_when_active(self, valid_certificate):
        """Tests is_valid returns True for active certificate"""
        assert valid_certificate.is_valid() is True

    def test_certificate_is_valid_when_revoked(self, valid_certificate):
        """Tests is_valid returns False for revoked certificate"""
        valid_certificate.status = CertificateStatus.REVOKED
        assert valid_certificate.is_valid() is False

    def test_certificate_is_valid_when_expired(self, valid_certificate):
        """Tests is_valid returns False for expired certificate"""
        valid_certificate.expiration_date = date.today() - timedelta(days=1)
        assert valid_certificate.is_valid() is False

    def test_certificate_revoke(self, valid_certificate):
        """Tests certificate revocation"""
        revoker_id = uuid4()
        valid_certificate.revoke("Academic misconduct", revoker_id)

        assert valid_certificate.status == CertificateStatus.REVOKED
        assert valid_certificate.revocation_reason == "Academic misconduct"
        assert valid_certificate.revoked_by == revoker_id
        assert valid_certificate.revoked_at is not None

    def test_certificate_check_expiration(self, valid_certificate):
        """Tests expiration check and status update"""
        valid_certificate.expiration_date = date.today() - timedelta(days=1)
        result = valid_certificate.check_expiration()

        assert result is True
        assert valid_certificate.status == CertificateStatus.EXPIRED

    def test_certificate_check_expiration_not_expired(self, valid_certificate):
        """Tests expiration check when not expired"""
        valid_certificate.expiration_date = date.today() + timedelta(days=30)
        result = valid_certificate.check_expiration()

        assert result is False
        assert valid_certificate.status == CertificateStatus.ACTIVE

    def test_certificate_skills_list(self, valid_certificate):
        """Tests certificate with skills list"""
        valid_certificate.skills_certified = [
            SkillCertification(uuid4(), "Python", "Advanced"),
            SkillCertification(uuid4(), "Docker", "Intermediate")
        ]
        assert len(valid_certificate.skills_certified) == 2

    def test_certificate_default_completion_percentage(self):
        """Tests default completion percentage"""
        cert = IssuedCertificate(
            title="Test",
            recipient_name="Test User"
        )
        assert cert.completion_percentage == Decimal("100.00")


# ============================================================================
# Certificate Verification Tests
# ============================================================================


class TestCertificateVerification:
    """Tests for CertificateVerification entity"""

    def test_verification_creation(self):
        """Tests verification record creation"""
        verification = CertificateVerification(
            certificate_id=uuid4(),
            verification_method=VerificationMethod.QR,
            verification_result=VerificationResult.VALID,
            verifier_organization="ACME Corp"
        )
        assert verification.verification_method == VerificationMethod.QR
        assert verification.verification_result == VerificationResult.VALID

    def test_verification_all_methods(self):
        """Tests all verification methods"""
        for method in VerificationMethod:
            verification = CertificateVerification(
                certificate_id=uuid4(),
                verification_method=method
            )
            assert verification.verification_method == method

    def test_verification_all_results(self):
        """Tests all verification results"""
        for result in VerificationResult:
            verification = CertificateVerification(
                certificate_id=uuid4(),
                verification_result=result
            )
            assert verification.verification_result == result


# ============================================================================
# Digital Badge Tests
# ============================================================================


class TestDigitalBadge:
    """Tests for DigitalBadge entity"""

    @pytest.fixture
    def valid_badge(self):
        """Creates a valid badge for testing"""
        return DigitalBadge(
            name="Python Expert",
            description="Awarded for demonstrating expert-level Python skills",
            image_url="https://example.com/badges/python-expert.png",
            issuer_name="Course Creator Platform",
            organization_id=uuid4()
        )

    def test_badge_creation_success(self, valid_badge):
        """Tests successful badge creation"""
        assert valid_badge.name == "Python Expert"
        assert valid_badge.badge_type == BadgeType.ACHIEVEMENT

    def test_badge_requires_name(self):
        """Tests that badge name is required"""
        with pytest.raises(ValueError, match="name is required"):
            DigitalBadge(
                name="",
                description="Test",
                image_url="https://example.com/badge.png",
                issuer_name="Test"
            )

    def test_badge_requires_description(self):
        """Tests that badge description is required"""
        with pytest.raises(ValueError, match="description is required"):
            DigitalBadge(
                name="Test",
                description="",
                image_url="https://example.com/badge.png",
                issuer_name="Test"
            )

    def test_badge_requires_image_url(self):
        """Tests that badge image URL is required"""
        with pytest.raises(ValueError, match="image URL is required"):
            DigitalBadge(
                name="Test",
                description="Test description",
                image_url="",
                issuer_name="Test"
            )

    def test_badge_requires_issuer_name(self):
        """Tests that issuer name is required"""
        with pytest.raises(ValueError, match="Issuer name is required"):
            DigitalBadge(
                name="Test",
                description="Test description",
                image_url="https://example.com/badge.png",
                issuer_name=""
            )

    def test_badge_to_open_badge_class(self, valid_badge):
        """Tests conversion to Open Badges 2.0 BadgeClass"""
        result = valid_badge.to_open_badge_class()

        assert result["@context"] == "https://w3id.org/openbadges/v2"
        assert result["type"] == "BadgeClass"
        assert result["name"] == "Python Expert"
        assert result["issuer"]["name"] == "Course Creator Platform"

    def test_badge_with_alignment(self, valid_badge):
        """Tests badge with external alignment"""
        valid_badge.alignment = [
            BadgeAlignment(
                target_name="Python Programming",
                target_framework="Skills Framework"
            )
        ]
        result = valid_badge.to_open_badge_class()
        assert "alignment" in result
        assert len(result["alignment"]) == 1

    def test_badge_all_types(self):
        """Tests all badge types"""
        for badge_type in BadgeType:
            badge = DigitalBadge(
                name="Test",
                description="Test",
                image_url="https://example.com/badge.png",
                issuer_name="Test",
                badge_type=badge_type
            )
            assert badge.badge_type == badge_type


# ============================================================================
# Badge Assertion Tests
# ============================================================================


class TestBadgeAssertion:
    """Tests for BadgeAssertion entity"""

    @pytest.fixture
    def valid_assertion(self):
        """Creates a valid assertion for testing"""
        return BadgeAssertion(
            badge_id=uuid4(),
            recipient_id=uuid4(),
            recipient_identity="sha256$abc123"
        )

    def test_assertion_creation_success(self, valid_assertion):
        """Tests successful assertion creation"""
        assert valid_assertion.recipient_hashed is True
        assert valid_assertion.status == "active"

    def test_assertion_requires_identity(self):
        """Tests that recipient identity is required"""
        with pytest.raises(ValueError, match="identity is required"):
            BadgeAssertion(
                badge_id=uuid4(),
                recipient_id=uuid4(),
                recipient_identity=""
            )

    def test_assertion_is_valid_when_active(self, valid_assertion):
        """Tests is_valid returns True for active assertion"""
        assert valid_assertion.is_valid() is True

    def test_assertion_is_valid_when_revoked(self, valid_assertion):
        """Tests is_valid returns False when revoked"""
        valid_assertion.revoked = True
        assert valid_assertion.is_valid() is False

    def test_assertion_is_valid_when_expired(self, valid_assertion):
        """Tests is_valid returns False when expired"""
        valid_assertion.expires_at = datetime.utcnow() - timedelta(days=1)
        assert valid_assertion.is_valid() is False

    def test_assertion_to_open_badge(self, valid_assertion):
        """Tests conversion to Open Badges 2.0 Assertion"""
        badge = DigitalBadge(
            name="Test Badge",
            description="Test",
            image_url="https://example.com/badge.png",
            issuer_name="Test Issuer"
        )
        result = valid_assertion.to_open_badge_assertion(badge)

        assert result["@context"] == "https://w3id.org/openbadges/v2"
        assert result["type"] == "Assertion"
        assert "badge" in result
        assert result["recipient"]["hashed"] is True

    def test_assertion_with_evidence(self, valid_assertion):
        """Tests assertion with evidence"""
        valid_assertion.evidence = [
            BadgeEvidence(
                evidence_id="ev-1",
                narrative="Completed all requirements"
            )
        ]
        badge = DigitalBadge(
            name="Test",
            description="Test",
            image_url="https://example.com/badge.png",
            issuer_name="Test"
        )
        result = valid_assertion.to_open_badge_assertion(badge)
        assert "evidence" in result
        assert len(result["evidence"]) == 1


# ============================================================================
# Certificate Share Tests
# ============================================================================


class TestCertificateShare:
    """Tests for CertificateShare entity"""

    def test_share_creation(self):
        """Tests share record creation"""
        share = CertificateShare(
            certificate_id=uuid4(),
            share_platform=SharePlatform.LINKEDIN,
            share_url="https://linkedin.com/in/johndoe/details/certifications"
        )
        assert share.share_platform == SharePlatform.LINKEDIN
        assert share.clicked_count == 0

    def test_share_record_click(self):
        """Tests recording a click on shared link"""
        share = CertificateShare(
            certificate_id=uuid4(),
            share_platform=SharePlatform.LINK
        )
        assert share.clicked_count == 0
        assert share.last_clicked_at is None

        share.record_click()

        assert share.clicked_count == 1
        assert share.last_clicked_at is not None

    def test_share_multiple_clicks(self):
        """Tests recording multiple clicks"""
        share = CertificateShare(
            certificate_id=uuid4(),
            share_platform=SharePlatform.EMAIL
        )
        for _ in range(5):
            share.record_click()

        assert share.clicked_count == 5

    def test_share_all_platforms(self):
        """Tests all share platforms"""
        for platform in SharePlatform:
            share = CertificateShare(
                certificate_id=uuid4(),
                share_platform=platform
            )
            assert share.share_platform == platform


# ============================================================================
# Certificate Renewal Tests
# ============================================================================


class TestCertificateRenewal:
    """Tests for CertificateRenewal entity"""

    @pytest.fixture
    def pending_renewal(self):
        """Creates a pending renewal for testing"""
        return CertificateRenewal(
            original_certificate_id=uuid4(),
            requested_by=uuid4(),
            request_reason="Certificate expiring soon"
        )

    def test_renewal_creation(self, pending_renewal):
        """Tests renewal request creation"""
        assert pending_renewal.status == RenewalStatus.PENDING
        assert pending_renewal.request_reason == "Certificate expiring soon"

    def test_renewal_approve(self, pending_renewal):
        """Tests approval of renewal request"""
        reviewer_id = uuid4()
        pending_renewal.approve(reviewer_id, "Approved for renewal")

        assert pending_renewal.status == RenewalStatus.APPROVED
        assert pending_renewal.reviewed_by == reviewer_id
        assert pending_renewal.review_notes == "Approved for renewal"
        assert pending_renewal.reviewed_at is not None

    def test_renewal_reject(self, pending_renewal):
        """Tests rejection of renewal request"""
        reviewer_id = uuid4()
        pending_renewal.reject(reviewer_id, "Requirements not met")

        assert pending_renewal.status == RenewalStatus.REJECTED
        assert pending_renewal.reviewed_by == reviewer_id
        assert pending_renewal.review_notes == "Requirements not met"

    def test_renewal_complete(self, pending_renewal):
        """Tests completing renewal with new certificate"""
        new_cert_id = uuid4()
        pending_renewal.approve(uuid4())
        pending_renewal.complete(new_cert_id)

        assert pending_renewal.status == RenewalStatus.COMPLETED
        assert pending_renewal.new_certificate_id == new_cert_id


# ============================================================================
# Certificate Analytics Tests
# ============================================================================


class TestCertificateAnalytics:
    """Tests for CertificateAnalytics entity"""

    def test_analytics_creation(self):
        """Tests analytics record creation"""
        analytics = CertificateAnalytics(
            organization_id=uuid4(),
            certificates_issued=100,
            certificates_revoked=5,
            certificates_expired=10,
            total_verifications=500,
            valid_verifications=480
        )
        assert analytics.certificates_issued == 100
        assert analytics.total_verifications == 500

    def test_analytics_verification_success_rate(self):
        """Tests verification success rate calculation"""
        analytics = CertificateAnalytics(
            organization_id=uuid4(),
            total_verifications=100,
            valid_verifications=95
        )
        assert analytics.verification_success_rate == Decimal("95.00")

    def test_analytics_verification_success_rate_zero(self):
        """Tests verification success rate with no verifications"""
        analytics = CertificateAnalytics(
            organization_id=uuid4(),
            total_verifications=0
        )
        assert analytics.verification_success_rate == Decimal("0")

    def test_analytics_total_active_certificates(self):
        """Tests total active certificates calculation"""
        analytics = CertificateAnalytics(
            organization_id=uuid4(),
            certificates_issued=100,
            certificates_revoked=5,
            certificates_expired=10
        )
        assert analytics.total_active_certificates == 85

    def test_analytics_verifier_countries(self):
        """Tests verifier countries tracking"""
        analytics = CertificateAnalytics(
            organization_id=uuid4(),
            verifier_countries={"US": 50, "UK": 30, "CA": 20}
        )
        assert analytics.verifier_countries["US"] == 50
        assert sum(analytics.verifier_countries.values()) == 100


# ============================================================================
# Integration Tests
# ============================================================================


class TestCertificationWorkflow:
    """Integration tests for certification workflow"""

    def test_complete_certification_workflow(self):
        """Tests complete certification issuance workflow"""
        # 1. Create template
        template = CertificateTemplate(
            name="Python Course Completion",
            organization_id=uuid4(),
            template_type=TemplateType.COMPLETION,
            title_template="Certificate of Completion for {{course_name}}"
        )

        # 2. Create signatory
        signatory = CertificateSignatory(
            name="Dr. Jane Smith",
            title="Director of Education",
            organization_id=template.organization_id
        )

        # 3. Issue certificate
        certificate = IssuedCertificate(
            certificate_number="CERT-2025-000001-XYZ1",
            verification_code="ABC12345-DEF4-GHI5",
            template_id=template.id,
            recipient_id=uuid4(),
            recipient_name="John Doe",
            title=template.render_title({"course_name": "Python 101"}),
            organization_id=template.organization_id,
            course_id=uuid4(),
            grade="A",
            score=Decimal("95.5")
        )

        assert certificate.is_valid()
        assert certificate.title == "Certificate of Completion for Python 101"

        # 4. Verify certificate
        verification = CertificateVerification(
            certificate_id=certificate.id,
            verification_method=VerificationMethod.QR,
            verification_result=VerificationResult.VALID,
            verifier_organization="ACME Corp"
        )

        assert verification.verification_result == VerificationResult.VALID

        # 5. Share certificate
        share = CertificateShare(
            certificate_id=certificate.id,
            share_platform=SharePlatform.LINKEDIN
        )
        share.record_click()

        assert share.clicked_count == 1

    def test_badge_issuance_workflow(self):
        """Tests digital badge issuance workflow"""
        # 1. Create badge definition
        badge = DigitalBadge(
            name="Python Expert",
            description="Expert-level Python programming skills",
            image_url="https://example.com/badges/python-expert.png",
            issuer_name="Course Creator Platform",
            badge_type=BadgeType.SKILL,
            criteria_narrative="Complete all advanced Python courses with 90%+ score"
        )

        # 2. Add alignment
        badge.alignment = [
            BadgeAlignment(
                target_name="Python Programming",
                target_framework="Internal Skills"
            )
        ]

        # 3. Issue badge
        assertion = BadgeAssertion(
            badge_id=badge.id,
            recipient_id=uuid4(),
            recipient_identity="sha256$user123hash",
            evidence=[
                BadgeEvidence(
                    evidence_id="ev-1",
                    narrative="Completed Python Advanced with 95%"
                )
            ]
        )

        assert assertion.is_valid()

        # 4. Generate Open Badge JSON
        assertion_json = assertion.to_open_badge_assertion(badge)
        assert assertion_json["type"] == "Assertion"
        assert "evidence" in assertion_json

    def test_certificate_renewal_workflow(self):
        """Tests certificate renewal workflow"""
        # 1. Original certificate
        original = IssuedCertificate(
            certificate_number="CERT-2024-000001-ABC1",
            verification_code="OLD12345-DEF4-GHI5",
            title="Professional Certification",
            recipient_name="Jane Doe",
            expiration_date=date.today() + timedelta(days=30)
        )

        # 2. Request renewal
        renewal = CertificateRenewal(
            original_certificate_id=original.id,
            requested_by=original.recipient_id,
            request_reason="Certificate expiring soon"
        )

        # 3. Approve renewal
        reviewer_id = uuid4()
        renewal.approve(reviewer_id, "All requirements met")
        assert renewal.status == RenewalStatus.APPROVED

        # 4. Issue new certificate
        new_cert = IssuedCertificate(
            certificate_number="CERT-2025-000002-DEF2",
            verification_code="NEW12345-DEF4-GHI5",
            title="Professional Certification",
            recipient_name="Jane Doe",
            expiration_date=date.today() + timedelta(days=365)
        )

        # 5. Complete renewal
        renewal.complete(new_cert.id)
        assert renewal.status == RenewalStatus.COMPLETED

        # 6. Supersede original
        original.status = CertificateStatus.SUPERSEDED
        assert original.is_valid() is False
        assert new_cert.is_valid() is True
