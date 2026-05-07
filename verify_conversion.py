#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PHP to Python Conversion Verifier
Checks all converted files for correctness
"""

import os
import re
import ast
import importlib.util
from pathlib import Path

class ConversionVerifier:
    def __init__(self, python_root, php_root):
        self.python_root = Path(python_root)
        self.php_root = Path(php_root)
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': [],
            'errors': []
        }
    
    def check_python_syntax(self, filepath):
        """Check if Python file has valid syntax"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return True, "Valid syntax"
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Error: {e}"
    
    def check_blueprint_definition(self, filepath):
        """Check if file has proper blueprint definition"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for Blueprint creation
            if 'Blueprint(' not in content:
                return False, "No Blueprint found"
            
            # Check for route definitions
            if '@' not in content or '.route' not in content:
                return False, "No route decorators found"
            
            # Check for login_required decorator
            if 'login_required' not in content:
                return False, "Missing login_required decorator"
            
            return True, "Valid blueprint structure"
        except Exception as e:
            return False, f"Error: {e}"
    
    def check_database_queries(self, filepath):
        """Check for common database issues"""
        warnings = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for cursor.execute() usage
            if 'cursor.execute' not in content and 'SELECT' in content:
                warnings.append("SELECT found but no cursor.execute()")
            
            # Check for connection closure
            if 'conn.close()' not in content and 'get_db()' in content:
                warnings.append("Database connection may not be closed")
            
            # Check for SQL injection vulnerabilities
            if 'f"' in content and 'SELECT' in content:
                if 'format' in content or '%s' not in content:
                    warnings.append("Possible SQL injection - use parameterized queries")
            
            return warnings
        except Exception as e:
            return [f"Error checking database: {e}"]
    
    def check_external_css_js(self, filepath):
        """Check if external CSS/JS are properly linked"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for internal CSS (should NOT have large style blocks)
            style_matches = re.findall(r'<style>(.*?)</style>', content, re.DOTALL)
            for style in style_matches:
                if len(style) > 500:  # More than 500 chars of CSS
                    return False, f"Large internal CSS block found ({len(style)} chars). Move to external file."
            
            # Check for external CSS links
            if '/static/css/core.css' not in content:
                return False, "Missing external core.css link"
            
            # Check for external JS links
            if '/static/js/core.js' not in content:
                return False, "Missing external core.js link"
            
            return True, "Properly uses external CSS/JS"
        except Exception as e:
            return False, f"Error checking CSS/JS: {e}"
    
    def compare_with_php(self, python_file, php_file):
        """Compare Python file with original PHP file for completeness"""
        try:
            with open(python_file, 'r', encoding='utf-8') as f:
                python_content = f.read()
            
            if not php_file.exists():
                return "warning", "PHP original not found"
            
            with open(php_file, 'r', encoding='utf-8') as f:
                php_content = f.read()
            
            # Extract table names from PHP
            php_tables = re.findall(r'FROM\s+(\w+)', php_content, re.IGNORECASE)
            php_tables.extend(re.findall(r'JOIN\s+(\w+)', php_content, re.IGNORECASE))
            php_tables = list(set(php_tables))
            
            # Extract table names from Python
            py_tables = re.findall(r'FROM\s+(\w+)', python_content, re.IGNORECASE)
            py_tables.extend(re.findall(r'JOIN\s+(\w+)', python_content, re.IGNORECASE))
            py_tables = list(set(py_tables))
            
            missing_tables = set(php_tables) - set(py_tables)
            if missing_tables:
                return "warning", f"Missing tables in Python: {missing_tables}"
            
            return "pass", "All tables appear to be converted"
        except Exception as e:
            return "error", f"Comparison error: {e}"
    
    def verify_file(self, python_file):
        """Run all checks on a single file"""
        rel_path = python_file.relative_to(self.python_root)
        php_file = self.php_root / rel_path.with_suffix('.php')
        
        print(f"\n{'='*60}")
        print(f"Checking: {rel_path}")
        print(f"{'='*60}")
        
        # Check 1: Python syntax
        syntax_ok, syntax_msg = self.check_python_syntax(python_file)
        print(f"  ✓ Syntax: {'✅' if syntax_ok else '❌'} {syntax_msg}")
        
        # Check 2: Blueprint structure
        bp_ok, bp_msg = self.check_blueprint_definition(python_file)
        print(f"  ✓ Blueprint: {'✅' if bp_ok else '❌'} {bp_msg}")
        
        # Check 3: External CSS/JS
        css_ok, css_msg = self.check_external_css_js(python_file)
        print(f"  ✓ CSS/JS: {'✅' if css_ok else '❌'} {css_msg}")
        
        # Check 4: Database queries
        db_warnings = self.check_database_queries(python_file)
        for warning in db_warnings:
            print(f"  ⚠️  Warning: {warning}")
        
        # Check 5: Compare with PHP
        comparison_status, comparison_msg = self.compare_with_php(python_file, php_file)
        if comparison_status == 'pass':
            print(f"  ✓ PHP Comparison: ✅ {comparison_msg}")
        elif comparison_status == 'warning':
            print(f"  ⚠️  PHP Comparison: {comparison_msg}")
        else:
            print(f"  ❌ PHP Comparison: {comparison_msg}")
        
        # Determine overall status
        if syntax_ok and bp_ok and css_ok:
            self.results['passed'].append(str(rel_path))
            print(f"\n  ✅ OVERALL: PASSED")
        else:
            self.results['failed'].append(str(rel_path))
            print(f"\n  ❌ OVERALL: FAILED")
        
        return syntax_ok and bp_ok and css_ok
    
    def scan_and_verify(self):
        """Scan all Python files in the director folder and verify"""
        print("\n" + "="*60)
        print("PHP TO PYTHON CONVERSION VERIFIER")
        print("="*60)
        
        # Find all Python files in director folder
        python_files = list(self.python_root.glob('director/*.py'))
        
        # Also check room_teacher folder
        python_files.extend(list(self.python_root.glob('room_teacher/**/*.py')))
        
        # Remove __init__.py and other special files
        python_files = [f for f in python_files if f.name != '__init__.py' and 'backup' not in f.name]
        
        print(f"\nFound {len(python_files)} Python files to verify\n")
        
        for py_file in python_files:
            self.verify_file(py_file)
        
        # Print summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print(f"✅ Passed: {len(self.results['passed'])} files")
        print(f"❌ Failed: {len(self.results['failed'])} files")
        
        if self.results['failed']:
            print("\nFailed files:")
            for f in self.results['failed']:
                print(f"  - {f}")
        
        return self.results

def main():
    python_root = r"C:\xampp\htdocs\roster_python"
    php_root = r"C:\xampp\htdocs\roster_php"
    
    verifier = ConversionVerifier(python_root, php_root)
    results = verifier.scan_and_verify()
    
    # Generate report
    report_path = os.path.join(python_root, 'conversion_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("PHP TO PYTHON CONVERSION REPORT\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total files checked: {len(results['passed']) + len(results['failed'])}\n")
        f.write(f"Passed: {len(results['passed'])}\n")
        f.write(f"Failed: {len(results['failed'])}\n\n")
        
        if results['failed']:
            f.write("FAILED FILES:\n")
            for file in results['failed']:
                f.write(f"  - {file}\n")
    
    print(f"\n📄 Detailed report saved to: {report_path}")

if __name__ == "__main__":
    main()