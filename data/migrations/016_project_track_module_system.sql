-- Migration 016: Project and Module Management System
-- Adds comprehensive project and module management for organization admins

-- =============================================================================
-- PROJECTS TABLE - Main project container for tracks and modules
-- =============================================================================

CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    target_roles JSONB DEFAULT '[]',
    duration_weeks INTEGER,
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, slug)
);

-- =============================================================================
-- PROJECT TRACKS - Associate tracks with projects
-- =============================================================================

-- Add project_id column to tracks table to link tracks to projects
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;

-- Add default track templates for common specialties
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS is_template BOOLEAN DEFAULT false;
ALTER TABLE tracks ADD COLUMN IF NOT EXISTS template_category VARCHAR(100);

-- =============================================================================
-- MODULES TABLE - Course content modules within tracks
-- =============================================================================

CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    module_order INTEGER NOT NULL DEFAULT 1,
    estimated_duration_hours DECIMAL(5,2),
    learning_objectives JSONB DEFAULT '[]',
    prerequisites JSONB DEFAULT '[]',
    
    -- AI-generated content fields
    ai_description_prompt TEXT, -- Original description provided by user for AI generation
    content_generation_status VARCHAR(50) DEFAULT 'pending' CHECK (content_generation_status IN ('pending', 'generating', 'completed', 'failed', 'needs_review')),
    generated_syllabus TEXT, -- AI-generated syllabus content
    generated_slides JSONB, -- AI-generated slide content
    generated_quizzes JSONB, -- AI-generated quiz content
    lab_environment_config JSONB, -- Lab environment configuration
    
    -- RAG integration fields
    rag_context_used TEXT, -- RAG context that was used for content generation
    rag_quality_score DECIMAL(5,2), -- Quality score from RAG system
    generation_metadata JSONB, -- Additional generation metadata
    
    -- Module lifecycle
    approval_status VARCHAR(50) DEFAULT 'draft' CHECK (approval_status IN ('draft', 'pending_approval', 'approved', 'rejected', 'needs_revision')),
    approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    approved_at TIMESTAMP WITH TIME ZONE,
    
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- MODULE CONTENT ITEMS - Detailed content within modules
-- =============================================================================

CREATE TABLE IF NOT EXISTS module_content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL CHECK (content_type IN ('syllabus', 'slide', 'quiz', 'exercise', 'lab', 'reading', 'video')),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    content_data JSONB, -- Structured content data (quiz questions, slide layouts, etc.)
    item_order INTEGER NOT NULL DEFAULT 1,
    
    -- AI generation tracking
    generated_by_ai BOOLEAN DEFAULT false,
    ai_prompt_used TEXT,
    rag_enhanced BOOLEAN DEFAULT false,
    generation_quality_score DECIMAL(5,2),
    
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- PROJECT MEMBERSHIPS - Users assigned to projects
-- =============================================================================

CREATE TABLE IF NOT EXISTS project_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('participant', 'instructor', 'mentor', 'admin')),
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP WITH TIME ZONE,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'active', 'completed', 'dropped', 'suspended')),
    UNIQUE(project_id, user_id)
);

-- =============================================================================
-- CONTENT GENERATION REQUESTS - Track AI content generation requests
-- =============================================================================

