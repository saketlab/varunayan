#!/usr/bin/env python3
"""
Build versioned documentation using sphinx-multiversion.

This script builds documentation for all tagged versions and the main branch,
creating a version switcher that allows users to view changelog and docs
for different versions.

Usage:
    python scripts/build_versioned_docs.py
    
    # Or from the project root:
    python -m scripts.build_versioned_docs

Requirements:
    - Git repository with tagged versions (format: v0.1.0, v1.0.0, etc.)
    - sphinx-multiversion installed
    - Documentation dependencies installed
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Exit code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        sys.exit(1)


def main():
    """Build versioned documentation."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"
    
    print("Building versioned documentation...")
    print(f"Project root: {project_root}")
    print(f"Docs directory: {docs_dir}")
    
    # Check if we're in a git repository
    try:
        run_command("git status", cwd=project_root)
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository or git not available")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: Git executable not found")
        sys.exit(1)
    
    # Check for git tags
    tags = run_command("git tag -l 'v*'", cwd=project_root)
    if not tags:
        print("Warning: No version tags found.")
        print("Versioned docs will only include the current branch.")
        print("To create versioned docs, tag your releases with: git tag v0.1.0")
        print("Building documentation for current branch only...")
    
    # Install documentation dependencies
    print("Installing documentation dependencies...")
    run_command(f"{sys.executable} -m pip install -e .[docs]", cwd=project_root)
    
    # Build documentation
    if tags:
        print("Building versioned documentation with sphinx-multiversion...")
        build_cmd = f"sphinx-multiversion {docs_dir} {docs_dir}/_build/html"
    else:
        print("Building single-version documentation with sphinx...")
        build_cmd = f"sphinx-build -b html {docs_dir} {docs_dir}/_build/html"
    
    try:
        run_command(build_cmd, cwd=project_root)
        if tags:
            print("Versioned documentation built successfully!")
        else:
            print("Documentation built successfully!")
        print(f"Documentation available at: {docs_dir}/_build/html/")
        print("\nTo serve locally:")
        print(f"  cd {docs_dir}/_build/html && python -m http.server 8000")
        print("  Then visit: http://localhost:8000")
    except KeyboardInterrupt:
        print("\nBuild interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()