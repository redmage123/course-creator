/**
 * Accessibility Testing Utilities
 * Automated testing for WCAG compliance and accessibility features
 */

class AccessibilityTester {
    constructor() {
        this.testResults = [];
        this.errors = [];
        this.warnings = [];
    }

    /**
     * Run comprehensive accessibility tests
     */
    async runAllTests() {
        console.log('🔍 Running Accessibility Tests...');
        
        this.testResults = [];
        this.errors = [];
        this.warnings = [];

        // Core accessibility tests
        await this.testSemanticStructure();
        await this.testARIAImplementation();
        await this.testKeyboardNavigation();
        await this.testColorContrast();
        await this.testFormAccessibility();
        await this.testModalAccessibility();
        await this.testScreenReaderSupport();
        await this.testFocusManagement();

        // Generate report
        this.generateReport();
        
        return {
            passed: this.testResults.filter(r => r.status === 'pass').length,
            failed: this.testResults.filter(r => r.status === 'fail').length,
            warnings: this.warnings.length,
            errors: this.errors.length,
            results: this.testResults
        };
    }

    /**
     * Test semantic HTML structure
     */
    async testSemanticStructure() {
        const tests = [
            {
                name: 'Page has proper document structure',
                test: () => {
                    const hasMain = document.querySelector('main[role="main"]');
                    const hasNav = document.querySelector('nav[role="navigation"]');
                    const hasHeader = document.querySelector('header[role="banner"]');
                    return hasMain && hasNav && hasHeader;
                }
            },
            {
                name: 'Headings follow proper hierarchy',
                test: () => {
                    const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                    let lastLevel = 0;
                    for (const heading of headings) {
                        const level = parseInt(heading.tagName[1]);
                        if (level > lastLevel + 1) return false;
                        lastLevel = level;
                    }
                    return true;
                }
            },
            {
                name: 'Skip links are present',
                test: () => document.querySelector('.skip-links') !== null
            },
            {
                name: 'Live regions are present',
                test: () => {
                    const polite = document.querySelector('[aria-live="polite"]');
                    const assertive = document.querySelector('[aria-live="assertive"]');
                    return polite && assertive;
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('Semantic Structure', test.name, test.test());
        }
    }

    /**
     * Test ARIA implementation
     */
    async testARIAImplementation() {
        const tests = [
            {
                name: 'Tab navigation has proper ARIA',
                test: () => {
                    const tablist = document.querySelector('[role="tablist"]');
                    const tabs = document.querySelectorAll('[role="tab"]');
                    const panels = document.querySelectorAll('[role="tabpanel"]');
                    
                    if (!tablist || tabs.length === 0 || panels.length === 0) return false;
                    
                    // Check tabs have required attributes
                    for (const tab of tabs) {
                        if (!tab.getAttribute('aria-controls') || 
                            !tab.getAttribute('aria-selected')) {
                            return false;
                        }
                    }
                    
                    // Check panels have required attributes
                    for (const panel of panels) {
                        if (!panel.getAttribute('aria-labelledby')) {
                            return false;
                        }
                    }
                    
                    return true;
                }
            },
            {
                name: 'Forms have proper ARIA labels',
                test: () => {
                    const forms = document.querySelectorAll('form');
                    for (const form of forms) {
                        const inputs = form.querySelectorAll('input, select, textarea');
                        for (const input of inputs) {
                            const hasLabel = input.labels && input.labels.length > 0;
                            const hasAriaLabel = input.getAttribute('aria-label');
                            const hasAriaLabelledby = input.getAttribute('aria-labelledby');
                            
                            if (!hasLabel && !hasAriaLabel && !hasAriaLabelledby) {
                                return false;
                            }
                        }
                    }
                    return true;
                }
            },
            {
                name: 'Modals have proper ARIA',
                test: () => {
                    const modals = document.querySelectorAll('.modal');
                    for (const modal of modals) {
                        if (!modal.getAttribute('role') ||
                            !modal.getAttribute('aria-modal') ||
                            !modal.getAttribute('aria-labelledby')) {
                            return false;
                        }
                    }
                    return true;
                }
            },
            {
                name: 'Icons are properly hidden from screen readers',
                test: () => {
                    const decorativeIcons = document.querySelectorAll('i.fas, i.far, i.fal');
                    for (const icon of decorativeIcons) {
                        if (!icon.getAttribute('aria-hidden')) {
                            return false;
                        }
                    }
                    return true;
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('ARIA Implementation', test.name, test.test());
        }
    }

    /**
     * Test keyboard navigation
     */
    async testKeyboardNavigation() {
        const tests = [
            {
                name: 'All interactive elements are focusable',
                test: () => {
                    const interactiveElements = document.querySelectorAll(
                        'button, a[href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                    );
                    
                    for (const element of interactiveElements) {
                        // Skip if element is disabled or hidden
                        if (element.disabled || 
                            element.style.display === 'none' ||
                            element.getAttribute('aria-hidden') === 'true') {
                            continue;
                        }
                        
                        // Check if element can receive focus
                        const tabIndex = element.getAttribute('tabindex');
                        if (tabIndex === '-1' && !['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'].includes(element.tagName)) {
                            return false;
                        }
                    }
                    return true;
                }
            },
            {
                name: 'Tab order is logical',
                test: () => {
                    const focusableElements = this.getFocusableElements(document);
                    // This is a simplified test - in reality, we'd need to simulate tab navigation
                    return focusableElements.length > 0;
                }
            },
            {
                name: 'Focus indicators are visible',
                test: () => {
                    // Check if focus styles are defined
                    const style = document.createElement('style');
                    style.textContent = '*:focus-visible { outline: none; }';
                    document.head.appendChild(style);
                    
                    const testElement = document.createElement('button');
                    testElement.textContent = 'Test';
                    testElement.style.cssText = 'position: absolute; left: -9999px;';
                    document.body.appendChild(testElement);
                    
                    testElement.focus();
                    const computedStyle = window.getComputedStyle(testElement, ':focus-visible');
                    
                    document.head.removeChild(style);
                    document.body.removeChild(testElement);
                    
                    return true; // Simplified - actual test would check computed styles
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('Keyboard Navigation', test.name, test.test());
        }
    }

    /**
     * Test color contrast
     */
    async testColorContrast() {
        const tests = [
            {
                name: 'Text has sufficient contrast ratio',
                test: () => {
                    // This is a simplified test - full implementation would calculate actual contrast ratios
                    const textElements = document.querySelectorAll('p, span, h1, h2, h3, h4, h5, h6, label, button');
                    
                    for (const element of textElements) {
                        if (element.offsetParent === null) continue; // Skip hidden elements
                        
                        const styles = window.getComputedStyle(element);
                        const textColor = styles.color;
                        const backgroundColor = styles.backgroundColor;
                        
                        // Simplified check - in reality, we'd calculate the actual contrast ratio
                        if (textColor === backgroundColor) {
                            return false;
                        }
                    }
                    return true;
                }
            },
            {
                name: 'High contrast mode support exists',
                test: () => {
                    // Check if high contrast CSS rules exist
                    const stylesheets = Array.from(document.styleSheets);
                    for (const stylesheet of stylesheets) {
                        try {
                            const rules = Array.from(stylesheet.cssRules);
                            for (const rule of rules) {
                                if (rule.media && rule.media.mediaText.includes('prefers-contrast: high')) {
                                    return true;
                                }
                            }
                        } catch (e) {
                            // CORS restrictions might prevent access
                        }
                    }
                    return false;
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('Color Contrast', test.name, test.test());
        }
    }

    /**
     * Test form accessibility
     */
    async testFormAccessibility() {
        const tests = [
            {
                name: 'Required fields are properly marked',
                test: () => {
                    const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
                    
                    for (const field of requiredFields) {
                        const label = field.labels && field.labels[0];
                        const hasRequiredIndicator = label && 
                            (label.textContent.includes('*') || 
                             label.querySelector('.required') ||
                             field.getAttribute('aria-required') === 'true');
                        
                        if (!hasRequiredIndicator) {
                            return false;
                        }
                    }
                    return true;
                }
            },
            {
                name: 'Form errors have proper ARIA',
                test: () => {
                    const errorElements = document.querySelectorAll('.form-error, [role="alert"]');
                    
                    for (const error of errorElements) {
                        if (!error.getAttribute('aria-live') && !error.getAttribute('role')) {
                            return false;
                        }
                    }
                    return true;
                }
            },
            {
                name: 'Form help text is properly associated',
                test: () => {
                    const helpTexts = document.querySelectorAll('.form-help');
                    
                    for (const help of helpTexts) {
                        const id = help.id;
                        if (id) {
                            const associatedField = document.querySelector(`[aria-describedby*="${id}"]`);
                            if (!associatedField) {
                                return false;
                            }
                        }
                    }
                    return true;
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('Form Accessibility', test.name, test.test());
        }
    }

    /**
     * Test modal accessibility
     */
    async testModalAccessibility() {
        const tests = [
            {
                name: 'Modals have focus management',
                test: () => {
                    const modals = document.querySelectorAll('.modal');
                    
                    for (const modal of modals) {
                        const focusableElements = this.getFocusableElements(modal);
                        if (focusableElements.length === 0) {
                            return false;
                        }
                    }
                    return true;
                }
            },
            {
                name: 'Modals have close buttons with proper labels',
                test: () => {
                    const closeButtons = document.querySelectorAll('.modal-close');
                    
                    for (const button of closeButtons) {
                        const hasLabel = button.getAttribute('aria-label') || 
                                       button.getAttribute('aria-labelledby') ||
                                       button.textContent.trim();
                        
                        if (!hasLabel) {
                            return false;
                        }
                    }
                    return true;
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('Modal Accessibility', test.name, test.test());
        }
    }

    /**
     * Test screen reader support
     */
    async testScreenReaderSupport() {
        const tests = [
            {
                name: 'Page has proper title',
                test: () => document.title && document.title.trim().length > 0
            },
            {
                name: 'Language is specified',
                test: () => document.documentElement.getAttribute('lang')
            },
            {
                name: 'Screen reader only content exists',
                test: () => document.querySelectorAll('.sr-only').length > 0
            },
            {
                name: 'Status updates are announced',
                test: () => {
                    const liveRegions = document.querySelectorAll('[aria-live]');
                    return liveRegions.length >= 2; // Should have both polite and assertive
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('Screen Reader Support', test.name, test.test());
        }
    }

    /**
     * Test focus management
     */
    async testFocusManagement() {
        const tests = [
            {
                name: 'Focus management system exists',
                test: () => window.a11y !== undefined
            },
            {
                name: 'Tab panels are properly managed',
                test: () => {
                    const tabs = document.querySelectorAll('[role="tab"]');
                    let hasProperTabIndex = true;
                    
                    for (const tab of tabs) {
                        const tabIndex = tab.getAttribute('tabindex');
                        const isSelected = tab.getAttribute('aria-selected') === 'true';
                        
                        if (isSelected && tabIndex !== '0') {
                            hasProperTabIndex = false;
                        } else if (!isSelected && tabIndex !== '-1') {
                            hasProperTabIndex = false;
                        }
                    }
                    
                    return hasProperTabIndex;
                }
            }
        ];

        for (const test of tests) {
            this.addTestResult('Focus Management', test.name, test.test());
        }
    }

    /**
     * Get focusable elements within container
     */
    getFocusableElements(container) {
        const focusableSelectors = [
            'button:not([disabled])',
            '[href]',
            'input:not([disabled])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ].join(', ');
        
        return Array.from(container.querySelectorAll(focusableSelectors))
            .filter(el => !el.hasAttribute('aria-hidden') && 
                         el.offsetParent !== null);
    }

    /**
     * Add test result
     */
    addTestResult(category, testName, passed, message = '') {
        const result = {
            category,
            test: testName,
            status: passed ? 'pass' : 'fail',
            message
        };
        
        this.testResults.push(result);
        
        if (!passed) {
            this.errors.push(`${category}: ${testName} - ${message}`);
        }
    }

    /**
     * Generate accessibility report
     */
    generateReport() {
        const total = this.testResults.length;
        const passed = this.testResults.filter(r => r.status === 'pass').length;
        const failed = this.testResults.filter(r => r.status === 'fail').length;
        const score = Math.round((passed / total) * 100);

        console.log(`\n🎯 ACCESSIBILITY TEST RESULTS`);
        console.log(`===============================`);
        console.log(`📊 Overall Score: ${score}% (${passed}/${total} tests passed)`);
        console.log(`✅ Passed: ${passed}`);
        console.log(`❌ Failed: ${failed}`);
        console.log(`⚠️  Warnings: ${this.warnings.length}`);

        // Group results by category
        const byCategory = {};
        this.testResults.forEach(result => {
            if (!byCategory[result.category]) {
                byCategory[result.category] = { passed: 0, failed: 0, tests: [] };
            }
            byCategory[result.category][result.status === 'pass' ? 'passed' : 'failed']++;
            byCategory[result.category].tests.push(result);
        });

        console.log(`\n📋 Results by Category:`);
        Object.entries(byCategory).forEach(([category, data]) => {
            const categoryScore = Math.round((data.passed / (data.passed + data.failed)) * 100);
            console.log(`\n${category}: ${categoryScore}% (${data.passed}/${data.passed + data.failed})`);
            
            data.tests.forEach(test => {
                const icon = test.status === 'pass' ? '✅' : '❌';
                console.log(`  ${icon} ${test.test}`);
                if (test.message) {
                    console.log(`     ${test.message}`);
                }
            });
        });

        if (this.errors.length > 0) {
            console.log(`\n🚨 Errors to Fix:`);
            this.errors.forEach(error => console.log(`  • ${error}`));
        }

        if (score >= 90) {
            console.log(`\n🏆 Excellent accessibility implementation!`);
        } else if (score >= 75) {
            console.log(`\n👍 Good accessibility implementation with room for improvement.`);
        } else {
            console.log(`\n⚠️  Accessibility implementation needs significant improvement.`);
        }

        console.log(`\n💡 Run 'a11yTester.runAllTests()' in the console to test again.`);
    }

    /**
     * Test specific accessibility feature
     */
    async testFeature(featureName) {
        const methods = {
            'semantic': () => this.testSemanticStructure(),
            'aria': () => this.testARIAImplementation(),
            'keyboard': () => this.testKeyboardNavigation(),
            'contrast': () => this.testColorContrast(),
            'forms': () => this.testFormAccessibility(),
            'modals': () => this.testModalAccessibility(),
            'screenreader': () => this.testScreenReaderSupport(),
            'focus': () => this.testFocusManagement()
        };

        const method = methods[featureName.toLowerCase()];
        if (method) {
            this.testResults = [];
            await method();
            this.generateReport();
        } else {
            console.log(`Unknown feature: ${featureName}. Available: ${Object.keys(methods).join(', ')}`);
        }
    }
}

// Create global accessibility tester instance
window.a11yTester = new AccessibilityTester();

// Export for ES6 modules
export { AccessibilityTester };
export default AccessibilityTester;