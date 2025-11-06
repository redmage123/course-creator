/**
 * Cookie Consent Banner - GDPR/CCPA/PIPEDA Compliant
 *
 * This script creates a cookie consent banner that appears on first visit
 * and allows users to manage their privacy preferences.
 *
 * LEGAL COMPLIANCE:
 * - GDPR Article 7: Consent must be freely given, specific, informed, and unambiguous
 * - GDPR Article 7(3): Withdrawal must be as easy as giving consent
 * - CCPA: "Do Not Sell My Personal Information" option
 * - PIPEDA: Clear consent with easy withdrawal
 */

(function() {
    const API_BASE_URL = '/api/v1/privacy';
    const PRIVACY_POLICY_VERSION = '3.3.0';

    // Check if consent has already been given
    function hasConsent() {
        return localStorage.getItem('cookie_consent_given') === 'true';
    }

    // Get or create session ID
    function getSessionId() {
        let sessionId = localStorage.getItem('guest_session_id');
        if (!sessionId) {
            sessionId = generateUUID();
            localStorage.setItem('guest_session_id', sessionId);
        }
        return sessionId;
    }

    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // Create and inject banner HTML
    function createBanner() {
        const bannerHTML = `
            <div id="cookie-banner" style="
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                animation: slideUp 0.5s ease-out;
            ">
                <style>
                    @keyframes slideUp {
                        from { transform: translateY(100%); }
                        to { transform: translateY(0); }
                    }

                    @keyframes fadeOut {
                        from { opacity: 1; }
                        to { opacity: 0; }
                    }

                    .cookie-banner-content {
                        max-width: 1200px;
                        margin: 0 auto;
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        gap: 20px;
                        flex-wrap: wrap;
                    }

                    .cookie-banner-text {
                        flex: 1;
                        min-width: 300px;
                    }

                    .cookie-banner-text h3 {
                        margin: 0 0 10px 0;
                        font-size: 20px;
                        font-weight: 600;
                    }

                    .cookie-banner-text p {
                        margin: 0;
                        opacity: 0.95;
                        line-height: 1.5;
                        font-size: 14px;
                    }

                    .cookie-banner-buttons {
                        display: flex;
                        gap: 10px;
                        flex-wrap: wrap;
                    }

                    .cookie-btn {
                        padding: 12px 24px;
                        border: none;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s;
                        white-space: nowrap;
                    }

                    .cookie-btn:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    }

                    .btn-accept-all {
                        background: #27ae60;
                        color: white;
                    }

                    .btn-accept-all:hover {
                        background: #229954;
                    }

                    .btn-reject-all {
                        background: #e74c3c;
                        color: white;
                    }

                    .btn-reject-all:hover {
                        background: #c0392b;
                    }

                    .btn-customize {
                        background: white;
                        color: #667eea;
                    }

                    .btn-customize:hover {
                        background: #f0f0f0;
                    }

                    .cookie-banner-links {
                        width: 100%;
                        margin-top: 10px;
                        font-size: 12px;
                        opacity: 0.9;
                    }

                    .cookie-banner-links a {
                        color: white;
                        text-decoration: underline;
                        margin-right: 15px;
                    }

                    .cookie-banner-links a:hover {
                        opacity: 0.8;
                    }

                    @media (max-width: 768px) {
                        .cookie-banner-content {
                            flex-direction: column;
                            align-items: stretch;
                        }

                        .cookie-banner-buttons {
                            flex-direction: column;
                        }

                        .cookie-btn {
                            width: 100%;
                        }
                    }
                </style>

                <div class="cookie-banner-content">
                    <div class="cookie-banner-text">
                        <h3>🍪 We Value Your Privacy</h3>
                        <p>
                            We use cookies to provide personalized demo experiences and improve our platform.
                            Your data is stored for max 30 days and never shared with third parties.
                            You can change your preferences or delete your data at any time.
                        </p>
                    </div>
                    <div class="cookie-banner-buttons">
                        <button id="accept-all-cookies" class="cookie-btn btn-accept-all" onclick="cookieConsent.acceptAll()">
                            ✅ Accept All
                        </button>
                        <button id="reject-all-cookies" class="cookie-btn btn-reject-all" onclick="cookieConsent.rejectAll()">
                            ❌ Necessary Only
                        </button>
                        <button id="customize-cookies" class="cookie-btn btn-customize" onclick="cookieConsent.showCustomize()">
                            ⚙️ Customize
                        </button>
                    </div>
                    <div class="cookie-banner-links">
                        <a href="/public/privacy-policy.html" target="_blank">Privacy Policy</a>
                        <a href="/public/cookie-policy.html" target="_blank">Cookie Policy</a>
                        <a href="/public/cookie-consent.html" target="_blank">Manage Preferences</a>
                        <a href="#" onclick="cookieConsent.ccpaOptOut(event)">Do Not Sell (CCPA)</a>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', bannerHTML);
    }

    // Save consent to backend
    async function saveConsent(preferences) {
        const sessionId = getSessionId();

        try {
            const response = await fetch(`${API_BASE_URL}/guest-session/${sessionId}/consent`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...preferences,
                    privacy_policy_version: PRIVACY_POLICY_VERSION
                })
            });

            if (response.ok) {
                localStorage.setItem('cookie_consent_given', 'true');
                localStorage.setItem('cookie_preferences', JSON.stringify(preferences));
                return true;
            } else {
                console.error('Failed to save consent preferences');
                return false;
            }
        } catch (error) {
            console.error('Error saving consent:', error);
            return false;
        }
    }

    // Hide banner with animation
    function hideBanner() {
        const banner = document.getElementById('cookie-banner');
        if (banner) {
            banner.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => {
                banner.remove();
            }, 300);
        }
    }

    // Public API
    window.cookieConsent = {
        // Accept all cookies
        acceptAll: async function() {
            const preferences = {
                functional_cookies: true,
                analytics_cookies: true,
                marketing_cookies: true
            };

            const success = await saveConsent(preferences);
            if (success) {
                console.log('✅ All cookies accepted');
                hideBanner();

                // Notify the application
                window.dispatchEvent(new CustomEvent('cookieConsentChanged', {
                    detail: preferences
                }));
            }
        },

        // Reject all optional cookies (keep only necessary)
        rejectAll: async function() {
            const preferences = {
                functional_cookies: false,
                analytics_cookies: false,
                marketing_cookies: false
            };

            const success = await saveConsent(preferences);
            if (success) {
                console.log('❌ Optional cookies rejected');
                hideBanner();

                window.dispatchEvent(new CustomEvent('cookieConsentChanged', {
                    detail: preferences
                }));
            }
        },

        // Show customization modal
        showCustomize: function() {
            // Create modal if it doesn't exist
            if (!document.getElementById('cookie-customize-modal')) {
                const modalHTML = `
                    <div id="cookie-customize-modal" style="
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: rgba(0, 0, 0, 0.7);
                        z-index: 10001;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        animation: fadeIn 0.3s ease-out;
                    ">
                        <style>
                            @keyframes fadeIn {
                                from { opacity: 0; }
                                to { opacity: 1; }
                            }
                            .cookie-modal-content {
                                background: white;
                                padding: 30px;
                                border-radius: 12px;
                                max-width: 500px;
                                width: 90%;
                                max-height: 80vh;
                                overflow-y: auto;
                                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                            }
                            .cookie-modal-content h2 {
                                margin: 0 0 20px 0;
                                color: #2c3e50;
                            }
                            .cookie-option {
                                margin-bottom: 20px;
                                padding: 15px;
                                background: #f8f9fa;
                                border-radius: 8px;
                            }
                            .cookie-option label {
                                display: flex;
                                align-items: center;
                                gap: 12px;
                                cursor: pointer;
                                font-weight: 600;
                                color: #2c3e50;
                            }
                            .cookie-option input[type="checkbox"] {
                                width: 20px;
                                height: 20px;
                                cursor: pointer;
                            }
                            .cookie-option p {
                                margin: 8px 0 0 32px;
                                font-size: 13px;
                                color: #666;
                                line-height: 1.4;
                            }
                            .modal-buttons {
                                display: flex;
                                gap: 10px;
                                margin-top: 25px;
                            }
                            .modal-btn {
                                flex: 1;
                                padding: 12px;
                                border: none;
                                border-radius: 6px;
                                font-size: 14px;
                                font-weight: 600;
                                cursor: pointer;
                                transition: all 0.2s;
                            }
                            .btn-save {
                                background: #27ae60;
                                color: white;
                            }
                            .btn-save:hover {
                                background: #229954;
                            }
                            .btn-cancel {
                                background: #95a5a6;
                                color: white;
                            }
                            .btn-cancel:hover {
                                background: #7f8c8d;
                            }
                        </style>
                        <div class="cookie-modal-content">
                            <h2>Cookie Preferences</h2>

                            <div class="cookie-option">
                                <label>
                                    <input type="checkbox" id="functional-cookies" checked>
                                    <span>Functional Cookies</span>
                                </label>
                                <p>Essential for the demo to work. Remembers your session and preferences. (Always enabled)</p>
                            </div>

                            <div class="cookie-option">
                                <label>
                                    <input type="checkbox" id="analytics-cookies">
                                    <span>Analytics Cookies</span>
                                </label>
                                <p>Helps us understand which features you use and improve the demo experience.</p>
                            </div>

                            <div class="cookie-option">
                                <label>
                                    <input type="checkbox" id="marketing-cookies">
                                    <span>Marketing Cookies</span>
                                </label>
                                <p>Used for internal lead scoring. We never sell your data to third parties.</p>
                            </div>

                            <div class="modal-buttons">
                                <button id="save-cookie-preferences" class="modal-btn btn-save" onclick="cookieConsent.saveCustomPreferences()">
                                    Save Preferences
                                </button>
                                <button class="modal-btn btn-cancel" onclick="cookieConsent.hideCustomize()">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHTML);

                // Functional cookies always enabled
                document.getElementById('functional-cookies').addEventListener('click', function(e) {
                    e.preventDefault();
                    this.checked = true;
                });
            } else {
                document.getElementById('cookie-customize-modal').style.display = 'flex';
            }
        },

        // Hide customization modal
        hideCustomize: function() {
            const modal = document.getElementById('cookie-customize-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        },

        // Save custom preferences
        saveCustomPreferences: async function() {
            const functional = document.getElementById('functional-cookies').checked;
            const analytics = document.getElementById('analytics-cookies').checked;
            const marketing = document.getElementById('marketing-cookies').checked;

            const preferences = {
                functional_cookies: functional,
                analytics_cookies: analytics,
                marketing_cookies: marketing
            };

            const success = await saveConsent(preferences);
            if (success) {
                console.log('✅ Custom preferences saved');
                this.hideCustomize();
                hideBanner();

                window.dispatchEvent(new CustomEvent('cookieConsentChanged', {
                    detail: preferences
                }));
            }
        },

        // Keep old customize function for compatibility
        customize: function() {
            this.showCustomize();
        },

        // CCPA "Do Not Sell" opt-out
        ccpaOptOut: async function(event) {
            if (event) event.preventDefault();

            const sessionId = getSessionId();

            try {
                const response = await fetch(`${API_BASE_URL}/guest-session/${sessionId}/do-not-sell`, {
                    method: 'POST'
                });

                if (response.ok) {
                    alert('✅ You have successfully opted out of data selling. Marketing cookies have been disabled.');

                    // Update preferences
                    const preferences = {
                        functional_cookies: true,
                        analytics_cookies: false,
                        marketing_cookies: false
                    };

                    await saveConsent(preferences);
                    hideBanner();
                } else {
                    alert('❌ Error processing your request. Please try again.');
                }
            } catch (error) {
                alert('❌ Network error. Please try again.');
            }
        },

        // Show banner programmatically
        show: function() {
            if (!document.getElementById('cookie-banner')) {
                createBanner();
            }
        },

        // Hide banner programmatically
        hide: function() {
            hideBanner();
        },

        // Get current consent status
        getConsent: function() {
            const prefsString = localStorage.getItem('cookie_preferences');
            return prefsString ? JSON.parse(prefsString) : null;
        },

        // Check if user has given consent
        hasConsent: function() {
            return hasConsent();
        }
    };

    // Auto-show banner on page load if consent not given
    if (!hasConsent() && document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            // Show banner immediately for testing
            createBanner();
        });
    } else if (!hasConsent()) {
        // Document already loaded - show immediately
        createBanner();
    }

    // Export for module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.cookieConsent;
    }
})();
