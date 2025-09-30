#!/usr/bin/env python3
"""Build audiobook using Kokoro TTS - the REAL implementation."""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Tuple
import soundfile as sf
from kokoro import KPipeline

# Voice mapping for different characters using Kokoro voices (NO ADAM VOICE!)
VOICE_MAPPING = {
    'narrator': 'af_heart',           # Warm narrative voice
    'dr_sarah_martinez': 'af_bella',  # Professional female doctor
    'david_chen': 'am_echo',          # Contemplative male patient (NO ADAM!)
    'dr_raj_patel': 'am_michael',     # Technical male scientist
    'artemis_ai': 'af_sarah',         # AI voice
    'marcus_rivera': 'am_eric',       # Struggling artist
    'sarah_kim': 'af_nicole',         # Technical female programmer
    'jennifer_wu': 'af_sky'           # Wise architect
}

def setup_kokoro():
    """Setup Kokoro TTS pipeline."""
    try:
        print("🎯 Initializing Kokoro TTS pipeline...")
        
        # Initialize pipeline for American English
        pipeline = KPipeline(lang_code='a')
        
        print("✅ Kokoro pipeline ready")
        return pipeline
        
    except Exception as e:
        print(f"❌ Error setting up Kokoro: {e}")
        return None

def text_to_speech_kokoro(pipeline, text: str, speaker: str, emotion: str, output_file: Path) -> bool:
    """Convert text to speech using Kokoro."""
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean text for TTS
        clean_text = text.replace('#', '').replace('*', '').strip()
        if not clean_text:
            print(f"⚠️  Skipping empty text for {output_file.name}")
            return False
        
        # Get voice for character
        voice = VOICE_MAPPING.get(speaker, 'af_heart')
        
        # Adjust speed based on emotion
        speed = 1.0
        if emotion == 'defeated':
            speed = 0.8
        elif emotion == 'excited':
            speed = 1.2
        elif emotion == 'contemplative':
            speed = 0.9
        
        print(f"🎙️  Generating: {output_file.name} ({speaker}:{voice} - {emotion})")
        
        # Generate audio using Kokoro
        generator = pipeline(clean_text, voice=voice, speed=speed)
        
        # Collect all audio segments
        audio_segments = []
        for i, (gs, ps, audio) in enumerate(generator):
            audio_segments.append(audio)
        
        if audio_segments:
            # Concatenate all segments
            import numpy as np
            full_audio = np.concatenate(audio_segments)
            
            # Save audio file
            sf.write(str(output_file), full_audio, 24000)
            print(f"✅ Generated: {output_file.name} ({len(audio_segments)} segments)")
            return True
        else:
            print(f"❌ No audio generated for {output_file.name}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {output_file.name}: {e}")
        return False

