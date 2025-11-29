#!/usr/bin/env python3

"""
Certification Domain Entities

WHAT: Domain entities for enhanced certification system including
templates, issued certificates, digital badges, and verification.

WHERE: Used by certification service for managing credentials

WHY: Provides verifiable, shareable credentials that validate learning
achievements with support for Open Badges 2.0 standard and professional
certificate generation.

## Educational Context:

### Certificate Types
- **Completion Certificates**: Standard course completion recognition
- **Competency Certificates**: Validate mastery of specific competencies
- **Skill Badges**: Micro-credentials for individual skills
- **Program Certificates**: Multi-course program completion
- **Professional Certifications**: Industry-recognized credentials

### Verification Features
- Unique verification codes and QR codes
- Cryptographic digital signatures
- Public verification API
- Revocation and renewal support

### Sharing Capabilities
- LinkedIn integration for professional profiles
- Embeddable certificate widgets
- PDF and image downloads
- Social media sharing

Author: Course Creator Platform
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4


# ============================================================================
# Enumerations
# ============================================================================


class TemplateType(Enum):
    """
    WHAT: Types of certificate templates
    WHERE: Used when creating certificate templates
    WHY: Different certificates serve different educational purposes
    """
    COMPLETION = "completion"      # Course completion certificate
    COMPETENCY = "competency"      # Competency mastery certificate
    SKILL = "skill"                # Skill badge
    PROGRAM = "program"            # Program completion certificate
    PROFESSIONAL = "professional"  # Professional certification


class AchievementType(Enum):
    """
    WHAT: Types of achievements that can be certified
    WHERE: Used when issuing certificates
    WHY: Distinguishes between levels of achievement
    """
    COMPLETION = "completion"      # Standard completion
    COMPETENCY = "competency"      # Competency mastery
    SKILL = "skill"                # Skill badge
    PROGRAM = "program"            # Program completion
    HONOR = "honor"                # With honors (high performance)
    DISTINCTION = "distinction"    # With distinction (exceptional)


class CertificateStatus(Enum):
    """
    WHAT: Status of an issued certificate
    WHERE: Used throughout certificate lifecycle
    WHY: Tracks certificate validity for verification
    """
    ACTIVE = "active"              # Valid and verifiable
    REVOKED = "revoked"            # Certificate revoked
    EXPIRED = "expired"            # Past expiration date
    SUPERSEDED = "superseded"      # Replaced by newer certificate
    PENDING = "pending"            # Awaiting approval


class SignatureStyle(Enum):
    """
    WHAT: How signature appears on certificate
    WHERE: Used for signatory configuration
    WHY: Supports different signature representation methods
    """
    IMAGE = "image"                # Uploaded signature image
    TYPED = "typed"                # Generated from name
    DRAWN = "drawn"                # Hand-drawn SVG


class BadgeType(Enum):
    """
    WHAT: Types of digital badges
    WHERE: Used in Open Badges 2.0 implementation
    WHY: Categorizes badges for discovery and display
    """
    ACHIEVEMENT = "achievement"    # General achievement
    SKILL = "skill"                # Skill mastery
    COMPETENCY = "competency"      # Competency certification
    PARTICIPATION = "participation"  # Participation badge
    MILESTONE = "milestone"        # Learning milestone


class VerificationMethod(Enum):
    """
    WHAT: Methods for verifying certificates
    WHERE: Used in verification logging
    WHY: Tracks how certificates are being verified
    """
    CODE = "code"                  # Verification code lookup
    QR = "qr"                      # QR code scan
    URL = "url"                    # Direct URL
    API = "api"                    # API verification


class VerificationResult(Enum):
    """
    WHAT: Result of certificate verification
    WHERE: Returned by verification process
    WHY: Communicates verification outcome clearly
    """
    VALID = "valid"                # Certificate is valid
    REVOKED = "revoked"            # Certificate was revoked
    EXPIRED = "expired"            # Certificate has expired
    NOT_FOUND = "not_found"        # Certificate not found
    INVALID = "invalid"            # Signature verification failed


class SharePlatform(Enum):
    """
    WHAT: Platforms for sharing certificates
    WHERE: Used in sharing tracking
    WHY: Tracks certificate distribution channels
    """
    LINKEDIN = "linkedin"          # LinkedIn
    TWITTER = "twitter"            # Twitter/X
    FACEBOOK = "facebook"          # Facebook
    EMAIL = "email"                # Email share
    EMBED = "embed"                # Embedded widget
    DOWNLOAD = "download"          # PDF download
    LINK = "link"                  # Direct link share


class RenewalStatus(Enum):
    """
    WHAT: Status of renewal request
    WHERE: Used in renewal workflow
    WHY: Tracks renewal processing state
    """
    PENDING = "pending"            # Awaiting review
    APPROVED = "approved"          # Renewal approved
    REJECTED = "rejected"          # Renewal rejected
    COMPLETED = "completed"        # New certificate issued


# ============================================================================
# Value Objects
# ============================================================================


@dataclass(frozen=True)
class DesignConfig:
    """
    WHAT: Certificate design configuration
    WHERE: Stored in template for rendering
    WHY: Enables customizable certificate appearance

    Design elements support flexible positioning and styling
    for professional certificate generation.
    """
    background_image: Optional[str] = None
    logo_position: Dict[str, int] = field(default_factory=lambda: {
        "x": 50, "y": 10, "width": 100, "height": 50
    })
    title_style: Dict[str, Any] = field(default_factory=lambda: {
        "font": "Georgia", "size": 36, "color": "#000000", "position": {"x": 50, "y": 25}
    })
    recipient_style: Dict[str, Any] = field(default_factory=lambda: {
        "font": "Georgia", "size": 28, "color": "#333333", "position": {"x": 50, "y": 45}
    })
    date_style: Dict[str, Any] = field(default_factory=lambda: {
        "font": "Georgia", "size": 14, "color": "#666666", "position": {"x": 50, "y": 70}
    })
    signature_positions: List[Dict[str, int]] = field(default_factory=lambda: [
        {"x": 50, "y": 80, "width": 150, "height": 50}
    ])
    custom_fields: List[Dict[str, Any]] = field(default_factory=list)
    border_style: Dict[str, Any] = field(default_factory=lambda: {
        "type": "double", "color": "#2563eb", "width": 3
    })
    watermark: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts to dictionary for JSON storage"""
        return {
            "background_image": self.background_image,
            "logo_position": self.logo_position,
            "title_style": self.title_style,
            "recipient_style": self.recipient_style,
            "date_style": self.date_style,
            "signature_positions": self.signature_positions,
            "custom_fields": self.custom_fields,
            "border_style": self.border_style,
            "watermark": self.watermark
        }


