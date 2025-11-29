-- Migration: 028_certification_enhancement.sql
-- Purpose: Enhanced certification system with templates, verification, and digital badges
-- Author: Course Creator Platform
-- Date: 2025-11-28

-- ============================================================================
-- WHAT: Enhanced certification schema for professional certificate management
-- WHERE: Supports course completion, competency, and skill-based certifications
-- WHY: Provides verifiable, shareable credentials that validate learning achievements
--
-- Features:
-- - Certificate templates with customizable designs
-- - Digital signatures with cryptographic verification
-- - Unique verification codes and QR codes
-- - LinkedIn and social sharing integration
-- - Certificate revocation and reissue capabilities
-- - Batch certificate generation
-- - Certificate analytics and tracking
-- ============================================================================

-- ============================================================================
-- Certificate Templates
-- ============================================================================

CREATE TABLE IF NOT EXISTS certificate_templates (
    -- Template Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Template Configuration
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL DEFAULT 'completion',
        -- completion: Course completion certificate
        -- competency: Competency mastery certificate
        -- skill: Skill badge
        -- program: Program completion certificate
        -- professional: Professional certification

    -- Design Configuration (JSON)
    design_config JSONB NOT NULL DEFAULT '{}'::JSONB,
        -- background_image: URL to background
        -- logo_position: {x, y, width, height}
        -- title_style: {font, size, color, position}
        -- recipient_style: {font, size, color, position}
        -- date_style: {font, size, color, position}
        -- signature_positions: [{x, y, width, height}]
        -- custom_fields: [{name, style, position}]
        -- border_style: {type, color, width}
        -- watermark: {text, opacity, rotation}

    -- Content Placeholders
    title_template VARCHAR(500) NOT NULL DEFAULT 'Certificate of {{certificate_type}}',
    subtitle_template VARCHAR(500),
    body_template TEXT,
    footer_template VARCHAR(500),

    -- Branding
    primary_color VARCHAR(7) DEFAULT '#2563eb',
    secondary_color VARCHAR(7) DEFAULT '#1e40af',
    accent_color VARCHAR(7) DEFAULT '#fbbf24',
    font_family VARCHAR(100) DEFAULT 'Georgia, serif',

    -- Certificate Settings
    include_qr_code BOOLEAN DEFAULT true,
    include_verification_url BOOLEAN DEFAULT true,
    include_skills_list BOOLEAN DEFAULT false,
    include_competencies BOOLEAN DEFAULT false,
    include_credits BOOLEAN DEFAULT false,
    include_grade BOOLEAN DEFAULT false,

    -- Validity Settings
    has_expiration BOOLEAN DEFAULT false,
    validity_period_months INTEGER,
    renewal_allowed BOOLEAN DEFAULT true,

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),

    CONSTRAINT valid_template_type CHECK (template_type IN
        ('completion', 'competency', 'skill', 'program', 'professional')),
    CONSTRAINT valid_colors CHECK (
        primary_color ~ '^#[0-9A-Fa-f]{6}$' AND
        secondary_color ~ '^#[0-9A-Fa-f]{6}$' AND
        accent_color ~ '^#[0-9A-Fa-f]{6}$'
    )
);

-- ============================================================================
-- Certificate Signatories
-- ============================================================================

CREATE TABLE IF NOT EXISTS certificate_signatories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Signatory Information
    name VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    email VARCHAR(255),

    -- Signature Configuration
    signature_image_url VARCHAR(1000),
    signature_style VARCHAR(50) DEFAULT 'image',
        -- image: Use uploaded signature image
        -- typed: Generate from name with script font
        -- drawn: Hand-drawn signature (stored as SVG)
    signature_data TEXT, -- SVG or base64 for drawn signatures

    -- Display Settings
    display_name VARCHAR(255), -- How name appears on certificate
    display_title VARCHAR(255), -- How title appears on certificate
    sort_order INTEGER DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_signature_style CHECK (signature_style IN
        ('image', 'typed', 'drawn'))
);

-- ============================================================================
-- Template-Signatory Association
-- ============================================================================

CREATE TABLE IF NOT EXISTS template_signatories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES certificate_templates(id) ON DELETE CASCADE,
    signatory_id UUID NOT NULL REFERENCES certificate_signatories(id) ON DELETE CASCADE,

    -- Position on certificate
    position_x INTEGER DEFAULT 50, -- percentage
    position_y INTEGER DEFAULT 80, -- percentage
    sort_order INTEGER DEFAULT 0,

    -- Override display for this template
    override_title VARCHAR(255),

    UNIQUE(template_id, signatory_id)
);

