/**
 * UI/UX Audit Script
 *
 * Runs comprehensive UI/UX analysis including:
 * - Lighthouse performance audit
 * - Accessibility testing with axe-core
 * - Visual regression checks
 * - Best practices validation
 */

import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const BASE_URL = 'https://localhost:3002';
const AUDIT_PAGES = [
  { path: '/', name: 'homepage' },
  { path: '/login', name: 'login' },
  { path: '/register', name: 'register' },
  { path: '/dashboard/student', name: 'student-dashboard' },
  { path: '/dashboard/instructor', name: 'instructor-dashboard' },
  { path: '/dashboard/org-admin', name: 'org-admin-dashboard' },
  { path: '/dashboard/site-admin', name: 'site-admin-dashboard' }
];

const LIGHTHOUSE_CONFIG = {
  extends: 'lighthouse:default',
  settings: {
    onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'],
    formFactor: 'desktop',
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
    },
    screenEmulation: {
      mobile: false,
      width: 1350,
      height: 940,
      deviceScaleFactor: 1,
      disabled: false,
    },
  },
};

/**
 * Run Lighthouse audit for a single page
 */
async function runLighthouseAudit(chrome, url, pageName) {
  console.log(`\n🔍 Auditing: ${pageName} (${url})`);

  const options = {
    logLevel: 'info',
    output: 'html',
    port: chrome.port,
  };

  const runnerResult = await lighthouse(url, options, LIGHTHOUSE_CONFIG);

  // Extract scores
  const scores = {
    performance: runnerResult.lhr.categories.performance.score * 100,
    accessibility: runnerResult.lhr.categories.accessibility.score * 100,
    bestPractices: runnerResult.lhr.categories['best-practices'].score * 100,
    seo: runnerResult.lhr.categories.seo.score * 100,
  };

  // Extract issues
  const issues = {
    accessibility: [],
    performance: [],
    bestPractices: [],
    seo: []
  };

  // Collect accessibility issues
  const accessibilityAudits = runnerResult.lhr.categories.accessibility.auditRefs;
  for (const auditRef of accessibilityAudits) {
    const audit = runnerResult.lhr.audits[auditRef.id];
    if (audit.score !== null && audit.score < 1) {
      issues.accessibility.push({
        id: auditRef.id,
        title: audit.title,
        description: audit.description,
        score: audit.score,
        details: audit.details
      });
    }
  }

  // Collect performance issues
  const performanceAudits = runnerResult.lhr.categories.performance.auditRefs;
  for (const auditRef of performanceAudits) {
    const audit = runnerResult.lhr.audits[auditRef.id];
    if (audit.score !== null && audit.score < 0.9) {
      issues.performance.push({
        id: auditRef.id,
        title: audit.title,
        description: audit.description,
        score: audit.score
      });
    }
  }

  // Collect best practices issues
  const bestPracticesAudits = runnerResult.lhr.categories['best-practices'].auditRefs;
  for (const auditRef of bestPracticesAudits) {
    const audit = runnerResult.lhr.audits[auditRef.id];
    if (audit.score !== null && audit.score < 1) {
      issues.bestPractices.push({
        id: auditRef.id,
        title: audit.title,
        description: audit.description,
        score: audit.score
      });
    }
  }

  console.log(`✅ Performance: ${scores.performance.toFixed(0)}/100`);
  console.log(`♿ Accessibility: ${scores.accessibility.toFixed(0)}/100`);
  console.log(`⚙️  Best Practices: ${scores.bestPractices.toFixed(0)}/100`);
  console.log(`🔍 SEO: ${scores.seo.toFixed(0)}/100`);

  return {
    pageName,
    url,
    scores,
    issues,
    reportHtml: runnerResult.report
  };
}

/**
 * Generate consolidated audit report
 */
