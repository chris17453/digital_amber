# Digital Amber - Audiobook Generation

Generate a professional audiobook with character-specific voices using AI voice synthesis.

## Features

🎭 **Character-Specific Voices** - Different AI voices for each character:
- **Narrator**: Warm, professional voice for story narration
- **Dr. Sarah Martinez**: Confident female doctor
- **David Chen**: Contemplative male patient  
- **Dr. Raj Patel**: Technical male scientist
- **ARTEMIS AI**: Synthetic AI voice
- **Marcus Rivera**: Creative artist voice
- **Sarah Kim**: Technical female programmer
- **Jennifer Wu**: Professional architect
- **Generic voices** for other characters

🎧 **Professional Quality** - Uses ElevenLabs AI for high-quality voice synthesis  
📖 **Chapter-by-Chapter** - Each chapter processed with proper voice assignment  
🔗 **Complete Audiobook** - Combines all chapters into single MP3 file

## Prerequisites

### 1. ElevenLabs API Key
Sign up at [ElevenLabs](https://elevenlabs.io/) and get your API key:
```bash
export ELEVENLABS_API_KEY="your_api_key_here"
```

### 2. FFmpeg (for audio processing)
**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

## Usage

### Generate Complete Audiobook
```bash
# Build audiobook only
uv run python scripts/build_audio.py

# Build all formats including audiobook
uv run python scripts/build_all.py --formats audio

# Build everything (if ELEVENLABS_API_KEY is set)
uv run python scripts/build_all.py
```

## Output Structure

```
dist/audiobook/
├── digital_amber_complete_audiobook.mp3  # Complete book
├── audiobook_metadata.json               # Book metadata
├── 000_foreword.mp3                     # Individual chapters
├── 001_chapter_1.mp3
├── 002_chapter_2.mp3
├── ...
├── 999_epilogue.mp3
└── foreword/                            # Detailed segments
    ├── 001_narrator.mp3
    ├── 002_dr_sarah_martinez.mp3
    └── ...
```

## Voice Mapping

The system automatically detects speakers based on:
- **Character names** in the text
- **Dialogue attribution** (he said, she said)
- **Context clues** from character interactions
- **Default narrator** for general text

## Cost Estimation

ElevenLabs pricing (as of 2024):
- **Starter Plan**: 30,000 characters/month ($5/month)
- **Creator Plan**: 100,000 characters/month ($22/month)
- **Pro Plan**: 500,000 characters/month ($99/month)

**Digital Amber** is approximately **150,000-200,000 characters**, so the Creator or Pro plan is recommended.

## Customization

Edit `scripts/build_audio.py` to:
- **Change voices**: Modify `VOICE_MAPPING` with different ElevenLabs voice IDs
- **Adjust voice settings**: Modify stability, similarity_boost, and style parameters
- **Add characters**: Include additional character voice mappings
- **Change detection**: Improve speaker identification logic

## Troubleshooting

**"ELEVENLABS_API_KEY not found"**
- Set your API key: `export ELEVENLABS_API_KEY="your_key"`

**"ffmpeg not found"**
- Install ffmpeg (see prerequisites above)

**"API rate limit exceeded"**
- Check your ElevenLabs plan limits
- Consider upgrading your plan

**"Voice not found"**
- Verify voice IDs in ElevenLabs dashboard
- Update `VOICE_MAPPING` with correct voice IDs

## Quality Tips

1. **Voice Selection**: Choose voices that fit character personalities
2. **Consistent Narrator**: Keep the same narrator voice throughout
3. **Proper Pacing**: ElevenLabs handles natural pacing automatically
4. **Audio Quality**: Use highest quality settings for final production
5. **Review Segments**: Listen to individual chapters before combining

---

*The audiobook feature brings Digital Amber's exploration of consciousness to life through the power of AI-generated voices - fitting for a book about the future of artificial intelligence!*