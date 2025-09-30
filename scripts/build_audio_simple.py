#!/usr/bin/env python3
"""Build audiobook using enhanced espeak with different voices - simple but effective."""

import os
import re
from pathlib import Path
import json
from typing import List, Tuple
import subprocess

# Voice configurations for different characters
VOICE_MAPPING = {
    'narrator': {
        'voice': 'en+m3',
        'speed': '160',
        'pitch': '50',
        'description': 'Warm male narrator'
    },
    'dr_sarah_martinez': {
        'voice': 'en+f3', 
        'speed': '170',
        'pitch': '60',
        'description': 'Dr. Sarah Martinez - confident female doctor'
    },
    'david_chen': {
        'voice': 'en+m2',
        'speed': '150', 
        'pitch': '45',
        'description': 'David Chen - contemplative male patient'
    },
    'dr_raj_patel': {
        'voice': 'en+m4',
        'speed': '165',
        'pitch': '55', 
        'description': 'Dr. Raj Patel - technical male scientist'
    },
    'artemis_ai': {
        'voice': 'en+m5',
        'speed': '140',
        'pitch': '30',
        'description': 'ARTEMIS AI - synthetic voice'
    },
    'marcus_rivera': {
        'voice': 'en+m1', 
        'speed': '155',
        'pitch': '48',
        'description': 'Marcus Rivera - struggling artist'
    },
    'sarah_kim': {
        'voice': 'en+f2',
        'speed': '165',
        'pitch': '55',
        'description': 'Sarah Kim - technical female programmer'
    },
    'jennifer_wu': {
        'voice': 'en+f4',
        'speed': '150',
        'pitch': '50', 
        'description': 'Jennifer Wu - wise architect'
    }
}

