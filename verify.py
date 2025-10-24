#!/usr/bin/env python
"""
Verification script to check application structure and dependencies.
Run this before deploying to ensure everything is properly configured.
"""

import sys
import os

def check_file_exists(filepath):
    """Check if a file exists."""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"{status} {filepath}")
    return exists

def check_structure():
    """Check if all required files and directories exist."""
    print("\n=== Checking Project Structure ===\n")
    
    required_files = [
        'requirements.txt',
        '.env.example',
        'run.py',
        'web.config',
        'README.md',
        'app/__init__.py',
        'app/main.py',
        'app/components/__init__.py',
        'app/components/layout.py',
        'app/components/callbacks.py',
        'app/components/modal_callbacks.py',
        'app/services/event_service.py',
        'app/services/event_creation_service.py',
        'app/services/event_listings_repository.py',
        'app/services/event_accounts_repository.py',
        'app/services/call_history_repository.py',
        'app/services/member_research_repository.py',
        'app/utils/__init__.py',
        'app/utils/database.py',
        'app/utils/cache.py',
        'app/utils/csv_validator.py',
        'config/__init__.py',
        'config/settings.py',
    ]
    
    all_exist = True
    for filepath in required_files:
        if not check_file_exists(filepath):
            all_exist = False
    
    required_dirs = [
        'app',
        'app/components',
        'app/services',
        'app/utils',
        'config',
        'static',
        'static/css',
        'static/js',
    ]
    
    print("\n=== Checking Directories ===\n")
    for dirpath in required_dirs:
        exists = os.path.isdir(dirpath)
        status = "✓" if exists else "✗"
        print(f"{status} {dirpath}/")
        if not exists:
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if required Python packages can be imported."""
    print("\n=== Checking Dependencies ===\n")
    
    dependencies = [
        'dash',
        'dash_bootstrap_components',
        'flask',
        'uvicorn',
        'pyodbc',
        'pandas',
        'numpy',
        'cachelib',
        'redis',
        'dotenv',
        'plotly',
    ]
    
    all_installed = True
    for package in dependencies:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            all_installed = False
    
    return all_installed

def check_syntax():
    """Check Python files for syntax errors."""
    print("\n=== Checking Python Syntax ===\n")
    
    import py_compile
    import glob
    
    python_files = glob.glob('**/*.py', recursive=True)
    all_valid = True
    
    for filepath in python_files:
        if '__pycache__' in filepath or '.venv' in filepath or 'venv' in filepath:
            continue
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✓ {filepath}")
        except py_compile.PyCompileError as e:
            print(f"✗ {filepath}: {e}")
            all_valid = False
    
    return all_valid

def main():
    """Run all verification checks."""
    print("=" * 60)
    print("Dash Call Behavior Application - Verification Script")
    print("=" * 60)
    
    structure_ok = check_structure()
    syntax_ok = check_syntax()
    
    # Dependencies check requires installation
    print("\n=== Dependency Check ===\n")
    print("To check dependencies, first install them:")
    print("  pip install -r requirements.txt")
    print("\nThen run this script again.\n")
    
    # Try to check dependencies if possible
    try:
        deps_ok = check_dependencies()
    except Exception as e:
        print(f"\nDependencies not yet installed: {e}")
        deps_ok = False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Project Structure: {'✓ PASS' if structure_ok else '✗ FAIL'}")
    print(f"Python Syntax: {'✓ PASS' if syntax_ok else '✗ FAIL'}")
    print(f"Dependencies: {'✓ PASS' if deps_ok else '⚠ NOT CHECKED (install first)'}")
    print("=" * 60)
    
    if structure_ok and syntax_ok:
        print("\n✓ Application structure is valid!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Copy .env.example to .env and configure database settings")
        print("3. Run the application: python run.py")
        return 0
    else:
        print("\n✗ Some checks failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
