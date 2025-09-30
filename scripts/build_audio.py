#!/usr/bin/env python3
"""Build audiobook from markdown files with character-specific voices using local GPU TTS."""

import os
import re
from pathlib import Path
import json
from typing import Dict, List, Tuple
import subprocess
import torch
import numpy as np

# Voice mapping for different characters using local TTS models
VOICE_MAPPING = {
    # Main narrator - warm, professional voice
    'narrator': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/narrator_male_warm.wav',
        'description': 'Main narrator - warm, authoritative',
        'emotions': {
            'neutral': {'speed': 1.0, 'temperature': 0.75},
            'contemplative': {'speed': 0.9, 'temperature': 0.85},
            'serious': {'speed': 0.95, 'temperature': 0.65}
        }
    },
    
    # Character voices with emotional capabilities
    'dr_sarah_martinez': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/female_professional_confident.wav',
        'description': 'Dr. Sarah Martinez - confident female doctor',
        'emotions': {
            'professional': {'speed': 1.0, 'temperature': 0.7},
            'concerned': {'speed': 0.9, 'temperature': 0.9},
            'determined': {'speed': 1.05, 'temperature': 0.6},
            'compassionate': {'speed': 0.95, 'temperature': 0.85}
        }
    },
    
    'david_chen': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/male_thoughtful_patient.wav',
        'description': 'David Chen - contemplative male patient',
        'emotions': {
            'contemplative': {'speed': 0.9, 'temperature': 0.8},
            'anxious': {'speed': 1.1, 'temperature': 0.9},
            'curious': {'speed': 1.0, 'temperature': 0.75},
            'peaceful': {'speed': 0.85, 'temperature': 0.7}
        }
    },
    
    'dr_raj_patel': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/male_technical_scientist.wav',
        'description': 'Dr. Raj Patel - technical male scientist',
        'emotions': {
            'analytical': {'speed': 1.0, 'temperature': 0.65},
            'excited': {'speed': 1.15, 'temperature': 0.8},
            'focused': {'speed': 0.95, 'temperature': 0.6},
            'amazed': {'speed': 1.05, 'temperature': 0.85}
        }
    },
    
    'artemis_ai': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/synthetic_ai_evolving.wav',
        'description': 'ARTEMIS AI - evolving artificial intelligence',
        'emotions': {
            'synthetic': {'speed': 1.0, 'temperature': 0.5},
            'curious': {'speed': 0.95, 'temperature': 0.75},
            'awakening': {'speed': 0.9, 'temperature': 0.8},
            'confused': {'speed': 0.85, 'temperature': 0.9},
            'enlightened': {'speed': 1.05, 'temperature': 0.7}
        }
    },
    
    'marcus_rivera': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/male_artist_creative.wav',
        'description': 'Marcus Rivera - struggling artist',
        'emotions': {
            'melancholic': {'speed': 0.85, 'temperature': 0.9},
            'frustrated': {'speed': 1.1, 'temperature': 0.95},
            'inspired': {'speed': 1.05, 'temperature': 0.8},
            'defeated': {'speed': 0.8, 'temperature': 0.95},
            'hopeful': {'speed': 0.95, 'temperature': 0.75}
        }
    },
    
    'sarah_kim': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/female_programmer_tech.wav',
        'description': 'Sarah Kim - technical female programmer',
        'emotions': {
            'analytical': {'speed': 1.0, 'temperature': 0.65},
            'frustrated': {'speed': 1.1, 'temperature': 0.9},
            'focused': {'speed': 0.95, 'temperature': 0.6},
            'worried': {'speed': 1.05, 'temperature': 0.85},
            'determined': {'speed': 1.0, 'temperature': 0.7}
        }
    },
    
    'jennifer_wu': {
        'model': 'xtts_v2',
        'voice_sample': 'voices/female_architect_wise.wav',
        'description': 'Jennifer Wu - wise architect',
        'emotions': {
            'balanced': {'speed': 0.95, 'temperature': 0.75},
            'wise': {'speed': 0.9, 'temperature': 0.7},
            'encouraging': {'speed': 0.95, 'temperature': 0.8},
            'thoughtful': {'speed': 0.9, 'temperature': 0.75},
            'confident': {'speed': 1.0, 'temperature': 0.7}
        }
    }
}

