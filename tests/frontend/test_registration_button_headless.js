/**
 * Headless Registration Button Test
 * Uses Puppeteer to test the registration button functionality
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

async function testRegistrationButton() {
    console.log('🚀 Starting Registration Button Test...\n');
    
    let browser;
    try {
        // Launch browser in headless mode
        browser = await puppeteer.launch({
            headless: true,
            ignoreHTTPSErrors: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        });
        
        const page = await browser.newPage();
        
        // Enable console logging
        page.on('console', (msg) => {
            console.log(`📝 BROWSER LOG [${msg.type()}]: ${msg.text()}`);
        });
        
        // Capture any JavaScript errors
        page.on('pageerror', (error) => {
            console.log(`❌ PAGE ERROR: ${error.message}`);
        });
        
        // Set viewport
        await page.setViewport({ width: 1200, height: 800 });
        
        console.log('📄 Loading main page...');
        
        // Navigate to the main page
        const response = await page.goto('https://localhost:3000/html/index.html', {
            waitUntil: 'networkidle2',
            timeout: 10000
        });
        
        console.log(`📡 Page loaded with status: ${response.status()}`);
        
        // Wait for the page to be fully loaded
        await page.waitForTimeout(2000);
        
        console.log('\n🔍 STEP 1: Checking if elements exist...');
        
        // Check if register button exists
        const registerBtnExists = await page.$('#registerBtn') !== null;
        console.log(`   Register Button exists: ${registerBtnExists ? '✅' : '❌'}`);
        
        if (!registerBtnExists) {
            console.log('❌ Test failed: Register button not found');
            return;
        }
        
        // Check if main content exists
        const mainContentExists = await page.$('#main-content') !== null;
        console.log(`   Main content exists: ${mainContentExists ? '✅' : '❌'}`);
        
        // Get initial main content
        const initialContent = await page.evaluate(() => {
            const main = document.getElementById('main-content');
            return main ? main.innerHTML.trim() : null;
        });
        
        console.log(`   Initial main content length: ${initialContent ? initialContent.length : 0} characters`);
        
        console.log('\n🔍 STEP 2: Checking if modules are loaded...');
        
        // Check if required modules are available
        const moduleCheck = await page.evaluate(() => {
            const results = {
                windowApp: typeof window.App !== 'undefined',
                windowNavigation: typeof window.Navigation !== 'undefined',
                navigationShowRegister: typeof window.Navigation?.showRegister === 'function',
                appObject: window.App,
                navigationObject: window.Navigation
            };
            
            // Try to get more info about available objects
            results.windowObjects = Object.keys(window).filter(key => 
                key.startsWith('App') || key.startsWith('Navigation') || key.startsWith('show')
            );
            
            return results;
        });
        
        console.log(`   window.App available: ${moduleCheck.windowApp ? '✅' : '❌'}`);
        console.log(`   window.Navigation available: ${moduleCheck.windowNavigation ? '✅' : '❌'}`);
        console.log(`   Navigation.showRegister available: ${moduleCheck.navigationShowRegister ? '✅' : '❌'}`);
        console.log(`   Available window objects: ${moduleCheck.windowObjects.join(', ')}`);
        
        console.log('\n🔍 STEP 3: Testing registration button click...');
        
        // Click the register button
        await page.click('#registerBtn');
        console.log('   ✅ Registration button clicked');
        
        // Wait for any potential async operations
        await page.waitForTimeout(1000);
        
        // Check if content changed
        const newContent = await page.evaluate(() => {
            const main = document.getElementById('main-content');
            return main ? main.innerHTML.trim() : null;
        });
        
        console.log(`   New main content length: ${newContent ? newContent.length : 0} characters`);
        
        const contentChanged = initialContent !== newContent;
        console.log(`   Content changed: ${contentChanged ? '✅' : '❌'}`);
        
        if (contentChanged) {
            // Check if it contains registration-related content
            const hasRegistrationContent = newContent && (
                newContent.includes('registration-options') ||
                newContent.includes('Register New Organization') ||
                newContent.includes('Join Existing Organization') ||
                newContent.includes('registration-card')
            );
            
            console.log(`   Contains registration content: ${hasRegistrationContent ? '✅' : '❌'}`);
            
            if (hasRegistrationContent) {
                console.log('   📝 Registration content preview:');
                console.log(`   ${newContent.substring(0, 200)}...`);
            } else {
                console.log('   📝 Actual content preview:');
                console.log(`   ${newContent.substring(0, 200)}...`);
            }
        } else {
            console.log('   ❌ Content did not change - registration button may not be working');
            console.log('   📝 Current content preview:');
            console.log(`   ${(newContent || '').substring(0, 200)}...`);
        }
        
        console.log('\n🔍 STEP 4: Testing Navigation.showRegister directly...');
        
        // Test calling Navigation.showRegister() directly
        const directCallResult = await page.evaluate(() => {
            try {
                if (window.Navigation && typeof window.Navigation.showRegister === 'function') {
                    window.Navigation.showRegister();
                    return { success: true, error: null };
                } else {
                    return { success: false, error: 'Navigation.showRegister not available' };
                }
            } catch (error) {
                return { success: false, error: error.message };
            }
        });
        
        console.log(`   Direct call result: ${directCallResult.success ? '✅' : '❌'}`);
        if (!directCallResult.success) {
            console.log(`   Error: ${directCallResult.error}`);
        }
        
        // Wait for content to update after direct call
        await page.waitForTimeout(500);
        
        const finalContent = await page.evaluate(() => {
            const main = document.getElementById('main-content');
            return main ? main.innerHTML.trim() : null;
        });
        
        const directCallWorked = finalContent && finalContent !== initialContent && (
            finalContent.includes('registration-options') ||
            finalContent.includes('Register New Organization')
        );
        
        console.log(`   Direct call changed content properly: ${directCallWorked ? '✅' : '❌'}`);
        
        console.log('\n📊 TEST SUMMARY:');
        console.log('================');
        console.log(`Button exists: ${registerBtnExists ? '✅' : '❌'}`);
        console.log(`Modules loaded: ${moduleCheck.windowNavigation ? '✅' : '❌'}`);
        console.log(`Button click works: ${contentChanged ? '✅' : '❌'}`);
        console.log(`Direct call works: ${directCallWorked ? '✅' : '❌'}`);
        
        const overallSuccess = registerBtnExists && moduleCheck.windowNavigation && (contentChanged || directCallWorked);
        console.log(`Overall result: ${overallSuccess ? '✅ PASS' : '❌ FAIL'}`);
        
        // Save detailed results to file
        const testResults = {
            timestamp: new Date().toISOString(),
            registerBtnExists,
            moduleCheck,
            initialContentLength: initialContent ? initialContent.length : 0,
            newContentLength: newContent ? newContent.length : 0,
            contentChanged,
            directCallResult,
            finalContentLength: finalContent ? finalContent.length : 0,
            overallSuccess
        };
        
        fs.writeFileSync('/tmp/registration_button_test_results.json', JSON.stringify(testResults, null, 2));
        console.log('\n📁 Detailed results saved to /tmp/registration_button_test_results.json');
        
    } catch (error) {
        console.error('❌ Test failed with error:', error);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Check if puppeteer is available
try {
    testRegistrationButton();
} catch (error) {
    console.error('❌ Puppeteer not available. Installing and running fallback test...');
    console.log('💡 Install puppeteer with: npm install puppeteer');
    
    // Fallback: Simple curl-based test
    console.log('\n🔄 Running fallback test with curl...');
    const { exec } = require('child_process');
    
    exec('curl -k -s https://localhost:3000/html/index.html', (error, stdout, stderr) => {
        if (error) {
            console.error('❌ Curl test failed:', error);
            return;
        }
        
        const hasRegisterBtn = stdout.includes('id="registerBtn"');
        const hasMainContent = stdout.includes('id="main-content"');
        const hasModuleScript = stdout.includes('type="module"');
        
        console.log('📋 Fallback Test Results:');
        console.log(`   Register button in HTML: ${hasRegisterBtn ? '✅' : '❌'}`);
        console.log(`   Main content in HTML: ${hasMainContent ? '✅' : '❌'}`);  
        console.log(`   Module script included: ${hasModuleScript ? '✅' : '❌'}`);
        
        if (!hasRegisterBtn) {
            console.log('❌ Register button missing from HTML');
        } else {
            console.log('⚠️  Register button exists but JavaScript functionality needs browser testing');
        }
    });
}