#!/usr/bin/env python3
"""
Script to regenerate protobuf Python files from the .proto schema.

Usage:
    python scripts/regenerate_protobuf.py

This script:
1. Navigates to the correct directory
2. Runs the protobuf compiler
3. Verifies the generation was successful  
4. Runs tests to ensure compatibility
"""

import re
import subprocess
import sys
from pathlib import Path


def main():
    """Regenerate protobuf files and verify they work."""
    project_root = Path(__file__).parent.parent
    proto_dir = project_root / "src" / "apple_notes_parser"
    proto_file = proto_dir / "notestore.proto"
    pb2_file = proto_dir / "notestore_pb2.py"
    
    print("🔧 Regenerating protobuf Python files...")
    
    # Check that proto file exists
    if not proto_file.exists():
        print(f"❌ Proto file not found: {proto_file}")
        return 1
        
    # Run protobuf compiler
    try:
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={proto_dir}",
            str(proto_file.name)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=proto_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Protobuf compilation failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return 1
            
    except FileNotFoundError:
        print("❌ grpcio-tools not found. Install with: uv add grpcio-tools")
        return 1
    
    # Verify the generated file
    if not pb2_file.exists():
        print(f"❌ Generated file not found: {pb2_file}")
        return 1
    
    # Check the version in the generated file
    try:
        with open(pb2_file, 'r') as f:
            content = f.read()
            
        # Look for the protobuf version line
        version_match = re.search(r'# Protobuf Python Version: ([\d.]+)', content)
        if version_match:
            version = version_match.group(1)
            print(f"✅ Generated protobuf file with version: {version}")
        else:
            print("⚠️  Could not detect protobuf version in generated file")
            
    except Exception as e:
        print(f"⚠️  Could not read generated file: {e}")
    
    # Run tests to verify everything works
    print("\n🧪 Running tests to verify compatibility...")
    try:
        test_cmd = [sys.executable, "-m", "pytest", "tests/", "-q"]
        result = subprocess.run(test_cmd, cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ All tests pass - protobuf regeneration successful!")
            return 0
        else:
            print("❌ Tests failed after protobuf regeneration:")
            print(result.stdout)
            print(result.stderr)
            return 1
            
    except FileNotFoundError:
        print("⚠️  pytest not found - skipping test verification")
        print("✅ Protobuf files regenerated successfully")
        return 0


if __name__ == "__main__":
    sys.exit(main())