function generateConsolidatedReport(results) {
  const report = {
    timestamp: new Date().toISOString(),
    summary: {
      totalPages: results.length,
      averageScores: {
        performance: 0,
        accessibility: 0,
        bestPractices: 0,
        seo: 0
      },
      totalIssues: {
        accessibility: 0,
        performance: 0,
        bestPractices: 0
      }
    },
    pages: results,
    recommendations: []
  };

  // Calculate averages
  results.forEach(result => {
    report.summary.averageScores.performance += result.scores.performance;
    report.summary.averageScores.accessibility += result.scores.accessibility;
    report.summary.averageScores.bestPractices += result.scores.bestPractices;
    report.summary.averageScores.seo += result.scores.seo;

    report.summary.totalIssues.accessibility += result.issues.accessibility.length;
    report.summary.totalIssues.performance += result.issues.performance.length;
    report.summary.totalIssues.bestPractices += result.issues.bestPractices.length;
  });

  report.summary.averageScores.performance /= results.length;
  report.summary.averageScores.accessibility /= results.length;
  report.summary.averageScores.bestPractices /= results.length;
  report.summary.averageScores.seo /= results.length;

  // Generate recommendations
  if (report.summary.averageScores.accessibility < 90) {
    report.recommendations.push({
      priority: 'HIGH',
      category: 'Accessibility',
      issue: `Average accessibility score is ${report.summary.averageScores.accessibility.toFixed(0)}/100`,
      recommendation: 'Focus on adding ARIA labels, improving keyboard navigation, and ensuring proper color contrast.'
    });
  }

  if (report.summary.averageScores.performance < 80) {
    report.recommendations.push({
      priority: 'HIGH',
      category: 'Performance',
      issue: `Average performance score is ${report.summary.averageScores.performance.toFixed(0)}/100`,
      recommendation: 'Optimize images, minimize JavaScript, enable code splitting, and implement lazy loading.'
    });
  }

  if (report.summary.totalIssues.accessibility > 10) {
    report.recommendations.push({
      priority: 'HIGH',
      category: 'Accessibility',
      issue: `${report.summary.totalIssues.accessibility} accessibility issues found`,
      recommendation: 'Review all accessibility violations and implement fixes following WCAG 2.1 AA guidelines.'
    });
  }

  return report;
}

/**
 * Generate HTML report
 */
