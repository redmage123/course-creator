/**
 * Track Name Generator (NLP-Based)
 *
 * BUSINESS CONTEXT:
 * Generates professional track names from audience identifiers using Natural
 * Language Processing (NLP) linguistic transformation rules. Converts profession
 * nouns (e.g., "developers") into discipline/field names (e.g., "Development").
 *
 * TECHNICAL IMPLEMENTATION:
 * - Applies morphological rules to transform profession → field/discipline
 * - Handles special cases (QA, DevOps, etc.)
 * - Returns properly capitalized track names
 * - Falls back to capitalization if no NLP rule matches
 *
 * LINGUISTIC TRANSFORMATIONS:
 * - developers → Development
 * - analysts → Analysis
 * - engineers → Engineering
 * - scientists → Science
 * - administrators → Administration
 *
 * SOLID PRINCIPLES:
 * - Single Responsibility: Track name generation only
 * - Open/Closed: Extensible by adding new transformation rules
 *
 * USAGE:
 * import { generateTrackName } from './track-generator.js';
 *
 * const trackName = generateTrackName('application_developers');
 * // Returns: "Application Development"
 *
 * @module projects/wizard/track-generator
 */
const PROFESSION_TO_FIELD = {
    // Plural forms (most common)
    'developers': 'Development',
    'analysts': 'Analysis',
    'engineers': 'Engineering',
    'scientists': 'Science',
    'administrators': 'Administration',
    'managers': 'Management',
    'consultants': 'Consulting',
    'architects': 'Architecture',
    'directors': 'Direction',
    'specialists': 'Specialization',
    'coordinators': 'Coordination',
    'leads': 'Leadership',

    // Singular forms (fallback)
    'developer': 'Development',
    'analyst': 'Analysis',
    'engineer': 'Engineering',
    'scientist': 'Science',
    'administrator': 'Administration',
    'manager': 'Management',
    'consultant': 'Consulting',
    'architect': 'Architecture',
    'director': 'Direction',
    'specialist': 'Specialization',
    'coordinator': 'Coordination',
    'lead': 'Leadership'
};

/**
 * Special case transformations
 *
 * BUSINESS CONTEXT:
 * Some roles don't follow standard morphological rules and need
 * special handling to maintain professional naming conventions.
 *
 * @constant
 * @type {Object.<string, string>}
 */
const SPECIAL_CASES = {
    'qa': 'QA',           // Quality Assurance (acronym)
    'devops': 'DevOps',   // Development Operations (compound)
    'cto': 'CTO',         // Chief Technology Officer (acronym)
    'cio': 'CIO',         // Chief Information Officer (acronym)
    'ceo': 'CEO',         // Chief Executive Officer (acronym)
    'ui': 'UI',           // User Interface (acronym)
    'ux': 'UX',           // User Experience (acronym)
    'api': 'API',         // Application Programming Interface (acronym)
    'bi': 'BI'            // Business Intelligence (acronym)
};

/**
 * Generate track name from audience identifier using NLP
 *
 * BUSINESS LOGIC:
 * Takes an underscore-separated audience identifier and generates a professional
 * track name by:
 * 1. Splitting identifier into words
 * 2. Identifying the profession word (last word)
 * 3. Applying linguistic transformation rules
 * 4. Capitalizing prefix words (with special case handling)
 * 5. Combining into final track name
 *
 * TECHNICAL IMPLEMENTATION:
 * - Pure function (no side effects)
 * - Handles edge cases gracefully
 * - Logs warnings for unknown professions
 * - Fallback to capitalization if no rule matches
 *
 * @param {string} audienceIdentifier - Underscore-separated role identifier
 * @returns {string} Properly formatted track name
 *
 * @example
 * // Standard transformation
 * generateTrackName('application_developers');
 * // Returns: "Application Development"
 *
 * @example
 * // Special case handling
 * generateTrackName('qa_engineers');
 * // Returns: "QA Engineering"
 *
 * @example
 * // Unknown profession (fallback)
 * generateTrackName('business_strategists');
 * // Returns: "Business Strategists" (with warning logged)
 */
