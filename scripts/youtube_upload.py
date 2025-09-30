#!/usr/bin/env python3
"""YouTube upload script for Digital Amber audiobook videos with chapter support."""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import timedelta
import librosa

def get_video_duration(video_path: Path) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', str(video_path)
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception as e:
        print(f"❌ Error getting duration for {video_path.name}: {e}")
        return 0.0

def format_timestamp(seconds: float) -> str:
    """Convert seconds to YouTube timestamp format (M:SS or H:MM:SS)."""
    td = timedelta(seconds=int(seconds))
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def get_chapter_titles() -> Dict[str, str]:
    """Get chapter titles from markdown files."""
    chapters = {}
    story_dir = Path("story")
    
    # Foreword
    foreword_file = story_dir / "foreword.md"
    if foreword_file.exists():
        chapters["foreword"] = "Foreword - The Digital Amber Concept"
    
    # Chapters 1-24
    for i in range(1, 25):
        chapter_file = story_dir / f"chapter_{i}.md"
        if chapter_file.exists():
            try:
                content = chapter_file.read_text(encoding='utf-8')
                # Extract title from first header
                lines = content.split('\n')
                title = f"Chapter {i}"
                for line in lines:
                    if line.startswith('# ') or line.startswith('## ') or line.startswith('### '):
                        title = line.strip('# ').strip()
                        break
                chapters[f"chapter_{i}"] = f"Chapter {i} - {title}"
            except Exception as e:
                print(f"⚠️  Could not read title for chapter {i}: {e}")
                chapters[f"chapter_{i}"] = f"Chapter {i}"
    
    # Epilogue
    epilogue_file = story_dir / "epilogue.md"
    if epilogue_file.exists():
        chapters["epilogue"] = "Epilogue - The Future Awakens"
    
    return chapters

def create_combined_video_with_chapters():
    """Create a single long video with all chapters and generate YouTube chapter timestamps."""
    print("🎬 Creating combined Digital Amber audiobook video with chapters")
    print("=" * 60)
    
    video_dir = Path("dist/audiobook_videos")
    output_dir = Path("dist/youtube")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all video files in order
    video_files = []
    chapter_titles = get_chapter_titles()
    
    # Foreword
    foreword_file = video_dir / "foreword.mp4"
    if foreword_file.exists():
        video_files.append(("foreword", foreword_file))
    
    # Chapters 1-24
    for i in range(1, 25):
        chapter_file = video_dir / f"chapter_{i}.mp4"
        if chapter_file.exists():
            video_files.append((f"chapter_{i}", chapter_file))
    
    # Epilogue
    epilogue_file = video_dir / "epilogue.mp4"
    if epilogue_file.exists():
        video_files.append(("epilogue", epilogue_file))
    
    if not video_files:
        print("❌ No video files found to combine")
        return
    
    print(f"📁 Found {len(video_files)} videos to combine")
    
    # Create file list for ffmpeg
    file_list_path = output_dir / "video_list.txt"
    chapter_timestamps = []
    current_time = 0.0
    
    with open(file_list_path, 'w') as f:
        for chapter_key, video_file in video_files:
            # Add chapter timestamp
            title = chapter_titles.get(chapter_key, chapter_key.replace('_', ' ').title())
            timestamp = format_timestamp(current_time)
            chapter_timestamps.append(f"{timestamp} {title}")
            
            # Add to ffmpeg file list
            f.write(f"file '{video_file.absolute()}'\n")
            
            # Add duration to current time
            duration = get_video_duration(video_file)
            current_time += duration
            print(f"   📹 {chapter_key}: {format_timestamp(duration)} (total: {format_timestamp(current_time)})")
    
    # Combine videos using ffmpeg
    combined_video_path = output_dir / "digital_amber_complete_audiobook.mp4"
    print(f"\n🔧 Combining videos into {combined_video_path.name}...")
    
    ffmpeg_cmd = [
        'ffmpeg', '-f', 'concat', '-safe', '0',
        '-i', str(file_list_path),
        '-c', 'copy', '-y', str(combined_video_path)
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"✅ Combined video created: {combined_video_path}")
        
        # Get final file size
        size_mb = combined_video_path.stat().st_size / (1024 * 1024)
        print(f"📊 Final size: {size_mb:.1f} MB")
        print(f"⏱️  Total duration: {format_timestamp(current_time)}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error combining videos: {e}")
        return
    
    # Create YouTube description with chapters
    description_path = output_dir / "youtube_description.txt"
    description = create_youtube_description(chapter_timestamps, current_time)
    
    with open(description_path, 'w') as f:
        f.write(description)
    
    print(f"\n📝 YouTube description with chapters saved to: {description_path}")
    print(f"🎬 Combined video ready for YouTube upload: {combined_video_path}")
    
    # Clean up
    file_list_path.unlink()
    
    return combined_video_path, description_path