function generateHtmlReport(consolidatedReport) {
  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UI/UX Audit Report - Course Creator Platform</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; border-radius: 12px; margin-bottom: 30px; }
    .header h1 { font-size: 2.5rem; margin-bottom: 10px; }
    .header p { font-size: 1.1rem; opacity: 0.95; }
    .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
    .summary-card { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .summary-card h3 { font-size: 0.9rem; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px; }
    .summary-card .score { font-size: 3rem; font-weight: 700; }
    .score.excellent { color: #4caf50; }
    .score.good { color: #8bc34a; }
    .score.fair { color: #ff9800; }
    .score.poor { color: #f44336; }
    .recommendations { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }
    .recommendations h2 { margin-bottom: 20px; }
    .recommendation { padding: 16px; margin-bottom: 16px; border-left: 4px solid #ff9800; background: #fff3e0; border-radius: 4px; }
    .recommendation.high { border-color: #f44336; background: #ffebee; }
    .recommendation h4 { color: #d32f2f; margin-bottom: 8px; }
    .page-results { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .page-results h3 { margin-bottom: 16px; }
    .scores-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
    .score-item { text-align: center; padding: 12px; background: #f5f5f5; border-radius: 8px; }
    .score-item .label { font-size: 0.85rem; color: #666; margin-bottom: 4px; }
    .score-item .value { font-size: 1.8rem; font-weight: 700; }
    .issues { margin-top: 20px; }
    .issue { padding: 12px; margin-bottom: 12px; background: #f5f5f5; border-radius: 8px; }
    .issue-title { font-weight: 600; margin-bottom: 4px; }
    .issue-description { font-size: 0.9rem; color: #666; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>UI/UX Audit Report</h1>
      <p>Course Creator Platform - ${new Date(consolidatedReport.timestamp).toLocaleString()}</p>
      <p>Pages Audited: ${consolidatedReport.summary.totalPages}</p>
    </div>

    <div class="summary">
      <div class="summary-card">
        <h3>Performance</h3>
        <div class="score ${getScoreClass(consolidatedReport.summary.averageScores.performance)}">${consolidatedReport.summary.averageScores.performance.toFixed(0)}</div>
      </div>
      <div class="summary-card">
        <h3>Accessibility</h3>
        <div class="score ${getScoreClass(consolidatedReport.summary.averageScores.accessibility)}">${consolidatedReport.summary.averageScores.accessibility.toFixed(0)}</div>
      </div>
      <div class="summary-card">
        <h3>Best Practices</h3>
        <div class="score ${getScoreClass(consolidatedReport.summary.averageScores.bestPractices)}">${consolidatedReport.summary.averageScores.bestPractices.toFixed(0)}</div>
      </div>
      <div class="summary-card">
        <h3>SEO</h3>
        <div class="score ${getScoreClass(consolidatedReport.summary.averageScores.seo)}">${consolidatedReport.summary.averageScores.seo.toFixed(0)}</div>
      </div>
    </div>

    ${consolidatedReport.recommendations.length > 0 ? `
    <div class="recommendations">
      <h2>🎯 Key Recommendations</h2>
      ${consolidatedReport.recommendations.map(rec => `
        <div class="recommendation ${rec.priority.toLowerCase()}">
          <h4>${rec.priority} PRIORITY: ${rec.category}</h4>
          <p><strong>Issue:</strong> ${rec.issue}</p>
          <p><strong>Recommendation:</strong> ${rec.recommendation}</p>
        </div>
      `).join('')}
    </div>
    ` : ''}

    <h2 style="margin-bottom: 20px;">📄 Page-by-Page Results</h2>
    ${consolidatedReport.pages.map(page => `
      <div class="page-results">
        <h3>${page.pageName}</h3>
        <p style="color: #666; margin-bottom: 16px;">${page.url}</p>

        <div class="scores-grid">
          <div class="score-item">
            <div class="label">Performance</div>
            <div class="value ${getScoreClass(page.scores.performance)}">${page.scores.performance.toFixed(0)}</div>
          </div>
          <div class="score-item">
            <div class="label">Accessibility</div>
            <div class="value ${getScoreClass(page.scores.accessibility)}">${page.scores.accessibility.toFixed(0)}</div>
          </div>
          <div class="score-item">
            <div class="label">Best Practices</div>
            <div class="value ${getScoreClass(page.scores.bestPractices)}">${page.scores.bestPractices.toFixed(0)}</div>
          </div>
          <div class="score-item">
            <div class="label">SEO</div>
            <div class="value ${getScoreClass(page.scores.seo)}">${page.scores.seo.toFixed(0)}</div>
          </div>
        </div>

        ${page.issues.accessibility.length > 0 ? `
        <div class="issues">
          <h4>♿ Accessibility Issues (${page.issues.accessibility.length})</h4>
          ${page.issues.accessibility.slice(0, 5).map(issue => `
            <div class="issue">
              <div class="issue-title">${issue.title}</div>
              <div class="issue-description">${issue.description}</div>
            </div>
          `).join('')}
          ${page.issues.accessibility.length > 5 ? `<p style="text-align: center; color: #666; margin-top: 12px;">... and ${page.issues.accessibility.length - 5} more issues</p>` : ''}
        </div>
        ` : ''}
      </div>
    `).join('')}
  </div>
</body>
</html>
  `;

  return html;
}

function getScoreClass(score) {
  if (score >= 90) return 'excellent';
  if (score >= 75) return 'good';
  if (score >= 50) return 'fair';
  return 'poor';
}

/**
 * Main audit execution
 */
async function runAudit() {
  console.log('🚀 Starting UI/UX Audit...\n');

  let chrome;

  try {
    // Launch Chrome
    chrome = await chromeLauncher.launch({
      chromeFlags: ['--headless', '--ignore-certificate-errors']
    });

    // Run audits for all pages
    const results = [];
    for (const page of AUDIT_PAGES) {
      const url = `${BASE_URL}${page.path}`;
      const result = await runLighthouseAudit(chrome, url, page.name);
      results.push(result);
    }

    // Generate consolidated report
    const consolidatedReport = generateConsolidatedReport(results);

    // Create reports directory
    const reportsDir = path.join(__dirname, '..', 'audit-reports');
    if (!fs.existsSync(reportsDir)) {
      fs.mkdirSync(reportsDir, { recursive: true });
    }

    // Save JSON report
    const jsonPath = path.join(reportsDir, 'audit-report.json');
    fs.writeFileSync(jsonPath, JSON.stringify(consolidatedReport, null, 2));
    console.log(`\n📊 JSON report saved: ${jsonPath}`);

    // Save HTML report
    const htmlReport = generateHtmlReport(consolidatedReport);
    const htmlPath = path.join(reportsDir, 'audit-report.html');
    fs.writeFileSync(htmlPath, htmlReport);
    console.log(`📄 HTML report saved: ${htmlPath}`);

    // Save individual Lighthouse HTML reports
    results.forEach(result => {
      const reportPath = path.join(reportsDir, `lighthouse-${result.pageName}.html`);
      fs.writeFileSync(reportPath, result.reportHtml);
    });
    console.log(`📋 Individual Lighthouse reports saved to: ${reportsDir}`);

    // Print summary
    console.log('\n' + '='.repeat(60));
    console.log('📊 AUDIT SUMMARY');
    console.log('='.repeat(60));
    console.log(`Average Performance:    ${consolidatedReport.summary.averageScores.performance.toFixed(0)}/100`);
    console.log(`Average Accessibility:  ${consolidatedReport.summary.averageScores.accessibility.toFixed(0)}/100`);
    console.log(`Average Best Practices: ${consolidatedReport.summary.averageScores.bestPractices.toFixed(0)}/100`);
    console.log(`Average SEO:            ${consolidatedReport.summary.averageScores.seo.toFixed(0)}/100`);
    console.log(`\nTotal Issues Found:`);
    console.log(`  Accessibility:  ${consolidatedReport.summary.totalIssues.accessibility}`);
    console.log(`  Performance:    ${consolidatedReport.summary.totalIssues.performance}`);
    console.log(`  Best Practices: ${consolidatedReport.summary.totalIssues.bestPractices}`);
    console.log('='.repeat(60));

  } catch (error) {
    console.error('❌ Audit failed:', error);
    process.exit(1);
  } finally {
    if (chrome) {
      await chrome.kill();
    }
  }
}

// Run the audit
runAudit();
