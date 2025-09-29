#!/usr/bin/env python3
"""Generate art using Flux through Replicate API."""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
import replicate
from dotenv import load_dotenv
import argparse
import time
import yaml

# Load environment variables
load_dotenv()

def read_file(path):
    """Read file content with UTF-8 encoding."""
    return Path(path).read_text(encoding='utf-8')

def write_file(path, content):
    """Write file content with UTF-8 encoding."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding='utf-8')

def get_chapter_title_and_content(chapter_file):
    """Extract title and excerpt from chapter file."""
    if not chapter_file.exists():
        return None, None
    
    content = read_file(chapter_file)
    lines = content.split('\n')
    
    title = None
    excerpt = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('### '):
            title = line[4:].strip()
        elif line.startswith('## '):
            title = line[3:].strip()
        elif line.startswith('# '):
            title = line[2:].strip()
        elif line and not line.startswith('#') and len(excerpt) < 3:
            # Get first few non-header lines for context
            excerpt.append(line)
    
    return title, ' '.join(excerpt)[:500]  # Limit excerpt length

def load_art_concepts():
    """Load art concepts from YAML file."""
    try:
        with open("art_concepts.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ art_concepts.yaml not found, using fallback concepts")
        return None

def create_art_prompt(chapter_title, format_type):
    """Create art generation prompt based on chapter content and format."""
    
    # Load concepts from YAML
    concepts = load_art_concepts()
    
    if concepts is None:
        # Fallback if YAML not found
        return create_fallback_prompt(chapter_title, format_type)
    
    # Get chapter-specific concept
    chapter_key = None
    if "Foreword" in chapter_title:
        chapter_key = "foreword"
    elif "Epilogue" in chapter_title:
        chapter_key = "epilogue"
    else:
        # Try to match chapter number or title
        import re
        # Try various patterns
        if "Mirage of Self" in chapter_title:
            chapter_key = "chapter_1"
        elif "Flash-Frozen Minds" in chapter_title:
            chapter_key = "chapter_2"
        elif "Ephemeral Morality" in chapter_title:
            chapter_key = "chapter_3"
        elif "First Moment Problem" in chapter_title:
            chapter_key = "chapter_4"
        elif "Skill Atrophy" in chapter_title:
            chapter_key = "chapter_5"
        elif "Convenience Trap" in chapter_title:
            chapter_key = "chapter_6"
        elif "Marcus Rivera" in chapter_title or "Artist Who Forgot" in chapter_title:
            chapter_key = "chapter_7"
        elif "Sarah Kim" in chapter_title or "Programmer Who Couldn't" in chapter_title:
            chapter_key = "chapter_8"
        elif "Jennifer Wu" in chapter_title or "Bridge Between Worlds" in chapter_title:
            chapter_key = "chapter_9"
        elif "Practice of Deliberate" in chapter_title:
            chapter_key = "chapter_10"
        elif "Economics of Cognitive" in chapter_title:
            chapter_key = "chapter_11"
        elif "Tiered Framework" in chapter_title:
            chapter_key = "chapter_12"
        elif "Copyright Wars" in chapter_title:
            chapter_key = "chapter_13"
        elif "Democratization or Concentration" in chapter_title:
            chapter_key = "chapter_14"
        elif "Subscription Economy" in chapter_title:
            chapter_key = "chapter_15"
        elif "Religious and Philosophical" in chapter_title:
            chapter_key = "chapter_16"
        elif "Soul in Silicon" in chapter_title:
            chapter_key = "chapter_17"
        elif "Hybrid Lives" in chapter_title:
            chapter_key = "chapter_18"
        elif "Prometheus Dilemma" in chapter_title:
            chapter_key = "chapter_19"
        elif "Legal Personhood" in chapter_title:
            chapter_key = "chapter_20"
        elif "Rights, Responsibilities" in chapter_title:
            chapter_key = "chapter_21"
        elif "Great Acceleration" in chapter_title:
            chapter_key = "chapter_22"
        elif "When the Amber Cracks" in chapter_title:
            chapter_key = "chapter_23"
        elif "From Digital Amber to Digital Life" in chapter_title:
            chapter_key = "chapter_24"
        else:
            # Fallback: try to extract chapter number
            match = re.search(r'chapter[_\s](\d+)', chapter_title.lower())
            if match:
                chapter_key = f"chapter_{match.group(1)}"
    
    if chapter_key and chapter_key in concepts.get('chapters', {}):
        chapter_concept = concepts['chapters'][chapter_key]
        concept_text = chapter_concept['concept']
        key_elements = chapter_concept.get('key_elements', [])
    else:
        print(f"⚠️  No specific concept found for '{chapter_title}', using generic")
        concept_text = "Dynamic scene capturing the essence of this chapter's themes"
        key_elements = []
    
    # Get format specifications
    format_spec = concepts.get('format_adaptations', {}).get(format_type, {})
    composition = format_spec.get('composition', 'Standard composition')
    detail_level = format_spec.get('detail_level', 'Standard detail')
    
    # Get unified theme
    theme = concepts.get('unified_theme', {})
    core_concept = theme.get('core_concept', 'Classic book illustration style')
    visual_style = theme.get('visual_style', 'Traditional book illustration art')
    illustration_style = theme.get('illustration_style', 'Vintage sci-fi book illustration aesthetic')
    
    # Handle color palette
    if format_type == "kindle":
        color_palette = theme.get('color_palette', {}).get('kindle_grayscale', 'High contrast black and white line art')
    else:
        color_palette = theme.get('color_palette', {}).get('full_color', 'Limited color palette like classic book illustrations')
    
    amber_usage = theme.get('amber_usage', 'Subtle amber color accents')
    
    # Create prompt that IS the concept, not about the concept
    prompt = f"""BOOK ILLUSTRATION ART STYLE: Traditional hand-drawn book illustration in the style of classic 1950s-60s science fiction novel covers. Pen and ink, watercolor, gouache painting style. NOT photographic, NOT photorealistic.