-- ============================================================================
-- Issued Certificates
-- ============================================================================

CREATE TABLE IF NOT EXISTS issued_certificates (
    -- Certificate Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_number VARCHAR(50) NOT NULL UNIQUE,
    verification_code VARCHAR(100) NOT NULL UNIQUE,

    -- Relationships
    template_id UUID NOT NULL REFERENCES certificate_templates(id),
    recipient_id UUID NOT NULL REFERENCES users(id),
    course_id UUID REFERENCES courses(id),
    program_id UUID REFERENCES training_programs(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),

    -- Certificate Content
    title VARCHAR(500) NOT NULL,
    recipient_name VARCHAR(255) NOT NULL,
    description TEXT,

    -- Achievement Details
    achievement_type VARCHAR(50) NOT NULL DEFAULT 'completion',
        -- completion: Course completion
        -- competency: Competency mastery
        -- skill: Skill badge
        -- program: Program completion
        -- honor: With honors
        -- distinction: With distinction

    -- Performance Data
    grade VARCHAR(10),
    score DECIMAL(5,2),
    credits_earned DECIMAL(5,2),
    completion_percentage DECIMAL(5,2) DEFAULT 100.00,

    -- Skills and Competencies (if applicable)
    skills_certified JSONB DEFAULT '[]'::JSONB,
        -- [{skill_id, skill_name, proficiency_level}]
    competencies_certified JSONB DEFAULT '[]'::JSONB,
        -- [{competency_id, competency_name, proficiency_level}]

    -- Dates
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    completion_date DATE,
    expiration_date DATE,

    -- Verification
    verification_url VARCHAR(1000),
    qr_code_data TEXT, -- Base64 QR code image
    digital_signature TEXT, -- Cryptographic signature
    signature_algorithm VARCHAR(50) DEFAULT 'SHA256withRSA',

    -- Generated Files
    pdf_url VARCHAR(1000),
    image_url VARCHAR(1000),
    thumbnail_url VARCHAR(1000),

    -- Status
    status VARCHAR(50) DEFAULT 'active',
        -- active: Valid and verifiable
        -- revoked: Certificate revoked
        -- expired: Past expiration date
        -- superseded: Replaced by newer certificate
        -- pending: Awaiting approval
    revocation_reason TEXT,
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by UUID REFERENCES users(id),

    -- Sharing Configuration
    is_public BOOLEAN DEFAULT false,
    linkedin_shared BOOLEAN DEFAULT false,
    linkedin_share_id VARCHAR(100),

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_achievement_type CHECK (achievement_type IN
        ('completion', 'competency', 'skill', 'program', 'honor', 'distinction')),
    CONSTRAINT valid_status CHECK (status IN
        ('active', 'revoked', 'expired', 'superseded', 'pending'))
);

-- ============================================================================
-- Certificate Verification Log
-- ============================================================================

CREATE TABLE IF NOT EXISTS certificate_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id UUID NOT NULL REFERENCES issued_certificates(id),

    -- Verification Details
    verification_method VARCHAR(50) NOT NULL,
        -- code: Verification code lookup
        -- qr: QR code scan
        -- url: Direct URL
        -- api: API verification

    -- Requester Information
    verifier_ip VARCHAR(45),
    verifier_user_agent TEXT,
    verifier_organization VARCHAR(255),
    verifier_email VARCHAR(255),

    -- Result
    verification_result VARCHAR(20) NOT NULL,
        -- valid: Certificate is valid
        -- revoked: Certificate was revoked
        -- expired: Certificate has expired
        -- not_found: Certificate not found
        -- invalid: Signature verification failed

    -- Location (approximate)
    country_code VARCHAR(2),
    region VARCHAR(100),

    -- Timestamp
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_verification_method CHECK (verification_method IN
        ('code', 'qr', 'url', 'api')),
    CONSTRAINT valid_verification_result CHECK (verification_result IN
        ('valid', 'revoked', 'expired', 'not_found', 'invalid'))
);

-- ============================================================================
-- Digital Badges (Open Badges 2.0 Compatible)
-- ============================================================================

