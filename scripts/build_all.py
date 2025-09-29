#!/usr/bin/env python3
"""Build all formats with versioning."""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import argparse

def read_file(path):
    """Read file content with UTF-8 encoding."""
    return Path(path).read_text(encoding='utf-8')

def write_file(path, content):
    """Write file content with UTF-8 encoding."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding='utf-8')

def get_git_info():
    """Get current git commit info."""
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
        commit_short = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode().strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        return {
            'commit_hash': commit_hash,
            'commit_short': commit_short,
            'branch': branch
        }
    except subprocess.CalledProcessError:
        return {
            'commit_hash': 'unknown',
            'commit_short': 'unknown',
            'branch': 'unknown'
        }

def get_version_info():
    """Get or create version information."""
    version_file = Path("version.json")
    
    if version_file.exists():
        version_data = json.loads(read_file(version_file))
    else:
        version_data = {
            "major": 1,
            "minor": 0,
            "patch": 0,
            "builds": []
        }
    
    return version_data

def update_version(version_data, version_type="patch"):
    """Update version number."""
    if version_type == "major":
        version_data["major"] += 1
        version_data["minor"] = 0
        version_data["patch"] = 0
    elif version_type == "minor":
        version_data["minor"] += 1
        version_data["patch"] = 0
    else:  # patch
        version_data["patch"] += 1
    
    return version_data

def create_build_info(version_data, formats_built):
    """Create build information."""
    git_info = get_git_info()
    
    build_info = {
        "version": f"{version_data['major']}.{version_data['minor']}.{version_data['patch']}",
        "build_date": datetime.now().isoformat(),
        "git_commit": git_info['commit_hash'],
        "git_commit_short": git_info['commit_short'],
        "git_branch": git_info['branch'],
        "formats": formats_built,
        "files": {}
    }
    
    return build_info

def run_build_script(script_name):
    """Run a build script and return success status."""
    try:
        result = subprocess.run([sys.executable, f"scripts/{script_name}"], 
                              check=True, capture_output=True, text=True)
        print(f"✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {script_name} failed:")
        print(e.stderr)
        return False

def copy_to_versioned_directory(dist_dir, version_dir, build_info):
    """Copy build artifacts to versioned directory."""
    if not dist_dir.exists():
        print(f"Warning: {dist_dir} doesn't exist")
        return
    
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all files from dist to versioned directory
    for file_path in dist_dir.iterdir():
        if file_path.is_file():
            dest_path = version_dir / file_path.name
            shutil.copy2(file_path, dest_path)
            build_info["files"][file_path.name] = {
                "size": file_path.stat().st_size,
                "created": datetime.now().isoformat()
            }
            print(f"  Copied {file_path.name} to {version_dir}")

def build_all_formats(version_type="patch", formats=None):
    """Build all formats with versioning."""
    if formats is None:
        formats = ["pages", "kindle", "epub", "pdf"]
    
    print("🚀 Starting build process...")
    
    # Get current version
    version_data = get_version_info()
    version_data = update_version(version_data, version_type)
    version_string = f"{version_data['major']}.{version_data['minor']}.{version_data['patch']}"
    
    print(f"📦 Building version {version_string}")
    
    # Ensure dist directory exists
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Build formats
    formats_built = []
    build_scripts = {
        "pages": "build_pages.py",
        "kindle": "build_kindle.py", 
        "epub": "build_epub.py",
        "pdf": "build_pdf.py"
    }
    
    for format_name in formats:
        if format_name in build_scripts:
            print(f"\n📖 Building {format_name} format...")
            if run_build_script(build_scripts[format_name]):
                formats_built.append(format_name)
            else:
                print(f"❌ Failed to build {format_name} format")
        else:
            print(f"⚠️  Unknown format: {format_name}")
    
    if not formats_built:
        print("❌ No formats were built successfully")
        return False
    
    # Create build info
    build_info = create_build_info(version_data, formats_built)
    
    # Create versioned directories
    versions_dir = Path("versions")
    versions_dir.mkdir(exist_ok=True)
    
    version_dir = versions_dir / f"v{version_string}"
    copy_to_versioned_directory(dist_dir, version_dir, build_info)
    
    # Save build info
    build_info_file = version_dir / "build_info.json"
    write_file(build_info_file, json.dumps(build_info, indent=2))
    
    # Update version.json
    version_data["builds"].append(build_info)
    write_file("version.json", json.dumps(version_data, indent=2))
    
    # Create latest symlink/copy
    latest_dir = versions_dir / "latest"
    if latest_dir.exists():
        if latest_dir.is_symlink():
            latest_dir.unlink()
        else:
            shutil.rmtree(latest_dir)
    
    # On Windows, copy instead of symlink
    if os.name == 'nt':
        shutil.copytree(version_dir, latest_dir)
    else:
        latest_dir.symlink_to(f"v{version_string}")
    
    print(f"\n✅ Build completed successfully!")
    print(f"📁 Version {version_string} saved to: {version_dir}")
    print(f"🔗 Latest version available at: {latest_dir}")
    print(f"📊 Built formats: {', '.join(formats_built)}")
    
    return True

def list_versions():
    """List all available versions."""
    versions_dir = Path("versions")
    if not versions_dir.exists():
        print("No versions found.")
        return
    
    print("📚 Available versions:")
    version_dirs = sorted([d for d in versions_dir.iterdir() if d.is_dir() and d.name.startswith('v')],
                         key=lambda x: x.name, reverse=True)
    
    for version_dir in version_dirs:
        build_info_file = version_dir / "build_info.json"
        if build_info_file.exists():
            build_info = json.loads(read_file(build_info_file))
            print(f"  {version_dir.name}: {build_info['build_date'][:10]} - {', '.join(build_info['formats'])}")
        else:
            print(f"  {version_dir.name}: (no build info)")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build Digital Amber book in multiple formats")
    parser.add_argument('--version-type', choices=['major', 'minor', 'patch'], 
                       default='patch', help='Version bump type')
    parser.add_argument('--formats', nargs='+', 
                       choices=['pages', 'kindle', 'epub', 'pdf'],
                       help='Formats to build (default: all)')
    parser.add_argument('--list', action='store_true', help='List available versions')
    
    args = parser.parse_args()
    
    if args.list:
        list_versions()
        return
    
    success = build_all_formats(args.version_type, args.formats)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()