@dataclass(frozen=True)
class SkillCertification:
    """
    WHAT: Record of a skill certification
    WHERE: Included in issued certificates
    WHY: Documents specific skills validated by certificate
    """
    skill_id: UUID
    skill_name: str
    proficiency_level: str


@dataclass(frozen=True)
class CompetencyCertification:
    """
    WHAT: Record of a competency certification
    WHERE: Included in issued certificates
    WHY: Documents competencies validated by certificate
    """
    competency_id: UUID
    competency_name: str
    proficiency_level: str


@dataclass(frozen=True)
class BadgeAlignment:
    """
    WHAT: Badge alignment to external standards
    WHERE: Used in Open Badges 2.0 implementation
    WHY: Links badges to recognized competency frameworks
    """
    target_name: str
    target_url: Optional[str] = None
    target_description: Optional[str] = None
    target_framework: Optional[str] = None
    target_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "targetName": self.target_name,
            "targetUrl": self.target_url,
            "targetDescription": self.target_description,
            "targetFramework": self.target_framework,
            "targetCode": self.target_code
        }


@dataclass(frozen=True)
class BadgeEvidence:
    """
    WHAT: Evidence supporting badge assertion
    WHERE: Attached to badge assertions
    WHY: Provides proof of achievement for verification
    """
    evidence_id: str
    narrative: str
    name: Optional[str] = None
    description: Optional[str] = None
    genre: Optional[str] = None
    audience: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.evidence_id,
            "narrative": self.narrative,
            "name": self.name,
            "description": self.description,
            "genre": self.genre,
            "audience": self.audience
        }


# ============================================================================
# Domain Entities
# ============================================================================


