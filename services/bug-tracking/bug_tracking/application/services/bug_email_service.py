"""
Bug Email Service

BUSINESS CONTEXT:
Sends email notifications for bug tracking:
- Analysis complete notifications
- Fix attempt results
- PR created notifications
- Status update notifications

TECHNICAL CONTEXT:
- Uses SMTP for email delivery
- Jinja2 templates for HTML emails
- Follows existing email_service.py pattern
"""

import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from bug_tracking.domain.entities.bug_report import BugReport
from bug_tracking.domain.entities.bug_analysis import BugAnalysisResult
from bug_tracking.domain.entities.bug_fix import BugFixAttempt


logger = logging.getLogger(__name__)


class BugEmailService:
    """
    Service for sending bug tracking email notifications.

    Sends notifications for:
    - Bug analysis complete
    - Fix generation results
    - PR creation
    - Status updates

    Example:
        service = BugEmailService()
        await service.send_bug_analysis_email(bug, analysis, fix_attempt)
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        template_dir: Optional[str] = None,
        mock_mode: bool = False
    ):
        """
        Initialize BugEmailService.

        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP username
            smtp_password: SMTP password
            from_email: Sender email address
            template_dir: Path to email templates
            mock_mode: If True, don't actually send emails (for testing)
        """
        self.smtp_host = smtp_host or os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.environ.get("SMTP_USER")
        self.smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD")
        self.from_email = from_email or os.environ.get("SMTP_FROM", "noreply@coursecreator.com")
        self.mock_mode = mock_mode or os.environ.get("EMAIL_MOCK_MODE", "false").lower() == "true"

        # Setup Jinja2 template environment
        template_path = template_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "templates"
        )
        self.template_env = Environment(
            loader=FileSystemLoader(template_path),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_bug_analysis_email(
        self,
        bug: BugReport,
        analysis: Optional[BugAnalysisResult],
        fix_attempt: Optional[BugFixAttempt] = None
    ) -> bool:
        """
        Send bug analysis notification email.

        Args:
            bug: Bug report
            analysis: Analysis results (if available)
            fix_attempt: Fix attempt (if available)

        Returns:
            bool: True if email sent successfully
        """
        subject = self._build_subject(bug, analysis, fix_attempt)
        html_body = self._build_html_body(bug, analysis, fix_attempt)
        text_body = self._build_text_body(bug, analysis, fix_attempt)

        return await self._send_email(
            to_email=bug.submitter_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

    async def send_status_update_email(
        self,
        bug: BugReport,
        old_status: str,
        new_status: str
    ) -> bool:
        """
        Send bug status update notification.

        Args:
            bug: Bug report
            old_status: Previous status
            new_status: New status

        Returns:
            bool: True if email sent successfully
        """
        subject = f"Bug Status Update: {bug.title[:50]}"

        html_body = f"""
        <html>
        <body>
            <h2>Bug Status Update</h2>
            <p><strong>Bug ID:</strong> {bug.id}</p>
            <p><strong>Title:</strong> {bug.title}</p>
            <p><strong>Status Changed:</strong> {old_status} → {new_status}</p>
            <p>
                <a href="https://coursecreator.com/bugs/{bug.id}">
                    View Bug Details
                </a>
            </p>
        </body>
        </html>
        """

        return await self._send_email(
            to_email=bug.submitter_email,
            subject=subject,
            html_body=html_body,
            text_body=f"Bug status changed from {old_status} to {new_status}"
        )

    def _build_subject(
        self,
        bug: BugReport,
        analysis: Optional[BugAnalysisResult],
        fix_attempt: Optional[BugFixAttempt]
    ) -> str:
        """Build email subject line."""
        if fix_attempt and fix_attempt.pr_url:
            return f"🔧 Bug Fix PR Created: {bug.title[:40]}"
        elif analysis:
            confidence = analysis.confidence_score
            emoji = "✅" if confidence >= 80 else "🔍"
            return f"{emoji} Bug Analysis Complete: {bug.title[:40]}"
        else:
            return f"📋 Bug Report Received: {bug.title[:40]}"

    def _build_html_body(
        self,
        bug: BugReport,
        analysis: Optional[BugAnalysisResult],
        fix_attempt: Optional[BugFixAttempt]
    ) -> str:
        """Build HTML email body."""
        try:
            template = self.template_env.get_template("bug_analysis_email.html")
            return template.render(
                bug=bug,
                analysis=analysis,
                fix_attempt=fix_attempt,
                now=datetime.utcnow()
            )
        except Exception as e:
            logger.warning(f"Template rendering failed, using fallback: {e}")
            return self._build_fallback_html(bug, analysis, fix_attempt)

    def _build_fallback_html(
        self,
        bug: BugReport,
        analysis: Optional[BugAnalysisResult],
        fix_attempt: Optional[BugFixAttempt]
    ) -> str:
        """Build fallback HTML if template fails."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 25px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge-critical {{ background: #e74c3c; color: white; }}
        .badge-high {{ background: #e67e22; color: white; }}
        .badge-medium {{ background: #f1c40f; color: #333; }}
        .badge-low {{ background: #27ae60; color: white; }}
        .code {{ background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; overflow-x: auto; }}
        .file-list {{ background: #f8f9fa; padding: 10px 15px; border-radius: 5px; }}
        .file-list li {{ margin: 5px 0; font-family: monospace; }}
        .confidence {{ font-size: 24px; font-weight: bold; }}
        .pr-link {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <h1>Bug Analysis Report</h1>

    <h2>Bug Information</h2>
    <p><strong>ID:</strong> {bug.id}</p>
    <p><strong>Title:</strong> {bug.title}</p>
    <p><strong>Severity:</strong> <span class="badge badge-{bug.severity.value}">{bug.severity.value.upper()}</span></p>
    <p><strong>Status:</strong> {bug.status.value}</p>

    <h2>Description</h2>
    <p>{bug.description}</p>
"""

        if analysis:
            html += f"""
    <h2>Root Cause Analysis</h2>
    <div class="code">
        {analysis.root_cause_analysis.replace(chr(10), '<br>')}
    </div>

    <h2>Suggested Fix</h2>
    <div class="code">
        {analysis.suggested_fix.replace(chr(10), '<br>')}
    </div>

    <h2>Affected Files</h2>
    <ul class="file-list">
        {''.join([f'<li>{f}</li>' for f in analysis.affected_files])}
    </ul>

    <h2>Analysis Confidence</h2>
    <p class="confidence">{analysis.confidence_score}%</p>
    <p>Complexity: {analysis.complexity_estimate.value}</p>
"""

        if fix_attempt and fix_attempt.pr_url:
            html += f"""
    <h2>Pull Request Created</h2>
    <p>An automated fix has been generated and a pull request has been opened.</p>
    <a href="{fix_attempt.pr_url}" class="pr-link">View Pull Request #{fix_attempt.pr_number}</a>
    <p><strong>Branch:</strong> {fix_attempt.branch_name}</p>
    <p><strong>Files Changed:</strong> {len(fix_attempt.files_changed)}</p>
    <p><strong>Tests:</strong> {fix_attempt.tests_passed} passed, {fix_attempt.tests_failed} failed</p>
"""
        elif fix_attempt and fix_attempt.error_message:
            html += f"""
    <h2>Fix Generation</h2>
    <p>Automated fix generation was attempted but encountered an issue:</p>
    <div class="code" style="color: #e74c3c;">{fix_attempt.error_message}</div>
"""

        html += f"""
    <div class="footer">
        <p>This is an automated message from the Course Creator Bug Tracking System.</p>
        <p>Bug ID: {bug.id} | Submitted: {bug.created_at.strftime('%Y-%m-%d %H:%M UTC')}</p>
    </div>
</body>
</html>
"""
        return html

    def _build_text_body(
        self,
        bug: BugReport,
        analysis: Optional[BugAnalysisResult],
        fix_attempt: Optional[BugFixAttempt]
    ) -> str:
        """Build plain text email body."""
        text = f"""
Bug Analysis Report
==================

Bug Information
---------------
ID: {bug.id}
Title: {bug.title}
Severity: {bug.severity.value}
Status: {bug.status.value}

Description
-----------
{bug.description}
"""

        if analysis:
            text += f"""
Root Cause Analysis
-------------------
{analysis.root_cause_analysis}

Suggested Fix
-------------
{analysis.suggested_fix}

Affected Files
--------------
{chr(10).join(['- ' + f for f in analysis.affected_files])}

Confidence Score: {analysis.confidence_score}%
Complexity: {analysis.complexity_estimate.value}
"""

        if fix_attempt and fix_attempt.pr_url:
            text += f"""
Pull Request Created
--------------------
PR URL: {fix_attempt.pr_url}
Branch: {fix_attempt.branch_name}
Files Changed: {len(fix_attempt.files_changed)}
Tests: {fix_attempt.tests_passed} passed, {fix_attempt.tests_failed} failed
"""

        return text

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content

        Returns:
            bool: True if sent successfully
        """
        if self.mock_mode:
            logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
            return True

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Attach both plain text and HTML versions
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