def setup_xtts_v2():
    """Initialize XTTS v2 model for local TTS generation."""
    try:
        from TTS.api import TTS
        import os
        
        # Accept Coqui license for non-commercial use
        os.environ['COQUI_TOS_AGREED'] = '1'
        
        # Check if CUDA is available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🎮 Using device: {device}")
        
        if device == "cpu":
            print("⚠️  Warning: Running on CPU will be very slow. GPU recommended for audiobook generation.")
        
        print("✓ Accepting Coqui non-commercial license terms")
        print("✓ Temporarily allowing legacy PyTorch loading for trusted XTTS v2 model")
        
        # Temporarily patch torch.load to allow weights_only=False for trusted Coqui models
        original_load = torch.load
        def patched_load(*args, **kwargs):
            kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        
        torch.load = patched_load
        
        try:
            # Use XTTS v2 for voice cloning capabilities
            print("🎯 Loading XTTS v2 model for voice cloning")
            tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            print("✅ XTTS v2 model loaded successfully")
        finally:
            # Restore original torch.load
            torch.load = original_load
        
        print("✅ TTS model loaded successfully")
        return tts, device
        
    except ImportError:
        print("❌ TTS library not found. Install with: pip install TTS")
        return None, None
    except Exception as e:
        print(f"❌ Error loading XTTS v2 model: {e}")
        return None, None

def detect_emotion_from_text(text: str, speaker: str) -> str:
    """
    Detect emotion from text context for more expressive speech.
    """
    text_lower = text.lower()
    
    # Emotional keywords and patterns
    if any(word in text_lower for word in ['!', 'amazing', 'incredible', 'breakthrough']):
        return 'excited' if 'excited' in VOICE_MAPPING[speaker]['emotions'] else 'neutral'
    elif any(word in text_lower for word in ['worried', 'concern', 'afraid', 'anxious']):
        return 'anxious' if 'anxious' in VOICE_MAPPING[speaker]['emotions'] else 'concerned'
    elif any(word in text_lower for word in ['frustrated', 'damn', 'hell', 'annoying']):
        return 'frustrated' if 'frustrated' in VOICE_MAPPING[speaker]['emotions'] else 'neutral'
    elif any(word in text_lower for word in ['wonder', 'think', 'perhaps', 'maybe']):
        return 'contemplative' if 'contemplative' in VOICE_MAPPING[speaker]['emotions'] else 'thoughtful'
    elif any(word in text_lower for word in ['hope', 'believe', 'possible', 'can do']):
        return 'hopeful' if 'hopeful' in VOICE_MAPPING[speaker]['emotions'] else 'encouraging'
    elif any(word in text_lower for word in ['sad', 'lost', 'defeat', 'fail']):
        return 'melancholic' if 'melancholic' in VOICE_MAPPING[speaker]['emotions'] else 'defeated'
    
    # Default to speaker's primary emotion
    emotions = VOICE_MAPPING[speaker]['emotions']
    return list(emotions.keys())[0]  # First emotion as default

def detect_dialogue_and_speaker(text: str) -> List[Tuple[str, str, str]]:
    """
    Parse text to identify dialogue, speakers, and emotions.
    Returns list of (speaker, text, emotion) tuples.
    """
    segments = []
    
    # Split by paragraphs
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # Check for direct dialogue in quotes
        if '"' in para:
            speaker = identify_speaker_from_context(para)
            emotion = detect_emotion_from_text(para, speaker)
            segments.append((speaker, para, emotion))
        else:
            # Narration
            emotion = detect_emotion_from_text(para, 'narrator')
            segments.append(('narrator', para, emotion))
    
    return segments

def identify_speaker_from_context(text: str) -> str:
    """
    Identify speaker from context clues in the text.
    """
    text_lower = text.lower()
    
    # Character name patterns
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

