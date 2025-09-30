#!/usr/bin/env python3
"""Create video version of Digital Amber audiobook with scrolling text, waveforms, and art."""

import os
import re
import json
import hashlib
import requests
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
import cupy as cp
import soundfile as sf
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
import cv2
import whisper_timestamped as whisper
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import pickle
from functools import lru_cache

# Configuration
VIDEO_CONFIG = {
    'resolution': (1920, 1080),  # Full HD
    'fps': 12,
    'background_color': (0, 0, 0),  # Black
    'text_color': (255, 255, 255),  # White
    'accent_color': (255, 165, 0),  # Orange (Digital Amber)
    'waveform_color': (255, 200, 100),  # Amber waveform
    'font_size': 96,  # Tripled from 32
    'scroll_speed': 50,  # pixels per second
    'waveform_height': 150,
    'text_margin': 100,
    'max_workers': min(48, cpu_count()),  # Use available threads
    'cache_dir': Path("cache/video_processing"),
    'lead_in_pause': 1.0,   # seconds of silence at start
    'lead_out_pause': 2.0   # seconds of silence at end
}

# Ensure cache directories exist
VIDEO_CONFIG['cache_dir'].mkdir(parents=True, exist_ok=True)
(VIDEO_CONFIG['cache_dir'] / "waveforms").mkdir(exist_ok=True)
(VIDEO_CONFIG['cache_dir'] / "text_layouts").mkdir(exist_ok=True)

def use_local_art():
    """Use art assets from local art folder."""
    print("🎨 Using local art assets...")
    
    art_dir = Path("art/pages")  # Use pages directory for web-optimized art
    if not art_dir.exists():
        print(f"❌ Art directory not found: {art_dir}")
        print("🎨 Creating placeholder art directory...")
        art_dir.mkdir(parents=True, exist_ok=True)
        
        # Create placeholder images if art folder doesn't exist
        art_files = ['cover.jpg', 'foreword.jpg', 'chapter_default.jpg', 'epilogue.jpg']
        for art_file in art_files:
            art_path = art_dir / art_file
            if not art_path.exists():
                print(f"Creating placeholder for {art_file}")
                create_placeholder_art(art_path, art_file.split('.')[0])
    
    return art_dir

