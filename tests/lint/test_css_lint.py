"""
CSS LINTING TEST SUITE
PURPOSE: Validate CSS code quality, consistency, and best practices
WHY: Ensure maintainable, performant stylesheets following modern CSS standards
"""

import subprocess
import sys
import os
from pathlib import Path
import re
import pytest

# Frontend CSS path
CSS_PATH = Path(__file__).parent.parent.parent / "frontend" / "css"

class TestCSSLinting:
    """
    CSS code quality validation tests
    """
    
    def test_css_syntax_validation(self):
        """
        Test CSS syntax validity
        WHY: Catch syntax errors that would break styling
        """
        css_files = list(CSS_PATH.rglob("*.css"))
        syntax_errors = []
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic syntax checks
            brace_count = content.count('{') - content.count('}')
            if brace_count != 0:
                syntax_errors.append(f"{css_file}: Mismatched braces (difference: {brace_count})")
            
            # Check for unterminated comments
            if '/*' in content:
                comment_starts = content.count('/*')
                comment_ends = content.count('*/')
                if comment_starts != comment_ends:
                    syntax_errors.append(f"{css_file}: Unterminated CSS comments")
            
            # Check for common syntax errors
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for missing semicolons (basic check)
                if ':' in line_stripped and line_stripped.endswith('}'):
                    if ';' not in line_stripped:
                        syntax_errors.append(f"{css_file}:{i}: Missing semicolon before closing brace")
        
        if syntax_errors:
            error_msg = "CSS syntax errors found:\n" + "\n".join(syntax_errors)
            assert False, error_msg
    
    def test_css_variable_usage(self):
        """
        Test consistent usage of CSS custom properties (variables)
        WHY: CSS variables improve maintainability and consistency
        """
        css_files = list(CSS_PATH.rglob("*.css"))
        # Exclude legacy backup files
        css_files = [f for f in css_files if 'legacy-backup' not in str(f)]
        variable_stats = {
            "files_using_vars": 0,
            "hardcoded_colors": [],
            "undefined_vars": []
        }
        
        # First pass: collect all defined variables
        defined_vars = set()
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find variable definitions
            var_definitions = re.findall(r'--[\w-]+:', content)
            for var_def in var_definitions:
                defined_vars.add(var_def.rstrip(':'))
        
        # Second pass: check usage
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if file uses CSS variables
            if 'var(--' in content:
                variable_stats["files_using_vars"] += 1
            
            # Find variable usage
            var_usage = re.findall(r'var\((--[\w-]+)\)', content)
            for var_name in var_usage:
                if var_name not in defined_vars:
                    variable_stats["undefined_vars"].append(f"{css_file}: {var_name}")
            
            # Check for hardcoded colors that could use variables
            hardcoded_colors = re.findall(r'#[0-9a-fA-F]{3,6}(?![^{]*:root)', content)
            if hardcoded_colors:
                variable_stats["hardcoded_colors"].extend([
                    f"{css_file}: {color}" for color in set(hardcoded_colors)
                ])
        
        print(f"CSS Variables usage: {variable_stats['files_using_vars']}/{len(css_files)} files")
        
        if variable_stats["undefined_vars"]:
            print(f"Undefined variables found: {variable_stats['undefined_vars'][:5]}")
        
        if variable_stats["hardcoded_colors"][:10]:
            print(f"Hardcoded colors found: {variable_stats['hardcoded_colors'][:10]}")
        
        # Ensure no undefined variables are used
        assert not variable_stats["undefined_vars"], f"Undefined CSS variables: {variable_stats['undefined_vars']}"
    
    def test_css_organization(self):
        """
        Test CSS file organization and structure
        WHY: Well-organized CSS is easier to maintain
        """
        css_files = list(CSS_PATH.rglob("*.css"))
        organization_issues = []
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for proper commenting
            if len(content) > 1000 and '/*' not in content:  # Large files should have comments
                organization_issues.append(f"{css_file}: Large file lacks comments")
            
            # Check for vendor prefixes consistency
            webkit_count = content.count('-webkit-')
            moz_count = content.count('-moz-')
            if webkit_count > 0 and moz_count == 0:
                organization_issues.append(f"{css_file}: Has -webkit- prefixes but no -moz- prefixes")
        
        if organization_issues:
            print("CSS organization suggestions:\n" + "\n".join(organization_issues[:5]))
    
    def test_responsive_design_patterns(self):
        """
        Test for responsive design best practices
        WHY: Ensures proper mobile-first responsive design
        """
        css_files = list(CSS_PATH.rglob("*.css"))
        responsive_stats = {
            "files_with_media_queries": 0,
            "mobile_first_violations": [],
            "common_breakpoints": []
        }
        
        common_breakpoints = ['768px', '992px', '1200px', '576px']
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for media queries
            if '@media' in content:
                responsive_stats["files_with_media_queries"] += 1
                
                # Find breakpoints
                breakpoints = re.findall(r'@media[^{]*\((?:min-width|max-width):\s*(\d+px)', content)
                responsive_stats["common_breakpoints"].extend(breakpoints)
                
                # Check for mobile-first approach (min-width vs max-width)
                min_width_count = content.count('min-width')
                max_width_count = content.count('max-width')
                
                if max_width_count > min_width_count:
                    responsive_stats["mobile_first_violations"].append(
                        f"{css_file}: More max-width than min-width queries (desktop-first)"
                    )
        
        print(f"Responsive design: {responsive_stats['files_with_media_queries']}/{len(css_files)} files have media queries")
        
        if responsive_stats["mobile_first_violations"]:
            print("Mobile-first violations:\n" + "\n".join(responsive_stats["mobile_first_violations"]))
    
    def test_css_performance_best_practices(self):
        """
        Test for CSS performance best practices
        WHY: Optimized CSS improves page load times
        """
        css_files = list(CSS_PATH.rglob("*.css"))
        performance_issues = []
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for expensive selectors
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Universal selector usage
                if line_stripped.startswith('* ') or line_stripped.startswith('*,'):
                    performance_issues.append(f"{css_file}:{i}: Universal selector (*) can be slow")
                
                # Complex descendant selectors
                if line_stripped.count(' ') > 4 and '{' in line_stripped:
                    performance_issues.append(f"{css_file}:{i}: Complex selector may impact performance")
                
                # !important usage
                if '!important' in line_stripped:
                    performance_issues.append(f"{css_file}:{i}: Avoid !important when possible")
        
        if performance_issues[:10]:
            print("Performance suggestions:\n" + "\n".join(performance_issues[:10]))
    
    def test_css_accessibility(self):
        """
        Test for CSS accessibility best practices
        WHY: Accessible CSS improves usability for all users
        """
        css_files = list(CSS_PATH.rglob("*.css"))
        accessibility_stats = {
            "focus_styles": 0,
            "color_contrast_warnings": [],
            "reduced_motion_support": 0
        }
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for focus styles
            if ':focus' in content:
                accessibility_stats["focus_styles"] += 1
            
            # Check for reduced motion support
            if 'prefers-reduced-motion' in content:
                accessibility_stats["reduced_motion_support"] += 1
            
            # Basic color contrast check (look for very light colors)
            light_colors = re.findall(r'color:\s*#[f-f][f-f][f-f]', content, re.IGNORECASE)
            if light_colors:
                accessibility_stats["color_contrast_warnings"].append(
                    f"{css_file}: Very light text colors may have poor contrast"
                )
        
        print(f"Accessibility: {accessibility_stats['focus_styles']}/{len(css_files)} files have focus styles")
        print(f"Reduced motion: {accessibility_stats['reduced_motion_support']}/{len(css_files)} files support reduced motion")
        
        # Ensure at least some files have focus styles
        assert accessibility_stats["focus_styles"] > 0, "No focus styles found - important for accessibility"
    
    def test_css_modern_features(self):
        """
        Test usage of modern CSS features
        WHY: Modern CSS features improve development efficiency
        """
        css_files = list(CSS_PATH.rglob("*.css"))
        modern_features = {
            "grid_usage": 0,
            "flexbox_usage": 0,
            "custom_properties": 0,
            "logical_properties": 0
        }
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'display: grid' in content or 'grid-template' in content:
                modern_features["grid_usage"] += 1
            
            if 'display: flex' in content or 'flex-' in content:
                modern_features["flexbox_usage"] += 1
            
            if '--' in content:  # CSS custom properties
                modern_features["custom_properties"] += 1
            
            if any(prop in content for prop in ['margin-inline', 'padding-block', 'border-inline']):
                modern_features["logical_properties"] += 1
        
        print(f"Modern CSS features usage:")
        print(f"  Grid: {modern_features['grid_usage']}/{len(css_files)} files")
        print(f"  Flexbox: {modern_features['flexbox_usage']}/{len(css_files)} files")
        print(f"  Custom properties: {modern_features['custom_properties']}/{len(css_files)} files")
        
        # Ensure modern layout methods are being used
        total_layout_usage = modern_features["grid_usage"] + modern_features["flexbox_usage"]
        assert total_layout_usage > 0, "No modern layout methods (Grid/Flexbox) found"