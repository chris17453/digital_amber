#!/usr/bin/env python3
"""Create basic voice samples for Digital Amber audiobook using local TTS."""

import os
from pathlib import Path
import subprocess

def create_voice_samples():
    """Create basic voice samples using available local TTS."""
    
    voices_dir = Path("voices")
    voices_dir.mkdir(exist_ok=True)
    
    # Sample text for voice generation
    sample_text = "The question isn't whether machines can think, but whether they can truly understand what it means to be conscious. In Digital Amber, we explore the boundaries between artificial intelligence and genuine awareness."
    
    voice_files = {
        'narrator_male_warm.wav': 'Warm, authoritative male narrator',
        'female_professional_confident.wav': 'Dr. Sarah Martinez - confident female doctor',
        'male_thoughtful_patient.wav': 'David Chen - contemplative male patient',
        'male_technical_scientist.wav': 'Dr. Raj Patel - technical male scientist',
        'synthetic_ai_evolving.wav': 'ARTEMIS AI - evolving artificial intelligence',
        'male_artist_creative.wav': 'Marcus Rivera - struggling artist',
        'female_programmer_tech.wav': 'Sarah Kim - technical female programmer',
        'female_architect_wise.wav': 'Jennifer Wu - wise architect'
    }
    
    print("🎙️  Creating basic voice samples for Digital Amber audiobook")
    print("=" * 60)
    
    # Try using espeak or espeak-ng (common on Linux)
    try:
        subprocess.run(['espeak', '--version'], capture_output=True, check=True)
        tts_engine = 'espeak'
        print("✅ Found espeak TTS engine")
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['espeak-ng', '--version'], capture_output=True, check=True)
            tts_engine = 'espeak-ng'
            print("✅ Found espeak-ng TTS engine")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ No TTS engine found. Please install espeak or espeak-ng:")
            print("   Ubuntu/Debian: sudo apt install espeak espeak-data")
            print("   or: sudo apt install espeak-ng espeak-ng-data")
            return False
    
    # Voice configurations for espeak
    voice_configs = {
        'narrator_male_warm.wav': {'voice': 'en+m3', 'speed': '160', 'pitch': '50'},
        'female_professional_confident.wav': {'voice': 'en+f3', 'speed': '170', 'pitch': '60'},
        'male_thoughtful_patient.wav': {'voice': 'en+m2', 'speed': '150', 'pitch': '45'},
        'male_technical_scientist.wav': {'voice': 'en+m4', 'speed': '165', 'pitch': '55'},
        'synthetic_ai_evolving.wav': {'voice': 'en+m5', 'speed': '140', 'pitch': '30'},
        'male_artist_creative.wav': {'voice': 'en+m1', 'speed': '155', 'pitch': '48'},
        'female_programmer_tech.wav': {'voice': 'en+f2', 'speed': '165', 'pitch': '55'},
        'female_architect_wise.wav': {'voice': 'en+f4', 'speed': '150', 'pitch': '50'}
    }
    
    created_count = 0
    
    for filename, description in voice_files.items():
        output_path = voices_dir / filename
        
        if output_path.exists():
            print(f"⏭️  Skipping {filename} (already exists)")
            continue
            
        config = voice_configs.get(filename, {'voice': 'en', 'speed': '160', 'pitch': '50'})
        
        try:
            # Generate voice sample using espeak
            cmd = [
                tts_engine,
                '-v', config['voice'],
                '-s', config['speed'],
                '-p', config['pitch'],
                '-w', str(output_path),
                sample_text
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and output_path.exists():
                print(f"✅ Created: {filename} ({description})")
                created_count += 1
            else:
                print(f"❌ Failed to create {filename}: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")
    
    print(f"\n🎉 Created {created_count} voice samples!")
    
    if created_count > 0:
        print("\n📋 Voice samples ready! You can now run:")
        print("   uv run python scripts/build_audio.py")
        print("\n💡 To improve voice quality:")
        print("   - Replace samples with higher-quality recordings")
        print("   - Use AI voice generators like Bark or Tortoise-TTS")
        print("   - Record yourself speaking in character")
    
    return created_count > 0

if __name__ == "__main__":
    create_voice_samples()