def create_placeholder_art(output_path: Path, art_type: str):
    """Create placeholder art with amber/digital theme."""
    width, height = 1920, 1080
    
    # Create gradient background
    img = Image.new('RGB', (width, height), color=(20, 15, 10))
    draw = ImageDraw.Draw(img)
    
    # Create amber gradient effect
    for y in range(height):
        alpha = y / height
        amber_intensity = int(50 + alpha * 100)
        color = (amber_intensity, int(amber_intensity * 0.6), 10)
        draw.line([(0, y), (width, y)], fill=color)
    
    # Add digital patterns
    for i in range(0, width, 100):
        for j in range(0, height, 100):
            if (i + j) % 200 == 0:
                draw.rectangle([i, j, i+50, j+50], outline=(100, 60, 20), width=1)
    
    # Add title text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    title_text = art_type.replace('_', ' ').title()
    if art_type == 'cover':
        title_text = "Digital Amber"
    
    # Calculate text position
    bbox = draw.textbbox((0, 0), title_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw text with outline
    draw.text((x-2, y-2), title_text, font=font, fill=(0, 0, 0))
    draw.text((x+2, y+2), title_text, font=font, fill=(0, 0, 0))
    draw.text((x, y), title_text, font=font, fill=(255, 165, 0))
    
    img.save(output_path, quality=95)
    print(f"✅ Created placeholder art: {output_path}")

def get_exact_word_timings_from_audio(audio_file: Path) -> List[Dict]:
    """Use Whisper to get EXACT word-level timestamps from audio with caching."""
    
    # Create cache directory if it doesn't exist
    cache_dir = Path("cache/whisper_timings")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate cache file name based on audio file hash and size
    audio_stats = audio_file.stat()
    file_hash = hashlib.md5(f"{audio_file.name}_{audio_stats.st_size}_{audio_stats.st_mtime}".encode()).hexdigest()
    cache_file = cache_dir / f"{audio_file.stem}_{file_hash}.json"
    
    # Check if cached result exists
    if cache_file.exists():
        try:
            print(f"📋 Loading cached Whisper timings for {audio_file.name}...")
            with open(cache_file, 'r') as f:
                cached_data = json.load(f)
            
            print(f"   ✅ Loaded {len(cached_data)} cached word timings")
            for i, w in enumerate(cached_data[:5]):  # Show first 5 words
                print(f"      {i+1}: '{w['word']}' [{w['start']:.2f}s - {w['end']:.2f}s]")
            
            return cached_data
        except Exception as e:
            print(f"   ⚠️  Cache read failed, running Whisper: {e}")
    
    # Run Whisper if no cache or cache failed
    try:
        print(f"🎯 Running Whisper speech recognition on {audio_file.name}...")
        
        # Load Whisper model (using tiny model for maximum speed)
        print("   📥 Loading Whisper model...")
        model = whisper.load_model("tiny")
        
        # Transcribe with word-level timestamps - optimized settings
        print("   🎙️  Transcribing audio (this may take a while)...")
        result = whisper.transcribe(
            model, 
            str(audio_file), 
            language="en",
            beam_size=1,  # Faster decoding
            best_of=1,    # No multiple attempts
            temperature=0.0  # Deterministic output
        )
        
        word_timings = []
        total_words = 0
        
        for segment in result["segments"]:
            if "words" in segment:
                for word_info in segment["words"]:
                    word_timings.append({
                        'word': word_info["text"].strip(),
                        'start': word_info["start"],
                        'end': word_info["end"],
                        'confidence': word_info.get("confidence", 1.0)
                    })
                    total_words += 1
        
        # Cache the results
        try:
            with open(cache_file, 'w') as f:
                json.dump(word_timings, f, indent=2)
            print(f"   💾 Cached Whisper results to {cache_file.name}")
        except Exception as e:
            print(f"   ⚠️  Failed to cache results: {e}")
        
        print(f"   ✅ Whisper detected {total_words} words with exact timestamps")
        for i, w in enumerate(word_timings[:5]):  # Show first 5 words
            print(f"      {i+1}: '{w['word']}' [{w['start']:.2f}s - {w['end']:.2f}s]")
        
        return word_timings
        
    except Exception as e:
        print(f"   ❌ Whisper failed: {e}")
        return []

def generate_frequency_meter_video_gpu(audio_file: Path, duration: float, bg_img: np.ndarray) -> cp.ndarray:
    """GPU-accelerated frequency band waveform with butterfly pattern."""
    # Check cache first - include background image hash in cache key
    cache_file = VIDEO_CONFIG['cache_dir'] / "waveforms" / f"{audio_file.stem}_waveform.pkl"
    audio_stats = audio_file.stat()
    
    # Include background image in cache key to handle art changes
    import hashlib
    bg_hash = hashlib.md5(bg_img.tobytes()).hexdigest()[:8]
    cache_key = f"{audio_file.name}_{audio_stats.st_size}_{audio_stats.st_mtime}_{bg_hash}"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
            if cached_data.get('cache_key') == cache_key:
                print(f"🎵 Loading cached waveform for {audio_file.name}...")
                return cp.asarray(cached_data['waveform_frames'])
        except Exception as e:
            print(f"   ⚠️  Cache read failed, regenerating: {e}")
    
    print(f"🎵 GPU-accelerated frequency waveform for {audio_file.name}...")
    
    # Load audio and transfer to GPU
    audio_data, sample_rate = sf.read(str(audio_file))
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)  # Convert to mono
    audio_gpu = cp.asarray(audio_data)
    
    width, height = VIDEO_CONFIG['resolution']
    meter_height = VIDEO_CONFIG['waveform_height']
    fps = VIDEO_CONFIG['fps']
    
    # Transfer background to GPU
    base_strip_gpu = cp.asarray(bg_img[height - meter_height:height, :, :3])
    
    # Waveform parameters
    waveform_width = int(width * 0.5)
    start_x = (width - waveform_width) // 2
    center_y = meter_height // 2
    
    # Frequency analysis setup on GPU
    num_bands = 48
    freq_ranges = cp.logspace(cp.log10(20), cp.log10(20000), num_bands + 1)
    band_width = waveform_width // num_bands
    
    total_frames = int(duration * fps)
    frame_size = int(sample_rate / fps)
    
    meter_frames_gpu = []
    
    # Process frames in parallel batches for better CPU utilization
    def process_frame_batch(frame_indices):
        """Process a batch of frames in parallel."""
        batch_frames = []
        for frame in frame_indices:
            # Start with background
            img_gpu = base_strip_gpu.copy()
            
            # Get audio chunk on GPU
            start_sample = frame * frame_size
            end_sample = min(start_sample + frame_size, len(audio_gpu))
            
            if start_sample < end_sample:
                frame_audio_gpu = audio_gpu[start_sample:end_sample]
                
                # GPU FFT
                fft_gpu = cp.fft.fft(frame_audio_gpu)
                freqs_gpu = cp.fft.fftfreq(len(frame_audio_gpu), 1/sample_rate)
                
                # Magnitude spectrum
                magnitude_gpu = cp.abs(fft_gpu[:len(fft_gpu)//2])
                positive_freqs_gpu = freqs_gpu[:len(freqs_gpu)//2]
                max_mag = cp.max(magnitude_gpu)
                
                if max_mag > 0:
                    # Process all bands vectorized on GPU
                    for band in range(num_bands):
                        freq_start = freq_ranges[band]
                        freq_end = freq_ranges[band + 1]
                        
                        # Band mask
                        band_mask = (positive_freqs_gpu >= freq_start) & (positive_freqs_gpu < freq_end)
                        
                        if cp.any(band_mask):
                            band_magnitude = cp.mean(magnitude_gpu[band_mask])
                            level = float(min(1.0, band_magnitude / max_mag))
                            
                            # Calculate visual properties
                            brightness = 0.5 + (0.5 * level)
                            bar_height = int(level * (center_y - 10))
                            band_x = start_x + band * band_width + band_width // 2
                            
                            # Color mapping (BGR for OpenCV)
                            if level < 0.25:
                                base_color = (0, 255, 0)  # Green
                            elif level < 0.5:
                                mix = (level - 0.25) / 0.25
                                base_color = (int(255 * mix), 255, 0)  # Green to Yellow
                            elif level < 0.75:
                                mix = (level - 0.5) / 0.25
                                base_color = (255, int(255 * (1 - mix * 0.5)), 0)  # Yellow to Orange
                            else:
                                mix = (level - 0.75) / 0.25
                                base_color = (255, int(128 * (1 - mix)), 0)  # Orange to Red
                            
                            color = tuple(int(c * brightness) for c in base_color)
                            
                            # Draw bars directly on GPU using indexing (much faster)
                            if bar_height > 2:
                                # Calculate bar coordinates
                                x1 = max(0, band_x - band_width//4)
                                x2 = min(waveform_width, band_x + band_width//4)
                                
                                # Upward bar
                                y1_up = max(0, center_y - bar_height)
                                y2_up = center_y
                                if y1_up < y2_up and x1 < x2:
                                    img_gpu[y1_up:y2_up, x1:x2, 0] = color[0]
                                    img_gpu[y1_up:y2_up, x1:x2, 1] = color[1]
                                    img_gpu[y1_up:y2_up, x1:x2, 2] = color[2]
                                
                                # Downward bar
                                y1_down = center_y
                                y2_down = min(meter_height, center_y + bar_height)
                                if y1_down < y2_down and x1 < x2:
                                    img_gpu[y1_down:y2_down, x1:x2, 0] = color[0]
                                    img_gpu[y1_down:y2_down, x1:x2, 1] = color[1]
                                    img_gpu[y1_down:y2_down, x1:x2, 2] = color[2]
            
            # Draw center line directly on GPU
            if start_x < img_gpu.shape[1] and center_y < img_gpu.shape[0]:
                end_x = min(start_x + waveform_width, img_gpu.shape[1])
                img_gpu[center_y, start_x:end_x, :] = cp.array([64, 64, 64])
            batch_frames.append(img_gpu)
        
        return batch_frames
    
    # Process frames more efficiently - larger batches, less GPU memory transfers
    batch_size = min(240, max(60, total_frames // 8))  # Bigger batches for efficiency
    
    with tqdm(total=total_frames, desc="🎵 GPU FFT Processing", unit="frames") as pbar:
        for start_frame in range(0, total_frames, batch_size):
            end_frame = min(start_frame + batch_size, total_frames)
            batch_indices = list(range(start_frame, end_frame))
            
            # Process entire batch on GPU without individual transfers
            batch_frames = process_frame_batch(batch_indices)
            if batch_frames:
                meter_frames_gpu.extend(batch_frames)
            pbar.update(len(batch_indices))
    
    print(f"   ✅ Generated {total_frames} waveform frames on GPU")
    result = cp.stack(meter_frames_gpu)
    
    # Cache the result
    try:
        cache_data = {
            'cache_key': cache_key,
            'waveform_frames': cp.asnumpy(result)  # Convert to numpy for pickling
        }
        with open(cache_file, 'wb') as f:
            pickle.dump(cache_data, f)
        print(f"   💾 Cached waveform to {cache_file.name}")
    except Exception as e:
        print(f"   ⚠️  Failed to cache waveform: {e}")
    
    return result

@lru_cache(maxsize=1000)
def _cached_mote_positions(t_discrete: int, width: int, height: int, num_motes: int):
    """Cache mote positions for repeated time values."""
    t = t_discrete / 100.0  # Convert back to float
    
    mote_ids = cp.arange(num_motes, dtype=cp.float32)
    seeds = mote_ids * 2.39996  # Golden angle
    speeds = 0.3 + (mote_ids % 5) * 0.15
    angles = (t * speeds + seeds) % (2 * cp.pi)
    
    base_x = mote_ids * width / num_motes
    base_y = (mote_ids * 73) % height
    
    orbit_radius = 40 + (mote_ids % 3) * 15
    mote_x = base_x + orbit_radius * cp.cos(angles)
    mote_y = base_y + orbit_radius * cp.sin(angles)
    
    pulse_phase = t * 3 + mote_ids * 0.8
    brightness = 0.4 + 0.3 * cp.sin(pulse_phase)
    
    return mote_x, mote_y, brightness

def create_floating_motes_gpu(width: int, height: int, t: float, duration: float) -> cp.ndarray:
    """CUDA-accelerated floating digital motes with simple pulsing circles."""
    
    # Create GPU arrays
    frame = cp.zeros((height, width, 3), dtype=cp.uint8)
    
    # Mote parameters - precomputed for efficiency
    num_motes = 25
    mote_radius = 8  # Simple circle radius
    
    # Use cached positions for performance
    t_discrete = int(t * 100)  # Discretize time for caching
    mote_x, mote_y, brightness = _cached_mote_positions(t_discrete, width, height, num_motes)
    
    # Amber color intensities
    red_intensity = (255 * brightness * 0.9).astype(cp.uint8)
    green_intensity = (180 * brightness).astype(cp.uint8) 
    blue_intensity = (40 * brightness * 0.4).astype(cp.uint8)
    
    # Draw circles using GPU-optimized approach
    for i in range(num_motes):
        cx, cy = int(mote_x[i]), int(mote_y[i])
        if 0 <= cx < width and 0 <= cy < height:
            # Simple filled circle using vectorized operations
            y_range = cp.arange(max(0, cy - mote_radius), min(height, cy + mote_radius + 1))
            x_range = cp.arange(max(0, cx - mote_radius), min(width, cx + mote_radius + 1))
            
            # Create coordinate grids
            yy, xx = cp.meshgrid(y_range, x_range, indexing='ij')
            
            # Distance from center
            dist_sq = (xx - cx)**2 + (yy - cy)**2
            circle_mask = dist_sq <= mote_radius**2
            
            # Anti-aliasing for smooth edges
            dist = cp.sqrt(dist_sq)
            alpha = cp.where(dist <= mote_radius - 1, 1.0, 
                           cp.where(dist <= mote_radius, mote_radius - dist, 0.0))
            
            if cp.any(circle_mask):
                # Apply color with alpha blending (additive)
                y_coords = yy[circle_mask]
                x_coords = xx[circle_mask]
                alpha_vals = alpha[circle_mask]
                
                # Additive blending for glow effect
                frame[y_coords, x_coords, 0] = cp.minimum(255, 
                    frame[y_coords, x_coords, 0] + (red_intensity[i] * alpha_vals).astype(cp.uint8))
                frame[y_coords, x_coords, 1] = cp.minimum(255,
                    frame[y_coords, x_coords, 1] + (green_intensity[i] * alpha_vals).astype(cp.uint8))  
                frame[y_coords, x_coords, 2] = cp.minimum(255,
                    frame[y_coords, x_coords, 2] + (blue_intensity[i] * alpha_vals).astype(cp.uint8))
    
    return frame

def create_scrolling_text_video(text: str, video_duration: float, art_path: Path, audio_file: Path, lead_in_time: float, audio_duration: float) -> VideoClip:
    """Create text video showing current line with word highlighting."""
    print(f"📜 Creating current-line text video with word highlighting...")
    
    width, height = VIDEO_CONFIG['resolution']
    fps = VIDEO_CONFIG['fps']
    
    # Load background art and prepare for zoom animation (starts at 130%, ends at 100%)
    try:
        original_bg = Image.open(art_path)
        
        # Create larger image for zoom animation (130% size)
        zoom_width = int(width * 1.3)
        zoom_height = int(height * 1.3)
        bg_img_large = original_bg.resize((zoom_width, zoom_height), Image.Resampling.LANCZOS)
        
        # Apply semi-transparent overlay for text readability
        overlay = Image.new('RGBA', (zoom_width, zoom_height), (0, 0, 0, 180))
        bg_img_large = Image.alpha_composite(bg_img_large.convert('RGBA'), overlay)
        bg_img_large = bg_img_large.convert('RGB')
        
        # Also prepare the final size version for reference
        bg_img_final = original_bg.resize((width, height), Image.Resampling.LANCZOS)
        bg_img_final = Image.alpha_composite(bg_img_final.convert('RGBA'), 
                                           Image.new('RGBA', (width, height), (0, 0, 0, 180)))
        bg_img_final = bg_img_final.convert('RGB')
        
    except Exception as e:
        print(f"⚠️  Could not load art, using gradient background: {e}")
        bg_img_large = create_gradient_background(int(width * 1.3), int(height * 1.3))
        bg_img_final = create_gradient_background(width, height)
    
    # Prepare text and organize by lines with word timing
    clean_text = clean_text_for_video(text)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", VIDEO_CONFIG['font_size'])
    except:
        font = ImageFont.load_default()
    
    # Split into lines and detect ACTUAL speech timing from audio
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    total_words = sum(len(line.split()) for line in lines)
    
    # Get EXACT word timings from audio using Whisper
    print(f"🔍 Getting exact word timings from audio...")
    whisper_word_timings = get_exact_word_timings_from_audio(audio_file)
    
    # Debug: Show first 5 word timings for validation
    print(f"   🔍 WORD TIMING VALIDATION (first 5 words):")
    for i, timing in enumerate(whisper_word_timings[:5]):
        print(f"      {i+1}: '{timing['word']}' [{timing['start']:.2f}s - {timing['end']:.2f}s]")
    print(f"   📊 Total words detected: {len(whisper_word_timings)}")
    
    # Check if we have cached text layout
    text_cache_file = VIDEO_CONFIG['cache_dir'] / "text_layouts" / f"{audio_file.stem}_layout.pkl"
    text_stats = audio_file.stat()
    text_cache_key = f"{audio_file.name}_{text_stats.st_size}_{len(clean_text)}_{len(whisper_word_timings)}"
    
    word_groups = None
    if text_cache_file.exists():
        try:
            with open(text_cache_file, 'rb') as f:
                cached_text_data = pickle.load(f)
            if cached_text_data.get('cache_key') == text_cache_key:
                print(f"   📋 Loading cached text layout...")
                word_groups = cached_text_data['word_groups']
        except Exception as e:
            print(f"   ⚠️  Text cache read failed: {e}")
    
    if word_groups is None:
        print(f"   📝 Creating text layout...")
        # Create sliding window groups with 5 words (2 left + active + 2 right) for balanced display
        word_groups = []
    
    # Create overlapping groups so each word can be centered with 2 words on each side
    for i in range(len(whisper_word_timings)):
        # Create a window of up to 5 words centered on word i
        start_idx = max(0, i - 2)  # 2 words before (or start of text)
        end_idx = min(len(whisper_word_timings), i + 3)  # 2 words after + current word
        
        group_words = whisper_word_timings[start_idx:end_idx]
        active_word_index = i - start_idx  # Index of the active word within this group
        
        word_groups.append({
            'words': [
                {
                    'text': w['word'],
                    'start_time': w['start'],  # Keep original timings
                    'end_time': w['end'],      # Keep original timings
                    'confidence': w['confidence']
                } for w in group_words
            ],
            'start_time': whisper_word_timings[i]['start'],  # Keep original start time
            'end_time': whisper_word_timings[i]['end'],      # Keep original end time
            'active_word_index': active_word_index         # Which word in the group is active
        })
    
        # Cache the text layout
        try:
            cache_data = {
                'cache_key': text_cache_key,
                'word_groups': word_groups
            }
            with open(text_cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            print(f"   💾 Cached text layout to {text_cache_file.name}")
        except Exception as e:
            print(f"   ⚠️  Failed to cache text layout: {e}")
    
    print(f"   📝 Using {len(word_groups)} sliding window groups for balanced display")
    line_data = word_groups
    
    # Create text frames with progress tracking
    frame_count = [0]  # Use list to allow modification in nested function
    total_expected_frames = int(video_duration * fps)
    
    # Pre-cache zoom frames for performance
    zoom_cache = {}
    zoom_steps = 100  # Number of pre-computed zoom levels
    
    for i in range(zoom_steps):
        progress = i / (zoom_steps - 1)
        current_zoom = 1.3 - (0.3 * progress)
        
        if current_zoom > 1.0:
            crop_width = int(width / current_zoom)
            crop_height = int(height / current_zoom)
            crop_x = (int(width * 1.3) - crop_width) // 2
            crop_y = (int(height * 1.3) - crop_height) // 2
            
            cropped = bg_img_large.crop((crop_x, crop_y, crop_x + crop_width, crop_y + crop_height))
            frame = cropped.resize((width, height), Image.Resampling.LANCZOS)
            zoom_cache[i] = np.array(frame)
        else:
            zoom_cache[i] = np.array(bg_img_final)
    
    def make_frame(t):
        # Update progress every few frames
        frame_count[0] += 1
        if frame_count[0] % (fps * 2) == 0:  # Every 2 seconds
            progress = (frame_count[0] / total_expected_frames) * 100
            print(f"   📹 Rendering frames: {progress:.1f}% ({frame_count[0]}/{total_expected_frames} frames)")
        
        # Use pre-cached zoom frame
        zoom_progress = min(0.99, t / video_duration)  # Ensure we don't exceed cache bounds
        cache_index = int(zoom_progress * (zoom_steps - 1))
        frame_array = zoom_cache[cache_index]
        
        # Add GPU-accelerated floating digital motes overlay  
        motes_gpu = create_floating_motes_gpu(width, height, t, video_duration)
        
        # Convert frame to GPU for efficient blending
        frame_gpu = cp.asarray(frame_array)
        
        # GPU-accelerated additive blending
        frame_gpu = cp.clip(frame_gpu + motes_gpu, 0, 255)
        
        # Convert back to PIL Image (only transfer from GPU when needed)
        frame = Image.fromarray(cp.asnumpy(frame_gpu).astype(np.uint8))
        draw = ImageDraw.Draw(frame)
        
        # Find the current word being spoken
        # Convert video time to audio time by subtracting lead_in_time
        audio_time = t - lead_in_time
        current_word = None
        
        # Debug: Print timing info every 5 seconds for validation
        if int(t * 2) % 10 == 0:  # Every 5 seconds
            print(f"   🔍 TEXT TIMING at video_time={t:.2f}s: audio_time={audio_time:.2f}s, in_audio_range={0 <= audio_time <= audio_duration}")
            if 0 <= audio_time <= audio_duration:
                active_words = [w for w in whisper_word_timings if w['start'] <= audio_time <= w['end']]
                if active_words:
                    print(f"      Active words: {[w['word'] for w in active_words]}")
                else:
                    print(f"      No active words at audio_time {audio_time:.2f}s")
        
        if 0 <= audio_time <= audio_duration:
            for timing in whisper_word_timings:
                # Use original whisper timings directly with audio_time
                if timing['start'] <= audio_time <= timing['end']:
                    current_word = timing['word'].strip()
                    break
            
            # If no current word, show the last spoken word
            if not current_word:
                for timing in reversed(whisper_word_timings):
                    if timing['end'] <= audio_time:
                        current_word = timing['word'].strip()
                        break

        # Display only the current word, centered on screen
        if current_word:
            # Calculate position to center the word
            bbox = draw.textbbox((0, 0), current_word, font=font)
            word_width = bbox[2] - bbox[0]
            word_height = bbox[3] - bbox[1]
            
            x = (width - word_width) // 2
            y = (height - word_height) // 2 - 100  # Slightly above center
            
            # Calculate fade level for silence periods
            fade_alpha = 1.0
            if 0 <= audio_time <= audio_duration:
                # During audio period - check if currently speaking
                if not any(timing['start'] <= audio_time <= timing['end'] for timing in whisper_word_timings):
                    # We're in a silence period, check how long since last word
                    last_word_end = max((timing['end'] for timing in whisper_word_timings if timing['end'] <= audio_time), default=0)
                    time_since_last = audio_time - last_word_end
                    if time_since_last > 2.0:  # Start fading after 2 seconds of silence
                        fade_factor = max(0.3, 1.0 - (time_since_last - 2.0) / 3.0)  # Fade over 3 seconds to 30%
                        fade_alpha = fade_factor
            else:
                # During lead-in or lead-out - fade to very dim
                fade_alpha = 0.2
            
            # Get the actual text bounding box at the final position for proper centering
            actual_bbox = draw.textbbox((x, y), current_word, font=font)
            
            # Add padding around the actual text bounds
            padding = 30
            bg_left = actual_bbox[0] - padding
            bg_right = actual_bbox[2] + padding
            bg_top = actual_bbox[1] - padding
            bg_bottom = actual_bbox[3] + padding
            
            # Draw fitted background rectangle
            bg_alpha = int(180 * fade_alpha)
            bg_color = (0, 0, 0, bg_alpha)
            
            bg_overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            bg_draw = ImageDraw.Draw(bg_overlay)
            bg_draw.rectangle([bg_left, bg_top, bg_right, bg_bottom], fill=bg_color)
            
            frame = Image.alpha_composite(frame.convert('RGBA'), bg_overlay).convert('RGB')
            draw = ImageDraw.Draw(frame)
            
            # Determine if word is currently being spoken
            is_speaking = (0 <= audio_time <= audio_duration and 
                          any(timing['start'] <= audio_time <= timing['end'] for timing in whisper_word_timings if timing['word'].strip() == current_word))
            
            if is_speaking:
                # Currently speaking word - bright amber highlight
                base_word_color = (255, 200, 50)  # Bright amber
                base_shadow_color = (120, 60, 0)  # Dark amber shadow
            else:
                # Not currently speaking - white
                base_word_color = (255, 255, 255)  # White
                base_shadow_color = (80, 80, 80)   # Gray shadow
            
            # Apply fade during silence
            word_color = tuple(int(c * fade_alpha) for c in base_word_color)
            shadow_color = tuple(int(c * fade_alpha) for c in base_shadow_color)
            
            # Draw word shadow for better visibility
            draw.text((x + 3, y + 3), current_word, font=font, fill=shadow_color)
            # Draw main word
            draw.text((x, y), current_word, font=font, fill=word_color)
        
        return np.array(frame)
    
    return VideoClip(make_frame, duration=video_duration)

def create_gradient_background(width: int, height: int) -> Image.Image:
    """Create amber gradient background."""
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    for y in range(height):
        # Create amber gradient
        ratio = y / height
        r = int(20 + ratio * 100)
        g = int(10 + ratio * 60)
        b = int(5 + ratio * 20)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return img

def clean_text_for_video(text: str) -> str:
    """Clean and format text for video display."""
    # Remove markdown
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # Format paragraphs
    paragraphs = text.split('\n\n')
    formatted_lines = []
    
    for para in paragraphs:
        para = para.strip()
        if para:
            # Word wrap
            words = para.split()
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                if len(test_line) > 80:  # Approximate character limit
                    if line:
                        formatted_lines.append(line)
                    line = word
                else:
                    line = test_line
            if line:
                formatted_lines.append(line)
            formatted_lines.append("")  # Paragraph break
    
    return '\n'.join(formatted_lines)

def create_chapter_video(chapter_file: Path, audio_file: Path, art_dir: Path, output_dir: Path) -> Path:
    """Create video for a single chapter."""
    # Output path
    output_file = output_dir / f"{chapter_file.stem}.mp4"
    
    # Check if video already exists
    if output_file.exists():
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"⏭️  Skipping {chapter_file.stem} - video already exists ({size_mb:.1f} MB)")
        return output_file
    
    print(f"🎬 Creating video for {chapter_file.stem}...")
    
    # Read chapter content
    print("   📄 Loading chapter content...")
    content = chapter_file.read_text(encoding='utf-8')
    
    # Determine art file
    print("   🎨 Setting up artwork...")
    art_file = art_dir / "chapter_1.png"  # Default chapter art
    if chapter_file.stem == "foreword":
        art_file = art_dir / "foreword.png"
    elif chapter_file.stem == "epilogue":
        art_file = art_dir / "epilogue.png"
    elif chapter_file.stem.startswith("chapter_"):
        chapter_num = chapter_file.stem.split("_")[1]
        specific_art = art_dir / f"chapter_{chapter_num}.png"
        if specific_art.exists():
            art_file = specific_art
    
    # Load audio to get duration
    print("   🎵 Analyzing audio...")
    audio_data, sample_rate = sf.read(str(audio_file))
    audio_duration = len(audio_data) / sample_rate
    
    # Add lead-in and lead-out pauses
    lead_in = VIDEO_CONFIG['lead_in_pause']
    lead_out = VIDEO_CONFIG['lead_out_pause']
    video_duration = lead_in + audio_duration + lead_out
    
    print(f"   ⏱️  Audio duration: {audio_duration:.1f}s ({audio_duration/60:.1f} minutes)")
    print(f"   ⏱️  Video duration: {video_duration:.1f}s (with {lead_in:.1f}s lead-in + {lead_out:.1f}s lead-out)")
    print(f"   🖼️  Using artwork: {art_file.name}")
    
    # Load background image for both text and waveform
    print("   🖼️  Processing background image...")
    bg_img = Image.open(art_file)
    bg_img = bg_img.resize(VIDEO_CONFIG['resolution'], Image.Resampling.LANCZOS)
    bg_img_np = np.array(bg_img.convert("RGB"))
    
    # Create text video
    print("   📝 Creating text video layer...")
    text_video = create_scrolling_text_video(content, video_duration, art_file, audio_file, lead_in, audio_duration)
    
    # Waveform disabled - background needs to be dynamic
    print("   🔇 Waveform visualization disabled (dynamic background incompatible with caching)")
    waveform_video = None
    
    # Load audio - keep it simple and cut it cleanly
    audio_clip = AudioFileClip(str(audio_file)).subclip(0, audio_duration)
    
    # Debug: Validate audio timing
    print(f"   🔍 AUDIO TIMING VALIDATION:")
    print(f"      Original audio duration: {audio_duration:.2f}s")
    print(f"      Audio will start at: {lead_in:.2f}s (lead-in time)")
    print(f"      Audio will end at: {lead_in + audio_duration:.2f}s")
    print(f"      Total video duration: {video_duration:.2f}s")
    
    # Composite video layers
    width, height = VIDEO_CONFIG['resolution']
    
    # Combine elements - just background with text (no waveform)
    final_video = text_video
    
    # Add delayed audio
    final_video = final_video.set_audio(audio_clip)
    
    # Render with progress tracking
    print(f"   🎥 Rendering {output_file.name}...")
    mp4_output = output_file.with_suffix('.mp4')
    
    # Custom progress callback for MoviePy
    def progress_callback(t, total_duration):
        progress = (t / total_duration) * 100 if total_duration > 0 else 0
        if int(progress) % 5 == 0:  # Show every 5%
            print(f"      📼 Video encoding: {progress:.1f}% ({t:.1f}s/{total_duration:.1f}s)")
    
    # Optimized rendering settings for speed
    final_video.write_videofile(
        str(mp4_output),
        fps=VIDEO_CONFIG['fps'],
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',  # Fastest encoding preset
        ffmpeg_params=['-crf', '23'],  # Balanced quality/speed
        threads=min(16, cpu_count()),  # Use available CPU cores
        verbose=False,
        logger='bar',
        temp_audiofile='temp-audio.m4a',  # Use temp audio file
        remove_temp=True
    )
    
    print(f"✅ Video created: {mp4_output}")
    return mp4_output

def create_audiobook_videos():
    """Create video versions of the audiobook."""
    print("🎬 Digital Amber - Video Audiobook Creation")
    print("=" * 50)
    
    # Setup directories
    art_dir = use_local_art()
    audio_dir = Path("dist/audiobook_kokoro")
    video_output_dir = Path("dist/audiobook_videos")
    video_output_dir.mkdir(parents=True, exist_ok=True)
    story_dir = Path("story")
    
    # Check if audio exists
    if not audio_dir.exists():
        print("❌ Kokoro audio not found. Generate audio first.")
        return
    
    # Process all chapters
    video_files = []
    
    # Process foreword
    foreword_md = story_dir / "foreword.md"
    foreword_audio = audio_dir / "000_foreword.wav"
    
    if foreword_md.exists() and foreword_audio.exists():
        print(f"\n🎬 Creating foreword video...")
        video_file = create_chapter_video(foreword_md, foreword_audio, art_dir, video_output_dir)
        if video_file:
            video_files.append(video_file)
            size_mb = video_file.stat().st_size / (1024 * 1024)
            print(f"✅ Foreword: {video_file.name} ({size_mb:.1f} MB)")
    
    # Process all chapters (1-24) sequentially - one at a time
    chapter_range = range(1, 25)
    total_chapters = len(chapter_range)
    
    with tqdm(total=total_chapters, desc="🎬 Creating Chapter Videos", unit="chapter") as pbar:
        for i in chapter_range:
            chapter_md = story_dir / f"chapter_{i}.md"
            chapter_audio = audio_dir / f"{i:03d}_chapter_{i}.wav"
            
            if chapter_md.exists() and chapter_audio.exists():
                try:
                    print(f"\n🎬 Creating Chapter {i} video...")
                    video_file = create_chapter_video(chapter_md, chapter_audio, art_dir, video_output_dir)
                    if video_file:
                        video_files.append(video_file)
                        size_mb = video_file.stat().st_size / (1024 * 1024)
                        print(f"✅ Chapter {i}: {video_file.name} ({size_mb:.1f} MB)")
                except Exception as e:
                    print(f"❌ Chapter {i} failed: {e}")
            else:
                print(f"⚠️  Chapter {i} files not found: {chapter_md.name}, {chapter_audio.name}")
            
            pbar.update(1)
    
    # Process epilogue
    epilogue_md = story_dir / "epilogue.md"
    epilogue_audio = audio_dir / "999_epilogue.wav"
    
    if epilogue_md.exists() and epilogue_audio.exists():
        print(f"\n🎬 Creating epilogue video...")
        video_file = create_chapter_video(epilogue_md, epilogue_audio, art_dir, video_output_dir)
        if video_file:
            video_files.append(video_file)
            size_mb = video_file.stat().st_size / (1024 * 1024)
            print(f"✅ Epilogue: {video_file.name} ({size_mb:.1f} MB)")
    
    # Final summary
    if video_files:
        total_size_mb = sum(f.stat().st_size for f in video_files) / (1024 * 1024)
        print(f"\n🎉 Video generation complete!")
        print(f"📁 Total videos created: {len(video_files)}")
        print(f"📊 Total size: {total_size_mb:.1f} MB")
        print(f"📂 Output directory: {video_output_dir}")
    else:
        print("❌ No videos created")
        return
    
    # Skip combined video creation
    if False:
        print("\n🎞️  Creating combined audiobook video...")
        combined_clips = [VideoFileClip(str(vf)) for vf in video_files]
        
        final_video = concatenate_videoclips(combined_clips, method="compose")
        
        # Output as MP4 format (WebP video not well supported)
        mp4_output = video_output_dir / "digital_amber_audiobook_video.mp4"
        
        final_video.write_videofile(
            str(mp4_output),
            fps=VIDEO_CONFIG['fps'],
            codec='libx264',
            audio_codec='aac',
            verbose=False,
            logger=None
        )
        
        print(f"🎉 Audiobook video complete!")
        print(f"📁 Output: {video_output_dir}")
        print(f"🎬 Video file: {mp4_output.name}")
        print(f"📊 Chapters: {len(video_files)}")
        
        # Show file size
        size_mb = mp4_output.stat().st_size / (1024 * 1024)
        print(f"📈 File size: {size_mb:.1f} MB")
        
        # Clean up individual chapter videos if desired
        # for vf in video_files:
        #     vf.unlink()
    
    else:
        print("❌ No videos created")

if __name__ == "__main__":
    create_audiobook_videos()