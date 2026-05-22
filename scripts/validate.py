#!/usr/bin/env python3
"""Pre-commit validation script for Amazon Connect MCP.

This script runs linting, type checking, and basic tests before commits.
Usage:
    python scripts/validate.py
    python scripts/validate.py --fix  # Auto-fix issues where possible
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def run_command(
    cmd: List[str],
    description: str,
    fix: bool = False
) -> Tuple[bool, str]:
    """Run a command and return success status with output."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True, result.stdout + result.stderr
        else:
            print(f"❌ {description} failed (exit code: {result.returncode})")
            return False, result.stdout + result.stderr
    except FileNotFoundError:
        print(f"⚠️  {description} skipped - tool not found")
        return True, ""  # Skip if tool not installed


def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description="Run pre-commit validation")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues where possible"
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip running tests"
    )
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    success = True
    results = []
    
    # 1. Run ruff linter
    ruff_cmd = ["ruff", "check", str(src_dir), str(tests_dir)]
    if args.fix:
        ruff_cmd.insert(2, "--fix")
    ok, output = run_command(ruff_cmd, "Ruff linter", fix=args.fix)
    success = success and ok
    results.append(("Ruff linter", ok))
    
    # 2. Run black format check (or apply)
    black_cmd = ["black", "--check", "--diff", str(src_dir), str(tests_dir)]
    if args.fix:
        black_cmd = ["black", str(src_dir), str(tests_dir)]
    ok, output = run_command(black_cmd, "Black formatter", fix=args.fix)
    success = success and ok
    results.append(("Black formatter", ok))
    
    # 3. Run mypy type checker
    mypy_cmd = [
        "mypy",
        str(src_dir / "amazon_connect_mcp"),
        str(src_dir / "contact_flows"),
        "--ignore-missing-imports",
        "--show-traceback"
    ]
    ok, output = run_command(mypy_cmd, "Mypy type checker")
    success = success and ok
    results.append(("Mypy type checker", ok))
    
    # 4. Run basic import checks
    import_check_cmd = [
        sys.executable,
        "-c",
        "import amazon_connect_mcp; import contact_flows; print('Imports OK')"
    ]
    ok, output = run_command(
        import_check_cmd,
        "Import check",
        cwd=str(project_root)
    )
    success = success and ok
    results.append(("Import check", ok))
    
    # 5. Run tests (unless --no-tests)
    if not args.no_tests:
        pytest_cmd = [
            "pytest",
            str(tests_dir),
            "-v",
            "--tb=short",
            "-x",  # Stop on first failure
            "-m", "unit"  # Run only unit tests
        ]
        ok, output = run_command(pytest_cmd, "Unit tests")
        success = success and ok
        results.append(("Unit tests", ok))
    
    # Print summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*60}")
    
    if success:
        print("🎉 All validations passed!")
        return 0
    else:
        print("⚠️  Some validations failed")
        if not args.fix:
            print("\n💡 Tip: Run with --fix to auto-fix formatting issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
