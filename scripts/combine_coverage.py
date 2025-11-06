#!/usr/bin/env python3
"""
Combined Coverage Report Generator

BUSINESS CONTEXT:
Combines Python backend and React frontend coverage data into a unified dashboard.
Provides platform-wide visibility into test coverage across all services and UI components.

TECHNICAL RATIONALE:
- Parses JSON coverage data from pytest-cov and Vitest
- Generates interactive HTML dashboard with service-level breakdown
- Calculates overall platform coverage percentage
- Identifies high-risk areas with low coverage
- Tracks coverage trends over time

INPUT FILES:
- coverage/python/coverage.json (pytest-cov format)
- coverage/react/coverage-final.json (Vitest/Istanbul format)

OUTPUT FILES:
- coverage/index.html (unified dashboard)
- coverage/combined-coverage.json (aggregated data)
- coverage/coverage-trends.json (historical tracking)

USAGE:
    python3 scripts/combine_coverage.py

CONFIGURATION:
- Minimum coverage threshold: 70%
- High coverage: 90%+
- Medium coverage: 70-89%
- Low coverage: <70%
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CoverageReportGenerator:
    """
    Generates combined coverage reports from Python and React coverage data.

    BUSINESS LOGIC:
    - Aggregates coverage from multiple sources
    - Normalizes different coverage formats
    - Calculates weighted averages
    - Generates visual HTML dashboard
    """

    def __init__(self, project_root: str):
        """Initialize the coverage report generator."""
        self.project_root = Path(project_root)
        self.coverage_dir = self.project_root / "coverage"
        self.python_coverage_file = self.coverage_dir / "python" / "coverage.json"
        self.react_coverage_file = self.coverage_dir / "react" / "coverage-final.json"
        self.combined_report_file = self.coverage_dir / "index.html"
        self.combined_data_file = self.coverage_dir / "combined-coverage.json"
        self.trends_file = self.coverage_dir / "coverage-trends.json"

        # Coverage thresholds
        self.threshold_low = 70
        self.threshold_high = 90

    def load_python_coverage(self) -> Dict[str, Any]:
        """
        Load Python coverage data from pytest-cov JSON output.

        RETURNS:
            Dictionary with coverage data or empty dict if file not found
        """
        if not self.python_coverage_file.exists():
            print(f"Warning: Python coverage file not found: {self.python_coverage_file}")
            return {}

        try:
            with open(self.python_coverage_file, "r") as f:
                data = json.load(f)
                print(f"✓ Loaded Python coverage data: {self.python_coverage_file}")
                return data
        except Exception as e:
            print(f"Error loading Python coverage: {e}")
            return {}

    def load_react_coverage(self) -> Dict[str, Any]:
        """
        Load React coverage data from Vitest/Istanbul JSON output.

        RETURNS:
            Dictionary with coverage data or empty dict if file not found
        """
        if not self.react_coverage_file.exists():
            print(f"Warning: React coverage file not found: {self.react_coverage_file}")
            return {}

        try:
            with open(self.react_coverage_file, "r") as f:
                data = json.load(f)
                print(f"✓ Loaded React coverage data: {self.react_coverage_file}")
                return data
        except Exception as e:
            print(f"Error loading React coverage: {e}")
            return {}

    def extract_python_summary(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract summary statistics from Python coverage data.

        BUSINESS LOGIC:
        - Totals: lines, statements, branches, functions
        - Percentages: coverage rates for each metric
        """
        if not data or "totals" not in data:
            return {
                "lines": 0,
                "statements": 0,
                "branches": 0,
                "functions": 0,
                "lines_pct": 0.0,
                "statements_pct": 0.0,
                "branches_pct": 0.0,
                "functions_pct": 0.0,
            }

        totals = data["totals"]
        return {
            "lines": totals.get("num_statements", 0),
            "covered_lines": totals.get("covered_lines", 0),
            "missing_lines": totals.get("missing_lines", 0),
            "statements": totals.get("num_statements", 0),
            "branches": totals.get("num_branches", 0),
            "functions": totals.get("num_statements", 0),  # Approximate
            "lines_pct": round(totals.get("percent_covered", 0.0), 2),
            "statements_pct": round(totals.get("percent_covered", 0.0), 2),
            "branches_pct": round(totals.get("percent_covered_display", 0.0), 2)
            if "percent_covered_display" in totals
            else round(totals.get("percent_covered", 0.0), 2),
            "functions_pct": round(totals.get("percent_covered", 0.0), 2),
        }

    def extract_react_summary(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract summary statistics from React coverage data.

        BUSINESS LOGIC:
        - Aggregates coverage across all files
        - Calculates percentages for lines, statements, branches, functions
        """
        if not data:
            return {
                "lines": 0,
                "statements": 0,
                "branches": 0,
                "functions": 0,
                "lines_pct": 0.0,
                "statements_pct": 0.0,
                "branches_pct": 0.0,
                "functions_pct": 0.0,
            }

        # Aggregate totals across all files
        total_lines = 0
        covered_lines = 0
        total_statements = 0
        covered_statements = 0
        total_branches = 0
        covered_branches = 0
        total_functions = 0
        covered_functions = 0

        for file_path, file_data in data.items():
            if isinstance(file_data, dict):
                # Lines
                if "lines" in file_data:
                    lines_data = file_data["lines"]
                    total_lines += lines_data.get("total", 0)
                    covered_lines += lines_data.get("covered", 0)

                # Statements
                if "statements" in file_data:
                    stmt_data = file_data["statements"]
                    total_statements += stmt_data.get("total", 0)
                    covered_statements += stmt_data.get("covered", 0)

                # Branches
                if "branches" in file_data:
                    branch_data = file_data["branches"]
                    total_branches += branch_data.get("total", 0)
                    covered_branches += branch_data.get("covered", 0)

                # Functions
                if "functions" in file_data:
                    func_data = file_data["functions"]
                    total_functions += func_data.get("total", 0)
                    covered_functions += func_data.get("covered", 0)

        # Calculate percentages
        return {
            "lines": total_lines,
            "covered_lines": covered_lines,
            "statements": total_statements,
            "branches": total_branches,
            "functions": total_functions,
            "lines_pct": round((covered_lines / total_lines * 100) if total_lines > 0 else 0.0, 2),
            "statements_pct": round(
                (covered_statements / total_statements * 100) if total_statements > 0 else 0.0, 2
            ),
            "branches_pct": round(
                (covered_branches / total_branches * 100) if total_branches > 0 else 0.0, 2
            ),
            "functions_pct": round(
                (covered_functions / total_functions * 100) if total_functions > 0 else 0.0, 2
            ),
        }

    def get_coverage_color(self, percentage: float) -> str:
        """
        Get color code for coverage percentage.

        BUSINESS LOGIC:
        - Green (high): 90%+
        - Yellow (medium): 70-89%
        - Red (low): <70%
        """
        if percentage >= self.threshold_high:
            return "#10b981"  # Green
        elif percentage >= self.threshold_low:
            return "#f59e0b"  # Yellow
        else:
            return "#ef4444"  # Red

    def get_coverage_status(self, percentage: float) -> str:
        """Get coverage status text."""
        if percentage >= self.threshold_high:
            return "Excellent"
        elif percentage >= self.threshold_low:
            return "Acceptable"
        else:
            return "Needs Improvement"

    def generate_html_report(
        self, python_summary: Dict[str, float], react_summary: Dict[str, float]
    ) -> str:
        """
        Generate HTML dashboard for combined coverage.

        BUSINESS LOGIC:
        - Visual dashboard with charts
        - Service-level breakdown
        - Coverage trends
        - Action items for improvement
        """
        # Calculate overall coverage (weighted average)
        total_lines = python_summary.get("lines", 0) + react_summary.get("lines", 0)
        python_weight = python_summary.get("lines", 0) / total_lines if total_lines > 0 else 0
        react_weight = react_summary.get("lines", 0) / total_lines if total_lines > 0 else 0

        overall_coverage = (
            python_summary.get("lines_pct", 0) * python_weight
            + react_summary.get("lines_pct", 0) * react_weight
        )

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Creator Platform - Test Coverage Dashboard</title>
    <style>
        :root {{
            --color-primary: #2563eb;
            --color-success: #10b981;
            --color-warning: #f59e0b;
            --color-danger: #ef4444;
            --color-bg: #f8fafc;
            --color-card: #ffffff;
            --color-border: #e2e8f0;
            --color-text: #1e293b;
            --color-text-light: #64748b;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .header {{
            text-align: center;
            margin-bottom: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, var(--color-primary) 0%, #1e40af 100%);
            border-radius: 1rem;
            color: white;
        }}

        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .timestamp {{
            text-align: center;
            color: var(--color-text-light);
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}

        .metric-card {{
            background: var(--color-card);
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border-left: 4px solid var(--color-primary);
        }}

        .metric-label {{
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--color-text-light);
            margin-bottom: 0.5rem;
        }}

        .metric-value {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        .metric-subtitle {{
            font-size: 0.875rem;
            color: var(--color-text-light);
        }}

        .coverage-section {{
            background: var(--color-card);
            border-radius: 0.75rem;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}

        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .section-icon {{
            width: 32px;
            height: 32px;
            border-radius: 0.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }}

        .coverage-breakdown {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }}

        .coverage-item {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .coverage-item-label {{
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--color-text-light);
        }}

        .coverage-bar-container {{
            background: var(--color-border);
            border-radius: 0.5rem;
            height: 1.5rem;
            overflow: hidden;
            position: relative;
        }}

        .coverage-bar {{
            height: 100%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 0.5rem;
            font-size: 0.75rem;
            font-weight: 600;
            color: white;
        }}

        .status-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status-excellent {{
            background: #d1fae5;
            color: #065f46;
        }}

        .status-acceptable {{
            background: #fef3c7;
            color: #92400e;
        }}

        .status-needs-improvement {{
            background: #fee2e2;
            color: #991b1b;
        }}

        .recommendation-box {{
            background: #fef3c7;
            border-left: 4px solid var(--color-warning);
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-top: 1rem;
        }}

        .recommendation-title {{
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #92400e;
        }}

        .recommendation-list {{
            list-style: none;
            padding-left: 0;
        }}

        .recommendation-list li {{
            padding: 0.5rem 0;
            padding-left: 1.5rem;
            position: relative;
        }}

        .recommendation-list li:before {{
            content: "→";
            position: absolute;
            left: 0;
            color: var(--color-warning);
            font-weight: 700;
        }}

        .footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--color-border);
            color: var(--color-text-light);
            font-size: 0.875rem;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 1rem;
            }}

            .header h1 {{
                font-size: 1.75rem;
            }}

            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Test Coverage Dashboard</h1>
            <p>Course Creator Platform - Comprehensive Coverage Analysis</p>
        </div>

        <div class="timestamp">
            Generated on {timestamp}
        </div>

        <div class="metrics-grid">
            <div class="metric-card" style="border-left-color: {self.get_coverage_color(overall_coverage)};">
                <div class="metric-label">Overall Coverage</div>
                <div class="metric-value" style="color: {self.get_coverage_color(overall_coverage)};">
                    {overall_coverage:.1f}%
                </div>
                <div class="metric-subtitle">
                    <span class="status-badge status-{self.get_coverage_status(overall_coverage).lower().replace(' ', '-')}">
                        {self.get_coverage_status(overall_coverage)}
                    </span>
                </div>
            </div>

            <div class="metric-card" style="border-left-color: {self.get_coverage_color(python_summary.get('lines_pct', 0))};">
                <div class="metric-label">Python Backend</div>
                <div class="metric-value" style="color: {self.get_coverage_color(python_summary.get('lines_pct', 0))};">
                    {python_summary.get('lines_pct', 0):.1f}%
                </div>
                <div class="metric-subtitle">
                    {python_summary.get('covered_lines', 0):,} / {python_summary.get('lines', 0):,} lines covered
                </div>
            </div>

            <div class="metric-card" style="border-left-color: {self.get_coverage_color(react_summary.get('lines_pct', 0))};">
                <div class="metric-label">React Frontend</div>
                <div class="metric-value" style="color: {self.get_coverage_color(react_summary.get('lines_pct', 0))};">
                    {react_summary.get('lines_pct', 0):.1f}%
                </div>
                <div class="metric-subtitle">
                    {react_summary.get('covered_lines', 0):,} / {react_summary.get('lines', 0):,} lines covered
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-label">Total Lines</div>
                <div class="metric-value">
                    {total_lines:,}
                </div>
                <div class="metric-subtitle">
                    Across all services and frontend
                </div>
            </div>
        </div>

        <div class="coverage-section">
            <div class="section-title">
                <div class="section-icon" style="background: #dbeafe; color: var(--color-primary);">
                    🐍
                </div>
                Python Backend Coverage
            </div>
            <div class="coverage-breakdown">
                <div class="coverage-item">
                    <div class="coverage-item-label">Lines</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {python_summary.get('lines_pct', 0)}%; background: {self.get_coverage_color(python_summary.get('lines_pct', 0))};">
                            {python_summary.get('lines_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-item-label">Statements</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {python_summary.get('statements_pct', 0)}%; background: {self.get_coverage_color(python_summary.get('statements_pct', 0))};">
                            {python_summary.get('statements_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-item-label">Branches</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {python_summary.get('branches_pct', 0)}%; background: {self.get_coverage_color(python_summary.get('branches_pct', 0))};">
                            {python_summary.get('branches_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-item-label">Functions</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {python_summary.get('functions_pct', 0)}%; background: {self.get_coverage_color(python_summary.get('functions_pct', 0))};">
                            {python_summary.get('functions_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
            </div>
            <div class="recommendation-box">
                <div class="recommendation-title">Python Coverage Analysis</div>
                <ul class="recommendation-list">
                    <li>View detailed report: <a href="python/index.html">Python Coverage Report</a></li>
                    <li>Focus on untested microservices and critical business logic</li>
                    <li>Add unit tests for data access layers and service classes</li>
                </ul>
            </div>
        </div>

        <div class="coverage-section">
            <div class="section-title">
                <div class="section-icon" style="background: #dbeafe; color: var(--color-primary);">
                    ⚛️
                </div>
                React Frontend Coverage
            </div>
            <div class="coverage-breakdown">
                <div class="coverage-item">
                    <div class="coverage-item-label">Lines</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {react_summary.get('lines_pct', 0)}%; background: {self.get_coverage_color(react_summary.get('lines_pct', 0))};">
                            {react_summary.get('lines_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-item-label">Statements</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {react_summary.get('statements_pct', 0)}%; background: {self.get_coverage_color(react_summary.get('statements_pct', 0))};">
                            {react_summary.get('statements_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-item-label">Branches</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {react_summary.get('branches_pct', 0)}%; background: {self.get_coverage_color(react_summary.get('branches_pct', 0))};">
                            {react_summary.get('branches_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
                <div class="coverage-item">
                    <div class="coverage-item-label">Functions</div>
                    <div class="coverage-bar-container">
                        <div class="coverage-bar" style="width: {react_summary.get('functions_pct', 0)}%; background: {self.get_coverage_color(react_summary.get('functions_pct', 0))};">
                            {react_summary.get('functions_pct', 0):.1f}%
                        </div>
                    </div>
                </div>
            </div>
            <div class="recommendation-box">
                <div class="recommendation-title">React Coverage Analysis</div>
                <ul class="recommendation-list">
                    <li>View detailed report: <a href="react/index.html">React Coverage Report</a></li>
                    <li>Focus on component logic and state management</li>
                    <li>Add tests for user interactions and accessibility</li>
                </ul>
            </div>
        </div>

        <div class="footer">
            <p>Generated by Course Creator Platform Coverage System</p>
            <p>For questions or issues, contact the development team</p>
        </div>
    </div>
</body>
</html>
"""
        return html

    def save_combined_data(
        self, python_summary: Dict[str, float], react_summary: Dict[str, float]
    ) -> None:
        """Save combined coverage data as JSON."""
        combined_data = {
            "timestamp": datetime.now().isoformat(),
            "python": python_summary,
            "react": react_summary,
            "overall": {
                "lines_pct": round(
                    (
                        python_summary.get("lines_pct", 0) * python_summary.get("lines", 0)
                        + react_summary.get("lines_pct", 0) * react_summary.get("lines", 0)
                    )
                    / (python_summary.get("lines", 0) + react_summary.get("lines", 0)),
                    2,
                )
                if (python_summary.get("lines", 0) + react_summary.get("lines", 0)) > 0
                else 0.0,
            },
        }

        with open(self.combined_data_file, "w") as f:
            json.dump(combined_data, f, indent=2)

        print(f"✓ Saved combined coverage data: {self.combined_data_file}")

    def update_trends(self, python_summary: Dict[str, float], react_summary: Dict[str, float]) -> None:
        """Update coverage trends file for historical tracking."""
        # Load existing trends
        trends = []
        if self.trends_file.exists():
            try:
                with open(self.trends_file, "r") as f:
                    trends = json.load(f)
            except Exception:
                pass

        # Add new entry
        trends.append(
            {
                "timestamp": datetime.now().isoformat(),
                "python_coverage": python_summary.get("lines_pct", 0),
                "react_coverage": react_summary.get("lines_pct", 0),
                "overall_coverage": round(
                    (
                        python_summary.get("lines_pct", 0) * python_summary.get("lines", 0)
                        + react_summary.get("lines_pct", 0) * react_summary.get("lines", 0)
                    )
                    / (python_summary.get("lines", 0) + react_summary.get("lines", 0)),
                    2,
                )
                if (python_summary.get("lines", 0) + react_summary.get("lines", 0)) > 0
                else 0.0,
            }
        )

        # Keep only last 30 entries
        trends = trends[-30:]

        with open(self.trends_file, "w") as f:
            json.dump(trends, f, indent=2)

        print(f"✓ Updated coverage trends: {self.trends_file}")

    def generate(self) -> bool:
        """
        Generate combined coverage report.

        RETURNS:
            True if successful, False otherwise
        """
        print("\n" + "=" * 70)
        print("Combining Coverage Reports")
        print("=" * 70 + "\n")

        # Load coverage data
        python_data = self.load_python_coverage()
        react_data = self.load_react_coverage()

        if not python_data and not react_data:
            print("\nError: No coverage data found!")
            print("Please run tests with coverage first.")
            return False

        # Extract summaries
        python_summary = self.extract_python_summary(python_data)
        react_summary = self.extract_react_summary(react_data)

        # Generate HTML report
        html_content = self.generate_html_report(python_summary, react_summary)

        # Save reports
        self.coverage_dir.mkdir(parents=True, exist_ok=True)

        with open(self.combined_report_file, "w") as f:
            f.write(html_content)

        print(f"\n✓ Generated HTML report: {self.combined_report_file}")

        # Save combined data
        self.save_combined_data(python_summary, react_summary)

        # Update trends
        self.update_trends(python_summary, react_summary)

        print("\n" + "=" * 70)
        print("Coverage Report Generation Complete!")
        print("=" * 70)
        print(f"\nOpen in browser: file://{self.combined_report_file.absolute()}")
        print()

        return True


def main():
    """Main entry point."""
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    generator = CoverageReportGenerator(str(project_root))

    try:
        success = generator.generate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
