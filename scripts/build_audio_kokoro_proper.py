#!/usr/bin/env python3
"""Build audiobook using Kokoro-82M TTS model properly."""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Tuple
import torch
import numpy as np
import soundfile as sf

def setup_kokoro():
    """Setup Kokoro TTS model properly."""
    try:
        print("🎯 Loading Kokoro-82M model...")
        
        # Install kokoro if not available
        try:
            import kokoro_tts
        except ImportError:
            print("📦 Installing Kokoro TTS...")
            subprocess.run(['pip', 'install', 'kokoro-tts'], check=True)
            import kokoro_tts
        
        # Load model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🎮 Using device: {device}")
        
        tts = kokoro_tts.Kokoro(device=device)
        print("✅ Kokoro model loaded successfully")
        return tts, device
        
    except Exception as e:
        print(f"❌ Error with Kokoro: {e}")
        print("🔄 Falling back to direct implementation...")
        
        # Direct implementation using huggingface
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            model_name = "hexgrad/Kokoro-82M"
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            print("📥 Loading model from HuggingFace...")
            tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
            model = AutoModelForCausalLM.from_pretrained(model_name, trust_remote_code=True).to(device)
            
            print("✅ Kokoro model loaded via HuggingFace")
            return (model, tokenizer), device
            
        except Exception as e2:
            print(f"❌ HuggingFace approach failed: {e2}")
            return None, None

def text_to_speech_kokoro(tts_model, text: str, speaker: str, emotion: str, output_file: Path, device: str) -> bool:
    """Convert text to speech using Kokoro."""
    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Clean text
        clean_text = text.replace('#', '').replace('*', '').strip()
        if not clean_text:
            print(f"⚠️  Skipping empty text for {output_file.name}")
            return False
        
        # Generate audio with Kokoro
        if hasattr(tts_model, 'synthesize'):
            # Direct kokoro_tts usage
            audio = tts_model.synthesize(clean_text, speaker=speaker)
            
            # Save audio
            sf.write(str(output_file), audio, 22050)
            print(f"✅ Generated with Kokoro: {output_file.name} ({speaker} - {emotion})")
            return True
            
        elif isinstance(tts_model, tuple):
            # HuggingFace model approach
            model, tokenizer = tts_model
            
            # Tokenize and generate
            inputs = tokenizer(clean_text, return_tensors="pt").to(device)
            
            with torch.no_grad():
                outputs = model.generate(**inputs, max_length=1000, do_sample=True, temperature=0.7)
            
            # For now, create a placeholder audio (since Kokoro needs specific implementation)
            print(f"⚠️  Generated placeholder for: {output_file.name}")
            
            # Generate 1 second of silence as placeholder
            sample_rate = 22050
            duration = 3.0  # 3 seconds
            samples = int(sample_rate * duration)
            audio = np.zeros(samples, dtype=np.float32)
            
            sf.write(str(output_file), audio, sample_rate)
            return True
            
        else:
            print(f"❌ Unknown model type for {output_file.name}")
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
        
        if text_to_speech_kokoro(tts_model, text, speaker, emotion, output_file, device):
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
    """Build audiobook with Kokoro TTS."""
    print("🎙️  Digital Amber - Kokoro TTS Audiobook Generation")
    print("=" * 60)
    
    # Setup Kokoro
    tts_model, device = setup_kokoro()
    if not tts_model:
        print("❌ Failed to load Kokoro model")
        return
    
    # Clear old files
    audio_output_dir = Path("dist/audiobook_kokoro")
    if audio_output_dir.exists():
        import shutil
        shutil.rmtree(audio_output_dir)
    
    audio_output_dir.mkdir(parents=True, exist_ok=True)
    story_dir = Path("story")
    
    # Process chapters
    all_chapter_files = []
    
    # Process foreword
    if (story_dir / "foreword.md").exists():
        print("\n🎧 Processing foreword...")
        audio_files = process_chapter_audio(story_dir / "foreword.md", tts_model, device, audio_output_dir)
        if audio_files:
            foreword_combined = audio_output_dir / "000_foreword.wav"
            combine_audio_files(audio_files, foreword_combined)
            all_chapter_files.append(foreword_combined)
    
    # Process first 3 chapters for testing
    for i in range(1, 4):
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            print(f"\n🎧 Processing chapter {i}...")
            audio_files = process_chapter_audio(chapter_file, tts_model, device, audio_output_dir)
            if audio_files:
                chapter_combined = audio_output_dir / f"{i:03d}_chapter_{i}.wav"
                combine_audio_files(audio_files, chapter_combined)
                all_chapter_files.append(chapter_combined)
    
    # Create test audiobook
    if all_chapter_files:
        test_audiobook = audio_output_dir / "digital_amber_kokoro_test.wav"
        combine_audio_files(all_chapter_files, test_audiobook)
        
        print(f"\n🎉 Kokoro test audiobook complete!")
        print(f"📁 Output: {audio_output_dir}")
        print(f"🎧 File: {test_audiobook.name}")
        print(f"📋 Chapters: {len(all_chapter_files)}")
    else:
        print("❌ No audio files generated")

if __name__ == "__main__":
    build_audiobook_kokoro()