@dataclass
class CertificateTemplate:
    """
    WHAT: Template for generating certificates with customizable design

    WHERE: Created by organization admins, used when issuing certificates

    WHY: Enables consistent, branded certificate generation while allowing
    customization for different achievement types and contexts.

    ## Template Components:
    - **Design Configuration**: Visual layout and styling
    - **Content Placeholders**: Dynamic text with variable substitution
    - **Branding**: Colors and fonts matching organization identity
    - **Settings**: QR codes, verification URLs, validity periods

    ## Usage:
    Templates are selected when issuing certificates. The template's
    design config and content templates are merged with recipient data
    to generate the final certificate.
    """
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Template Configuration
    name: str = ""
    description: Optional[str] = None
    template_type: TemplateType = TemplateType.COMPLETION

    # Design Configuration
    design_config: DesignConfig = field(default_factory=DesignConfig)

    # Content Templates (with {{variable}} placeholders)
    title_template: str = "Certificate of {{certificate_type}}"
    subtitle_template: Optional[str] = None
    body_template: Optional[str] = None
    footer_template: Optional[str] = None

    # Branding
    primary_color: str = "#2563eb"
    secondary_color: str = "#1e40af"
    accent_color: str = "#fbbf24"
    font_family: str = "Georgia, serif"

    # Certificate Settings
    include_qr_code: bool = True
    include_verification_url: bool = True
    include_skills_list: bool = False
    include_competencies: bool = False
    include_credits: bool = False
    include_grade: bool = False

    # Validity Settings
    has_expiration: bool = False
    validity_period_months: Optional[int] = None
    renewal_allowed: bool = True

    # Status
    is_active: bool = True
    is_default: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    def __post_init__(self):
        """Validates template data"""
        if not self.name:
            raise ValueError("Template name is required")
        if len(self.name) > 255:
            raise ValueError("Template name must be 255 characters or less")
        if not self._is_valid_color(self.primary_color):
            raise ValueError("Invalid primary color format")
        if not self._is_valid_color(self.secondary_color):
            raise ValueError("Invalid secondary color format")
        if not self._is_valid_color(self.accent_color):
            raise ValueError("Invalid accent color format")

    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Validates hex color format"""
        import re
        return bool(re.match(r'^#[0-9A-Fa-f]{6}$', color))

    def render_title(self, data: Dict[str, Any]) -> str:
        """Renders title with variable substitution"""
        return self._render_template(self.title_template, data)

    def _render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Simple template rendering with {{variable}} substitution"""
        result = template
        for key, value in data.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result