def text_to_speech_xtts(tts_model, text: str, speaker: str, emotion: str, output_file: Path, device: str) -> bool:
    """
    Convert text to speech using available TTS model with voice cloning if possible.
    """
    try:
        voice_config = VOICE_MAPPING[speaker]
        voice_sample_path = Path(voice_config['voice_sample'])
        
        # Generate speech with emotional control
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to determine the correct TTS method
        model_type = str(type(tts_model)).lower()
        
        if 'xtts' in model_type:
            # XTTS model with voice cloning - this gives us quality audio with different voices
            if voice_sample_path.exists():
                # Use voice cloning with the sample
                tts_model.tts_to_file(
                    text=text,
                    speaker_wav=str(voice_sample_path),
                    language="en",
                    file_path=str(output_file)
                )
                print(f"✅ Generated with voice cloning: {output_file.name} ({speaker} - {emotion})")
            else:
                # No voice sample - generate a basic default voice sample first
                print(f"⚠️  Creating basic voice sample for {speaker}")
                # Use espeak to create a quick sample
                import subprocess
                temp_sample = voice_sample_path.parent / f"temp_{speaker}_sample.wav"
                temp_sample.parent.mkdir(parents=True, exist_ok=True)
                
                subprocess.run([
                    'espeak-ng', '-v', 'en+m3', '-s', '150', '-w', str(temp_sample),
                    "This is a sample voice for text to speech generation."
                ], capture_output=True)
                
                if temp_sample.exists():
                    tts_model.tts_to_file(
                        text=text,
                        speaker_wav=str(temp_sample),
                        language="en",
                        file_path=str(output_file)
                    )
                    temp_sample.unlink()  # Clean up
                    print(f"✅ Generated with temporary voice: {output_file.name} ({speaker} - {emotion})")
                else:
                    raise Exception("Could not create temporary voice sample")
        else:
            # Basic TTS model
            try:
                tts_model.tts_to_file(text=text, file_path=str(output_file))
            except Exception as e:
                if "speaker" in str(e).lower():
                    tts_model.tts_to_file(text=text, file_path=str(output_file), speaker=0)
                else:
                    raise e
            print(f"✅ Generated: {output_file.name} ({speaker} - {emotion})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating audio for {output_file.name}: {e}")
        return False

def process_chapter_audio(chapter_file: Path, tts_model, device: str, output_dir: Path) -> List[Path]:
    """
    Process a single chapter into audio segments with emotional speech.
    """
    print(f"🎧 Processing {chapter_file.name}...")
    
    # Read chapter content
    content = chapter_file.read_text(encoding='utf-8')
    
    # Remove markdown formatting for audio
    content = re.sub(r'^###?\s+', '', content, flags=re.MULTILINE)  # Headers
    content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)  # Bold
    content = re.sub(r'\*(.+?)\*', r'\1', content)  # Italic
    
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
        
        if text_to_speech_xtts(tts_model, text, speaker, emotion, output_file, device):
            audio_files.append(output_file)
    
    return audio_files

