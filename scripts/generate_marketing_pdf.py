#!/usr/bin/env python3
"""
Generate a professional Marketing and Research Plan PDF
with stylish design, consistent branding, and professional layout.
"""

import os
import re
from fpdf import FPDF, XPos, YPos
from datetime import datetime


# Brand Colors
BRAND_PRIMARY = (41, 128, 185)      # Blue
BRAND_SECONDARY = (52, 73, 94)      # Dark Blue-Gray
BRAND_ACCENT = (46, 204, 113)       # Green
BRAND_DARK = (44, 62, 80)           # Dark
BRAND_LIGHT = (236, 240, 241)       # Light Gray
BRAND_WHITE = (255, 255, 255)
BRAND_TEXT = (33, 33, 33)


class ProfessionalPDF(FPDF):
    """Professional PDF with consistent branding and styling."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)
        self.current_section = ""
        self.is_title_page = True

    def header(self):
        if self.page_no() <= 2:  # Skip header on title and TOC pages
            return

        # Top accent line
        self.set_draw_color(*BRAND_PRIMARY)
        self.set_line_width(0.8)
        self.line(10, 8, 200, 8)

        # Header text
        self.set_y(10)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*BRAND_SECONDARY)
        self.cell(95, 5, 'Course Creator Platform', new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font('Helvetica', 'I', 8)
        self.cell(95, 5, self.current_section, align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(8)

    def footer(self):
        self.set_y(-20)

        # Footer line
        self.set_draw_color(*BRAND_LIGHT)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())

        # Footer content
        self.set_y(-15)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*BRAND_SECONDARY)
        self.cell(95, 5, 'Confidential - For Investor Review Only', new_x=XPos.RIGHT, new_y=YPos.TOP)

        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(*BRAND_PRIMARY)
        self.cell(95, 5, f'Page {self.page_no()}', align='R', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def safe_text(self, text, max_len=500):
        """Clean and encode text safely."""
        if not text:
            return ""
        text = str(text)
        text = text.encode('latin-1', errors='replace').decode('latin-1')
        if len(text) > max_len:
            text = text[:max_len] + "..."
        return text

    def add_section_cover(self, section_num, title, subtitle):
        """Add a professional section cover page."""
        self.add_page()
        self.current_section = title

        # Large section number
        self.ln(50)
        self.set_font('Helvetica', 'B', 72)
        self.set_text_color(*BRAND_PRIMARY)
        self.cell(0, 30, f'{section_num:02d}', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Decorative line
        self.set_draw_color(*BRAND_ACCENT)
        self.set_line_width(2)
        self.line(70, self.get_y() + 5, 140, self.get_y() + 5)
        self.ln(20)

        # Section title
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(*BRAND_DARK)
        self.cell(0, 12, self.safe_text(title, 50), align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(8)

        # Subtitle
        self.set_font('Helvetica', 'I', 12)
        self.set_text_color(*BRAND_SECONDARY)
        self.cell(0, 8, self.safe_text(subtitle, 80), align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def add_heading(self, text, level=1):
        """Add styled heading."""
        text = self.safe_text(text, 120)
        if not text:
            return

        if level == 1:
            self.ln(8)
            # Blue left border accent
            y_start = self.get_y()
            self.set_fill_color(*BRAND_PRIMARY)
            self.rect(10, y_start, 3, 10, 'F')
            self.set_x(18)
            self.set_font('Helvetica', 'B', 14)
            self.set_text_color(*BRAND_DARK)
            self.cell(0, 10, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(4)

        elif level == 2:
            self.ln(6)
            self.set_font('Helvetica', 'B', 12)
            self.set_text_color(*BRAND_PRIMARY)
            self.cell(0, 8, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            # Subtle underline
            self.set_draw_color(*BRAND_LIGHT)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 100, self.get_y())
            self.ln(4)

        else:
            self.ln(4)
            self.set_font('Helvetica', 'B', 10)
            self.set_text_color(*BRAND_SECONDARY)
            self.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(2)

    def add_paragraph(self, text):
        """Add body paragraph."""
        text = self.safe_text(text, 400)
        if not text or len(text) < 3:
            return

        self.set_font('Helvetica', '', 9)
        self.set_text_color(*BRAND_TEXT)

        # Word wrap manually
        words = text.split()
        line = ""
        for word in words:
            test_line = line + " " + word if line else word
            if len(test_line) > 95:
                if line:
                    self.cell(0, 5, line.strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                line = word
            else:
                line = test_line
        if line:
            self.cell(0, 5, line.strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def add_bullet(self, text, indent=0):
        """Add styled bullet point."""
        text = self.safe_text(text, 150)
        if not text:
            return

        self.set_font('Helvetica', '', 9)
        self.set_text_color(*BRAND_TEXT)

        # Colored bullet
        x = 15 + (indent * 8)
        self.set_x(x)
        self.set_text_color(*BRAND_ACCENT)
        self.cell(6, 5, chr(149), new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_text_color(*BRAND_TEXT)

        # Truncate if needed
        if len(text) > 90:
            text = text[:87] + "..."
        self.cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def add_styled_table(self, headers, rows):
        """Add professionally styled table."""
        if not headers or not rows:
            return

        self.ln(4)

        # Limit columns
        num_cols = min(len(headers), 5)
        headers = headers[:num_cols]
        col_width = 180 / num_cols

        # Header row with gradient effect
        self.set_font('Helvetica', 'B', 8)
        self.set_fill_color(*BRAND_PRIMARY)
        self.set_text_color(*BRAND_WHITE)
        self.set_draw_color(*BRAND_PRIMARY)

        for i, header in enumerate(headers):
            header_text = self.safe_text(header, 22)
            self.cell(col_width, 7, header_text, border=1, fill=True, align='C',
                     new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.ln()

        # Data rows with alternating colors
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*BRAND_TEXT)
        self.set_draw_color(*BRAND_LIGHT)

        for idx, row in enumerate(rows[:12]):
            # Alternating row colors
            if idx % 2 == 0:
                self.set_fill_color(250, 252, 255)
            else:
                self.set_fill_color(*BRAND_WHITE)

            row = row[:num_cols]
            for cell in row:
                cell_text = self.safe_text(cell, 25)
                self.cell(col_width, 6, cell_text, border=1, fill=True,
                         new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.ln()

        self.ln(5)

    def add_highlight_box(self, title, content, box_type='info'):
        """Add a styled highlight box."""
        self.ln(4)

        # Choose colors based on type
        if box_type == 'success':
            bg_color = (232, 245, 233)
            border_color = BRAND_ACCENT
            title_color = (27, 94, 32)
        elif box_type == 'warning':
            bg_color = (255, 243, 224)
            border_color = (255, 152, 0)
            title_color = (230, 81, 0)
        else:  # info
            bg_color = (227, 242, 253)
            border_color = BRAND_PRIMARY
            title_color = BRAND_PRIMARY

        # Draw box
        y_start = self.get_y()
        self.set_fill_color(*bg_color)
        self.set_draw_color(*border_color)
        self.set_line_width(0.5)

        # Left accent bar
        self.set_fill_color(*border_color)
        self.rect(10, y_start, 3, 18, 'F')

        # Box background
        self.set_fill_color(*bg_color)
        self.rect(13, y_start, 187, 18, 'F')

        # Title
        self.set_xy(18, y_start + 2)
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*title_color)
        self.cell(0, 5, self.safe_text(title, 60), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Content
        self.set_x(18)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*BRAND_TEXT)
        self.cell(0, 5, self.safe_text(content, 100), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_y(y_start + 22)

    def add_divider(self):
        """Add a subtle section divider."""
        self.ln(6)
        self.set_draw_color(*BRAND_LIGHT)
        self.set_line_width(0.5)
        y = self.get_y()
        self.line(60, y, 150, y)
        self.ln(6)


def clean_markdown(text):
    """Clean markdown formatting."""
    if not text:
        return ""
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\[[ x]\]', '', text)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text.strip()


def parse_table(lines):
    """Parse markdown table."""
    headers = []
    rows = []

    for i, line in enumerate(lines):
        if '|' not in line:
            continue
        cells = [clean_markdown(c.strip()) for c in line.split('|') if c.strip()]

        if i == 0:
            headers = cells
        elif '---' in line:
            continue
        elif cells:
            rows.append(cells)

    return headers, rows


def process_document(pdf, filepath, section_num, title, subtitle):
    """Process a markdown document with professional styling."""
    if not os.path.exists(filepath):
        print(f"  Skipping: {filepath} not found")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add section cover
    pdf.add_section_cover(section_num, title, subtitle)
    pdf.add_page()

    lines = content.split('\n')
    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]

        # Track code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            i += 1
            continue

        if in_code_block:
            i += 1
            continue

        line = line.strip()

        if not line:
            i += 1
            continue

        # Headers
        if line.startswith('# '):
            pdf.add_heading(clean_markdown(line[2:]), level=1)
        elif line.startswith('## '):
            pdf.add_heading(clean_markdown(line[3:]), level=2)
        elif line.startswith('### ') or line.startswith('#### '):
            header_text = re.sub(r'^#+\s*', '', line)
            pdf.add_heading(clean_markdown(header_text), level=3)

        # Tables
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            if table_lines:
                headers, rows = parse_table(table_lines)
                if headers and rows:
                    pdf.add_styled_table(headers, rows)
            continue

        # Bullet points
        elif line.startswith('- ') or line.startswith('* '):
            pdf.add_bullet(clean_markdown(line[2:]))

        # Numbered lists
        elif re.match(r'^\d+\. ', line):
            text = re.sub(r'^\d+\. ', '', line)
            pdf.add_bullet(clean_markdown(text))

        # Horizontal rules
        elif line.startswith('---'):
            pdf.add_divider()

        # Regular text
        else:
            text = clean_markdown(line)
            if text and len(text) > 3:
                pdf.add_paragraph(text)

        i += 1


def create_title_page(pdf):
    """Create a stunning title page."""
    pdf.add_page()

    # Top accent bar
    pdf.set_fill_color(*BRAND_PRIMARY)
    pdf.rect(0, 0, 210, 40, 'F')

    # Gradient effect with secondary color
    pdf.set_fill_color(*BRAND_SECONDARY)
    pdf.rect(0, 35, 210, 10, 'F')

    # Company name in header
    pdf.set_xy(0, 12)
    pdf.set_font('Helvetica', 'B', 28)
    pdf.set_text_color(*BRAND_WHITE)
    pdf.cell(0, 15, 'COURSE CREATOR', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Main content area
    pdf.ln(50)

    # Document title
    pdf.set_font('Helvetica', 'B', 32)
    pdf.set_text_color(*BRAND_DARK)
    pdf.cell(0, 15, 'Marketing &', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 15, 'Research Plan', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(10)

    # Decorative element
    pdf.set_draw_color(*BRAND_ACCENT)
    pdf.set_line_width(3)
    pdf.line(75, pdf.get_y(), 135, pdf.get_y())

    pdf.ln(15)

    # Tagline
    pdf.set_font('Helvetica', 'I', 14)
    pdf.set_text_color(*BRAND_SECONDARY)
    pdf.cell(0, 8, 'AI-Powered Corporate Training Platform', align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(25)

    # Key metrics box
    pdf.set_fill_color(*BRAND_LIGHT)
    pdf.rect(40, pdf.get_y(), 130, 45, 'F')

    y_box = pdf.get_y() + 5
    metrics = [
        ("Target Market", "$165B by 2034"),
        ("Year 5 ARR Target", "$49M"),
        ("Seed Round", "$2M"),
    ]

    for label, value in metrics:
        pdf.set_xy(50, y_box)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*BRAND_SECONDARY)
        pdf.cell(60, 6, label, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*BRAND_PRIMARY)
        pdf.cell(50, 6, value, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y_box += 12

    pdf.set_y(y_box + 20)

    # Document info
    pdf.set_font('Helvetica', '', 10)
    pdf.set_text_color(*BRAND_TEXT)

    info = [
        f"Prepared: {datetime.now().strftime('%B %d, %Y')}",
        "Version 1.0 | Confidential",
        "",
        "For Investor & Partner Review"
    ]

    for line in info:
        pdf.cell(0, 6, line, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Bottom accent
    pdf.set_fill_color(*BRAND_PRIMARY)
    pdf.rect(0, 277, 210, 20, 'F')


def create_toc_page(pdf):
    """Create a professional table of contents."""
    pdf.add_page()

    # TOC Header
    pdf.ln(10)
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(*BRAND_DARK)
    pdf.cell(0, 12, 'Contents', align='L', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Accent line
    pdf.set_draw_color(*BRAND_PRIMARY)
    pdf.set_line_width(2)
    pdf.line(10, pdf.get_y() + 2, 50, pdf.get_y() + 2)

    pdf.ln(15)

    sections = [
        (1, "Investor Pitch Deck",
         "15-slide presentation: problem, solution, market, financials, team, and ask"),
        (2, "Comprehensive Startup Plan",
         "Market analysis, GTM strategy, product roadmap, financial plan, and milestones"),
        (3, "Revenue Model Projections",
         "5-year projections for SaaS, Enterprise License, and Hybrid revenue models"),
        (4, "Competitive Intelligence",
         "SWOT analysis, competitor profiles, positioning strategy, and sales battle cards"),
    ]

    for num, title, desc in sections:
        # Section number
        pdf.set_font('Helvetica', 'B', 28)
        pdf.set_text_color(*BRAND_PRIMARY)
        pdf.cell(25, 20, f'{num:02d}', new_x=XPos.RIGHT, new_y=YPos.TOP)

        # Section title and description
        y = pdf.get_y()
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*BRAND_DARK)
        pdf.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_x(35)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*BRAND_SECONDARY)
        pdf.cell(0, 5, desc, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(10)

        # Subtle divider
        pdf.set_draw_color(*BRAND_LIGHT)
        pdf.set_line_width(0.3)
        pdf.line(35, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)


def create_executive_summary(pdf):
    """Create an executive summary page."""
    pdf.add_page()
    pdf.current_section = "Executive Summary"

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 20)
    pdf.set_text_color(*BRAND_DARK)
    pdf.cell(0, 10, 'Executive Summary', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Accent line
    pdf.set_draw_color(*BRAND_PRIMARY)
    pdf.set_line_width(2)
    pdf.line(10, pdf.get_y() + 2, 60, pdf.get_y() + 2)
    pdf.ln(12)

    # The Opportunity
    pdf.add_highlight_box(
        "The Opportunity",
        "$165B market by 2034. AI-powered training with unique lab environments.",
        'info'
    )

    # Key sections
    summaries = [
        ("The Problem",
         "Course creation takes 40-200 hours. 44% of skills changing by 2028. "
         "No hands-on lab platforms exist for technical training."),
        ("Our Solution",
         "AI generates complete courses in under 1 hour. Integrated VSCode, Jupyter, "
         "IntelliJ lab environments. All-in-one platform replacing 3-5 tools."),
        ("Business Model",
         "Hybrid SaaS + Enterprise License. $49M ARR target by Year 5. "
         "73% recurring revenue. 81% gross margin. 10.5:1 LTV:CAC."),
        ("Competitive Advantage",
         "Only platform with integrated lab environments. AI-native architecture. "
         "18+ month technical moat. GDPR/CCPA compliant."),
        ("The Ask",
         "$2M Seed Round at $8M pre-money. 18-month runway to Series A. "
         "Target: 50 customers, $500K ARR, SOC 2 certification."),
    ]

    for title, content in summaries:
        pdf.ln(2)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*BRAND_PRIMARY)
        pdf.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*BRAND_TEXT)

        # Word wrap
        words = content.split()
        line = ""
        for word in words:
            test = line + " " + word if line else word
            if len(test) > 95:
                pdf.cell(0, 5, line.strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                line = word
            else:
                line = test
        if line:
            pdf.cell(0, 5, line.strip(), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)


def main():
    """Generate the professional PDF."""
    docs_dir = '/home/bbrelin/course-creator/docs'
    output_path = os.path.join(docs_dir, 'Course_Creator_Marketing_Research_Plan.pdf')

    print("=" * 60)
    print("  Generating Professional Marketing & Research Plan PDF")
    print("=" * 60)

    # Create PDF
    pdf = ProfessionalPDF()

    # Title page
    print("  [1/6] Creating title page...")
    create_title_page(pdf)

    # Table of contents
    print("  [2/6] Creating table of contents...")
    create_toc_page(pdf)

    # Executive summary
    print("  [3/6] Adding executive summary...")
    create_executive_summary(pdf)

    # Process documents
    documents = [
        ('INVESTOR_PITCH_DECK.md', 1, 'Investor Pitch Deck',
         'Company Overview, Market Opportunity & Investment Ask'),
        ('STARTUP_PLAN.md', 2, 'Startup Plan',
         'Market Analysis, GTM Strategy & Execution Roadmap'),
        ('DUAL_REVENUE_MODEL_PROJECTIONS.md', 3, 'Revenue Projections',
         '5-Year Financial Models & Unit Economics'),
        ('COMPETITIVE_INTELLIGENCE.md', 4, 'Competitive Intelligence',
         'SWOT Analysis & Competitor Battle Cards'),
    ]

    for i, (filename, section_num, title, subtitle) in enumerate(documents, 4):
        filepath = os.path.join(docs_dir, filename)
        print(f"  [{i}/6] Processing {filename}...")
        try:
            process_document(pdf, filepath, section_num, title, subtitle)
        except Exception as e:
            print(f"       Warning: {e}")

    # Save PDF
    pdf.output(output_path)

    print("=" * 60)
    print(f"  PDF Generated Successfully!")
    print(f"  Location: {output_path}")
    print(f"  Pages: {pdf.page_no()}")
    print("=" * 60)


if __name__ == '__main__':
    main()