CREATE TABLE IF NOT EXISTS digital_badges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Badge Definition (Open Badges 2.0)
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    image_url VARCHAR(1000) NOT NULL,
    criteria_url VARCHAR(1000),
    criteria_narrative TEXT,

    -- Badge Type
    badge_type VARCHAR(50) NOT NULL DEFAULT 'achievement',
        -- achievement: General achievement
        -- skill: Skill mastery
        -- competency: Competency certification
        -- participation: Participation badge
        -- milestone: Learning milestone

    -- Issuer Information (for Open Badges)
    issuer_name VARCHAR(255) NOT NULL,
    issuer_url VARCHAR(1000),
    issuer_email VARCHAR(255),
    issuer_image_url VARCHAR(1000),

    -- Alignment (to standards/competencies)
    alignment JSONB DEFAULT '[]'::JSONB,
        -- [{targetName, targetUrl, targetDescription, targetFramework, targetCode}]

    -- Tags for discovery
    tags JSONB DEFAULT '[]'::JSONB,

    -- Requirements
    requirements JSONB DEFAULT '{}'::JSONB,
        -- courses: [course_ids]
        -- competencies: [competency_ids]
        -- skills: [skill_ids]
        -- min_score: minimum score
        -- completion_criteria: text description

    -- Status
    is_active BOOLEAN DEFAULT true,
    is_stackable BOOLEAN DEFAULT false, -- Can be combined with other badges

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_badge_type CHECK (badge_type IN
        ('achievement', 'skill', 'competency', 'participation', 'milestone'))
);

-- ============================================================================
-- Badge Assertions (Issued Badges)
-- ============================================================================

CREATE TABLE IF NOT EXISTS badge_assertions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    badge_id UUID NOT NULL REFERENCES digital_badges(id),
    recipient_id UUID NOT NULL REFERENCES users(id),

    -- Recipient Identity (for Open Badges)
    recipient_type VARCHAR(50) DEFAULT 'email',
    recipient_identity VARCHAR(255) NOT NULL, -- Hashed or plain email
    recipient_hashed BOOLEAN DEFAULT true,
    recipient_salt VARCHAR(100),

    -- Evidence
    evidence JSONB DEFAULT '[]'::JSONB,
        -- [{id, narrative, name, description, genre, audience}]

    -- Verification
    verification_type VARCHAR(50) DEFAULT 'hosted',
        -- hosted: Badge JSON hosted at URL
        -- signed: Cryptographically signed
    verification_url VARCHAR(1000),

    -- Dates
    issued_on TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Status
    status VARCHAR(20) DEFAULT 'active',
    revoked BOOLEAN DEFAULT false,
    revocation_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_recipient_type CHECK (recipient_type IN
        ('email', 'url', 'telephone')),
    CONSTRAINT valid_verification_type CHECK (verification_type IN
        ('hosted', 'signed')),
    CONSTRAINT unique_badge_recipient UNIQUE(badge_id, recipient_id)
);

-- ============================================================================
-- Certificate Sharing History
-- ============================================================================

CREATE TABLE IF NOT EXISTS certificate_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    certificate_id UUID NOT NULL REFERENCES issued_certificates(id),

    -- Share Details
    share_platform VARCHAR(50) NOT NULL,
        -- linkedin: LinkedIn
        -- twitter: Twitter/X
        -- facebook: Facebook
        -- email: Email share
        -- embed: Embedded widget
        -- download: PDF download
        -- link: Direct link share

    -- Share Data
    share_url VARCHAR(1000),
    external_id VARCHAR(100), -- Platform-specific ID

    -- Recipient (for email shares)
    recipient_email VARCHAR(255),
    recipient_name VARCHAR(255),

    -- Tracking
    shared_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    clicked_count INTEGER DEFAULT 0,
    last_clicked_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_share_platform CHECK (share_platform IN
        ('linkedin', 'twitter', 'facebook', 'email', 'embed', 'download', 'link'))
);

-- ============================================================================
-- Certificate Analytics
-- ============================================================================