@dataclass
class CertificateSignatory:
    """
    WHAT: Authorized signatory for certificates

    WHERE: Associated with templates and appear on issued certificates

    WHY: Adds authority and authenticity to certificates through
    official signatures from recognized individuals.

    ## Signature Options:
    - **Image**: Uploaded signature scan/image
    - **Typed**: Script font rendering of name
    - **Drawn**: Hand-drawn SVG signature
    """
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Signatory Information
    name: str = ""
    title: str = ""
    email: Optional[str] = None

    # Signature Configuration
    signature_image_url: Optional[str] = None
    signature_style: SignatureStyle = SignatureStyle.IMAGE
    signature_data: Optional[str] = None  # SVG or base64

    # Display Settings
    display_name: Optional[str] = None
    display_title: Optional[str] = None
    sort_order: int = 0

    # Status
    is_active: bool = True

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validates signatory data"""
        if not self.name:
            raise ValueError("Signatory name is required")
        if not self.title:
            raise ValueError("Signatory title is required")

    def get_display_name(self) -> str:
        """Returns name to display on certificate"""
        return self.display_name or self.name

    def get_display_title(self) -> str:
        """Returns title to display on certificate"""
        return self.display_title or self.title


@dataclass
class IssuedCertificate:
    """
    WHAT: An issued certificate for a specific recipient

    WHERE: Created when user earns a certificate, used for verification

    WHY: Represents the official credential awarded to a learner,
    providing verifiable proof of their achievement.

    ## Certificate Data:
    - **Identity**: Unique certificate number and verification code
    - **Achievement**: What was accomplished (course, program, skills)
    - **Performance**: Grade, score, credits if applicable
    - **Verification**: Digital signature, QR code, verification URL
    - **Generated Files**: PDF and image versions

    ## Lifecycle:
    Certificates can be active, revoked, expired, or superseded.
    Revocation requires a reason and is logged for audit.
    """
    id: UUID = field(default_factory=uuid4)
    certificate_number: str = ""
    verification_code: str = ""

    # Relationships
    template_id: UUID = field(default_factory=uuid4)
    recipient_id: UUID = field(default_factory=uuid4)
    course_id: Optional[UUID] = None
    program_id: Optional[UUID] = None
    organization_id: UUID = field(default_factory=uuid4)

    # Certificate Content
    title: str = ""
    recipient_name: str = ""
    description: Optional[str] = None

    # Achievement Details
    achievement_type: AchievementType = AchievementType.COMPLETION

    # Performance Data
    grade: Optional[str] = None
    score: Optional[Decimal] = None
    credits_earned: Optional[Decimal] = None
    completion_percentage: Decimal = Decimal("100.00")

    # Skills and Competencies
    skills_certified: List[SkillCertification] = field(default_factory=list)
    competencies_certified: List[CompetencyCertification] = field(default_factory=list)

    # Dates
    issue_date: date = field(default_factory=date.today)
    completion_date: Optional[date] = None
    expiration_date: Optional[date] = None

    # Verification
    verification_url: Optional[str] = None
    qr_code_data: Optional[str] = None
    digital_signature: Optional[str] = None
    signature_algorithm: str = "SHA256withRSA"

    # Generated Files
    pdf_url: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None

    # Status
    status: CertificateStatus = CertificateStatus.ACTIVE
    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None

    # Sharing
    is_public: bool = False
    linkedin_shared: bool = False
    linkedin_share_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validates certificate data"""
        if not self.title:
            raise ValueError("Certificate title is required")
        if not self.recipient_name:
            raise ValueError("Recipient name is required")

    def is_valid(self) -> bool:
        """Checks if certificate is currently valid"""
        if self.status != CertificateStatus.ACTIVE:
            return False
        if self.expiration_date and self.expiration_date < date.today():
            return False
        return True

    def revoke(self, reason: str, revoked_by: UUID) -> None:
        """Revokes the certificate"""
        self.status = CertificateStatus.REVOKED
        self.revocation_reason = reason
        self.revoked_at = datetime.utcnow()
        self.revoked_by = revoked_by
        self.updated_at = datetime.utcnow()

    def check_expiration(self) -> bool:
        """Updates status if expired, returns True if expired"""
        if (self.expiration_date and
            self.expiration_date < date.today() and
            self.status == CertificateStatus.ACTIVE):
            self.status = CertificateStatus.EXPIRED
            self.updated_at = datetime.utcnow()
            return True
        return False


