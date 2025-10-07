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
            <div id="cookie-consent-banner" style="
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
                        <button class="cookie-btn btn-accept-all" onclick="cookieConsent.acceptAll()">
                            ✅ Accept All
                        </button>
                        <button class="cookie-btn btn-reject-all" onclick="cookieConsent.rejectAll()">
                            ❌ Necessary Only
                        </button>
                        <button class="cookie-btn btn-customize" onclick="cookieConsent.customize()">
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
        const banner = document.getElementById('cookie-consent-banner');
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

        // Open customization page
        customize: function() {
            window.location.href = '/public/cookie-consent.html';
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
            if (!document.getElementById('cookie-consent-banner')) {
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
            // Delay banner by 1 second for better UX
            setTimeout(createBanner, 1000);
        });
    } else if (!hasConsent()) {
        // Document already loaded
        setTimeout(createBanner, 1000);
    }

    // Export for module systems
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = window.cookieConsent;
    }
})();
