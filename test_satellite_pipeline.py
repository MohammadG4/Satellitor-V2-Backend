#!/usr/bin/env python3
"""
Test script for the satellite data pipeline
Run this to test the fetch_satellite_data management command
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    return result.returncode == 0

def main():
    print("🛰️  Testing Satellite Data Pipeline")
    print("=" * 50)
    
    # Check if Docker is running
    print("\n1. Checking Docker...")
    if not run_command("docker compose ps"):
        print("❌ Docker Compose is not running. Please start it first:")
        print("   docker compose up -d")
        return
    
    # Test dry run
    print("\n2. Testing dry run...")
    if run_command("docker compose exec web python Satellitor/manage.py fetch_satellite_data --dry-run"):
        print("✅ Dry run successful!")
    else:
        print("❌ Dry run failed!")
        return
    
    # Test actual run (if you want to)
    print("\n3. Do you want to run the actual pipeline? (y/n)")
    response = input().lower().strip()
    
    if response == 'y':
        print("Running actual pipeline...")
        if run_command("docker compose exec web python Satellitor/manage.py fetch_satellite_data"):
            print("✅ Pipeline run successful!")
        else:
            print("❌ Pipeline run failed!")
    else:
        print("Skipping actual run.")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()