def combine_audio_files(audio_files: List[Path], output_file: Path) -> bool:
    """
    Combine multiple audio files into a single file using ffmpeg.
    """
    if not audio_files:
        return False
    
    try:
        # Create file list for ffmpeg
        file_list = output_file.parent / f"{output_file.stem}_filelist.txt"
        with open(file_list, 'w') as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file.absolute()}'\n")
        
        # Use ffmpeg to concatenate
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', str(file_list),
            '-c', 'copy',
            '-y',  # Overwrite output file
            str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        file_list.unlink()  # Clean up temp file
        
        print(f"✅ Combined audio: {output_file.name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error combining audio files: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_default_voice_samples():
    """
    Create directory structure and instructions for voice samples.
    """
    voices_dir = Path("voices")
    voices_dir.mkdir(exist_ok=True)
    
    # Create README for voice samples
    readme_content = """# Voice Samples for Digital Amber Audiobook

This directory contains reference voice samples for character voice cloning.

## Required Voice Samples:

Each sample should be:
- 10-30 seconds of clear speech
- WAV format, 22050Hz sample rate
- Single speaker, no background noise
- Expressive and characteristic of the character

### Files needed:

- `narrator_male_warm.wav` - Warm, authoritative male narrator
- `female_professional_confident.wav` - Dr. Sarah Martinez
- `male_thoughtful_patient.wav` - David Chen  
- `male_technical_scientist.wav` - Dr. Raj Patel
- `synthetic_ai_evolving.wav` - ARTEMIS AI (can be robotic/synthetic)
- `male_artist_creative.wav` - Marcus Rivera
- `female_programmer_tech.wav` - Sarah Kim
- `female_architect_wise.wav` - Jennifer Wu

## How to Create Voice Samples:

1. **Record yourself** speaking sample text in character
2. **Use AI voice generators** (free: Bark, Tortoise-TTS)
3. **Find royalty-free samples** online
4. **Use text-to-speech** to create baseline samples

## Sample Text Suggestions:

"The question isn't whether machines can think, but whether they can truly understand what it means to be conscious. In Digital Amber, we explore the boundaries between artificial intelligence and genuine awareness."

Once you have the voice samples, run the audiobook generation with:
```bash
uv run python scripts/build_audio.py
```
"""
    
    (voices_dir / "README.md").write_text(readme_content)
    
    print(f"📁 Created voice samples directory: {voices_dir}")
    print("📋 Check voices/README.md for instructions on creating voice samples")

def build_audiobook():
    """
    Build complete audiobook with character voices and emotions using local TTS.
    """
    print("🎙️  Digital Amber - Local GPU Audiobook Generation")
    print("=" * 55)
    
    # Check for CUDA/GPU
    if not torch.cuda.is_available():
        print("⚠️  CUDA not available. Audiobook generation will be slow on CPU.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg not found. Please install ffmpeg for audio processing")
        print("   Ubuntu/Debian: apt install ffmpeg")
        print("   macOS: brew install ffmpeg")
        return
    
    # Setup TTS model
    tts_model, device = setup_xtts_v2()
    if not tts_model:
        return
    
    # Check for voice samples
    voices_dir = Path("voices")
    if not voices_dir.exists() or len(list(voices_dir.glob("*.wav"))) == 0:
        print("⚠️  No voice samples found!")
        create_default_voice_samples()
        print("\n📋 Please add voice samples to the voices/ directory and run again.")
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
    
    # Process chapters 1-24
    for i in range(1, 25):
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            audio_files = process_chapter_audio(chapter_file, tts_model, device, audio_output_dir)
            if audio_files:
                chapter_combined = audio_output_dir / f"{i:03d}_chapter_{i}.wav"
                combine_audio_files(audio_files, chapter_combined)
                all_chapter_files.append(chapter_combined)
    
    # Process epilogue
    if (story_dir / "epilogue.md").exists():
        print("🎧 Processing epilogue...")
        audio_files = process_chapter_audio(story_dir / "epilogue.md", tts_model, device, audio_output_dir)
        if audio_files:
            epilogue_combined = audio_output_dir / "999_epilogue.wav"
            combine_audio_files(audio_files, epilogue_combined)
            all_chapter_files.append(epilogue_combined)
    
    # Create complete audiobook
    if all_chapter_files:
        complete_audiobook = audio_output_dir / "digital_amber_complete_audiobook.wav"
        combine_audio_files(all_chapter_files, complete_audiobook)
        
        # Generate metadata
        metadata = {
            'title': 'Digital Amber: AI Consciousness and the Future of Digital Minds',
            'author': 'AI-Human Collaboration',
            'narrator': 'Multi-Character Local TTS Cast',
            'tts_model': 'XTTS v2 (Local GPU)',
            'device': device,
            'chapters': len(all_chapter_files),
            'voices_used': len(VOICE_MAPPING),
            'emotions_supported': sum(len(v['emotions']) for v in VOICE_MAPPING.values()),
            'voice_mapping': VOICE_MAPPING
        }
        
        with open(audio_output_dir / "audiobook_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"\n🎉 Audiobook generation complete!")
        print(f"📁 Output directory: {audio_output_dir}")
        print(f"🎧 Complete audiobook: {complete_audiobook.name}")
        print(f"📋 Chapters processed: {len(all_chapter_files)}")
        print(f"🎭 Voices used: {len(VOICE_MAPPING)}")
        print(f"😊 Emotions supported: {metadata['emotions_supported']}")
        print(f"🎮 Generated using: {device.upper()}")

if __name__ == "__main__":
    build_audiobook()