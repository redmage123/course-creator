/**
 * Audience-to-Track Mapping Configuration
 *
 * BUSINESS CONTEXT:
 * Predefined mappings between target audiences (roles/professions) and appropriate
 * track configurations. Each audience type gets a tailored track with relevant
 * skills, difficulty level, and description optimized for that role.
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure configuration object (no logic)
 * - 20+ predefined audience types covering technical and business roles
 * - Used by wizard to auto-generate tracks based on selected audiences
 * - Track names follow NLP linguistic transformation patterns
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Configuration data only
 * - Open/Closed: Extensible by adding new audience types
 *
 * USAGE:
 * import { AUDIENCE_TRACK_MAPPING, getTrackConfigForAudience } from './audience-mapping.js';
 *
 * const config = getTrackConfigForAudience('application_developers');
 * // Returns: { name, description, difficulty, skills }
 *
 * @module projects/wizard/audience-mapping
 */
export const AUDIENCE_TRACK_MAPPING = {
    application_developers: {
        name: 'Application Development',
        description: 'Comprehensive training for software application development, covering modern programming practices, frameworks, and deployment strategies',
        difficulty: 'intermediate',
        skills: ['coding', 'software design', 'debugging', 'testing', 'deployment']
    },
    business_analysts: {
        name: 'Business Analysis',
        description: 'Requirements gathering and business process analysis training focused on stakeholder management and documentation',
        difficulty: 'beginner',
        skills: ['requirements analysis', 'documentation', 'stakeholder management', 'process modeling']
    },
    operations_engineers: {
        name: 'Operations Engineering',
        description: 'System operations, monitoring, and infrastructure management with emphasis on reliability and performance',
        difficulty: 'intermediate',
        skills: ['system administration', 'monitoring', 'troubleshooting', 'automation']
    },
    data_scientists: {
        name: 'Data Science',
        description: 'Data analysis, machine learning, and statistical modeling training with practical applications',
        difficulty: 'advanced',
        skills: ['data analysis', 'machine learning', 'statistics', 'Python', 'visualization']
    },
    qa_engineers: {
        name: 'QA Engineering',
        description: 'Quality assurance and testing methodologies including automation and continuous integration',
        difficulty: 'intermediate',
        skills: ['testing', 'automation', 'quality assurance', 'bug tracking', 'test planning']
    },
    devops_engineers: {
        name: 'DevOps Engineering',
        description: 'DevOps practices, CI/CD pipelines, containerization, and cloud infrastructure management',
        difficulty: 'advanced',
        skills: ['CI/CD', 'containerization', 'cloud platforms', 'infrastructure as code', 'automation']
    },
    security_engineers: {
        name: 'Security Engineering',
        description: 'Cybersecurity fundamentals, threat analysis, and security best practices',
        difficulty: 'advanced',
        skills: ['security analysis', 'threat modeling', 'penetration testing', 'compliance']
    },
    database_administrators: {
        name: 'Database Administration',
        description: 'Database design, optimization, backup strategies, and performance tuning',
        difficulty: 'intermediate',
        skills: ['database design', 'SQL', 'performance tuning', 'backup and recovery']
    },
    system_administrators: {
        name: 'System Administration',
        description: 'System configuration, maintenance, monitoring, and infrastructure management',
        difficulty: 'intermediate',
        skills: ['system configuration', 'Linux/Windows', 'scripting', 'monitoring', 'troubleshooting']
    },
    technical_architects: {
        name: 'Technical Architecture',
        description: 'System design, architectural patterns, scalability, and technical decision-making',
        difficulty: 'advanced',
        skills: ['system design', 'architectural patterns', 'scalability', 'cloud architecture', 'technical leadership']
    },
    product_managers: {
        name: 'Product Management',
        description: 'Product strategy, roadmap planning, stakeholder management, and feature prioritization',
        difficulty: 'intermediate',
        skills: ['product strategy', 'roadmap planning', 'stakeholder management', 'market research', 'prioritization']
    },
    project_managers: {
        name: 'Project Management',
        description: 'Project planning, team coordination, risk management, and delivery execution',
        difficulty: 'beginner',
        skills: ['project planning', 'agile methodologies', 'risk management', 'team coordination', 'stakeholder communication']
    },
    business_consultants: {
        name: 'Business Consulting',
        description: 'Business strategy, process improvement, change management, and client advisory',
        difficulty: 'advanced',
        skills: ['strategic analysis', 'process improvement', 'change management', 'client advisory', 'presentation skills']
    },
    data_analysts: {
        name: 'Data Analysis',
        description: 'Data exploration, statistical analysis, reporting, and business intelligence',
        difficulty: 'intermediate',
        skills: ['data visualization', 'SQL', 'Excel', 'statistical analysis', 'business intelligence']
    },
    data_engineers: {
        name: 'Data Engineering',
        description: 'Data pipeline development, ETL processes, data warehousing, and big data technologies',
        difficulty: 'advanced',
        skills: ['ETL development', 'data pipelines', 'SQL', 'big data technologies', 'data warehousing']
    },
    business_intelligence_analysts: {
        name: 'Business Intelligence Analysis',
        description: 'BI reporting, dashboard development, data modeling, and analytics',
        difficulty: 'intermediate',
        skills: ['BI tools', 'dashboard design', 'data modeling', 'SQL', 'analytics']
    },
    engineering_managers: {
        name: 'Engineering Management',
        description: 'Team leadership, technical mentorship, project delivery, and people management',
        difficulty: 'advanced',
        skills: ['team leadership', 'technical mentorship', 'performance management', 'hiring', 'strategic planning']
    },
    team_leads: {
        name: 'Team Leadership',
        description: 'Team coordination, technical guidance, sprint planning, and hands-on development',
        difficulty: 'intermediate',
        skills: ['team coordination', 'technical guidance', 'agile practices', 'code review', 'mentoring']
    },
    technical_directors: {
        name: 'Technical Direction',
        description: 'Technology strategy, architecture oversight, innovation, and cross-team leadership',
        difficulty: 'advanced',
        skills: ['technology strategy', 'architecture governance', 'innovation', 'cross-functional leadership', 'vendor management']
    },
    cto: {
        name: 'Technology Leadership',
        description: 'Technology vision, executive strategy, organizational transformation, and C-level decision-making',
        difficulty: 'advanced',
        skills: ['technology vision', 'strategic planning', 'organizational transformation', 'executive decision-making', 'board communication']
    }
};