export function generateTrackName(audienceIdentifier) {
    // Validate input
    if (!audienceIdentifier || typeof audienceIdentifier !== 'string') {
        console.warn('Invalid audience identifier:', audienceIdentifier);
        return 'Track';
    }

    // Split identifier into words
    const words = audienceIdentifier.split('_');

    if (words.length === 0) {
        return 'Track';
    }

    // Get the last word (profession/role)
    const profession = words[words.length - 1];

    // Get prefix words (modifiers like "application", "business", "senior", etc.)
    const prefixWords = words.slice(0, -1);

    // Apply linguistic transformation: Profession → Field/Discipline
    let fieldName = PROFESSION_TO_FIELD[profession.toLowerCase()];

    if (!fieldName) {
        // Fallback: Capitalize the profession if no NLP rule matches
        fieldName = profession.charAt(0).toUpperCase() + profession.slice(1);
        console.warn(`No NLP transformation rule for profession: ${profession}. Using fallback capitalization.`);
    }

    // Capitalize prefix words with special case handling
    const capitalizedPrefix = prefixWords.map(word => capitalizeWord(word));

    // Combine prefix + field name
    return [...capitalizedPrefix, fieldName].join(' ');
}

/**
 * Capitalize word with special case handling
 *
 * BUSINESS LOGIC:
 * Handles proper capitalization of words including:
 * - Acronyms (QA, DevOps, etc.)
 * - Standard words (Application, Business, etc.)
 *
 * @param {string} word - Word to capitalize
 * @returns {string} Properly capitalized word
 *
 * @example
 * capitalizeWord('application'); // "Application"
 * capitalizeWord('qa');          // "QA"
 * capitalizeWord('devops');      // "DevOps"
 */
function capitalizeWord(word) {
    if (!word) {
        return '';
    }

    const lowerWord = word.toLowerCase();

    // Check for special cases
    if (SPECIAL_CASES[lowerWord]) {
        return SPECIAL_CASES[lowerWord];
    }

    // Standard capitalization
    return word.charAt(0).toUpperCase() + word.slice(1);
}

/**
 * Generate track slug from audience identifier
 *
 * BUSINESS LOGIC:
 * Generates URL-friendly slug from audience identifier.
 * Useful for routing and API endpoints.
 *
 * @param {string} audienceIdentifier - Underscore-separated audience identifier
 * @returns {string} URL-friendly slug
 *
 * @example
 * generateTrackSlug('application_developers');
 * // Returns: "application-developers-track"
 */
export function generateTrackSlug(audienceIdentifier) {
    if (!audienceIdentifier) {
        return 'track';
    }

    // Replace underscores with hyphens and append '-track'
    return `${audienceIdentifier.replace(/_/g, '-')}-track`;
}

/**
 * Generate track description from audience identifier
 *
 * BUSINESS LOGIC:
 * Generates a generic but professional description for tracks
 * without predefined configurations. Uses track name for consistency.
 *
 * @param {string} audienceIdentifier - Underscore-separated audience identifier
 * @returns {string} Generic track description
 *
 * @example
 * generateTrackDescription('application_developers');
 * // Returns: "Training track tailored for Application Development professionals"
 */
export function generateTrackDescription(audienceIdentifier) {
    const trackName = generateTrackName(audienceIdentifier);
    return `Training track tailored for ${trackName} professionals`;
}

/**
 * Validate audience identifier format
 *
 * BUSINESS LOGIC:
 * Checks if audience identifier follows the expected format:
 * - Lowercase letters and underscores only
 * - At least one word
 * - No leading/trailing underscores
 *
 * @param {string} audienceIdentifier - Identifier to validate
 * @returns {boolean} True if valid format
 *
 * @example
 * validateAudienceIdentifier('application_developers'); // true
 * validateAudienceIdentifier('Application_Developers'); // false (uppercase)
 * validateAudienceIdentifier('_developers');            // false (leading underscore)
 */
export function validateAudienceIdentifier(audienceIdentifier) {
    if (!audienceIdentifier || typeof audienceIdentifier !== 'string') {
        return false;
    }

    // Check format: lowercase letters and underscores only
    const formatRegex = /^[a-z]+(_[a-z]+)*$/;
    return formatRegex.test(audienceIdentifier);
}