@dataclass
class CertificateVerification:
    """
    WHAT: Record of a certificate verification request

    WHERE: Created each time someone verifies a certificate

    WHY: Provides audit trail and analytics on certificate verification
    patterns, supporting fraud detection and usage insights.

    ## Tracked Data:
    - Verification method (code, QR, URL, API)
    - Verifier information (anonymized)
    - Geographic location
    - Verification result
    """
    id: UUID = field(default_factory=uuid4)
    certificate_id: UUID = field(default_factory=uuid4)

    # Verification Details
    verification_method: VerificationMethod = VerificationMethod.CODE

    # Requester Information (anonymized)
    verifier_ip: Optional[str] = None
    verifier_user_agent: Optional[str] = None
    verifier_organization: Optional[str] = None
    verifier_email: Optional[str] = None

    # Result
    verification_result: VerificationResult = VerificationResult.VALID

    # Location
    country_code: Optional[str] = None
    region: Optional[str] = None

    # Timestamp
    verified_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DigitalBadge:
    """
    WHAT: Digital badge definition following Open Badges 2.0 standard

    WHERE: Created by organizations to recognize achievements

    WHY: Provides portable, verifiable micro-credentials that can be
    shared across platforms and verified by third parties.

    ## Open Badges 2.0 Compliance:
    - Badge class with required metadata
    - Issuer information
    - Alignment to external standards
    - Evidence support

    ## Badge Types:
    - Achievement badges for accomplishments
    - Skill badges for specific abilities
    - Competency badges for demonstrated mastery
    - Participation badges for engagement
    - Milestone badges for learning progress
    """
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Badge Definition
    name: str = ""
    description: str = ""
    image_url: str = ""
    criteria_url: Optional[str] = None
    criteria_narrative: Optional[str] = None

    # Badge Type
    badge_type: BadgeType = BadgeType.ACHIEVEMENT

    # Issuer Information
    issuer_name: str = ""
    issuer_url: Optional[str] = None
    issuer_email: Optional[str] = None
    issuer_image_url: Optional[str] = None

    # Alignment
    alignment: List[BadgeAlignment] = field(default_factory=list)

    # Tags
    tags: List[str] = field(default_factory=list)

    # Requirements
    requirements: Dict[str, Any] = field(default_factory=dict)

    # Status
    is_active: bool = True
    is_stackable: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validates badge data"""
        if not self.name:
            raise ValueError("Badge name is required")
        if not self.description:
            raise ValueError("Badge description is required")
        if not self.image_url:
            raise ValueError("Badge image URL is required")
        if not self.issuer_name:
            raise ValueError("Issuer name is required")

    def to_open_badge_class(self) -> Dict[str, Any]:
        """Converts to Open Badges 2.0 BadgeClass JSON"""
        badge_class = {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "BadgeClass",
            "id": f"urn:uuid:{self.id}",
            "name": self.name,
            "description": self.description,
            "image": self.image_url,
            "criteria": {
                "narrative": self.criteria_narrative
            } if self.criteria_narrative else {"id": self.criteria_url},
            "issuer": {
                "type": "Issuer",
                "name": self.issuer_name,
                "url": self.issuer_url,
                "email": self.issuer_email,
                "image": self.issuer_image_url
            },
            "tags": self.tags
        }
        if self.alignment:
            badge_class["alignment"] = [a.to_dict() for a in self.alignment]
        return badge_class


@dataclass
class BadgeAssertion:
    """
    WHAT: Issued badge assertion linking a badge to a recipient

    WHERE: Created when a user earns a badge

    WHY: Represents the verifiable claim that a specific person
    earned a specific badge at a specific time.

    ## Open Badges 2.0 Assertion:
    - Recipient identity (hashed for privacy)
    - Evidence of achievement
    - Verification method
    """
    id: UUID = field(default_factory=uuid4)
    badge_id: UUID = field(default_factory=uuid4)
    recipient_id: UUID = field(default_factory=uuid4)

    # Recipient Identity (Open Badges)
    recipient_type: str = "email"
    recipient_identity: str = ""  # Hashed or plain email
    recipient_hashed: bool = True
    recipient_salt: Optional[str] = None

    # Evidence
    evidence: List[BadgeEvidence] = field(default_factory=list)

    # Verification
    verification_type: str = "hosted"
    verification_url: Optional[str] = None

    # Dates
    issued_on: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    # Status
    status: str = "active"
    revoked: bool = False
    revocation_reason: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validates assertion data"""
        if not self.recipient_identity:
            raise ValueError("Recipient identity is required")

    def is_valid(self) -> bool:
        """Checks if assertion is currently valid"""
        if self.revoked:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def to_open_badge_assertion(self, badge: DigitalBadge) -> Dict[str, Any]:
        """Converts to Open Badges 2.0 Assertion JSON"""
        assertion = {
            "@context": "https://w3id.org/openbadges/v2",
            "type": "Assertion",
            "id": f"urn:uuid:{self.id}",
            "badge": badge.to_open_badge_class(),
            "recipient": {
                "type": self.recipient_type,
                "identity": self.recipient_identity,
                "hashed": self.recipient_hashed
            },
            "verification": {
                "type": self.verification_type
            },
            "issuedOn": self.issued_on.isoformat()
        }
        if self.recipient_salt:
            assertion["recipient"]["salt"] = self.recipient_salt
        if self.verification_url:
            assertion["verification"]["url"] = self.verification_url
        if self.evidence:
            assertion["evidence"] = [e.to_dict() for e in self.evidence]
        if self.expires_at:
            assertion["expires"] = self.expires_at.isoformat()
        return assertion


