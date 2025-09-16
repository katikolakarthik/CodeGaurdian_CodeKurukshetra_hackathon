"""
AI Code Reviewer & Bug Fixer utility.
Detects syntax errors, performance bottlenecks, and security issues.
"""

import ast
import re
import os
from typing import List, Dict, Any, Optional
import warnings

class CodeReviewer:
    """Comprehensive code analysis for multiple programming languages."""
    
    def __init__(self):
        self.supported_languages = {
            'python': self._analyze_python,
            'java': self._analyze_java,
            'javascript': self._analyze_javascript,
            'c': self._analyze_c,
            'cpp': self._analyze_cpp
        }
    
    def analyze_code(self, code: str, language: str, filename: str = "") -> Dict[str, Any]:
        """
        Analyze code for bugs, performance issues, and security vulnerabilities.
        
        Args:
            code: Source code string
            language: Programming language
            filename: Optional filename for context
            
        Returns:
            Dictionary with analysis results
        """
        if language not in self.supported_languages:
            return {
                'success': False,
                'error': f'Unsupported language: {language}',
                'bugs': [],
                'performance_issues': [],
                'security_issues': [],
                'suggestions': []
            }
        
        try:
            analyzer = self.supported_languages[language]
            return analyzer(code, filename)
        except Exception as e:
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}',
                'bugs': [],
                'performance_issues': [],
                'security_issues': [],
                'suggestions': []
            }
    
    def _analyze_python(self, code: str, filename: str) -> Dict[str, Any]:
        """Analyze Python code for issues."""
        bugs = []
        performance_issues = []
        security_issues = []
        suggestions = []
        
        # Syntax errors
        try:
            ast.parse(code)
        except SyntaxError as e:
            bugs.append({
                'type': 'syntax_error',
                'severity': 'high',
                'line': e.lineno,
                'message': f'Syntax error: {e.msg}',
                'suggestion': 'Fix syntax error before running code'
            })
        
        # Performance issues
        performance_issues.extend(self._check_python_performance(code))
        
        # Security issues
        security_issues.extend(self._check_python_security(code))
        
        # General suggestions
        suggestions.extend(self._get_python_suggestions(code))
        
        return {
            'success': True,
            'language': 'python',
            'filename': filename,
            'bugs': bugs,
            'performance_issues': performance_issues,
            'security_issues': security_issues,
            'suggestions': suggestions,
            'total_issues': len(bugs) + len(performance_issues) + len(security_issues)
        }
    
    def _analyze_java(self, code: str, filename: str) -> Dict[str, Any]:
        """Analyze Java code for issues."""
        bugs = []
        performance_issues = []
        security_issues = []
        suggestions = []
        
        # Basic Java pattern checks
        bugs.extend(self._check_java_syntax_patterns(code))
        performance_issues.extend(self._check_java_performance(code))
        security_issues.extend(self._check_java_security(code))
        suggestions.extend(self._get_java_suggestions(code))
        
        return {
            'success': True,
            'language': 'java',
            'filename': filename,
            'bugs': bugs,
            'performance_issues': performance_issues,
            'security_issues': security_issues,
            'suggestions': suggestions,
            'total_issues': len(bugs) + len(performance_issues) + len(security_issues)
        }
    
    def _analyze_javascript(self, code: str, filename: str) -> Dict[str, Any]:
        """Analyze JavaScript code for issues."""
        bugs = []
        performance_issues = []
        security_issues = []
        suggestions = []
        
        # Basic JS pattern checks
        bugs.extend(self._check_js_syntax_patterns(code))
        performance_issues.extend(self._check_js_performance(code))
        security_issues.extend(self._check_js_security(code))
        suggestions.extend(self._get_js_suggestions(code))
        
        return {
            'success': True,
            'language': 'javascript',
            'filename': filename,
            'bugs': bugs,
            'performance_issues': performance_issues,
            'security_issues': security_issues,
            'suggestions': suggestions,
            'total_issues': len(bugs) + len(performance_issues) + len(security_issues)
        }
    
    def _analyze_c(self, code: str, filename: str) -> Dict[str, Any]:
        """Analyze C code for issues."""
        bugs = []
        performance_issues = []
        security_issues = []
        suggestions = []
        
        # Basic C pattern checks
        bugs.extend(self._check_c_syntax_patterns(code))
        performance_issues.extend(self._check_c_performance(code))
        security_issues.extend(self._check_c_security(code))
        suggestions.extend(self._get_c_suggestions(code))
        
        return {
            'success': True,
            'language': 'c',
            'filename': filename,
            'bugs': bugs,
            'performance_issues': performance_issues,
            'security_issues': security_issues,
            'suggestions': suggestions,
            'total_issues': len(bugs) + len(performance_issues) + len(security_issues)
        }
    
    def _analyze_cpp(self, code: str, filename: str) -> Dict[str, Any]:
        """Analyze C++ code for issues."""
        bugs = []
        performance_issues = []
        security_issues = []
        suggestions = []
        
        # Basic C++ pattern checks
        bugs.extend(self._check_cpp_syntax_patterns(code))
        performance_issues.extend(self._check_cpp_performance(code))
        security_issues.extend(self._check_cpp_security(code))
        suggestions.extend(self._get_cpp_suggestions(code))
        
        return {
            'success': True,
            'language': 'cpp',
            'filename': filename,
            'bugs': bugs,
            'performance_issues': performance_issues,
            'security_issues': security_issues,
            'suggestions': suggestions,
            'total_issues': len(bugs) + len(performance_issues) + len(security_issues)
        }
    
    # Python-specific checks
    def _check_python_performance(self, code: str) -> List[Dict[str, Any]]:
        """Check Python code for performance issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Nested loops
            if line.strip().startswith('for ') and 'for ' in line:
                issues.append({
                    'type': 'nested_loop',
                    'severity': 'medium',
                    'line': i,
                    'message': 'Potential nested loop detected',
                    'suggestion': 'Consider using list comprehensions or vectorized operations'
                })
            
            # Unused imports
            if line.strip().startswith('import ') and not any(word in code for word in line.split()[1:]):
                issues.append({
                    'type': 'unused_import',
                    'severity': 'low',
                    'line': i,
                    'message': 'Unused import detected',
                    'suggestion': 'Remove unused imports to improve performance'
                })
            
            # String concatenation in loop
            if 'for ' in line and '+= ' in code[code.find(line):code.find(line) + 200]:
                issues.append({
                    'type': 'string_concat_loop',
                    'severity': 'medium',
                    'line': i,
                    'message': 'String concatenation in loop',
                    'suggestion': 'Use join() method for better performance'
                })
        
        return issues
    
    def _check_python_security(self, code: str) -> List[Dict[str, Any]]:
        """Check Python code for security issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Hardcoded secrets
            if any(keyword in line.lower() for keyword in ['password', 'secret', 'key', 'token']):
                if '=' in line and not any(var in line for var in ['input(', 'getenv(', 'os.environ']):
                    issues.append({
                        'type': 'hardcoded_secret',
                        'severity': 'high',
                        'line': i,
                        'message': 'Potential hardcoded secret detected',
                        'suggestion': 'Use environment variables or secure configuration'
                    })
            
            # SQL injection
            if 'execute(' in line and ('%' in line or '+' in line):
                issues.append({
                    'type': 'sql_injection',
                    'severity': 'high',
                    'line': i,
                    'message': 'Potential SQL injection vulnerability',
                    'suggestion': 'Use parameterized queries or prepared statements'
                })
            
            # eval() usage
            if 'eval(' in line:
                issues.append({
                    'type': 'eval_usage',
                    'severity': 'high',
                    'line': i,
                    'message': 'eval() function detected',
                    'suggestion': 'Avoid eval() as it can execute arbitrary code'
                })
        
        return issues
    
    def _get_python_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get general Python code suggestions."""
        suggestions = []
        
        # Check for missing docstrings
        if 'def ' in code and '"""' not in code:
            suggestions.append({
                'type': 'missing_docstring',
                'severity': 'low',
                'message': 'Consider adding docstrings to functions',
                'suggestion': 'Add docstrings to improve code documentation'
            })
        
        # Check for magic numbers
        if re.search(r'\b\d{3,}\b', code):
            suggestions.append({
                'type': 'magic_numbers',
                'severity': 'low',
                'message': 'Magic numbers detected',
                'suggestion': 'Use named constants instead of magic numbers'
            })
        
        return suggestions
    
    # Java-specific checks
    def _check_java_syntax_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Check Java code for syntax patterns."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Missing semicolon
            if (line.strip().endswith('}') or line.strip().endswith(')')) and not line.strip().endswith(';'):
                if not line.strip().startswith('//') and 'class ' not in line and 'public ' not in line:
                    issues.append({
                        'type': 'missing_semicolon',
                        'severity': 'high',
                        'line': i,
                        'message': 'Missing semicolon',
                        'suggestion': 'Add semicolon at end of statement'
                    })
        
        return issues
    
    def _check_java_performance(self, code: str) -> List[Dict[str, Any]]:
        """Check Java code for performance issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # String concatenation in loop
            if 'for ' in line and '+= ' in code[code.find(line):code.find(line) + 200]:
                issues.append({
                    'type': 'string_concat_loop',
                    'severity': 'medium',
                    'line': i,
                    'message': 'String concatenation in loop',
                    'suggestion': 'Use StringBuilder for better performance'
                })
        
        return issues
    
    def _check_java_security(self, code: str) -> List[Dict[str, Any]]:
        """Check Java code for security issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Hardcoded secrets
            if any(keyword in line.lower() for keyword in ['password', 'secret', 'key', 'token']):
                if '=' in line and not any(var in line for var in ['System.getenv', 'getProperty']):
                    issues.append({
                        'type': 'hardcoded_secret',
                        'severity': 'high',
                        'line': i,
                        'message': 'Potential hardcoded secret detected',
                        'suggestion': 'Use environment variables or secure configuration'
                    })
        
        return issues
    
    def _get_java_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get Java code suggestions."""
        suggestions = []
        
        if 'public class' in code and 'private' not in code:
            suggestions.append({
                'type': 'encapsulation',
                'severity': 'low',
                'message': 'Consider using private fields',
                'suggestion': 'Encapsulate class fields with private access modifiers'
            })
        
        return suggestions
    
    # JavaScript-specific checks
    def _check_js_syntax_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Check JavaScript code for syntax patterns."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Missing semicolon
            if line.strip() and not line.strip().endswith((';', '{', '}', '//')):
                if not line.strip().startswith('//'):
                    issues.append({
                        'type': 'missing_semicolon',
                        'severity': 'medium',
                        'line': i,
                        'message': 'Missing semicolon',
                        'suggestion': 'Add semicolon at end of statement'
                    })
        
        return issues
    
    def _check_js_performance(self, code: str) -> List[Dict[str, Any]]:
        """Check JavaScript code for performance issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # DOM queries in loop
            if 'for ' in line and ('getElementById' in code or 'querySelector' in code):
                issues.append({
                    'type': 'dom_query_loop',
                    'severity': 'medium',
                    'line': i,
                    'message': 'DOM query in loop',
                    'suggestion': 'Cache DOM elements outside the loop'
                })
        
        return issues
    
    def _check_js_security(self, code: str) -> List[Dict[str, Any]]:
        """Check JavaScript code for security issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # eval() usage
            if 'eval(' in line:
                issues.append({
                    'type': 'eval_usage',
                    'severity': 'high',
                    'line': i,
                    'message': 'eval() function detected',
                    'suggestion': 'Avoid eval() as it can execute arbitrary code'
                })
            
            # innerHTML without sanitization
            if 'innerHTML' in line and 'sanitize' not in code:
                issues.append({
                    'type': 'xss_vulnerability',
                    'severity': 'high',
                    'line': i,
                    'message': 'Potential XSS vulnerability',
                    'suggestion': 'Sanitize user input before setting innerHTML'
                })
        
        return issues
    
    def _get_js_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get JavaScript code suggestions."""
        suggestions = []
        
        if 'var ' in code and 'let ' not in code and 'const ' not in code:
            suggestions.append({
                'type': 'var_usage',
                'severity': 'low',
                'message': 'Consider using let/const instead of var',
                'suggestion': 'Use let/const for better block scoping'
            })
        
        return suggestions
    
    # C/C++ specific checks
    def _check_c_syntax_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Check C code for syntax patterns."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Missing semicolon
            if line.strip() and not line.strip().endswith((';', '{', '}', '//', '/*')):
                if not line.strip().startswith(('#', '//', '/*')):
                    issues.append({
                        'type': 'missing_semicolon',
                        'severity': 'high',
                        'line': i,
                        'message': 'Missing semicolon',
                        'suggestion': 'Add semicolon at end of statement'
                    })
        
        return issues
    
    def _check_c_performance(self, code: str) -> List[Dict[str, Any]]:
        """Check C code for performance issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # malloc without free
            if 'malloc(' in line and 'free(' not in code:
                issues.append({
                    'type': 'memory_leak',
                    'severity': 'high',
                    'line': i,
                    'message': 'Potential memory leak',
                    'suggestion': 'Ensure malloc() is paired with free()'
                })
        
        return issues
    
    def _check_c_security(self, code: str) -> List[Dict[str, Any]]:
        """Check C code for security issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # strcpy usage
            if 'strcpy(' in line:
                issues.append({
                    'type': 'buffer_overflow',
                    'severity': 'high',
                    'line': i,
                    'message': 'strcpy() can cause buffer overflow',
                    'suggestion': 'Use strncpy() or strlcpy() instead'
                })
            
            # gets() usage
            if 'gets(' in line:
                issues.append({
                    'type': 'buffer_overflow',
                    'severity': 'high',
                    'line': i,
                    'message': 'gets() is dangerous',
                    'suggestion': 'Use fgets() instead of gets()'
                })
        
        return issues
    
    def _get_c_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get C code suggestions."""
        suggestions = []
        
        if 'printf(' in code and 'scanf(' in code:
            suggestions.append({
                'type': 'io_validation',
                'severity': 'low',
                'message': 'Consider input validation',
                'suggestion': 'Add input validation for scanf()'
            })
        
        return suggestions
    
    def _check_cpp_syntax_patterns(self, code: str) -> List[Dict[str, Any]]:
        """Check C++ code for syntax patterns."""
        return self._check_c_syntax_patterns(code)  # Similar to C
    
    def _check_cpp_performance(self, code: str) -> List[Dict[str, Any]]:
        """Check C++ code for performance issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # new without delete
            if 'new ' in line and 'delete ' not in code:
                issues.append({
                    'type': 'memory_leak',
                    'severity': 'high',
                    'line': i,
                    'message': 'Potential memory leak',
                    'suggestion': 'Ensure new is paired with delete or use smart pointers'
                })
        
        return issues
    
    def _check_cpp_security(self, code: str) -> List[Dict[str, Any]]:
        """Check C++ code for security issues."""
        return self._check_c_security(code)  # Similar to C
    
    def _get_cpp_suggestions(self, code: str) -> List[Dict[str, Any]]:
        """Get C++ code suggestions."""
        suggestions = []
        
        if 'new ' in code and 'std::unique_ptr' not in code:
            suggestions.append({
                'type': 'smart_pointers',
                'severity': 'low',
                'message': 'Consider using smart pointers',
                'suggestion': 'Use std::unique_ptr or std::shared_ptr for automatic memory management'
            })
        
        return suggestions

# Global instance
code_reviewer = CodeReviewer()
