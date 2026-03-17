const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ ignoreHTTPSErrors: true });
  const page = await context.newPage();

  // Capture all network requests/responses
  page.on('response', response => {
    const url = response.url();
    if (url.includes('/demo/') || url.includes('.mp4') || url.includes('.mp3')) {
      console.log('Network:', response.status(), url.slice(0, 100));
    }
  });
  page.on('requestfailed', request => {
    console.log('Request Failed:', request.url(), request.failure().errorText);
  });
  page.on('console', msg => {
    if (msg.text().includes('[DemoPlayer]') || msg.type() === 'error') {
      console.log('Console:', msg.type(), msg.text());
    }
  });
  page.on('pageerror', err => console.log('Page Error:', err.message));

  try {
    console.log('Loading demo page...');
    await page.goto('https://localhost:3000/demo', { waitUntil: 'networkidle', timeout: 45000 });

    // Wait for video element
    await page.waitForSelector('video', { timeout: 5000 });

    // Check video source
    const videoSrc = await page.evaluate(() => {
      const video = document.querySelector('video');
      return video ? video.src : 'No video found';
    });
    console.log('Video src:', videoSrc);

    // Check if video can play
    const canPlayInfo = await page.evaluate(() => {
      const video = document.querySelector('video');
      if (!video) return 'No video element';
      return {
        src: video.src,
        readyState: video.readyState,
        error: video.error ? video.error.message : null,
        errorCode: video.error ? video.error.code : null,
        networkState: video.networkState,
        paused: video.paused,
        duration: video.duration
      };
    });
    console.log('Video state:', JSON.stringify(canPlayInfo, null, 2));

    // Try to play
    const playResult = await page.evaluate(async () => {
      const video = document.querySelector('video');
      if (!video) return 'No video';
      try {
        await video.play();
        return 'Playing';
      } catch (e) {
        return 'Play error: ' + e.message;
      }
    });
    console.log('Play result:', playResult);

  } catch (error) {
    console.error('Error:', error.message);
  }

  await browser.close();
})();