def detect_emotion_from_text(text: str, speaker: str) -> str:
    """Detect emotion from text context for more expressive speech."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['!', 'amazing', 'incredible', 'breakthrough']):
        return 'excited'
    elif any(word in text_lower for word in ['worried', 'concern', 'afraid', 'anxious']):
        return 'concerned'
    elif any(word in text_lower for word in ['frustrated', 'damn', 'hell', 'annoying']):
        return 'frustrated'
    elif any(word in text_lower for word in ['wonder', 'think', 'perhaps', 'maybe']):
        return 'contemplative'
    elif any(word in text_lower for word in ['hope', 'believe', 'possible', 'can do']):
        return 'hopeful'
    elif any(word in text_lower for word in ['sad', 'lost', 'defeat', 'fail']):
        return 'defeated'
    else:
        return 'neutral'

def detect_dialogue_and_speaker(text: str) -> List[Tuple[str, str, str]]:
    """Parse text to identify dialogue, speakers, and emotions."""
    segments = []
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if '"' in para:
            speaker = identify_speaker_from_context(para)
            emotion = detect_emotion_from_text(para, speaker)
            segments.append((speaker, para, emotion))
        else:
            emotion = detect_emotion_from_text(para, 'narrator')
            segments.append(('narrator', para, emotion))
    
    return segments

def identify_speaker_from_context(text: str) -> str:
    """Identify speaker from context clues in the text."""
    text_lower = text.lower()
    
    if 'sarah martinez' in text_lower or 'dr. martinez' in text_lower:
        return 'dr_sarah_martinez'
    elif 'david chen' in text_lower and '"' in text:
        return 'david_chen'
    elif 'raj patel' in text_lower or 'dr. patel' in text_lower:
        return 'dr_raj_patel'
    elif 'artemis' in text_lower and '"' in text:
        return 'artemis_ai'
    elif 'marcus rivera' in text_lower or 'marcus said' in text_lower:
        return 'marcus_rivera'
    elif 'sarah kim' in text_lower:
        return 'sarah_kim'
    elif 'jennifer wu' in text_lower or 'jennifer said' in text_lower:
        return 'jennifer_wu'
    else:
        return 'narrator'

def text_to_speech_espeak(text: str, speaker: str, emotion: str, output_file: Path) -> bool:
    """Convert text to speech using espeak with character-specific voices."""
    try:
        voice_config = VOICE_MAPPING[speaker]
        
        # Adjust speed based on emotion
        speed = int(voice_config['speed'])
        if emotion == 'defeated':
            speed = max(120, speed - 30)
        elif emotion == 'excited':
            speed = min(200, speed + 20)
        elif emotion == 'contemplative':
            speed = max(130, speed - 20)
        
        # Generate speech
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean text for speech
        clean_text = text.replace('#', '').replace('*', '')
        
        if not clean_text.strip():
            print(f"⚠️  Skipping empty text for {output_file.name}")
            return False
            
        result = subprocess.run([
            'espeak-ng',
            '-v', voice_config['voice'],
            '-s', str(speed),
            '-p', voice_config['pitch'],
            '-w', str(output_file),
            clean_text
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and output_file.exists():
            print(f"✅ Generated: {output_file.name} ({speaker} - {emotion})")
            return True
        else:
            print(f"❌ Failed to generate {output_file.name}: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating audio for {output_file.name}: {e}")
        return False

def enhance_audio_with_sox(input_file: Path, output_file: Path) -> bool:
    """Enhance audio quality using sox if available."""
    try:
        # Check if sox is available
        subprocess.run(['sox', '--version'], capture_output=True, check=True)
        
        # Apply audio enhancements
        cmd = [
            'sox', str(input_file), str(output_file),
            'norm', '-3',      # Normalize volume
            'compand', '0.02,0.20', '-60,-40,-10', '-5', '-90', '0.1',  # Compression
            'reverb', '10', '0.5', '20', '0.2',  # Subtle reverb
            'equalizer', '200', '1', '2',        # Boost low frequencies
            'equalizer', '3000', '1', '-2'       # Slightly reduce harsh frequencies
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Sox not available, just copy the file
        pass
    
    # Fallback: copy original file
    try:
        import shutil
        shutil.copy2(input_file, output_file)
        return True
    except:
        return False

def process_chapter_audio(chapter_file: Path, output_dir: Path) -> List[Path]:
    """Process a single chapter into audio segments with character voices."""
    print(f"🎧 Processing {chapter_file.name}...")
    
    content = chapter_file.read_text(encoding='utf-8')
    
    # Remove markdown formatting for audio
    content = re.sub(r'^###?\s+', '', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
    content = re.sub(r'\*(.+?)\*', r'\1', content)
    
    # Parse dialogue, speakers, and emotions
    segments = detect_dialogue_and_speaker(content)
    
    # Generate audio for each segment
    audio_files = []
    chapter_audio_dir = output_dir / chapter_file.stem
    chapter_audio_dir.mkdir(parents=True, exist_ok=True)
    
    for i, (speaker, text, emotion) in enumerate(segments):
        if not text.strip():
            continue
            
        raw_file = chapter_audio_dir / f"{i+1:03d}_{speaker}_{emotion}_raw.wav"
        enhanced_file = chapter_audio_dir / f"{i+1:03d}_{speaker}_{emotion}.wav"
        
        if text_to_speech_espeak(text, speaker, emotion, raw_file):
            if enhance_audio_with_sox(raw_file, enhanced_file):
                audio_files.append(enhanced_file)
                # Clean up raw file
                raw_file.unlink()
            else:
                audio_files.append(raw_file)
    
    return audio_files

def combine_audio_files(audio_files: List[Path], output_file: Path) -> bool:
    """Combine multiple audio files into a single file using ffmpeg."""
    if not audio_files:
        return False
    
    try:
        file_list = output_file.parent / f"{output_file.stem}_filelist.txt"
        with open(file_list, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file.absolute()}'\n")
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', str(file_list),
            '-c', 'copy',
            '-y',
            str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        file_list.unlink()
        
        print(f"✅ Combined audio: {output_file.name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error combining audio files: {e}")
        return False

def build_audiobook_simple():
    """Build audiobook using enhanced espeak voices."""
    print("🎙️  Digital Amber - Simple Multi-Character Audiobook")
    print("=" * 55)
    
    # Check for required tools
    try:
        subprocess.run(['espeak-ng', '--version'], capture_output=True, check=True)
        print("✅ espeak-ng found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ espeak-ng not found. Please install: sudo apt install espeak-ng")
        return
    
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ ffmpeg found")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install: sudo apt install ffmpeg")
        return
    
    try:
        subprocess.run(['sox', '--version'], capture_output=True, check=True)
        print("✅ sox found - will enhance audio quality")
        sox_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  sox not found - audio will be basic quality")
        print("   Install with: sudo apt install sox")
        sox_available = False
    
    print("\n🎭 Voice Cast:")
    for speaker, config in VOICE_MAPPING.items():
        print(f"   {speaker}: {config['description']}")
    
    story_dir = Path("story")
    audio_output_dir = Path("dist/audiobook")
    audio_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each chapter
    all_chapter_files = []
    
    # Process foreword
    if (story_dir / "foreword.md").exists():
        print("\n🎧 Processing foreword...")
        audio_files = process_chapter_audio(story_dir / "foreword.md", audio_output_dir)
        if audio_files:
            foreword_combined = audio_output_dir / "000_foreword.wav"
            combine_audio_files(audio_files, foreword_combined)
            all_chapter_files.append(foreword_combined)
    
    # Process ALL chapters (1-24)
    for i in range(1, 25):
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            print(f"\n🎧 Processing chapter {i}...")
            audio_files = process_chapter_audio(chapter_file, audio_output_dir)
            if audio_files:
                chapter_combined = audio_output_dir / f"{i:03d}_chapter_{i}.wav"
                combine_audio_files(audio_files, chapter_combined)
                all_chapter_files.append(chapter_combined)
    
    # Process epilogue
    if (story_dir / "epilogue.md").exists():
        print("\n🎧 Processing epilogue...")
        audio_files = process_chapter_audio(story_dir / "epilogue.md", audio_output_dir)
        if audio_files:
            epilogue_combined = audio_output_dir / "999_epilogue.wav"
            combine_audio_files(audio_files, epilogue_combined)
            all_chapter_files.append(epilogue_combined)
    
    # Create audiobook
    if all_chapter_files:
        audiobook_file = audio_output_dir / "digital_amber_complete_audiobook.wav"
        print(f"\n🎵 Creating combined audiobook...")
        combine_audio_files(all_chapter_files, audiobook_file)
        
        # Generate metadata
        metadata = {
            'title': 'Digital Amber: AI Consciousness and the Future of Digital Minds (Complete)',
            'author': 'AI-Human Collaboration',
            'narrator': 'Multi-Character Espeak Cast',
            'tts_engine': 'espeak-ng with enhancements',
            'audio_enhancement': 'sox' if sox_available else 'none',
            'chapters': len(all_chapter_files),
            'voices_used': len(VOICE_MAPPING),
            'voice_mapping': VOICE_MAPPING
        }
        
        with open(audio_output_dir / "audiobook_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n🎉 Audiobook generation complete!")
        print(f"📁 Output directory: {audio_output_dir}")
        print(f"🎧 Audiobook file: {audiobook_file.name}")
        print(f"📋 Chapters processed: {len(all_chapter_files)}")
        print(f"🎭 Character voices: {len(VOICE_MAPPING)}")
        print(f"🔊 Audio enhancement: {'Enabled (sox)' if sox_available else 'Basic (espeak only)'}")
        
        # Show file sizes
        size_mb = audiobook_file.stat().st_size / (1024 * 1024)
        print(f"📊 File size: {size_mb:.1f} MB")
        
        print("\n💡 To improve quality further:")
        if not sox_available:
            print("   - Install sox: sudo apt install sox")
        print("   - Use higher quality TTS engines like XTTS-v2 when properly configured")
        print("   - Record human voices for character samples")

if __name__ == "__main__":
    build_audiobook_simple()