CREATE TABLE IF NOT EXISTS certificate_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),

    -- Time Period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    period_type VARCHAR(20) NOT NULL DEFAULT 'monthly',

    -- Issuance Metrics
    certificates_issued INTEGER DEFAULT 0,
    certificates_revoked INTEGER DEFAULT 0,
    certificates_expired INTEGER DEFAULT 0,

    -- Verification Metrics
    total_verifications INTEGER DEFAULT 0,
    unique_verifiers INTEGER DEFAULT 0,
    valid_verifications INTEGER DEFAULT 0,
    failed_verifications INTEGER DEFAULT 0,

    -- Sharing Metrics
    linkedin_shares INTEGER DEFAULT 0,
    email_shares INTEGER DEFAULT 0,
    download_count INTEGER DEFAULT 0,
    public_view_count INTEGER DEFAULT 0,

    -- Achievement Distribution
    completion_certificates INTEGER DEFAULT 0,
    competency_certificates INTEGER DEFAULT 0,
    skill_badges INTEGER DEFAULT 0,
    program_certificates INTEGER DEFAULT 0,

    -- Geographic Distribution (top countries)
    verifier_countries JSONB DEFAULT '{}'::JSONB,

    -- Calculated at
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT valid_period_type CHECK (period_type IN
        ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
    CONSTRAINT unique_period UNIQUE(organization_id, period_start, period_end, period_type)
);

-- ============================================================================
-- Certificate Renewal Requests
-- ============================================================================

CREATE TABLE IF NOT EXISTS certificate_renewals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_certificate_id UUID NOT NULL REFERENCES issued_certificates(id),

    -- Request Details
    requested_by UUID NOT NULL REFERENCES users(id),
    request_reason TEXT,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',
        -- pending: Awaiting review
        -- approved: Renewal approved
        -- rejected: Renewal rejected
        -- completed: New certificate issued

    -- Review
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,

    -- New Certificate
    new_certificate_id UUID REFERENCES issued_certificates(id),

    -- Requirements for renewal
    renewal_requirements JSONB DEFAULT '{}'::JSONB,
        -- required_assessments: [assessment_ids]
        -- required_courses: [course_ids]
        -- completion_status: {assessment_id: completed}

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT valid_renewal_status CHECK (status IN
        ('pending', 'approved', 'rejected', 'completed'))
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Certificate Templates
CREATE INDEX IF NOT EXISTS idx_cert_templates_org ON certificate_templates(organization_id);
CREATE INDEX IF NOT EXISTS idx_cert_templates_type ON certificate_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_cert_templates_active ON certificate_templates(is_active);

-- Signatories
CREATE INDEX IF NOT EXISTS idx_cert_signatories_org ON certificate_signatories(organization_id);

-- Issued Certificates
CREATE INDEX IF NOT EXISTS idx_issued_certs_recipient ON issued_certificates(recipient_id);
CREATE INDEX IF NOT EXISTS idx_issued_certs_course ON issued_certificates(course_id);
CREATE INDEX IF NOT EXISTS idx_issued_certs_org ON issued_certificates(organization_id);
CREATE INDEX IF NOT EXISTS idx_issued_certs_status ON issued_certificates(status);
CREATE INDEX IF NOT EXISTS idx_issued_certs_number ON issued_certificates(certificate_number);
CREATE INDEX IF NOT EXISTS idx_issued_certs_verification ON issued_certificates(verification_code);
CREATE INDEX IF NOT EXISTS idx_issued_certs_issue_date ON issued_certificates(issue_date DESC);

-- Verifications
CREATE INDEX IF NOT EXISTS idx_cert_verifications_cert ON certificate_verifications(certificate_id);
CREATE INDEX IF NOT EXISTS idx_cert_verifications_date ON certificate_verifications(verified_at DESC);
CREATE INDEX IF NOT EXISTS idx_cert_verifications_result ON certificate_verifications(verification_result);

-- Digital Badges
CREATE INDEX IF NOT EXISTS idx_badges_org ON digital_badges(organization_id);
CREATE INDEX IF NOT EXISTS idx_badges_type ON digital_badges(badge_type);

-- Badge Assertions
CREATE INDEX IF NOT EXISTS idx_badge_assertions_recipient ON badge_assertions(recipient_id);
CREATE INDEX IF NOT EXISTS idx_badge_assertions_badge ON badge_assertions(badge_id);

-- Shares
CREATE INDEX IF NOT EXISTS idx_cert_shares_cert ON certificate_shares(certificate_id);
CREATE INDEX IF NOT EXISTS idx_cert_shares_platform ON certificate_shares(share_platform);

-- Analytics
CREATE INDEX IF NOT EXISTS idx_cert_analytics_org ON certificate_analytics(organization_id);
CREATE INDEX IF NOT EXISTS idx_cert_analytics_period ON certificate_analytics(period_start, period_end);

