/**
 * Production Build UI/UX Audit Script
 *
 * Runs Lighthouse audits against production build on port 3003
 */

const lighthouse = require('lighthouse').default;
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://localhost:3003';
const AUDIT_DIR = path.join(__dirname, '../audit-reports');

const pages = [
  { name: 'homepage', path: '/' },
  { name: 'login', path: '/login' },
  { name: 'register', path: '/register' },
  { name: 'student-dashboard', path: '/dashboard/student' },
  { name: 'instructor-dashboard', path: '/dashboard/instructor' },
  { name: 'org-admin-dashboard', path: '/dashboard/org-admin' },
  { name: 'site-admin-dashboard', path: '/dashboard/site-admin' },
];

// Lighthouse configuration
const config = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    skipAudits: ['uses-http2'], // Skip HTTP/2 check for local dev
  },
};

// Chrome flags for local HTTPS
const chromeFlags = [
  '--headless',
  '--ignore-certificate-errors',
  '--allow-insecure-localhost',
  '--disable-gpu',
  '--no-sandbox',
];

async function runAudit(url, pageName) {
  console.log(`\n🔍 Auditing: ${pageName} (${url})`);

  const chrome = await chromeLauncher.launch({ chromeFlags });

  try {
    const options = {
      logLevel: 'error',
      output: 'json',
      port: chrome.port,
    };

    const runnerResult = await lighthouse(url, options, config);

    return {
      pageName,
      url,
      scores: {
        performance: Math.round(runnerResult.lhr.categories.performance.score * 100),
        accessibility: Math.round(runnerResult.lhr.categories.accessibility.score * 100),
        bestPractices: Math.round(runnerResult.lhr.categories['best-practices'].score * 100),
        seo: Math.round(runnerResult.lhr.categories.seo.score * 100),
      },
      reportHtml: runnerResult.report,
      issues: extractIssues(runnerResult.lhr),
    };
  } finally {
    await chrome.kill();
  }
}

function extractIssues(lhr) {
  const issues = {
    performance: [],
    accessibility: [],
    bestPractices: [],
    seo: [],
  };

  Object.entries(lhr.audits).forEach(([id, audit]) => {
    if (audit.score !== null && audit.score < 1) {
      const issue = {
        id,
        title: audit.title,
        description: audit.description,
        score: audit.score,
      };

      if (lhr.categories.performance.auditRefs.find(ref => ref.id === id)) {
        issues.performance.push(issue);
      }
      if (lhr.categories.accessibility.auditRefs.find(ref => ref.id === id)) {
        issues.accessibility.push(issue);
      }
      if (lhr.categories['best-practices'].auditRefs.find(ref => ref.id === id)) {
        issues.bestPractices.push(issue);
      }
      if (lhr.categories.seo.auditRefs.find(ref => ref.id === id)) {
        issues.seo.push(issue);
      }
    }
  });

  return issues;
}

function generateReport(results) {
  const summary = {
    totalPages: results.length,
    averageScores: {
      performance: Math.round(results.reduce((sum, r) => sum + r.scores.performance, 0) / results.length),
      accessibility: Math.round(results.reduce((sum, r) => sum + r.scores.accessibility, 0) / results.length),
      bestPractices: Math.round(results.reduce((sum, r) => sum + r.scores.bestPractices, 0) / results.length),
      seo: Math.round(results.reduce((sum, r) => sum + r.scores.seo, 0) / results.length),
    },
    totalIssues: {
      accessibility: results.reduce((sum, r) => sum + r.issues.accessibility.length, 0),
      performance: results.reduce((sum, r) => sum + r.issues.performance.length, 0),
      bestPractices: results.reduce((sum, r) => sum + r.issues.bestPractices.length, 0),
    },
  };

  return { summary, pages: results };
}

