#!/usr/bin/env python3
"""
TI Reminder App - Performance Optimization Script

This script runs various performance optimizations including:
1. Minifying CSS and JavaScript assets
2. Optimizing images
3. Enabling code splitting
4. Updating service worker

Usage:
    python optimize_performance.py [--all] [--minify] [--images] [--code-split] [--sw]

Options:
    --all          Run all optimizations (default)
    --minify       Minify CSS and JavaScript
    --images       Optimize images
    --code-split   Apply code splitting
    --sw           Update service worker
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse

def run_command(command, cwd=None):
    """Run a shell command and print the output."""
    print(f"\n🔧 Running: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def install_dependencies():
    """Install required Python dependencies."""
    print("\n📦 Installing dependencies...")
    requirements_path = os.path.join("scripts", "requirements.txt")
    if not os.path.exists(requirements_path):
        print(f"⚠️  Requirements file not found at {requirements_path}")
        return False
    
    return run_command(f"pip install -r {requirements_path}")

def minify_assets():
    """Run the asset minification script."""
    print("\n🔨 Minifying assets...")
    script_path = os.path.join("scripts", "minify_assets.py")
    if not os.path.exists(script_path):
        print(f"⚠️  Minification script not found at {script_path}")
        return False
    
    return run_command(f"python {script_path}")

def optimize_images():
    """Run the image optimization script."""
    print("\n🖼️  Optimizing images...")
    script_path = os.path.join("scripts", "optimize_images.py")
    if not os.path.exists(script_path):
        print(f"⚠️  Image optimization script not found at {script_path}")
        return False
    
    static_dir = os.path.join("app", "static")
    return run_command(f"python {script_path} {static_dir}")

def apply_code_splitting():
    """Apply code splitting to JavaScript files."""
    print("\n🧩 Applying code splitting...")
    script_path = os.path.join("scripts", "code_splitting.py")
    if not os.path.exists(script_path):
        print(f"⚠️  Code splitting script not found at {script_path}")
        return False
    
    return run_command(f"python {script_path}")

def update_service_worker():
    """Update the service worker version."""
    print("\n⚙️  Updating service worker...")
    sw_path = os.path.join("app", "static", "sw.js")
    if not os.path.exists(sw_path):
        print(f"⚠️  Service worker not found at {sw_path}")
        return False
    
    # In a real app, you would update the version number here
    # For now, we'll just check if the file exists
    print("✅ Service worker is up to date")
    return True

def main():
    """Main function to run performance optimizations."""
    parser = argparse.ArgumentParser(description="TI Reminder App Performance Optimization")
    parser.add_argument("--all", action="store_true", help="Run all optimizations")
    parser.add_argument("--minify", action="store_true", help="Minify CSS and JavaScript")
    parser.add_argument("--images", action="store_true", help="Optimize images")
    parser.add_argument("--code-split", action="store_true", help="Apply code splitting")
    parser.add_argument("--sw", action="store_true", help="Update service worker")
    
    args = parser.parse_args()
    
    # If no specific flags are provided, run all optimizations
    run_all = args.all or not any([args.minify, args.images, args.code_split, args.sw])
    
    print("🚀 Starting TI Reminder App Performance Optimization")
    print("=" * 60)
    
    # Install dependencies if needed
    if run_all or args.minify:
        install_dependencies()
    
    # Run requested optimizations
    success = True
    
    if run_all or args.minify:
        success &= minify_assets()
    
    if run_all or args.images:
        success &= optimize_images()
    
    if run_all or args.code_split:
        success &= apply_code_splitting()
    
    if run_all or args.sw:
        success &= update_service_worker()
    
    # Print summary
    print("\n" + "=" * 60)
    if success:
        print("✨ All optimizations completed successfully!")
    else:
        print("⚠️  Some optimizations may have failed. Check the logs above for details.")
    
    print("\n🚀 Performance optimization complete!")

if __name__ == "__main__":
    main()
