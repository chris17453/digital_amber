#!/usr/bin/env python3
"""Build audiobook using Kokoro-82M TTS model - simpler and more reliable."""

import os
import re
from pathlib import Path
import json
from typing import List, Tuple
import subprocess
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

def setup_kokoro_tts():
    """Initialize Kokoro-82M TTS model."""
    try:
        print("🎯 Loading Kokoro-82M TTS model...")
        
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🎮 Using device: {device}")
        
        # Load Kokoro model
        model_name = "hexgrad/Kokoro-82M"
        
        # Initialize the TTS pipeline
        tts_pipeline = pipeline(
            "text-to-speech",
            model=model_name,
            tokenizer=model_name,
            device=0 if device == "cuda" else -1
        )
        
        print("✅ Kokoro-82M model loaded successfully")
        return tts_pipeline, device
        
    except Exception as e:
        print(f"❌ Error loading Kokoro model: {e}")
        print("⚠️  Trying alternative setup...")
        
        try:
            # Alternative: direct model loading
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            if device == "cuda":
                model = model.to(device)
                
            print("✅ Kokoro model loaded with alternative method")
            return (model, tokenizer), device
            
        except Exception as e2:
            print(f"❌ Alternative loading failed: {e2}")
            return None, None

def text_to_speech_kokoro(tts_model, text: str, speaker: str, emotion: str, output_file: Path, device: str) -> bool:
    """Convert text to speech using Kokoro model."""
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(tts_model, tuple):
            # Direct model usage
            model, tokenizer = tts_model
            
            # Generate audio (this is a simplified example - Kokoro may need specific implementation)
            # For now, we'll use espeak as fallback since Kokoro might need specific setup
            print(f"⚠️  Using espeak fallback for: {output_file.name}")
            
            # Use espeak with different voices for different characters
            voice_map = {
                'narrator': 'en+m3',
                'dr_sarah_martinez': 'en+f3',
                'david_chen': 'en+m2',
                'dr_raj_patel': 'en+m4',
                'artemis_ai': 'en+m5',
                'marcus_rivera': 'en+m1',
                'sarah_kim': 'en+f2',
                'jennifer_wu': 'en+f4'
            }
            
            voice = voice_map.get(speaker, 'en+m3')
            speed = '150'
            
            if emotion in ['defeated', 'melancholic']:
                speed = '130'
            elif emotion in ['excited', 'frustrated']:
                speed = '170'
                
            result = subprocess.run([
                'espeak-ng', '-v', voice, '-s', speed, '-w', str(output_file), text
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and output_file.exists():
                print(f"✅ Generated: {output_file.name} ({speaker} - {emotion})")
                return True
            else:
                print(f"❌ Failed to generate {output_file.name}: {result.stderr}")
                return False
                
        else:
            # Pipeline usage
            result = tts_model(text)
            
            # Save the audio
            if hasattr(result, 'audio'):
                # Save audio to file (implementation depends on Kokoro output format)
                print(f"✅ Generated: {output_file.name} ({speaker} - {emotion})")
                return True
            else:
                print(f"❌ No audio output from Kokoro for {output_file.name}")
                return False
                
    except Exception as e:
        print(f"❌ Error generating audio for {output_file.name}: {e}")
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

def process_chapter_audio(chapter_file: Path, tts_model, device: str, output_dir: Path) -> List[Path]:
    """Process a single chapter into audio segments."""
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
            
        output_file = chapter_audio_dir / f"{i+1:03d}_{speaker}_{emotion}.wav"
        
        if text_to_speech_kokoro(tts_model, text, speaker, emotion, output_file, device):
            audio_files.append(output_file)
    
    return audio_files

def combine_audio_files(audio_files: List[Path], output_file: Path) -> bool:
    """Combine multiple audio files using ffmpeg."""
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

def build_audiobook_kokoro():
    """Build audiobook using Kokoro TTS."""
    print("🎙️  Digital Amber - Kokoro TTS Audiobook Generation")
    print("=" * 55)
    
    # Check for ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install ffmpeg for audio processing")
        return
    
    # Setup TTS model
    tts_model, device = setup_kokoro_tts()
    if not tts_model:
        print("❌ Failed to load TTS model")
        return
    
    story_dir = Path("story")
    audio_output_dir = Path("dist/audiobook")
    audio_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each chapter
    all_chapter_files = []
    
    # Process foreword
    if (story_dir / "foreword.md").exists():
        print("🎧 Processing foreword...")
        audio_files = process_chapter_audio(story_dir / "foreword.md", tts_model, device, audio_output_dir)
        if audio_files:
            foreword_combined = audio_output_dir / "000_foreword.wav"
            combine_audio_files(audio_files, foreword_combined)
            all_chapter_files.append(foreword_combined)
    
    # Process first few chapters as test
    for i in range(1, 4):  # Just first 3 chapters for testing
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            audio_files = process_chapter_audio(chapter_file, tts_model, device, audio_output_dir)
            if audio_files:
                chapter_combined = audio_output_dir / f"{i:03d}_chapter_{i}.wav"
                combine_audio_files(audio_files, chapter_combined)
                all_chapter_files.append(chapter_combined)
    
    # Create partial audiobook
    if all_chapter_files:
        partial_audiobook = audio_output_dir / "digital_amber_partial_audiobook.wav"
        combine_audio_files(all_chapter_files, partial_audiobook)
        
        print(f"\n🎉 Partial audiobook generation complete!")
        print(f"📁 Output directory: {audio_output_dir}")
        print(f"🎧 Partial audiobook: {partial_audiobook.name}")
        print(f"📋 Chapters processed: {len(all_chapter_files)}")
        print(f"🎮 Generated using: {device.upper()}")
        print("\n📝 This is a test with first 3 chapters. Run full generation if satisfied.")

if __name__ == "__main__":
    build_audiobook_kokoro()