/**
 * Extract profession from audience identifier
 *
 * UTILITY:
 * Extracts the profession word (last word) from an audience identifier.
 * Useful for analytics and categorization.
 *
 * @param {string} audienceIdentifier - Audience identifier
 * @returns {string} Profession word
 *
 * @example
 * extractProfession('application_developers'); // "developers"
 * extractProfession('senior_qa_engineers');    // "engineers"
 */
export function extractProfession(audienceIdentifier) {
    if (!audienceIdentifier) {
        return '';
    }

    const words = audienceIdentifier.split('_');
    return words[words.length - 1] || '';
}

/**
 * Extract prefix modifiers from audience identifier
 *
 * UTILITY:
 * Extracts prefix words (modifiers) from an audience identifier.
 * Examples: "application", "senior", "business", etc.
 *
 * @param {string} audienceIdentifier - Audience identifier
 * @returns {string[]} Array of prefix words
 *
 * @example
 * extractPrefixes('application_developers'); // ["application"]
 * extractPrefixes('senior_qa_engineers');    // ["senior", "qa"]
 */
export function extractPrefixes(audienceIdentifier) {
    if (!audienceIdentifier) {
        return [];
    }

    const words = audienceIdentifier.split('_');
    return words.slice(0, -1);
}

/**
 * Check if profession has NLP transformation rule
 *
 * UTILITY:
 * Checks if a profession has a defined linguistic transformation rule.
 *
 * @param {string} profession - Profession word to check
 * @returns {boolean} True if transformation rule exists
 *
 * @example
 * hasProfessionRule('developers'); // true
 * hasProfessionRule('strategists'); // false
 */
export function hasProfessionRule(profession) {
    return profession.toLowerCase() in PROFESSION_TO_FIELD;
}

/**
 * Add custom profession transformation rule
 *
 * EXTENSIBILITY:
 * Allows adding custom profession-to-field transformations at runtime.
 * Useful for organization-specific role naming conventions.
 *
 * @param {string} profession - Profession word (lowercase)
 * @param {string} field - Field/discipline name (capitalized)
 *
 * @example
 * addProfessionRule('strategists', 'Strategy');
 * generateTrackName('business_strategists'); // Now returns "Business Strategy"
 */
export function addProfessionRule(profession, field) {
    if (!profession || !field) {
        console.warn('Both profession and field are required');
        return;
    }

    PROFESSION_TO_FIELD[profession.toLowerCase()] = field;
    console.log(`✅ Added profession rule: ${profession} → ${field}`);
}

/**
 * USAGE EXAMPLES:
 *
 * Example 1: Basic track name generation
 * ========================================
 * import { generateTrackName } from './track-generator.js';
 *
 * const trackName = generateTrackName('application_developers');
 * console.log(trackName); // "Application Development"
 *
 *
 * Example 2: Handle special cases
 * ================================
 * import { generateTrackName } from './track-generator.js';
 *
 * const qaTrack = generateTrackName('qa_engineers');
 * console.log(qaTrack); // "QA Engineering"
 *
 * const devopsTrack = generateTrackName('devops_engineers');
 * console.log(devopsTrack); // "DevOps Engineering"
 *
 *
 * Example 3: Generate track metadata
 * ====================================
 * import { generateTrackName, generateTrackSlug, generateTrackDescription } from './track-generator.js';
 *
 * const audience = 'data_scientists';
 * const trackData = {
 *   name: generateTrackName(audience),
 *   slug: generateTrackSlug(audience),
 *   description: generateTrackDescription(audience)
 * };
 * // Returns complete track metadata
 *
 *
 * Example 4: Validate audience identifier
 * =========================================
 * import { validateAudienceIdentifier } from './track-generator.js';
 *
 * if (validateAudienceIdentifier('application_developers')) {
 *   // Proceed with track generation
 * }
 *
 *
 * Example 5: Add custom transformation rule
 * ===========================================
 * import { addProfessionRule, generateTrackName } from './track-generator.js';
 *
 * // Add custom rule for organization-specific role
 * addProfessionRule('coaches', 'Coaching');
 * const trackName = generateTrackName('agile_coaches');
 * console.log(trackName); // "Agile Coaching"
 */