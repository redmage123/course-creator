# Playwright MCP Server - Installation Complete

**Status:** ✅ Installed and configured
**Date:** 2025-11-06

---

## What is Playwright MCP Server?

The Playwright MCP (Model Context Protocol) server allows Claude Code to control a web browser using Playwright - a modern, stable alternative to Selenium WebDriver.

**Benefits over Selenium:**
- ✅ Modern API with better reliability
- ✅ Built-in auto-waiting for elements
- ✅ Better handling of modern web frameworks
- ✅ Multiple browser support (Chrome, Firefox, WebKit)
- ✅ Better debugging with trace files and videos
- ✅ More stable in headless mode

---

## Installation Complete

**Package:** `@playwright/mcp` version 0.0.45
**Playwright:** Version 1.56.1
**Configuration:** `/home/bbrelin/.config/Claude/claude_desktop_config.json`

---

## Configuration

The MCP server is configured to run via npx:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@playwright/mcp"
      ],
      "env": {
        "PLAYWRIGHT_BROWSERS_PATH": "/home/bbrelin/.cache/ms-playwright"
      }
    }
  }
}
```

---

## Available Capabilities

The Playwright MCP server provides these capabilities to Claude Code:

### Browser Control
- Navigate to URLs
- Click elements
- Type text into inputs
- Take screenshots
- Execute JavaScript
- Handle dialogs and popups

### Advanced Features
- Vision capabilities (OCR, image analysis)
- PDF generation
- Device emulation (iPhone, iPad, etc.)
- Network interception
- Geolocation mocking
- Video recording of sessions

### Test-Specific Features
- Custom test ID attributes
- Storage state management
- Trace recording for debugging
- Configurable timeouts

---

## Usage Examples

### Basic Browser Automation
```python
# Claude Code can now use Playwright tools via MCP
# Example: Navigate to homepage and take screenshot
playwright.navigate("https://localhost:3000")
playwright.screenshot("homepage.png")
```

### Element Interaction
```python
# Click button by test ID
playwright.click('[data-testid="login-button"]')

# Fill form inputs
playwright.fill('#email', 'user@example.com')
playwright.fill('#password', 'SecurePassword123')
```

### Advanced Testing
```python
# Enable video recording
playwright.configure(save_video="1920x1080")

# Enable trace recording for debugging
playwright.configure(save_trace=True)

# Test with device emulation
playwright.configure(device="iPhone 15")
```

---

## MCP Server Options

The server supports extensive configuration options:

### Browser Options
- `--browser chrome|firefox|webkit|msedge` - Browser to use
- `--headless` - Run in headless mode
- `--device "iPhone 15"` - Emulate mobile device
- `--viewport-size 1920x1080` - Set viewport size

### Security Options
- `--no-sandbox` - Disable sandbox (Docker/CI)
- `--ignore-https-errors` - Ignore SSL errors
- `--allowed-origins <origins>` - CORS configuration

### Testing Options
- `--test-id-attribute data-testid` - Custom test ID attribute
- `--timeout-action 5000` - Action timeout (ms)
- `--timeout-navigation 60000` - Navigation timeout (ms)

### Recording Options
- `--save-trace` - Save Playwright trace
- `--save-video 1920x1080` - Save video recording
- `--save-session` - Save browser session

---

## Comparison: Selenium vs Playwright

| Feature | Selenium + Docker Grid | Playwright MCP |
|---------|------------------------|----------------|
| Setup | Docker service required | Built-in via npx |
| Browser Versions | Chrome 119 (fixed) | Latest stable |
| Auto-waiting | Manual WebDriverWait | Automatic |
| Network Control | Limited | Full interception |
| Screenshots | Basic | Advanced (full page) |
| Video Recording | External tool needed | Built-in |
| Trace Debugging | No | Yes (timeline viewer) |
| Mobile Emulation | Limited | Excellent |
| PDF Generation | External library | Built-in |

---

## When to Use Each

### Use Selenium Docker Grid when:
- ✅ You need a specific Chrome version (119)
- ✅ You want isolation from host system
- ✅ You prefer traditional Selenium Page Objects
- ✅ Existing tests are written for Selenium

### Use Playwright MCP when:
- ✅ You want the latest stable browsers
- ✅ You need advanced debugging (traces, videos)
- ✅ You want better auto-waiting behavior
- ✅ You need mobile device emulation
- ✅ You want simpler setup (no Docker required)

---

## Migrating from Selenium to Playwright

### Selenium (Old)
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Remote('http://localhost:4444', options=options)
driver.get('https://localhost:3000')

# Manual wait
wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.ID, 'login-button')))
element.click()
```

### Playwright MCP (New)
```python
# Claude Code will handle via MCP - simpler and more reliable
playwright.navigate('https://localhost:3000')
playwright.click('#login-button')  # Auto-waits automatically
```

---

## Testing the Installation

To verify Playwright MCP is working, restart Claude Code and you should see the Playwright MCP server tools available in your tool list.

**Test command:**
```bash
npx -y @playwright/mcp --help
```

**Expected output:** Help text with all available options

---

## Troubleshooting

### Server doesn't start
**Check:** Configuration file syntax
```bash
cat ~/.config/Claude/claude_desktop_config.json
```

### Browser not found
**Solution:** Install browsers
```bash
npx playwright install chromium
```

### Permission errors
**Solution:** Ensure browsers directory exists
```bash
mkdir -p ~/.cache/ms-playwright
chmod 755 ~/.cache/ms-playwright
```

---

## Next Steps

1. **Restart Claude Code** to load the MCP server
2. **Verify tools available** - Look for Playwright-related tools
3. **Run simple test** - Navigate to homepage and take screenshot
4. **Consider migration** - Evaluate moving E2E tests from Selenium to Playwright

---

## Resources

- **Playwright Docs:** https://playwright.dev
- **MCP Server GitHub:** https://github.com/playwright/playwright
- **Playwright Test Runner:** https://playwright.dev/docs/test-intro

---

**Installation Complete!**
The Playwright MCP server is ready to use for modern browser automation with Claude Code.
