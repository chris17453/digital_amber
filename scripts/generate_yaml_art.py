#!/usr/bin/env python3
"""Generate art ONLY from YAML concepts file. No markdown, no story content."""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime
import replicate
from dotenv import load_dotenv
import argparse
import time

# Load environment variables
load_dotenv()

def load_art_concepts():
    """Load art concepts from YAML file."""
    with open("art_concepts.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def create_prompt_from_concept(concept_data, format_type, unified_theme):
    """Create art prompt from YAML concept data only."""
    
    concept_text = concept_data['concept']
    key_elements = concept_data.get('key_elements', [])
    
    # Get format specifications
    format_spec = unified_theme.get('format_adaptations', {}).get(format_type, {})
    composition = format_spec.get('composition', 'Standard composition')
    detail_level = format_spec.get('detail_level', 'Standard detail')
    
    # Get theme
    core_concept = unified_theme.get('core_concept', 'Classic book illustration style')
    visual_style = unified_theme.get('visual_style', 'Traditional book illustration art')
    illustration_style = unified_theme.get('illustration_style', 'Vintage sci-fi book illustration aesthetic')
    
    # Handle color palette
    if format_type == "kindle":
        color_palette = unified_theme.get('color_palette', {}).get('kindle_grayscale', 'High contrast black and white')
    else:
        color_palette = unified_theme.get('color_palette', {}).get('full_color', 'Limited color palette')
    
    amber_usage = unified_theme.get('amber_usage', 'Subtle amber accents')
    
    # Create prompt that IS the concept
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

def generate_art_from_yaml(format_type, force=False):
    """Generate art for all concepts in YAML file."""
    
    # Load concepts
    concepts = load_art_concepts()
    unified_theme = concepts['unified_theme']
    
    # Collect all concept types
    all_concepts = {}
    if 'chapters' in concepts:
        all_concepts.update(concepts['chapters'])
    if 'cover_art' in concepts:
        all_concepts.update(concepts['cover_art'])
    if 'external_art' in concepts:
        all_concepts.update(concepts['external_art'])
    
    # Set up Replicate client
    replicate_token = os.getenv('REPLICATE_API_TOKEN')
    if not replicate_token:
        print("❌ No REPLICATE_API_TOKEN found in .env file")
        return False
    
    client = replicate.Client(api_token=replicate_token)
    
    # Create output directory
    art_dir = Path("art") / format_type
    art_dir.mkdir(parents=True, exist_ok=True)
    
    total_concepts = len(all_concepts)
    completed = 0
    
    print(f"🎨 Generating art for {total_concepts} concepts in {format_type} format...")
    
    for concept_key, concept_data in all_concepts.items():
        title = concept_data['title']
        print(f"\n📖 Processing {concept_key}: {title}")
        
        # Check if art already exists
        art_file = art_dir / f"{concept_key}.png"
        if art_file.exists() and not force:
            print(f"🎨 Art already exists for {concept_key}")
            completed += 1
            continue
        
        # Create prompt from YAML concept only
        prompt = create_prompt_from_concept(concept_data, format_type, unified_theme)
        
        print(f"🎨 Generating art for '{title}'...")
        print(f"📝 Concept: {concept_data['concept'][:100]}...")
        
        try:
            # Use Flux 1.1 Pro model
            model = "black-forest-labs/flux-1.1-pro"
            
            # Base parameters
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
                # Handle single output
                image_url = output if isinstance(output, str) else str(output)
                
                # Download the image
                import requests
                response = requests.get(image_url)
                if response.status_code == 200:
                    with open(art_file, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"✅ Art saved to {art_file}")
                    
                    # Save metadata
                    metadata_file = art_dir / f"{concept_key}_metadata.json"
                    metadata = {
                        "concept_key": concept_key,
                        "title": title,
                        "concept": concept_data['concept'],
                        "format": format_type,
                        "prompt": prompt,
                        "generated_at": datetime.now().isoformat(),
                        "model": model,
                        "image_url": str(image_url),
                        "aspect_ratio": input_params['aspect_ratio'],
                        "key_elements": concept_data.get('key_elements', [])
                    }
                    
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    completed += 1
                else:
                    print(f"❌ Failed to download image: {response.status_code}")
            else:
                print("❌ No output from model")
                
        except Exception as e:
            print(f"❌ Error generating art: {str(e)}")
        
        # Rate limiting
        time.sleep(2)
        
        print(f"📊 Progress: {completed}/{total_concepts} ({completed/total_concepts*100:.1f}%)")
    
    print(f"\n✅ YAML art generation completed!")
    print(f"📊 Successfully generated {completed}/{total_concepts} images")
    
    return completed == total_concepts

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate art from YAML concepts only")
    parser.add_argument('--formats', nargs='+', 
                       choices=['kindle', 'epub', 'pdf', 'pages'],
                       help='Formats to generate art for (default: pages)')
    parser.add_argument('--force', action='store_true', 
                       help='Regenerate art even if it already exists')
    
    args = parser.parse_args()
    
    formats = args.formats or ["pages"]
    
    for format_type in formats:
        print(f"\n🎨 Generating {format_type} format art from YAML concepts...")
        success = generate_art_from_yaml(format_type, args.force)
        if not success:
            print(f"❌ Failed to generate all {format_type} art")

if __name__ == "__main__":
    main()