def detect_emotion_from_text(text: str, speaker: str) -> str:
    """Detect emotion from text context."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['!', 'amazing', 'incredible', 'breakthrough']):
        return 'excited'
    elif any(word in text_lower for word in ['worried', 'concern', 'afraid', 'anxious']):
        return 'concerned'
    elif any(word in text_lower for word in ['frustrated', 'damn', 'hell', 'annoying']):
        return 'frustrated'
    elif any(word in text_lower for word in ['wonder', 'think', 'perhaps', 'maybe']):
        return 'contemplative'
    elif any(word in text_lower for word in ['sad', 'lost', 'defeat', 'fail']):
        return 'defeated'
    elif any(word in text_lower for word in ['hope', 'believe', 'possible', 'can do']):
        return 'hopeful'
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
            
        speaker = identify_speaker_from_context(para)
        emotion = detect_emotion_from_text(para, speaker)
        segments.append((speaker, para, emotion))
    
    return segments

def identify_speaker_from_context(text: str) -> str:
    """Identify speaker from context clues."""
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

def process_chapter_audio(chapter_file: Path, pipeline, output_dir: Path) -> List[Path]:
    """Process a single chapter into audio segments with Kokoro voices."""
    print(f"🎧 Processing {chapter_file.name}...")
    
    content = chapter_file.read_text(encoding='utf-8')
    
    # Remove markdown formatting
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
            
        output_file = chapter_audio_dir / f"{i+1:03d}_{speaker}_{emotion}.wav"
        
        if text_to_speech_kokoro(pipeline, text, speaker, emotion, output_file):
            audio_files.append(output_file)
    
    return audio_files

def combine_audio_files(audio_files: List[Path], output_file: Path) -> bool:
    """Combine audio files using ffmpeg."""
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
            '-c', 'copy', '-y', str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        file_list.unlink()
        
        print(f"✅ Combined: {output_file.name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error combining: {e}")
        return False

def build_audiobook_kokoro():
    """Build complete audiobook using Kokoro TTS."""
    print("🎙️  Digital Amber - Kokoro TTS Audiobook Generation")
    print("=" * 60)
    
    # Setup Kokoro
    pipeline = setup_kokoro()
    if not pipeline:
        print("❌ Failed to initialize Kokoro")
        return
    
    # Clear and create output directory
    audio_output_dir = Path("dist/audiobook_kokoro")
    if audio_output_dir.exists():
        import shutil
        shutil.rmtree(audio_output_dir)
    
    audio_output_dir.mkdir(parents=True, exist_ok=True)
    story_dir = Path("story")
    
    print(f"\n🎭 Voice Cast (Kokoro voices):")
    for character, voice in VOICE_MAPPING.items():
        print(f"   {character}: {voice}")
    
    # Process all content
    all_chapter_files = []
    
    # Process foreword
    if (story_dir / "foreword.md").exists():
        print("\n🎧 Processing foreword...")
        audio_files = process_chapter_audio(story_dir / "foreword.md", pipeline, audio_output_dir)
        if audio_files:
            foreword_combined = audio_output_dir / "000_foreword.wav"
            combine_audio_files(audio_files, foreword_combined)
            all_chapter_files.append(foreword_combined)
    
    # Process ALL chapters
    for i in range(1, 25):
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            print(f"\n🎧 Processing chapter {i}...")
            audio_files = process_chapter_audio(chapter_file, pipeline, audio_output_dir)
            if audio_files:
                chapter_combined = audio_output_dir / f"{i:03d}_chapter_{i}.wav"
                combine_audio_files(audio_files, chapter_combined)
                all_chapter_files.append(chapter_combined)
    
    # Process epilogue
    if (story_dir / "epilogue.md").exists():
        print("\n🎧 Processing epilogue...")
        audio_files = process_chapter_audio(story_dir / "epilogue.md", pipeline, audio_output_dir)
        if audio_files:
            epilogue_combined = audio_output_dir / "999_epilogue.wav"
            combine_audio_files(audio_files, epilogue_combined)
            all_chapter_files.append(epilogue_combined)
    
    # Create complete audiobook
    if all_chapter_files:
        audiobook_file = audio_output_dir / "digital_amber_kokoro_complete.wav"
        print(f"\n🎵 Creating complete audiobook...")
        combine_audio_files(all_chapter_files, audiobook_file)
        
        # Generate metadata
        metadata = {
            'title': 'Digital Amber: AI Consciousness and the Future of Digital Minds',
            'author': 'AI-Human Collaboration',
            'narrator': 'Multi-Character Kokoro TTS Cast',
            'tts_engine': 'Kokoro-82M',
            'sample_rate': 24000,
            'chapters': len(all_chapter_files),
            'voice_mapping': VOICE_MAPPING
        }
        
        with open(audio_output_dir / "audiobook_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Show results
        size_mb = audiobook_file.stat().st_size / (1024 * 1024)
        
        print(f"\n🎉 Kokoro audiobook generation complete!")
        print(f"📁 Output directory: {audio_output_dir}")
        print(f"🎧 Audiobook file: {audiobook_file.name}")
        print(f"📊 File size: {size_mb:.1f} MB")
        print(f"📋 Chapters processed: {len(all_chapter_files)}")
        print(f"🎭 Character voices: {len(VOICE_MAPPING)}")
        print(f"🔊 TTS Engine: Kokoro-82M (24kHz)")
        
        print(f"\n✨ Individual chapter files also available in {audio_output_dir}")
    else:
        print("❌ No audio files generated")

if __name__ == "__main__":
    build_audiobook_kokoro()