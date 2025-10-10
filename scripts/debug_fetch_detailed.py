#!/usr/bin/env python3
"""
Detailed debugging of fetch behavior inside handleCredentialsLogin
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_fetch():
    """Debug exactly what happens to the fetch call"""

    print("="*80)
    print("DETAILED FETCH DEBUGGING")
    print("="*80)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--ignore-certificate-errors',
                '--allow-insecure-localhost',
                '--window-position=0,0',
                '--window-size=1920,1080'
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )

        page = await context.new_page()

        # Log everything
        page.on('console', lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on('request', lambda request: print(f"[REQUEST] {request.method} {request.url}"))
        page.on('response', lambda response: print(f"[RESPONSE] {response.status} {response.url}"))
        page.on('requestfailed', lambda request: print(f"[FAILED] {request.url} - {request.failure}"))

        print("\n1. Loading login page...")
        await page.goto('https://localhost:3000/html/student-login.html',
                       wait_until='networkidle',
                       timeout=30000)
        await asyncio.sleep(2)

        print("\n2. Filling credentials...")
        await page.fill('#email', 'orgadmin@e2etest.com')
        await page.fill('#password', 'org_admin_password')

        print("\n3. Injecting detailed fetch monitoring...")
        await page.evaluate("""
            () => {
                // Override fetch to log everything
                const originalFetch = window.fetch;
                window.fetchCalls = [];

                window.fetch = function(...args) {
                    const callInfo = {
                        url: args[0],
                        options: args[1],
                        timestamp: new Date().toISOString(),
                        status: 'pending'
                    };
                    window.fetchCalls.push(callInfo);
                    console.log('[FETCH CALLED]', JSON.stringify(callInfo));

                    return originalFetch(...args)
                        .then(response => {
                            callInfo.status = 'resolved';
                            callInfo.responseStatus = response.status;
                            callInfo.responseOk = response.ok;
                            console.log('[FETCH RESOLVED]', JSON.stringify(callInfo));
                            return response;
                        })
                        .catch(error => {
                            callInfo.status = 'rejected';
                            callInfo.error = error.message;
                            callInfo.errorName = error.name;
                            callInfo.errorStack = error.stack;
                            console.log('[FETCH REJECTED]', JSON.stringify(callInfo));
                            throw error;
                        });
                };

                console.log('[FETCH MONITOR] Installed');
            }
        """)

        print("\n4. Calling handleCredentialsLogin with detailed logging...")
        result = await page.evaluate("""
            async () => {
                try {
                    console.log('[TEST] Starting handleCredentialsLogin call');

                    // Create a fake submit event
                    const form = document.getElementById('credentialsForm');
                    const fakeEvent = {
                        preventDefault: () => { console.log('[TEST] preventDefault called'); },
                        target: form
                    };

                    console.log('[TEST] About to call handleCredentialsLogin');

                    // Call the handler
                    const loginPromise = handleCredentialsLogin(fakeEvent);
                    console.log('[TEST] handleCredentialsLogin returned a promise');

                    // Wait for it to complete
                    await loginPromise;
                    console.log('[TEST] handleCredentialsLogin promise resolved');

                    return {
                        success: true,
                        fetchCalls: window.fetchCalls,
                        currentUrl: window.location.href
                    };
                } catch (error) {
                    console.log('[TEST] handleCredentialsLogin threw error:', error.message);
                    return {
                        success: false,
                        error: error.message,
                        errorName: error.name,
                        errorStack: error.stack,
                        fetchCalls: window.fetchCalls,
                        currentUrl: window.location.href
                    };
                }
            }
        """)

        print("\n" + "="*80)
        print("RESULT:")
        print("="*80)
        import json
        print(json.dumps(result, indent=2))

        print("\n5. Checking error message on page...")
        await asyncio.sleep(1)
        try:
            error_msg = await page.query_selector('#errorMessage')
            if error_msg and await error_msg.is_visible():
                error_text = await error_msg.inner_text()
                print(f"Error message: {error_text}")
        except:
            pass

        print("\n6. Current URL:", page.url)

        print("\n7. Waiting 5 more seconds for any delayed activity...")
        await asyncio.sleep(5)

        print("\n" + "="*80)
        print("DEBUG COMPLETE")
        print("="*80)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_fetch())