CREATE TABLE IF NOT EXISTS content_generation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    request_type VARCHAR(50) NOT NULL CHECK (request_type IN ('full_module', 'syllabus', 'slides', 'quizzes', 'exercises')),
    user_description TEXT NOT NULL, -- Description provided by user for AI generation
    
    -- RAG integration
    rag_query_used TEXT,
    rag_context_retrieved TEXT,
    rag_enhancement_applied BOOLEAN DEFAULT false,
    
    -- Generation status and results
    generation_status VARCHAR(50) DEFAULT 'pending' CHECK (generation_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    generated_content JSONB,
    error_message TEXT,
    quality_assessment JSONB, -- Quality metrics and feedback
    
    -- User feedback and iteration
    user_feedback TEXT,
    requires_revision BOOLEAN DEFAULT false,
    revision_notes TEXT,
    
    requested_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    reviewed_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- DEFAULT TRACK TEMPLATES - Pre-configured track templates
-- =============================================================================

-- Insert default track templates for common specialties
INSERT INTO tracks (organization_id, name, description, difficulty_level, estimated_duration_hours, is_template, template_category, learning_objectives) 
VALUES 
    (
        (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
        'Application Development Track',
        'Comprehensive training for software application developers covering full-stack development, testing, and deployment',
        'intermediate',
        160,
        true,
        'software_development',
        '["Develop full-stack web applications", "Implement automated testing strategies", "Deploy applications to cloud platforms", "Follow software development best practices", "Collaborate effectively in development teams"]'::jsonb
    ),
    (
        (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
        'Business Analyst Track',
        'Training program for business analysts focusing on requirements gathering, process analysis, and stakeholder communication',
        'beginner',
        120,
        true,
        'business_analysis',
        '["Gather and document business requirements", "Analyze business processes and workflows", "Create process models and documentation", "Facilitate stakeholder communications", "Support project delivery and change management"]'::jsonb
    ),
    (
        (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
        'DevOps Engineer Track',
        'DevOps engineering track covering infrastructure automation, CI/CD pipelines, and cloud operations',
        'advanced',
        200,
        true,
        'devops',
        '["Implement Infrastructure as Code", "Build and maintain CI/CD pipelines", "Manage cloud infrastructure and services", "Implement monitoring and logging solutions", "Ensure security and compliance in operations"]'::jsonb
    ),
    (
        (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
        'Data Science Track',
        'Data science specialization covering data analysis, machine learning, and statistical modeling',
        'intermediate',
        180,
        true,
        'data_science',
        '["Perform exploratory data analysis", "Build predictive models using machine learning", "Visualize data insights effectively", "Work with big data technologies", "Communicate findings to stakeholders"]'::jsonb
    ),
    (
        (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
        'Cybersecurity Specialist Track',
        'Cybersecurity training focusing on threat assessment, security implementation, and incident response',
        'advanced',
        160,
        true,
        'cybersecurity',
        '["Assess and mitigate security threats", "Implement security controls and policies", "Respond to security incidents", "Conduct security audits and assessments", "Design secure system architectures"]'::jsonb
    )
ON CONFLICT DO NOTHING;

-- =============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Project indexes
CREATE INDEX IF NOT EXISTS idx_projects_organization ON projects(organization_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_dates ON projects(start_date, end_date);

-- Module indexes
CREATE INDEX IF NOT EXISTS idx_modules_track ON modules(track_id);
CREATE INDEX IF NOT EXISTS idx_modules_created_by ON modules(created_by);
CREATE INDEX IF NOT EXISTS idx_modules_order ON modules(track_id, module_order);
CREATE INDEX IF NOT EXISTS idx_modules_status ON modules(content_generation_status, approval_status);

-- Module content item indexes
CREATE INDEX IF NOT EXISTS idx_module_content_module ON module_content_items(module_id);
CREATE INDEX IF NOT EXISTS idx_module_content_type ON module_content_items(content_type);
CREATE INDEX IF NOT EXISTS idx_module_content_order ON module_content_items(module_id, item_order);

-- Project membership indexes
CREATE INDEX IF NOT EXISTS idx_project_memberships_project ON project_memberships(project_id);
CREATE INDEX IF NOT EXISTS idx_project_memberships_user ON project_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_project_memberships_role ON project_memberships(role);

-- Content generation request indexes
CREATE INDEX IF NOT EXISTS idx_content_gen_module ON content_generation_requests(module_id);
CREATE INDEX IF NOT EXISTS idx_content_gen_requested_by ON content_generation_requests(requested_by);
CREATE INDEX IF NOT EXISTS idx_content_gen_status ON content_generation_requests(generation_status);

-- Track template indexes
CREATE INDEX IF NOT EXISTS idx_tracks_template ON tracks(is_template, template_category);
CREATE INDEX IF NOT EXISTS idx_tracks_project ON tracks(project_id);

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =============================================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add updated_at triggers
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_modules_updated_at BEFORE UPDATE ON modules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_module_content_items_updated_at BEFORE UPDATE ON module_content_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for project summary with track and module counts
CREATE OR REPLACE VIEW project_summary AS
SELECT 
    p.id,
    p.organization_id,
    p.name,
    p.slug,
    p.description,
    p.status,
    p.start_date,
    p.end_date,
    p.current_participants,
    p.max_participants,
    COUNT(DISTINCT t.id) as track_count,
    COUNT(DISTINCT m.id) as module_count,
    COUNT(DISTINCT pm.user_id) as enrolled_users,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN tracks t ON t.project_id = p.id
LEFT JOIN modules m ON m.track_id = t.id
LEFT JOIN project_memberships pm ON pm.project_id = p.id AND pm.status = 'enrolled'
GROUP BY p.id, p.organization_id, p.name, p.slug, p.description, p.status, 
         p.start_date, p.end_date, p.current_participants, p.max_participants,
         p.created_at, p.updated_at;

-- View for module progress within tracks
CREATE OR REPLACE VIEW module_progress_summary AS
SELECT 
    m.id,
    m.track_id,
    m.name,
    m.module_order,
    m.content_generation_status,
    m.approval_status,
    COUNT(DISTINCT mci.id) as content_item_count,
    COUNT(DISTINCT CASE WHEN mci.is_published THEN mci.id END) as published_items,
    COALESCE(ROUND((COUNT(DISTINCT CASE WHEN mci.is_published THEN mci.id END) * 100.0 / NULLIF(COUNT(DISTINCT mci.id), 0)), 2), 0) as completion_percentage,
    m.created_at,
    m.updated_at
FROM modules m
LEFT JOIN module_content_items mci ON mci.module_id = m.id
GROUP BY m.id, m.track_id, m.name, m.module_order, m.content_generation_status, 
         m.approval_status, m.created_at, m.updated_at;

-- =============================================================================
-- PERMISSIONS AND SECURITY
-- =============================================================================

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA course_creator TO course_creator_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA course_creator TO course_creator_app;

-- =============================================================================
-- MIGRATION COMPLETE
-- =============================================================================

SELECT 'Migration 016: Project and Module Management System completed successfully' as status;