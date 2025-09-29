#!/usr/bin/env python3
"""Optimize images for different book formats without modifying originals."""

import os
from pathlib import Path
from PIL import Image, ImageOps
import shutil

# Device-specific specifications
DEVICE_SPECS = {
    'kindle': {
        'max_width': 600,      # Kindle screen width
        'max_height': 800,     # Kindle screen height  
        'quality': 85,         # JPEG quality for compression
        'grayscale': True,     # Convert to grayscale for e-ink
        'format': 'JPEG'       # Use JPEG for better compression
    },
    'epub': {
        'max_width': 768,      # Standard tablet width
        'max_height': 1024,    # Standard tablet height
        'quality': 90,         # Higher quality for color displays
        'grayscale': False,    # Keep color
        'format': 'JPEG'       # JPEG for smaller file size
    },
    'pdf': {
        'max_width': 1200,     # Print quality
        'max_height': 1600,    # Print quality
        'quality': 95,         # High quality for print
        'grayscale': False,    # Keep color for print
        'format': 'PNG'        # PNG for print quality
    },
    'pages': {
        'max_width': 800,      # Web display
        'max_height': 600,     # Web display (landscape)
        'quality': 88,         # Good web quality
        'grayscale': False,    # Keep color for web
        'format': 'JPEG'       # JPEG for web
    }
}

def optimize_image(source_path, target_path, spec):
    """Optimize a single image according to device specifications."""
    try:
        # Open and process image
        with Image.open(source_path) as img:
            # Convert to RGB if needed (handles RGBA, etc.)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Convert to grayscale if specified
            if spec['grayscale']:
                img = ImageOps.grayscale(img)
                if spec['format'] == 'JPEG':
                    # Convert back to RGB for JPEG (JPEG doesn't support grayscale mode in PIL)
                    img = img.convert('RGB')
            
            # Calculate resize dimensions while maintaining aspect ratio
            original_width, original_height = img.size
            max_width, max_height = spec['max_width'], spec['max_height']
            
            # Calculate scaling factor
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_factor = min(width_ratio, height_ratio, 1.0)  # Don't upscale
            
            if scale_factor < 1.0:
                new_width = int(original_width * scale_factor)
                new_height = int(original_height * scale_factor)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save with appropriate format and quality
            save_kwargs = {}
            if spec['format'] == 'JPEG':
                save_kwargs = {
                    'format': 'JPEG',
                    'quality': spec['quality'],
                    'optimize': True,
                    'progressive': True
                }
            else:  # PNG
                save_kwargs = {
                    'format': 'PNG',
                    'optimize': True
                }
            
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save optimized image
            img.save(target_path, **save_kwargs)
            
            # Get file sizes for reporting
            original_size = source_path.stat().st_size
            optimized_size = target_path.stat().st_size
            compression_ratio = (1 - optimized_size / original_size) * 100
            
            print(f"  {source_path.name} -> {target_path.name}")
            print(f"    {original_size:,} bytes -> {optimized_size:,} bytes ({compression_ratio:.1f}% smaller)")
            print(f"    {original_width}x{original_height} -> {img.size[0]}x{img.size[1]}")
            
            return True
            
    except Exception as e:
        print(f"  ❌ Error optimizing {source_path}: {e}")
        return False

def optimize_format_images(format_name):
    """Optimize all images for a specific format."""
    if format_name not in DEVICE_SPECS:
        print(f"❌ Unknown format: {format_name}")
        return
    
    spec = DEVICE_SPECS[format_name]
    source_dir = Path(f"art/{format_name}")
    optimized_dir = Path(f"art/{format_name}_optimized")
    
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        return
    
    print(f"📱 Optimizing images for {format_name}...")
    print(f"   Target: {spec['max_width']}x{spec['max_height']}, {spec['format']}, quality {spec['quality']}")
    if spec['grayscale']:
        print(f"   Converting to grayscale for e-ink display")
    
    # Find all PNG files in source directory
    png_files = list(source_dir.glob("*.png"))
    if not png_files:
        print(f"  ❌ No PNG files found in {source_dir}")
        return
    
    success_count = 0
    total_original_size = 0
    total_optimized_size = 0
    
    for png_file in png_files:
        # Skip metadata files
        if png_file.name.endswith('_metadata.json'):
            continue
            
        # Determine target filename
        if spec['format'] == 'JPEG':
            target_name = png_file.stem + '.jpg'
        else:
            target_name = png_file.name
            
        target_path = optimized_dir / target_name
        
        # Get original size for totals
        original_size = png_file.stat().st_size
        total_original_size += original_size
        
        if optimize_image(png_file, target_path, spec):
            success_count += 1
            total_optimized_size += target_path.stat().st_size
    
    # Summary
    if success_count > 0:
        total_compression = (1 - total_optimized_size / total_original_size) * 100
        print(f"✅ Optimized {success_count}/{len(png_files)} images")
        print(f"   Total size: {total_original_size:,} -> {total_optimized_size:,} bytes")
        print(f"   Overall compression: {total_compression:.1f}%")
        print(f"   Saved to: {optimized_dir}")
    else:
        print(f"❌ No images were successfully optimized")

def optimize_all_formats():
    """Optimize images for all book formats."""
    print("🖼️  Image Optimization for Mobile/E-reader Formats")
    print("=" * 60)
    
    for format_name in DEVICE_SPECS.keys():
        optimize_format_images(format_name)
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Optimize specific format
        format_name = sys.argv[1]
        optimize_format_images(format_name)
    else:
        # Optimize all formats
        optimize_all_formats()