function generateHTML(report) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Production Build Audit - Course Creator Platform</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; border-radius: 12px; margin-bottom: 30px; }
    .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
    .badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 600; margin-left: 10px; }
    .badge.production { background: #4caf50; color: white; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
    .summary-card { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .summary-card h3 { font-size: 0.9rem; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
    .summary-card .score { font-size: 3rem; font-weight: 700; }
    .score.excellent { color: #4caf50; }
    .score.good { color: #8bc34a; }
    .score.fair { color: #ff9800; }
    .score.poor { color: #f44336; }
    .page-results { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .scores-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
    .score-item { text-align: center; padding: 12px; background: #f5f5f5; border-radius: 8px; }
    .score-item .label { font-size: 0.85rem; color: #666; margin-bottom: 4px; }
    .score-item .value { font-size: 1.8rem; font-weight: 700; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Production Build Audit <span class="badge production">PRODUCTION</span></h1>
      <p>Course Creator Platform - ${new Date().toLocaleString()}</p>
      <p>Build: Minified & Optimized | Pages Audited: ${report.summary.totalPages}</p>
    </div>

    <div class="summary">
      <div class="summary-card">
        <h3>Performance</h3>
        <div class="score ${getScoreClass(report.summary.averageScores.performance)}">${report.summary.averageScores.performance}</div>
      </div>
      <div class="summary-card">
        <h3>Accessibility</h3>
        <div class="score ${getScoreClass(report.summary.averageScores.accessibility)}">${report.summary.averageScores.accessibility}</div>
      </div>
      <div class="summary-card">
        <h3>Best Practices</h3>
        <div class="score ${getScoreClass(report.summary.averageScores.bestPractices)}">${report.summary.averageScores.bestPractices}</div>
      </div>
      <div class="summary-card">
        <h3>SEO</h3>
        <div class="score ${getScoreClass(report.summary.averageScores.seo)}">${report.summary.averageScores.seo}</div>
      </div>
    </div>

    <h2 style="margin-bottom: 20px;">📄 Page-by-Page Results</h2>

    ${report.pages.map(page => `
      <div class="page-results">
        <h3>${page.pageName}</h3>
        <p style="color: #666; margin-bottom: 16px;">${page.url}</p>

        <div class="scores-grid">
          <div class="score-item">
            <div class="label">Performance</div>
            <div class="value ${getScoreClass(page.scores.performance)}">${page.scores.performance}</div>
          </div>
          <div class="score-item">
            <div class="label">Accessibility</div>
            <div class="value ${getScoreClass(page.scores.accessibility)}">${page.scores.accessibility}</div>
          </div>
          <div class="score-item">
            <div class="label">Best Practices</div>
            <div class="value ${getScoreClass(page.scores.bestPractices)}">${page.scores.bestPractices}</div>
          </div>
          <div class="score-item">
            <div class="label">SEO</div>
            <div class="value ${getScoreClass(page.scores.seo)}">${page.scores.seo}</div>
          </div>
        </div>
      </div>
    `).join('')}
  </div>
</body>
</html>`;
}

function getScoreClass(score) {
  if (score >= 90) return 'excellent';
  if (score >= 75) return 'good';
  if (score >= 50) return 'fair';
  return 'poor';
}

async function main() {
  console.log('🚀 Starting Production Build Audit...\n');
  console.log(`Testing production build at: ${BASE_URL}\n`);

  // Ensure audit directory exists
  if (!fs.existsSync(AUDIT_DIR)) {
    fs.mkdirSync(AUDIT_DIR, { recursive: true });
  }

  const results = [];

  for (const page of pages) {
    const url = `${BASE_URL}${page.path}`;
    const result = await runAudit(url, page.name);
    results.push(result);

    console.log(`✅ Performance: ${result.scores.performance}/100`);
    console.log(`♿ Accessibility: ${result.scores.accessibility}/100`);
    console.log(`⚙️  Best Practices: ${result.scores.bestPractices}/100`);
    console.log(`🔍 SEO: ${result.scores.seo}/100`);
  }

  const report = generateReport(results);

  // Save JSON report
  const jsonPath = path.join(AUDIT_DIR, 'production-audit-report.json');
  fs.writeFileSync(jsonPath, JSON.stringify(report, null, 2));
  console.log(`\n📊 JSON report saved: ${jsonPath}`);

  // Save HTML report
  const htmlPath = path.join(AUDIT_DIR, 'production-audit-report.html');
  fs.writeFileSync(htmlPath, generateHTML(report));
  console.log(`📄 HTML report saved: ${htmlPath}`);

  // Print summary
  console.log('\n============================================================');
  console.log('📊 PRODUCTION BUILD AUDIT SUMMARY');
  console.log('============================================================');
  console.log(`Average Performance:    ${report.summary.averageScores.performance}/100`);
  console.log(`Average Accessibility:  ${report.summary.averageScores.accessibility}/100`);
  console.log(`Average Best Practices: ${report.summary.averageScores.bestPractices}/100`);
  console.log(`Average SEO:            ${report.summary.averageScores.seo}/100`);
  console.log(`\nTotal Issues Found:`);
  console.log(`  Accessibility:  ${report.summary.totalIssues.accessibility}`);
  console.log(`  Performance:    ${report.summary.totalIssues.performance}`);
  console.log(`  Best Practices: ${report.summary.totalIssues.bestPractices}`);
  console.log('============================================================\n');
}

main().catch(console.error);