/**
 * Get track configuration for a specific audience
 *
 * BUSINESS LOGIC:
 * Retrieves the predefined track configuration for a given audience identifier.
 * Returns null if audience is not found in the mapping.
 *
 * @param {string} audienceIdentifier - Underscore-separated audience identifier (e.g., 'application_developers')
 * @returns {Object|null} Track configuration or null if not found
 *
 * @example
 * const config = getTrackConfigForAudience('application_developers');
 * // Returns: { name: 'Application Development', description: '...', difficulty: 'intermediate', skills: [...] }
 */
export function getTrackConfigForAudience(audienceIdentifier) {
    return AUDIENCE_TRACK_MAPPING[audienceIdentifier] || null;
}

/**
 * Check if audience has predefined mapping
 *
 * @param {string} audienceIdentifier - Audience identifier to check
 * @returns {boolean} True if audience has predefined mapping
 *
 * @example
 * hasAudienceMapping('application_developers'); // true
 * hasAudienceMapping('unknown_role'); // false
 */
export function hasAudienceMapping(audienceIdentifier) {
    return audienceIdentifier in AUDIENCE_TRACK_MAPPING;
}

/**
 * Get all available audience identifiers
 *
 * @returns {string[]} Array of audience identifiers
 *
 * @example
 * const audiences = getAllAudienceIdentifiers();
 * // Returns: ['application_developers', 'business_analysts', ...]
 */