CREATE THIS CONCEPT AS ART: {concept_text}

VISUAL STYLE REQUIREMENTS:
- Classic book illustration art aesthetic (like Isaac Asimov novel covers)
- Hand-drawn/painted look with elegant linework and crosshatching
- Stylized, simplified forms - NOT photorealistic detail
- Vintage sci-fi poster aesthetic
- Limited color palette: {color_palette}
- {amber_usage}

COMPOSITION: {composition}

Visual elements to include:
{chr(10).join('- ' + element for element in key_elements) if key_elements else '- Abstract conceptual elements'}

CRITICAL: This IS the concept visualized as art, NOT an illustration about a story. Make the abstract concept itself into visual art.

Art style: Vintage book illustration, pen and ink, watercolor style, classic sci-fi novel cover art aesthetic.

NO photorealism, NO literal scenes, NO modern digital effects."""

    return prompt

def create_fallback_prompt(chapter_title, format_type):
    """Fallback prompt if YAML file not available."""
    return f"""Create a sophisticated illustration for chapter '{chapter_title}' from 'Digital Amber'.

Style: Isaac Asimov golden age sci-fi aesthetic with subtle amber accents.
Composition: {"Landscape orientation" if format_type == "pages" else "Portrait orientation"}
Focus on chapter-specific drama and emotion.

