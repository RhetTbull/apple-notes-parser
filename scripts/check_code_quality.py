#!/usr/bin/env python3
"""
Code quality check script for apple-notes-parser.

This script runs all the code quality tools in the correct order:
1. Ruff linting with automatic fixes
2. Ruff formatting
3. MyPy type checking
4. Optional: Run tests

Usage:
    python scripts/check_code_quality.py
    python scripts/check_code_quality.py --with-tests
    python scripts/check_code_quality.py --fix-only
    python scripts/check_code_quality.py --check-only
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(cmd: List[str], description: str, cwd: Path = None) -> Tuple[bool, str, str]:
    """
    Run a command and return success status and output.
    
    Args:
        cmd: Command and arguments as list
        description: Human-readable description of the command
        cwd: Working directory (defaults to project root)
    
    Returns:
        Tuple of (success, stdout, stderr)
    """
    print(f"🔄 {description}...")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        success = result.returncode == 0
        if success:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED")
            
        return success, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False, "", "Command timed out after 5 minutes"
    except FileNotFoundError:
        print(f"💥 {description} - COMMAND NOT FOUND")
        return False, "", f"Command not found: {cmd[0]}"
    except Exception as e:
        print(f"💥 {description} - ERROR")
        return False, "", str(e)


def check_uv_available() -> bool:
    """Check if uv is available."""
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def main():
    """Main script execution."""
    parser = argparse.ArgumentParser(
        description="Run code quality checks for apple-notes-parser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/check_code_quality.py                    # Run all checks
  python scripts/check_code_quality.py --with-tests       # Include test suite
  python scripts/check_code_quality.py --fix-only         # Only run fixing tools
  python scripts/check_code_quality.py --check-only       # Only run checking tools
  python scripts/check_code_quality.py --no-format        # Skip formatting
        """
    )
    
    parser.add_argument(
        "--with-tests", 
        action="store_true", 
        help="Run test suite after quality checks"
    )
    parser.add_argument(
        "--fix-only", 
        action="store_true", 
        help="Only run tools that fix issues (ruff check --fix, ruff format)"
    )
    parser.add_argument(
        "--check-only", 
        action="store_true", 
        help="Only run tools that check without fixing (ruff check, mypy)"
    )
    parser.add_argument(
        "--no-format", 
        action="store_true", 
        help="Skip ruff formatting"
    )
    parser.add_argument(
        "--no-fix", 
        action="store_true", 
        help="Skip automatic fixes in ruff check"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Show detailed output from tools"
    )
    
    args = parser.parse_args()
    
    # Validate mutually exclusive options
    if args.fix_only and args.check_only:
        print("❌ Cannot use --fix-only and --check-only together")
        return 1
    
    # Project paths
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    print("🚀 Starting code quality checks for apple-notes-parser")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Source directory: {src_dir}")
    
    # Check if uv is available
    use_uv = check_uv_available()
    if use_uv:
        print("📦 Using uv for command execution")
        cmd_prefix = ["uv", "run"]
    else:
        print("📦 Using direct python execution (uv not found)")
        cmd_prefix = []
    
    # Track results
    all_results = []
    failed_checks = []
    
    print("\n" + "="*60)
    
    # 1. Ruff linting with fixes (unless check-only or no-fix)
    if not args.check_only:
        if args.no_fix:
            success, stdout, stderr = run_command(
                cmd_prefix + ["ruff", "check", str(src_dir)],
                "Ruff linting (check only)",
                cwd=project_root
            )
        else:
            success, stdout, stderr = run_command(
                cmd_prefix + ["ruff", "check", "--fix", str(src_dir)],
                "Ruff linting with automatic fixes",
                cwd=project_root
            )
        
        all_results.append(("ruff_lint", success, stdout, stderr))
        if not success:
            failed_checks.append("Ruff linting")
            
        if args.verbose and (stdout or stderr):
            print(f"📝 Ruff lint output:\n{stdout}")
            if stderr:
                print(f"📝 Ruff lint errors:\n{stderr}")
    
    # 2. Ruff formatting (unless check-only or no-format)
    if not args.check_only and not args.no_format:
        success, stdout, stderr = run_command(
            cmd_prefix + ["ruff", "format", str(src_dir)],
            "Ruff code formatting",
            cwd=project_root
        )
        
        all_results.append(("ruff_format", success, stdout, stderr))
        if not success:
            failed_checks.append("Ruff formatting")
            
        if args.verbose and (stdout or stderr):
            print(f"📝 Ruff format output:\n{stdout}")
            if stderr:
                print(f"📝 Ruff format errors:\n{stderr}")
    
    # 3. Ruff check without fixes (if we did fixes above, check again)
    if not args.fix_only and not args.no_fix and not args.check_only:
        success, stdout, stderr = run_command(
            cmd_prefix + ["ruff", "check", str(src_dir)],
            "Ruff linting verification (after fixes)",
            cwd=project_root
        )
        
        all_results.append(("ruff_verify", success, stdout, stderr))
        if not success:
            failed_checks.append("Ruff verification")
            
        if args.verbose and (stdout or stderr):
            print(f"📝 Ruff verify output:\n{stdout}")
            if stderr:
                print(f"📝 Ruff verify errors:\n{stderr}")
    
    # 4. Ruff check only (if check-only mode)
    if args.check_only:
        success, stdout, stderr = run_command(
            cmd_prefix + ["ruff", "check", str(src_dir)],
            "Ruff linting check",
            cwd=project_root
        )
        
        all_results.append(("ruff_check", success, stdout, stderr))
        if not success:
            failed_checks.append("Ruff check")
            
        if args.verbose and (stdout or stderr):
            print(f"📝 Ruff check output:\n{stdout}")
            if stderr:
                print(f"📝 Ruff check errors:\n{stderr}")
    
    # 5. MyPy type checking (unless fix-only)
    if not args.fix_only:
        success, stdout, stderr = run_command(
            cmd_prefix + ["mypy", str(src_dir / "apple_notes_parser")],
            "MyPy static type checking",
            cwd=project_root
        )
        
        all_results.append(("mypy", success, stdout, stderr))
        if not success:
            failed_checks.append("MyPy type checking")
        
        if args.verbose and (stdout or stderr):
            print(f"📝 MyPy output:\n{stdout}")
            if stderr:
                print(f"📝 MyPy errors:\n{stderr}")
    
    # 6. Optional: Run tests
    if args.with_tests and not args.fix_only:
        success, stdout, stderr = run_command(
            cmd_prefix + ["pytest", "tests/", "-v"],
            "Test suite execution",
            cwd=project_root
        )
        
        all_results.append(("tests", success, stdout, stderr))
        if not success:
            failed_checks.append("Test suite")
        
        if args.verbose and (stdout or stderr):
            print(f"📝 Test output:\n{stdout}")
            if stderr:
                print(f"📝 Test errors:\n{stderr}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    total_checks = len(all_results)
    passed_checks = sum(1 for _, success, _, _ in all_results if success)
    
    print(f"✅ Passed: {passed_checks}")
    print(f"❌ Failed: {len(failed_checks)}")
    print(f"📝 Total:  {total_checks}")
    
    if failed_checks:
        print(f"\n❌ Failed checks:")
        for check in failed_checks:
            print(f"   • {check}")
        
        print(f"\n💡 To see detailed output, run with --verbose")
        
        # Show errors for failed checks if not verbose
        if not args.verbose:
            print(f"\n📋 Error details:")
            for name, success, stdout, stderr in all_results:
                if not success and stderr:
                    print(f"\n{name.upper()} ERRORS:")
                    print(stderr[:500] + ("..." if len(stderr) > 500 else ""))
    
    # Final result
    if failed_checks:
        print(f"\n💥 Code quality checks FAILED")
        return 1
    else:
        print(f"\n🎉 All code quality checks PASSED!")
        return 0


if __name__ == "__main__":
    sys.exit(main())