export function getAllAudienceIdentifiers() {
    return Object.keys(AUDIENCE_TRACK_MAPPING);
}

/**
 * Get audiences by difficulty level
 *
 * BUSINESS LOGIC:
 * Filters audiences based on training difficulty level.
 * Useful for organizing tracks by complexity.
 *
 * @param {string} difficulty - Difficulty level ('beginner'|'intermediate'|'advanced')
 * @returns {Object} Object mapping audience identifiers to their configurations
 *
 * @example
 * const beginnerAudiences = getAudiencesByDifficulty('beginner');
 * // Returns audiences with beginner-level tracks
 */
export function getAudiencesByDifficulty(difficulty) {
    const filtered = {};

    for (const [audience, config] of Object.entries(AUDIENCE_TRACK_MAPPING)) {
        if (config.difficulty === difficulty) {
            filtered[audience] = config;
        }
    }

    return filtered;
}

/**
 * Search audiences by skill
 *
 * BUSINESS LOGIC:
 * Finds all audiences whose tracks include a specific skill.
 * Useful for skill-based track recommendations.
 *
 * @param {string} skill - Skill to search for
 * @returns {string[]} Array of matching audience identifiers
 *
 * @example
 * const audiences = searchAudiencesBySkill('Python');
 * // Returns: ['data_scientists', ...]
 */
export function searchAudiencesBySkill(skill) {
    const skillLower = skill.toLowerCase();
    const matches = [];

    for (const [audience, config] of Object.entries(AUDIENCE_TRACK_MAPPING)) {
        const hasSkill = config.skills.some(s => s.toLowerCase().includes(skillLower));
        if (hasSkill) {
            matches.push(audience);
        }
    }

    return matches;
}

/**
 * Map multiple audiences to track configs
 *
 * BUSINESS LOGIC:
 * Convenience function to map an array of audience identifiers to their
 * full track configurations. Useful for batch operations.
 *
 * @param {string[]} audiences - Array of audience identifiers
 * @returns {Object[]} Array of track configurations with audience reference
 *
 * @example
 * const audiences = ['application_developers', 'data_scientists'];
 * const trackConfigs = mapAudiencesToConfigs(audiences);
 * // Returns array of track configs with audience field added
 */
export function mapAudiencesToConfigs(audiences) {
    if (!audiences || audiences.length === 0) {
        return [];
    }

    return audiences
        .map(audience => {
            const config = getTrackConfigForAudience(audience);
            if (!config) {
                return null;
            }
            return {
                ...config,
                audience: audience
            };
        })
        .filter(config => config !== null);
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Get specific audience config
 * ======================================
 * import { getTrackConfigForAudience } from './audience-mapping.js';
 *
 * const config = getTrackConfigForAudience('application_developers');
 * console.log(config.name); // "Application Development"
 * console.log(config.skills); // ['coding', 'software design', ...]
 *
 *
 * Example 2: Check if audience exists
 * ====================================
 * import { hasAudienceMapping } from './audience-mapping.js';
 *
 * if (hasAudienceMapping('application_developers')) {
 *   // Use predefined mapping
 * } else {
 *   // Generate track name using NLP
 * }
 *
 *
 * Example 3: Filter by difficulty
 * ================================
 * import { getAudiencesByDifficulty } from './audience-mapping.js';
 *
 * const beginnerTracks = getAudiencesByDifficulty('beginner');
 * // Returns only audiences with beginner-level training
 *
 *
 * Example 4: Search by skill
 * ===========================
 * import { searchAudiencesBySkill } from './audience-mapping.js';
 *
 * const pythonAudiences = searchAudiencesBySkill('Python');
 * console.log(pythonAudiences); // ['data_scientists', ...]
 *
 *
 * Example 5: Batch mapping
 * =========================
 * import { mapAudiencesToConfigs } from './audience-mapping.js';
 *
 * const selected = ['application_developers', 'qa_engineers'];
 * const trackConfigs = mapAudiencesToConfigs(selected);
 * // Returns array of full track configurations
 */