@dataclass
class CertificateShare:
    """
    WHAT: Record of certificate sharing activity

    WHERE: Created when certificates are shared externally

    WHY: Tracks certificate distribution and engagement for
    analytics and user insight into their credential reach.
    """
    id: UUID = field(default_factory=uuid4)
    certificate_id: UUID = field(default_factory=uuid4)

    # Share Details
    share_platform: SharePlatform = SharePlatform.LINK

    # Share Data
    share_url: Optional[str] = None
    external_id: Optional[str] = None

    # Recipient (for email shares)
    recipient_email: Optional[str] = None
    recipient_name: Optional[str] = None

    # Tracking
    shared_at: datetime = field(default_factory=datetime.utcnow)
    clicked_count: int = 0
    last_clicked_at: Optional[datetime] = None

    def record_click(self) -> None:
        """Records a click on the shared link"""
        self.clicked_count += 1
        self.last_clicked_at = datetime.utcnow()


@dataclass
class CertificateRenewal:
    """
    WHAT: Request to renew an expiring or expired certificate

    WHERE: Used in renewal workflow

    WHY: Allows certificates with expiration to be renewed while
    maintaining clear audit trail and approval process.

    ## Renewal Process:
    1. User requests renewal
    2. Admin reviews requirements
    3. Admin approves/rejects
    4. If approved, new certificate is issued
    5. Original marked as superseded
    """
    id: UUID = field(default_factory=uuid4)
    original_certificate_id: UUID = field(default_factory=uuid4)

    # Request Details
    requested_by: UUID = field(default_factory=uuid4)
    request_reason: Optional[str] = None

    # Status
    status: RenewalStatus = RenewalStatus.PENDING

    # Review
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    # New Certificate
    new_certificate_id: Optional[UUID] = None

    # Requirements
    renewal_requirements: Dict[str, Any] = field(default_factory=dict)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def approve(self, reviewer: UUID, notes: Optional[str] = None) -> None:
        """Approves the renewal request"""
        self.status = RenewalStatus.APPROVED
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes
        self.updated_at = datetime.utcnow()

    def reject(self, reviewer: UUID, notes: str) -> None:
        """Rejects the renewal request"""
        self.status = RenewalStatus.REJECTED
        self.reviewed_by = reviewer
        self.reviewed_at = datetime.utcnow()
        self.review_notes = notes
        self.updated_at = datetime.utcnow()

    def complete(self, new_certificate_id: UUID) -> None:
        """Marks renewal as completed with new certificate"""
        self.status = RenewalStatus.COMPLETED
        self.new_certificate_id = new_certificate_id
        self.updated_at = datetime.utcnow()


@dataclass
class CertificateAnalytics:
    """
    WHAT: Aggregated certificate analytics for an organization

    WHERE: Used in analytics dashboards and reports

    WHY: Provides insights into certificate issuance, verification,
    and sharing patterns for organizational decision-making.
    """
    id: UUID = field(default_factory=uuid4)
    organization_id: UUID = field(default_factory=uuid4)

    # Time Period
    period_start: date = field(default_factory=date.today)
    period_end: date = field(default_factory=date.today)
    period_type: str = "monthly"

    # Issuance Metrics
    certificates_issued: int = 0
    certificates_revoked: int = 0
    certificates_expired: int = 0

    # Verification Metrics
    total_verifications: int = 0
    unique_verifiers: int = 0
    valid_verifications: int = 0
    failed_verifications: int = 0

    # Sharing Metrics
    linkedin_shares: int = 0
    email_shares: int = 0
    download_count: int = 0
    public_view_count: int = 0

    # Achievement Distribution
    completion_certificates: int = 0
    competency_certificates: int = 0
    skill_badges: int = 0
    program_certificates: int = 0

    # Geographic Distribution
    verifier_countries: Dict[str, int] = field(default_factory=dict)

    # Calculated
    calculated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def verification_success_rate(self) -> Decimal:
        """Calculates verification success rate"""
        if self.total_verifications == 0:
            return Decimal("0")
        return Decimal(str(
            (self.valid_verifications / self.total_verifications) * 100
        )).quantize(Decimal("0.01"))

    @property
    def total_active_certificates(self) -> int:
        """Calculates total active certificates"""
        return (self.certificates_issued -
                self.certificates_revoked -
                self.certificates_expired)