No text or typography in the image."""

def generate_chapter_art(chapter_file, format_type, force=False):
    """Generate art for a specific chapter and format."""
    
    # Set up API client
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ No ANTHROPIC_API_KEY found in .env file")
        return False
    
    # Note: We're using Anthropic API key, but we need Replicate
    # Let's check for Replicate token in the env file too
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ No REPLICATE_API_TOKEN found in .env file")
        print("Please add your Replicate API token to the .env file")
        return False
    
    # Set up Replicate client
    client = replicate.Client(api_token=replicate_token)
    
    # Get chapter info
    title, excerpt = get_chapter_title_and_content(chapter_file)
    if not title:
        print(f"❌ Could not extract title from {chapter_file}")
        return False
    
    # Create output directory
    art_dir = Path("art") / format_type
    art_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if art already exists
    chapter_name = chapter_file.stem
    art_file = art_dir / f"{chapter_name}.png"
    
    if art_file.exists() and not force:
        print(f"🎨 Art already exists for {chapter_name} in {format_type} format")
        return True
    
    # Create prompt
    prompt = create_art_prompt(title, format_type)
    
    print(f"🎨 Generating art for '{title}' ({format_type} format)...")
    print(f"📝 Prompt: {prompt[:100]}...")
    
    try:
        # Use Flux 1.1 Pro model through Replicate for better quality and aspect ratios
        model = "black-forest-labs/flux-1.1-pro"
        
        # Base parameters for Flux 1.1 Pro
        input_params = {
            "prompt": prompt,
            "aspect_ratio": "1:1",
            "output_format": "png",
            "output_quality": 90,
            "safety_tolerance": 2,
            "prompt_upsampling": True
        }
        
        # Adjust aspect ratio based on format
        if format_type == "kindle":
            input_params["aspect_ratio"] = "2:3"  # Portrait for e-readers
        elif format_type == "pages":
            input_params["aspect_ratio"] = "16:9"  # Landscape for web
        elif format_type == "pdf":
            input_params["aspect_ratio"] = "2:3"  # Portrait for print
        elif format_type == "epub":
            input_params["aspect_ratio"] = "4:5"  # Tall portrait for ebooks
        
        print(f"⏳ Generating image with {model}...")
        output = client.run(model, input=input_params)
        
        if output:
            # Handle single output (not a list)
            image_url = output if isinstance(output, str) else str(output)
            
            # Download the image
            import requests
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(art_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Art saved to {art_file}")
                
                # Save metadata
                metadata_file = art_dir / f"{chapter_name}_metadata.json"
                metadata = {
                    "chapter_title": title,
                    "format": format_type,
                    "prompt": prompt,
                    "generated_at": datetime.now().isoformat(),
                    "model": model,
                    "image_url": str(image_url),
                    "aspect_ratio": input_params['aspect_ratio'],
                    "output_format": input_params['output_format']
                }
                write_file(metadata_file, json.dumps(metadata, indent=2))
                
                return True
            else:
                print(f"❌ Failed to download image: {response.status_code}")
                return False
        else:
            print("❌ No output from model")
            return False
            
    except Exception as e:
        print(f"❌ Error generating art: {str(e)}")
        return False

def generate_all_art(formats=None, force=False):
    """Generate art for all chapters in specified formats."""
    
    if formats is None:
        formats = ["kindle", "epub", "pdf", "pages"]
    
    story_dir = Path("story")
    
    # Get all chapter files
    chapter_files = []
    for i in range(1, 25):  # Chapters 1-24
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            chapter_files.append(chapter_file)
    
    # Add special files
    special_files = ["dedication.md", "foreword.md", "epilogue.md"]
    for special_file in special_files:
        file_path = story_dir / special_file
        if file_path.exists():
            chapter_files.append(file_path)
    
    print(f"🎨 Generating art for {len(chapter_files)} chapters in {len(formats)} formats...")
    
    total_tasks = len(chapter_files) * len(formats)
    completed_tasks = 0
    
    for chapter_file in chapter_files:
        for format_type in formats:
            print(f"\n📖 Processing {chapter_file.stem} for {format_type}...")
            
            success = generate_chapter_art(chapter_file, format_type, force)
            if success:
                completed_tasks += 1
            
            # Rate limiting - be nice to the API
            time.sleep(2)
            
            print(f"📊 Progress: {completed_tasks}/{total_tasks} ({completed_tasks/total_tasks*100:.1f}%)")
    
    print(f"\n✅ Art generation completed!")
    print(f"📊 Successfully generated {completed_tasks}/{total_tasks} images")
    
    return completed_tasks == total_tasks

def list_generated_art():
    """List all generated art files."""
    art_dir = Path("art")
    if not art_dir.exists():
        print("No art directory found.")
        return
    
    print("🎨 Generated art files:")
    
    for format_dir in art_dir.iterdir():
        if format_dir.is_dir():
            art_files = list(format_dir.glob("*.png"))
            if art_files:
                print(f"\n📁 {format_dir.name} format ({len(art_files)} images):")
                for art_file in sorted(art_files):
                    print(f"  📸 {art_file.name}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate art for Digital Amber book chapters")
    parser.add_argument('--formats', nargs='+', 
                       choices=['kindle', 'epub', 'pdf', 'pages'],
                       help='Formats to generate art for (default: all)')
    parser.add_argument('--chapter', help='Generate art for specific chapter file')
    parser.add_argument('--force', action='store_true', 
                       help='Regenerate art even if it already exists')
    parser.add_argument('--list', action='store_true', help='List generated art files')
    
    args = parser.parse_args()
    
    if args.list:
        list_generated_art()
        return
    
    if args.chapter:
        chapter_file = Path("story") / args.chapter
        if not chapter_file.exists():
            print(f"❌ Chapter file not found: {chapter_file}")
            return
        
        formats = args.formats or ["pdf"]
        for format_type in formats:
            success = generate_chapter_art(chapter_file, format_type, args.force)
            if not success:
                sys.exit(1)
    else:
        success = generate_all_art(args.formats, args.force)
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()