-- Renewals
CREATE INDEX IF NOT EXISTS idx_cert_renewals_original ON certificate_renewals(original_certificate_id);
CREATE INDEX IF NOT EXISTS idx_cert_renewals_status ON certificate_renewals(status);

-- ============================================================================
-- Functions for Certificate Management
-- ============================================================================

-- Generate unique certificate number
CREATE OR REPLACE FUNCTION generate_certificate_number()
RETURNS VARCHAR(50) AS $$
DECLARE
    cert_number VARCHAR(50);
    year_part VARCHAR(4);
    seq_part VARCHAR(6);
    random_part VARCHAR(4);
BEGIN
    year_part := TO_CHAR(CURRENT_DATE, 'YYYY');
    seq_part := LPAD(NEXTVAL('certificate_number_seq')::TEXT, 6, '0');
    random_part := UPPER(SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 4));
    cert_number := 'CERT-' || year_part || '-' || seq_part || '-' || random_part;
    RETURN cert_number;
END;
$$ LANGUAGE plpgsql;

-- Create sequence for certificate numbers
CREATE SEQUENCE IF NOT EXISTS certificate_number_seq START 1;

-- Generate verification code
CREATE OR REPLACE FUNCTION generate_verification_code()
RETURNS VARCHAR(100) AS $$
DECLARE
    code VARCHAR(100);
BEGIN
    code := UPPER(
        SUBSTRING(MD5(RANDOM()::TEXT || CURRENT_TIMESTAMP::TEXT) FROM 1 FOR 8) ||
        '-' ||
        SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 4) ||
        '-' ||
        SUBSTRING(MD5(RANDOM()::TEXT) FROM 1 FOR 4)
    );
    RETURN code;
END;
$$ LANGUAGE plpgsql;

-- Update certificate status based on expiration
CREATE OR REPLACE FUNCTION update_certificate_expiration_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expiration_date IS NOT NULL AND
       NEW.expiration_date < CURRENT_DATE AND
       NEW.status = 'active' THEN
        NEW.status := 'expired';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER check_certificate_expiration
    BEFORE INSERT OR UPDATE ON issued_certificates
    FOR EACH ROW
    EXECUTE FUNCTION update_certificate_expiration_status();

-- ============================================================================
-- Materialized View for Certificate Statistics
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_certificate_statistics AS
SELECT
    o.id as organization_id,
    o.name as organization_name,
    COUNT(ic.id) as total_certificates,
    COUNT(ic.id) FILTER (WHERE ic.status = 'active') as active_certificates,
    COUNT(ic.id) FILTER (WHERE ic.status = 'revoked') as revoked_certificates,
    COUNT(ic.id) FILTER (WHERE ic.status = 'expired') as expired_certificates,
    COUNT(DISTINCT ic.recipient_id) as unique_recipients,
    COUNT(DISTINCT ic.course_id) as courses_certified,
    COUNT(cv.id) as total_verifications,
    COUNT(cv.id) FILTER (WHERE cv.verification_result = 'valid') as successful_verifications,
    COUNT(cs.id) FILTER (WHERE cs.share_platform = 'linkedin') as linkedin_shares,
    MAX(ic.issue_date) as last_certificate_date
FROM organizations o
LEFT JOIN issued_certificates ic ON o.id = ic.organization_id
LEFT JOIN certificate_verifications cv ON ic.id = cv.certificate_id
LEFT JOIN certificate_shares cs ON ic.id = cs.certificate_id
GROUP BY o.id, o.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_cert_stats_org
    ON mv_certificate_statistics(organization_id);

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE certificate_templates IS 'Templates for generating certificates with customizable designs';
COMMENT ON TABLE certificate_signatories IS 'Authorized signatories for certificates with signature configurations';
COMMENT ON TABLE issued_certificates IS 'Issued certificates with verification codes and digital signatures';
COMMENT ON TABLE certificate_verifications IS 'Log of certificate verification requests for auditing';
COMMENT ON TABLE digital_badges IS 'Open Badges 2.0 compatible digital badge definitions';
COMMENT ON TABLE badge_assertions IS 'Issued badge assertions linking badges to recipients';
COMMENT ON TABLE certificate_shares IS 'Tracking of certificate sharing across platforms';
COMMENT ON TABLE certificate_analytics IS 'Aggregated analytics for certificate metrics';
COMMENT ON TABLE certificate_renewals IS 'Certificate renewal requests and processing';