def create_youtube_description(chapter_timestamps: List[str], total_duration: float) -> str:
    """Create YouTube description with chapter timestamps and book info."""
    description = f"""Digital Amber: AI Consciousness and the Future of Digital Minds
Complete Audiobook with Neural TTS Narration

🎧 Experience the full journey through AI consciousness and the evolution of digital minds in this groundbreaking exploration of artificial intelligence, identity, and what it means to be truly "alive" in the digital age.

📖 About This Book:
Digital Amber examines the fascinating intersection of artificial intelligence and consciousness through interconnected narratives and philosophical discussions. The book addresses fundamental questions about the nature of consciousness, identity, and the future of human-AI collaboration.

🎙️ Narration: Multi-Character Neural TTS (Kokoro-82M)
⏱️  Total Duration: {format_timestamp(total_duration)}
📚 Chapters: {len(chapter_timestamps)}

📑 CHAPTERS:
{chr(10).join(chapter_timestamps)}

🔧 Technical Details:
• Neural TTS Generation: Kokoro-82M (82 million parameter model)
• Voice Synthesis: Multi-character voices with emotional dynamics
• Video Format: Center-mirrored frequency visualization with word-level timing
• Text Display: Real-time word highlighting with Whisper speech recognition

🌐 Read Online: https://chris17453.github.io/digital_amber/
📖 Download Book: https://github.com/chris17453/digital_amber

🎨 Features:
✓ 26 interconnected chapters exploring AI consciousness
✓ Original conceptual artwork for each chapter
✓ Word-level speech synchronization
✓ Real-time audio frequency visualization
✓ Professional multi-character narration

🤖 About the Creation:
This audiobook represents an innovative collaboration between human creativity and AI assistance, exploring the very technologies used in its creation. The book serves as both subject matter and example of human-AI collaborative potential.

#DigitalAmber #AIConsciousness #Audiobook #NeuralTTS #ArtificialIntelligence #DigitalMinds #FutureOfAI #TechPhilosophy #AIEthics #DigitalIdentity

---
🔊 Generated with Kokoro Neural TTS
🎬 Video created with Python automation
📚 Open source book project
"""
    return description

def create_individual_chapter_uploads():
    """Create upload scripts for individual chapter videos."""
    print("\n📱 Creating individual chapter upload information...")
    
    video_dir = Path("dist/audiobook_videos")
    output_dir = Path("dist/youtube/individual")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    chapter_titles = get_chapter_titles()
    upload_info = []
    
    for chapter_key, title in chapter_titles.items():
        if chapter_key == "foreword":
            video_file = video_dir / "foreword.mp4"
        elif chapter_key == "epilogue":
            video_file = video_dir / "epilogue.mp4"
        else:
            # Extract chapter number
            chapter_num = chapter_key.split('_')[1]
            video_file = video_dir / f"chapter_{chapter_num}.mp4"
        
        if video_file.exists():
            duration = get_video_duration(video_file)
            size_mb = video_file.stat().st_size / (1024 * 1024)
            
            upload_info.append({
                'title': f"Digital Amber - {title}",
                'file': str(video_file),
                'duration': format_timestamp(duration),
                'size_mb': round(size_mb, 1)
            })
    
    # Save upload information
    upload_info_path = output_dir / "upload_info.json"
    with open(upload_info_path, 'w') as f:
        json.dump(upload_info, f, indent=2)
    
    print(f"📋 Individual upload info saved to: {upload_info_path}")
    print(f"📁 {len(upload_info)} individual videos ready for upload")
    
    return upload_info

def main():
    """Main function to create YouTube-ready content."""
    print("🎬 Digital Amber - YouTube Upload Preparation")
    print("=" * 50)
    
    # Create combined video with chapters
    combined_result = create_combined_video_with_chapters()
    
    # Create individual chapter information
    individual_info = create_individual_chapter_uploads()
    
    print(f"\n🎉 YouTube upload preparation complete!")
    print(f"📺 Combined video: Ready for single upload with chapters")
    print(f"📱 Individual videos: {len(individual_info)} files ready")
    print(f"📂 Output directory: dist/youtube/")

if __name__ == "__main__":
    main()