# cinematic_pipeline.py — TRUE Cinematic Video Production
# Rebuilt from scratch with: per-scene sync, sidechain ducking, quality gates
# Now with STOCK VIDEO support via Pexels API!

import os, sys, json, math, subprocess, textwrap, logging, random, shutil, base64, io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from enum import Enum

import numpy as np
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from moviepy.editor import (
    AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip,
    ColorClip, CompositeAudioClip, concatenate_videoclips
)
from moviepy.video.VideoClip import VideoClip
from moviepy.video.fx.all import fadein, fadeout
from openai import OpenAI
import requests

# Stock video integration
try:
    from stock_videos import StockVideoFetcher
    STOCK_VIDEO_AVAILABLE = True
except ImportError:
    STOCK_VIDEO_AVAILABLE = False

# API Usage Tracking
try:
    from api_usage_tracker import get_tracker, reset_tracker, get_usage_summary, APIUsage
    API_TRACKING_AVAILABLE = True
except ImportError:
    API_TRACKING_AVAILABLE = False
    def get_tracker(): return None
    def reset_tracker(): return None
    def get_usage_summary(): return {}

# Video effects module
try:
    from video_effects import (
        apply_all_effects, apply_film_grain, apply_vignette,
        apply_color_grade, create_light_leak_overlay
    )
    VIDEO_EFFECTS_AVAILABLE = True
except ImportError:
    VIDEO_EFFECTS_AVAILABLE = False

# ══════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════

load_dotenv()

# Paths
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"
(ASSETS / "bgm").mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format="🎬 %(levelname)s | %(message)s")
log = logging.getLogger("cinematic")

# API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    log.error("OPENAI_API_KEY missing"); sys.exit(1)
client = OpenAI(api_key=OPENAI_API_KEY, timeout=180)

# Models
IMAGE_MODEL = "dall-e-3"
SCRIPT_MODEL = "gpt-4o"
TTS_MODEL = "gpt-4o-mini-tts"  # Most natural sounding
TTS_VOICE = "nova"  # Warm, expressive, human-like female voice
# Alternative voices: "alloy" (neutral), "fable" (British), "shimmer" (expressive female)

# Canvas
WIDTH, HEIGHT = 1080, 1920
FPS = 60  # NON-NEGOTIABLE

# FFmpeg - find the executable robustly
import imageio_ffmpeg

def get_ffmpeg_path():
    """Find FFmpeg executable."""
    # Try environment variable first
    env_path = os.getenv("FFMPEG_LOCAL")
    if env_path and Path(env_path).exists():
        return env_path
    # Try imageio_ffmpeg
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except:
        pass
    # Try PATH
    path_ffmpeg = shutil.which("ffmpeg")
    if path_ffmpeg:
        return path_ffmpeg
    # Give up - will error later
    return "ffmpeg"

FFMPEG = get_ffmpeg_path()
log.info(f"Using FFmpeg: {FFMPEG}")

# Font
FONT_PATH = r"C:\Windows\Fonts\arialbd.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"

# ══════════════════════════════════════════════════════════════
# UTILITIES
# ══════════════════════════════════════════════════════════════

def to_rgb_uint8(arr):
    """Ensure MoviePy-safe frame."""
    if not isinstance(arr, np.ndarray):
        arr = np.array(arr)
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    if arr.shape[-1] == 4:
        arr = arr[..., :3]
    return np.clip(arr, 0, 255).astype(np.uint8)

def get_audio_duration(path: Path) -> float:
    """Get exact audio duration using MoviePy (more reliable than ffprobe)."""
    try:
        clip = AudioFileClip(str(path))
        dur = clip.duration
        clip.close()
        return dur
    except Exception as e:
        log.warning(f"Could not get audio duration: {e}")
        return 3.0  # Fallback

def lerp(a, b, t): return a + (b - a) * t
def ease_out_cubic(t): return 1 - pow(1 - t, 3)

# Pillow compatibility
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# ══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════

class Emotion(Enum):
    EPIC = "epic"
    CALM = "calm"
    INTENSE = "intense"
    MYSTERIOUS = "mysterious"
    UPLIFTING = "uplifting"
    NEUTRAL = "neutral"

class CameraMove(Enum):
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    ZOOM_PULSE = "zoom_pulse"  # Subtle breathing zoom
    FLOAT = "float"  # Gentle floating movement

@dataclass
class Scene:
    """A single scene with locked audio-visual sync."""
    index: int
    text: str
    emotion: Emotion
    camera: CameraMove
    audio_path: Optional[Path] = None
    image_path: Optional[Path] = None
    video_path: Optional[Path] = None  # Stock video (if available)
    duration: float = 0.0  # LOCKED to audio duration
    use_video: bool = False  # True if using stock video

@dataclass
class Script:
    title: str
    hook: str
    beats: List[str]
    cta: str
    theme: str = "epic"
    emotions: List[str] = field(default_factory=list)

# ══════════════════════════════════════════════════════════════
# EMOTION → CAMERA MAPPING (INTENTIONAL, NOT RANDOM)
# ══════════════════════════════════════════════════════════════

EMOTION_CAMERA_MAP = {
    Emotion.EPIC: CameraMove.DOLLY_IN,
    Emotion.CALM: CameraMove.FLOAT,  # Gentle floating for calm scenes
    Emotion.INTENSE: CameraMove.PAN_RIGHT,
    Emotion.MYSTERIOUS: CameraMove.CRANE_UP,
    Emotion.UPLIFTING: CameraMove.CRANE_DOWN,  # Rising feeling
    Emotion.NEUTRAL: CameraMove.ZOOM_PULSE,  # Subtle breathing
}

def get_camera_for_emotion(emotion: Emotion) -> CameraMove:
    """Intentional camera selection based on emotion."""
    return EMOTION_CAMERA_MAP.get(emotion, CameraMove.DOLLY_IN)

# ══════════════════════════════════════════════════════════════
# SCRIPT GENERATION
# ══════════════════════════════════════════════════════════════

SCRIPT_SYSTEM = """You are an ELITE Hollywood screenwriter and documentary filmmaker.
Create CINEMATIC MASTERPIECES that captivate from the first word.

═══ NARRATIVE ARCHITECTURE ═══
1. HOOK (5-8 words): A statement so powerful it stops the scroll. Use intrigue, bold claims, or visceral imagery.
2. BEATS (5 scenes): Build a emotional arc - START intriguing, ESCALATE tension, PEAK with revelation, RESOLVE with meaning.
3. CTA: End with lasting resonance - a thought that echoes.

═══ STYLE RULES ═══
• DOCUMENTARY topics (places, people, events, history): Use AUTHORITATIVE narration. Facts laced with wonder. "This is where gods once walked..."
• ABSTRACT topics (concepts, emotions, future): Use POETIC narrative. Metaphors, sensory language. "Hope rises like smoke..."
• PRODUCT/TECH topics: Use VISIONARY tone. Bold futures, transformation language.

═══ WRITING CRAFT ═══
• SHORT punchy sentences for impact. Long flowing for atmosphere.
• ACTIVE VOICE always. "The empire CRUMBLED" not "was destroyed"
• SENSORY details: Describe what we SEE, HEAR, FEEL
• AVOID: clichés, "in a world where", generic phrases
• RHYTHM: Vary sentence length. Short. Punchy. Then let a longer sentence breathe and flow like water.

═══ VISUAL PROMPTS ═══
Each beat MUST have a concrete, filmable image. Describe:
- SUBJECT: WHO/WHAT is in frame (be specific)
- ACTION: What are they DOING
- ENVIRONMENT: WHERE, time of day, weather
- MOOD: Lighting, colors, atmosphere

BAD: "Technology advancing" 
GOOD: "A scientist's hands adjust holographic code, blue light dancing across her face in a dark lab, rain on windows behind"

Return STRICT JSON:
{
  "title": "Compelling Title (3-5 words, no clichés)",
  "hook": "Explosive opening that demands attention",
  "beats": ["Scene 1 narration", "Scene 2 narration", "Scene 3 narration", "Scene 4 narration", "Scene 5 narration"],
  "cta": "Powerful closing that resonates",
  "theme": "epic|documentary|mysterious|inspiring|intense|peaceful",
  "emotions": ["emotion for beat 1", "emotion for beat 2", "emotion for beat 3", "emotion for beat 4", "emotion for beat 5"]
}

WORD COUNT: 140-180 total. Quality over quantity. Every word EARNS its place."""

def generate_script(topic: str) -> Script:
    """Generate a cinematic script."""
    log.info("📝 Generating script...")
    resp = client.chat.completions.create(
        model=SCRIPT_MODEL,
        temperature=0.75,
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM},
            {"role": "user", "content": f'Create a CINEMATIC MASTERPIECE about: "{topic}"'}
        ],
        response_format={"type": "json_object"}
    )
    # ... (rest of function is unchanged implicitly by replace_file_content if I don't touch it, but I am replacing the block)
    # Wait, I need to include the rest of the function if I replace the start.
    # Actually, I can just replace SCRIPT_SYSTEM definition and the start of the function.
    
    data = json.loads(resp.choices[0].message.content)
    return Script(**data)

# ... (skip to create_title_clip) 



    data = json.loads(resp.choices[0].message.content)
    data.setdefault("emotions", ["epic"] * len(data.get("beats", [])))
    return Script(**{k: v for k, v in data.items() if k in Script.__dataclass_fields__})

# ══════════════════════════════════════════════════════════════
# PER-SCENE TTS (CRITICAL FOR SYNC)
# ══════════════════════════════════════════════════════════════

def generate_scene_tts(text: str, output_path: Path, emotion: str = "epic") -> Tuple[Path, float]:
    """Generate TTS with CINEMATIC human-like emotional delivery."""
    log.info(f"🎤 TTS: {text[:40]}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    mp3_path = output_path.with_suffix(".mp3")
    
    # CINEMATIC voiceover instructions - like a movie trailer narrator
    # These are designed to produce AWARD-WINNING documentary narration
    emotion_instructions = {
        "epic": """You are a LEGENDARY narrator like Morgan Freeman meets David Attenborough.
DELIVERY STYLE:
- Speak with DEEP gravitas and commanding presence
- Use DRAMATIC PAUSES between key phrases (count 1-2 beats of silence)
- Let important words LAND with weight - slow down for emphasis
- Build INTENSITY through the sentence, crescendo to powerful moments
- Speak at 0.85x normal speed - this is CINEMA, not a podcast
- Your voice should give chills. Every word matters.
- Breathe... Pause... Deliver with purpose.""",
        
        "calm": """You are narrating a BBC nature documentary at golden hour.
DELIVERY STYLE:
- Speak SOFTLY, gently, with warmth and deep serenity
- Let silences BREATHE - pause 2 beats between thoughts
- Your voice should feel like a warm embrace, a cozy blanket
- Slow, measured, unhurried - let each word settle
- Whisper-soft in places, like sharing a beautiful secret
- Float through the words like clouds drifting across sky.""",
        
        "intense": """You are narrating an action thriller movie trailer.
DELIVERY STYLE:  
- Speak with CONTROLLED URGENCY - tension in every syllable
- STACCATO delivery for impact words - punch them hard
- Build tension through pacing - speed up then SUDDEN PAUSE
- Some words should HIT LIKE THUNDER
- Edge-of-seat energy - make them feel the adrenaline
- Breathless at times, powerful always.""",
        
        "mysterious": """You are narrating a noir mystery film at midnight.
DELIVERY STYLE:
- Speak in a HUSHED, intriguing near-whisper
- Create SUSPENSE with every pause - let silence build tension
- Darkness and wonder seep through your voice
- Enigmatic delivery - you know secrets you're not telling
- Some words barely audible... others cut through silence
- The truth hides in the shadows of your pauses.""",
        
        "uplifting": """You are narrating an Oscar-winning inspirational documentary.
DELIVERY STYLE:
- Start GENTLE, build to POWERFUL triumph
- Your voice should LIFT SPIRITS, inspire hope
- Warmth that spreads through every word
- Build emotional crescendo - from whisper to proclamation
- Pause before the most inspiring moments - let hope SWELL
- Make them believe in something greater.""",
        
        "neutral": """You are a trusted professional documentary narrator.
DELIVERY STYLE:
- Speak CLEARLY with natural warmth and quiet authority
- Well-paced, articulate - the voice of knowledge
- Professional but engaging - trustworthy guide
- Measured pauses for comprehension
- Steady, reliable, informative yet captivating."""
    }

    
    instruction = emotion_instructions.get(emotion, emotion_instructions["epic"])
    
    # Track API usage
    tracker = get_tracker()
    if tracker:
        tracker.log_openai_tts(len(text))
    
    try:
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=text,
            instructions=instruction,
        )
    except Exception as e:
        log.warning(f"Using fallback TTS: {e}")
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="nova",
            input=text,
        )
    
    with open(mp3_path, "wb") as f:
        f.write(response.read())
    
    # Convert to WAV with high quality
    cmd = [FFMPEG, "-y", "-i", str(mp3_path), "-ar", "48000", "-ac", "2", str(output_path)]
    subprocess.run(cmd, capture_output=True)
    mp3_path.unlink(missing_ok=True)
    
    # Get EXACT duration
    duration = get_audio_duration(output_path)
    log.info(f"   ✅ Duration: {duration:.2f}s")
    return output_path, duration

# ══════════════════════════════════════════════════════════════
# IMAGE GENERATION
# ══════════════════════════════════════════════════════════════

def generate_cinematic_prompt(text: str, emotion: Emotion, topic: str = "") -> str:
    """Generate ULTRA-CINEMATIC image prompt for Hollywood-quality visuals."""
    
    # Rich style mappings with specific cinematography details
    style_map = {
        Emotion.EPIC: {
            "lighting": "dramatic IMAX golden hour lighting, god rays piercing through clouds",
            "composition": "sweeping wide angle, rule of thirds, leading lines to hero subject",
            "colors": "rich warm highlights, deep cool shadows, teal-orange color grade",
            "atmosphere": "volumetric fog, particle dust in air, sense of scale and grandeur"
        },
        Emotion.CALM: {
            "lighting": "soft diffused natural light, gentle rim lighting on subject",
            "composition": "centered symmetry, lots of negative space, shallow depth of field",
            "colors": "muted pastels, soft blues and creams, low contrast harmony",
            "atmosphere": "peaceful, serene, bokeh background, dreamy gaussian blur"
        },
        Emotion.INTENSE: {
            "lighting": "high contrast chiaroscuro, dramatic rim light, stark shadows",
            "composition": "dutch angle, tight framing, dynamic diagonal lines",
            "colors": "saturated reds and blacks, neon accents, high vibrance",
            "atmosphere": "motion blur, rain effects, electric tension, adrenaline feel"
        },
        Emotion.MYSTERIOUS: {
            "lighting": "noir side lighting, single source dramatic shadows, silhouettes",
            "composition": "off-center framing, obscured elements, reflection shots",
            "colors": "desaturated cool tones, deep blues and purples, moonlight silver",
            "atmosphere": "fog, mist, smoke, hidden details, sense of unknown"
        },
        Emotion.UPLIFTING: {
            "lighting": "warm golden sunlight from behind, lens flares, halo effects",
            "composition": "low angle looking up, subject in center, expansive sky",
            "colors": "warm yellows, hopeful oranges, clean whites, vibrant greens",
            "atmosphere": "light rays, floating particles, sense of possibility and hope"
        },
        Emotion.NEUTRAL: {
            "lighting": "balanced three-point lighting, clean professional setup",
            "composition": "standard documentary framing, clear subject focus",
            "colors": "natural color balance, realistic tones, subtle enhancement",
            "atmosphere": "clean, professional, trustworthy, informative"
        },
    }
    
    style = style_map.get(emotion, style_map[Emotion.EPIC])
    
    return f"""ULTRA-CINEMATIC MASTERPIECE | 9:16 VERTICAL | 8K QUALITY

SCENE NARRATIVE: {text}
{f'TOPIC CONTEXT: {topic}' if topic else ''}

CINEMATOGRAPHY:
• LIGHTING: {style['lighting']}
• COMPOSITION: {style['composition']}
• COLOR PALETTE: {style['colors']}
• ATMOSPHERE: {style['atmosphere']}

TECHNICAL REQUIREMENTS:
- Roger Deakins-level lighting mastery
- Christopher Nolan IMAX film quality
- Anamorphic lens characteristics with subtle bokeh
- Film grain texture (fine, not digital noise)
- Ultra-sharp subject with smooth depth falloff
- Professional color grading applied

CRITICAL RULES:
- NO text, watermarks, UI elements, or logos anywhere
- NO phone/camera frames or device mockups
- Photo-realistic, NOT illustrated or painted
- Clear distinct subject in frame
- Professional photography composition"""



def generate_image(prompt: str, output_path: Path) -> Path:
    """Generate HD cinematic image."""
    log.info(f"🎨 Generating image (FALLBACK - no suitable stock video)...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Track API usage
    tracker = get_tracker()
    if tracker:
        tracker.log_openai_image()
    
    for attempt in range(3):
        try:
            resp = client.images.generate(
                model=IMAGE_MODEL,
                prompt=prompt,
                size="1024x1792",
                quality="hd" if attempt == 0 else "standard",
                n=1,
            )
            img_data = resp.data[0]
            if img_data.url:
                img_bytes = requests.get(img_data.url, timeout=60).content
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            else:
                img = Image.open(io.BytesIO(base64.b64decode(img_data.b64_json))).convert("RGB")
            
            # Resize to exact canvas
            img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
            
            # Apply cinematic enhancement
            img = enhance_cinematic(img)
            
            img.save(output_path, "JPEG", quality=98)
            log.info(f"   ✅ AI Image saved")
            return output_path
        except Exception as e:
            log.warning(f"   Attempt {attempt+1} failed: {e}")
    
    # Placeholder on failure
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 15))
    img.save(output_path, "JPEG")
    return output_path

# ══════════════════════════════════════════════════════════════
# STOCK VIDEO FETCHING (with GPT-powered contextual search)
# ══════════════════════════════════════════════════════════════

def generate_video_search_query(scene_text: str, emotion: str) -> str:
    """
    Use GPT to generate the PERFECT stock video search query
    that matches the scene's meaning and context.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap
            temperature=0.3,
            max_tokens=50,
            messages=[
                {
                    "role": "system",
                    "content": """You are a stock video search expert. Given a scene description and the overall TOPIC, 
generate the PERFECT 3-5 word search query for finding a matching stock video.

RULES:
- The TOPIC is your anchor. If topic is "Egypt", search for "Egypt pyramids" not just "sand".
- Focus on VISUAL elements that can be filmed.
- Use concrete nouns: nature, people, objects, places.
- NO quotes, just the search terms.
- Examples:
  Topic: "AI Future" | Scene: "The future is here" → "futuristic data center AI"
  Topic: "Egypt" | Scene: "Ancient gods ruled" → "Egypt pyramids ancient ruins"
  Topic: "Coffee" | Scene: "Morning ritual" → "pouring coffee cinematic morning"
"""
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}\nScene: \"{scene_text}\"\nEmotion: {emotion}\n\nGenerate search query:"
                }
            ]
        )
        query = response.choices[0].message.content.strip().strip('"')
        return query
    except Exception as e:
        log.warning(f"GPT query generation failed: {e}")
        return f"{topic} {emotion}"

def fetch_stock_video(scene_text: str, emotion: str, output_path: Path, topic: str = "") -> Optional[Path]:
    """
    Fetch a CONTEXTUALLY RELEVANT stock video from Pexels.
    Uses GPT to understand scene meaning and generate smart search queries based on TOPIC.
    PRIORITY: This is the PRIMARY visual source - AI images are fallback only.
    """
    if not STOCK_VIDEO_AVAILABLE:
        log.warning("   ⚠️ Pexels module not available")
        return None
    
    pexels_key = os.getenv("PEXELS_API_KEY")
    if not pexels_key:
        log.warning("   ⚠️ PEXELS_API_KEY not set - using AI images instead")
        return None
    
    tracker = get_tracker()
    
    try:
        fetcher = StockVideoFetcher(pexels_key)
        
        # Use GPT to generate a contextually relevant search query
        query = generate_video_search_query(scene_text, emotion, topic)
        log.info(f"🎥 PRIMARY SEARCH: '{query}' (Topic: '{topic}')")
        
        if tracker:
            tracker.log_pexels_search()
        
        # STRICT 9:16 portrait orientation
        video_url = fetcher.search_video(query, orientation="portrait", min_duration=5)
        
        # Fallback 1: Topic-focused query
        if not video_url:
            fallback1 = f"{topic} cinematic vertical"
            log.info(f"   → Fallback 1: '{fallback1}'")
            if tracker:
                tracker.log_pexels_search()
            video_url = fetcher.search_video(fallback1, orientation="portrait")
        
        # Fallback 2: Emotion-based generic query
        if not video_url:
            fallback2 = f"{emotion} cinematic nature"
            log.info(f"   → Fallback 2: '{fallback2}'")
            if tracker:
                tracker.log_pexels_search()
            video_url = fetcher.search_video(fallback2, orientation="portrait")
        
        if video_url:
            if tracker:
                tracker.log_pexels_download()
            log.info(f"   ✅ Found video - downloading...")
            return fetcher.download_video(video_url, output_path)
        else:
            log.warning(f"   ⚠️ No suitable video found for '{topic}' - will use AI image")
        
    except Exception as e:
        log.error(f"   ❌ Stock video fetch failed: {e}")
    
    return None

def enhance_cinematic(img: Image.Image) -> Image.Image:
    """Apply Hollywood-grade color grading."""
    # Sharpening
    img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=100, threshold=2))
    # Color boost
    img = ImageEnhance.Color(img).enhance(1.12)
    # Contrast
    img = ImageEnhance.Contrast(img).enhance(1.06)
    # Subtle vignette
    arr = np.array(img).astype(np.float32)
    y, x = np.ogrid[:HEIGHT, :WIDTH]
    cx, cy = WIDTH / 2, HEIGHT / 2
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = np.sqrt(cx**2 + cy**2)
    vignette = 1 - (dist / max_dist) * 0.25
    arr = arr * vignette[:, :, np.newaxis]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ══════════════════════════════════════════════════════════════
# AUDIO MASTERING (FFMPEG SIDECHAIN)
# ══════════════════════════════════════════════════════════════

def master_audio_hollywood(voice_paths: List[Path], bgm_path: Optional[Path], 
                           output_path: Path, total_duration: float) -> Path:
    """Professional audio mastering with sidechain ducking."""
    log.info("🎚️ Mastering audio with sidechain ducking...")
    
    # Concatenate all voice files first
    voice_concat = output_path.parent / "voice_concat.wav"
    
    # Create file list for concat
    list_file = output_path.parent / "voice_list.txt"
    with open(list_file, "w") as f:
        for vp in voice_paths:
            f.write(f"file '{vp.absolute()}'\n")
    
    # Concat voices
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
           "-c", "copy", str(voice_concat)]
    subprocess.run(cmd, capture_output=True)
    
    if bgm_path and bgm_path.exists():
        # SIDECHAIN DUCKING - Music ducks under voice
        cmd = [
            FFMPEG, "-y",
            "-i", str(voice_concat),
            "-i", str(bgm_path),
            "-filter_complex",
            # Voice EQ: cut rumble, boost presence
            "[0:a]equalizer=f=80:t=h:w=80:g=-3,equalizer=f=3000:t=q:w=2:g=2[voice];"
            # BGM: loop if needed, EQ to avoid clash, then sidechain compress
            f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total_duration},"
            "equalizer=f=200:t=q:w=1.5:g=-2,equalizer=f=3000:t=q:w=2:g=-3,"
            "volume=0.4[bgm];"
            # Sidechain compression: music ducks when voice is present
            "[bgm][voice]sidechaincompress=threshold=0.02:ratio=8:attack=5:release=200:makeup=1[ducked];"
            # Mix: voice louder
            "[ducked][voice]amix=inputs=2:weights=0.35 0.65:duration=first[mixed];"
            # Final limiting and loudness normalization
            "[mixed]alimiter=limit=0.95:attack=3:release=50,"
            "loudnorm=I=-14:TP=-1.0:LRA=7[out]",
            "-map", "[out]",
            "-ar", "48000", "-ac", "2",
            "-b:a", "320k",
            str(output_path)
        ]
    else:
        # Voice only - still apply EQ and limiting
        cmd = [
            FFMPEG, "-y",
            "-i", str(voice_concat),
            "-af",
            "equalizer=f=80:t=h:w=80:g=-3,equalizer=f=3000:t=q:w=2:g=2,"
            "alimiter=limit=0.95,loudnorm=I=-14:TP=-1.0:LRA=7",
            "-ar", "48000", "-ac", "2",
            "-b:a", "320k",
            str(output_path)
        ]
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        log.warning(f"Audio mastering warning: {result.stderr.decode()[:200]}")
        # Fallback: just use voice
        shutil.copy(voice_concat, output_path)
    
    log.info("   ✅ Audio mastered")
    return output_path

# ══════════════════════════════════════════════════════════════
# VIDEO CLIP CREATION
# ══════════════════════════════════════════════════════════════

def apply_camera_movement(img: Image.Image, camera: CameraMove, t: float, duration: float) -> Image.Image:
    """Apply intentional camera movement."""
    progress = min(max(t / max(duration, 0.001), 0), 1)
    eased = ease_out_cubic(progress)
    
    if camera == CameraMove.DOLLY_IN:
        scale = lerp(1.0, 1.12, eased)
        offset = (0, 0)
    elif camera == CameraMove.DOLLY_OUT:
        scale = lerp(1.12, 1.0, eased)
        offset = (0, 0)
    elif camera == CameraMove.PAN_RIGHT:
        scale = 1.15
        offset = (int(-60 * eased), 0)
    elif camera == CameraMove.PAN_LEFT:
        scale = 1.15
        offset = (int(60 * eased), 0)
    elif camera == CameraMove.CRANE_UP:
        scale = 1.10
        offset = (0, int(40 * eased))
    elif camera == CameraMove.CRANE_DOWN:
        scale = 1.10
        offset = (0, int(-40 * eased))
    elif camera == CameraMove.ZOOM_PULSE:
        # Subtle breathing zoom effect
        pulse = math.sin(progress * math.pi * 2) * 0.03
        scale = 1.05 + pulse
        offset = (0, 0)
    elif camera == CameraMove.FLOAT:
        # Gentle floating movement (combination of subtle pan and zoom)
        scale = 1.08
        float_x = int(math.sin(progress * math.pi) * 20)
        float_y = int(math.cos(progress * math.pi * 0.5) * 15)
        offset = (float_x, float_y)
    else:
        scale = 1.08
        offset = (0, 0)
    
    # Apply
    new_size = (int(WIDTH * scale), int(HEIGHT * scale))
    scaled = img.resize(new_size, Image.LANCZOS)
    
    # Center and offset
    x = (WIDTH - new_size[0]) // 2 + offset[0]
    y = (HEIGHT - new_size[1]) // 2 + offset[1]
    
    canvas = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
    canvas.paste(scaled, (x, y))
    return canvas

# ══════════════════════════════════════════════════════════════
# ATMOSPHERE & TRANSITION HELPERS
# ══════════════════════════════════════════════════════════════

def create_dust_overlay(t: float, duration: float, num_particles: int = 30) -> np.ndarray:
    """Create floating dust particles overlay for cinematic atmosphere."""
    overlay = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    # Seed based on duration to keep consistent particles
    np.random.seed(42)
    particles = []
    for _ in range(num_particles):
        x = np.random.randint(0, WIDTH)
        y = np.random.randint(0, HEIGHT)
        size = np.random.randint(2, 6)
        speed = np.random.uniform(0.3, 1.2)
        brightness = np.random.randint(180, 255)
        particles.append((x, y, size, speed, brightness))
    
    # Animate particles based on time
    progress = t / max(duration, 1)
    for (x, y, size, speed, brightness) in particles:
        # Slow drift upward
        new_y = int((y - speed * t * 30) % HEIGHT)
        new_x = int(x + math.sin(t + y) * 3) % WIDTH
        
        # Draw particle with slight glow
        for dx in range(-size, size+1):
            for dy in range(-size, size+1):
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= size:
                    px, py = (new_x + dx) % WIDTH, (new_y + dy) % HEIGHT
                    alpha = int(brightness * (1 - dist / size) * 0.4)
                    overlay[py, px] = [alpha, alpha, alpha]
    
    return overlay

def get_scene_transition(scene_index: int, total_scenes: int) -> str:
    """Select appropriate transition for scene position."""
    transitions = ["crossfade", "crossfade", "crossfade"]  # Default: smooth crossfades
    
    # Vary transitions based on position
    if scene_index == 0:
        return "crossfade"  # First scene: smooth entry
    elif scene_index == total_scenes - 1:
        return "crossfade"  # Last scene: smooth exit
    elif scene_index % 3 == 0:
        return "crossfade"  # Every 3rd: crossfade
    else:
        return "crossfade"  # Keep consistent for now (can add more later)
    
    return "crossfade"

def create_scene_clip(scene: Scene) -> VideoClip:
    """Create a clip for a scene - uses stock video or animated image."""
    dur = scene.duration
    
    if scene.use_video and scene.video_path and scene.video_path.exists():
        # Use stock video
        log.info(f"   🎥 Using stock video for scene {scene.index}")
        try:
            video = VideoFileClip(str(scene.video_path))
            
            # Resize to fit our canvas (9:16)
            # Calculate scaling to cover the frame
            video_aspect = video.w / video.h
            target_aspect = WIDTH / HEIGHT
            
            if video_aspect > target_aspect:
                # Video is wider, scale by height
                new_h = HEIGHT
                new_w = int(HEIGHT * video_aspect)
            else:
                # Video is taller, scale by width
                new_w = WIDTH
                new_h = int(WIDTH / video_aspect)
            
            video = video.resize((new_w, new_h))
            
            # Center crop to exact size
            x_center = (new_w - WIDTH) // 2
            y_center = (new_h - HEIGHT) // 2
            video = video.crop(x1=x_center, y1=y_center, x2=x_center+WIDTH, y2=y_center+HEIGHT)
            
            # Trim or loop to match audio duration
            if video.duration >= dur:
                video = video.subclip(0, dur)
            else:
                # Loop video to fill duration
                from moviepy.editor import concatenate_videoclips as concat_clips
                loops_needed = int(dur / video.duration) + 1
                video = concat_clips([video] * loops_needed).subclip(0, dur)
            # Apply cinematic effects to video frames
            if VIDEO_EFFECTS_AVAILABLE:
                def apply_effects(get_frame, t):
                    frame = get_frame(t)
                    return apply_all_effects(frame, t, dur, grain=True, vignette=True, color_grade="cinematic")
                video = video.fl(apply_effects)
            
            return video
            
        except Exception as e:
            log.warning(f"   ⚠️ Video processing failed: {e}, falling back to image")
    
    # Fallback: Animated image with Ken Burns + effects
    img = Image.open(scene.image_path).convert("RGB")
    
    def make_frame(t):
        frame = apply_camera_movement(img, scene.camera, t, dur)
        frame_array = to_rgb_uint8(np.array(frame))
        
        # Apply cinematic effects
        if VIDEO_EFFECTS_AVAILABLE:
            frame_array = apply_all_effects(frame_array, t, dur, grain=True, vignette=True, color_grade="cinematic")
        
        # Add floating dust particles for atmosphere (subtle blend)
        dust = create_dust_overlay(t, dur, num_particles=25)
        frame_array = np.clip(frame_array.astype(np.float32) + dust.astype(np.float32) * 0.3, 0, 255).astype(np.uint8)
        
        return frame_array
    
    clip = VideoClip(make_frame=make_frame, duration=dur)
    return clip

def create_caption_clip(text: str, duration: float, emotion: str = "epic") -> ImageClip:
    """Create PREMIUM Netflix-style animated caption."""
    # Word wrap with optimal line length
    wrapped = textwrap.fill(text, width=32)
    
    # Emotion-based accent colors
    accent_colors = {
        "epic": (255, 215, 0),      # Gold
        "calm": (135, 206, 235),    # Sky blue
        "intense": (255, 69, 0),    # Red-orange
        "mysterious": (138, 43, 226), # Purple
        "uplifting": (50, 205, 50),  # Lime green
        "neutral": (200, 200, 200)   # Silver
    }
    accent = accent_colors.get(emotion, accent_colors["epic"])
    
    # Smart font selection
    fonts = [
        r"C:\Windows\Fonts\segoeui.ttf",   # Modern UI font
        r"C:\Windows\Fonts\calibri.ttf",   # Clean
        FONT_PATH
    ]
    font_path = FONT_PATH
    for f in fonts:
        if Path(f).exists():
            font_path = f
            break
    
    try:
        font = ImageFont.truetype(font_path, 52)
    except:
        font = ImageFont.load_default()
    
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
    w, h = bbox[2] - bbox[0] + 80, bbox[3] - bbox[1] + 50
    
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Gradient-style background (dark to darker)
    for i in range(h):
        alpha = int(200 - (i / h) * 40)  # Subtle gradient
        draw.line([(0, i), (w, i)], fill=(10, 10, 20, alpha))
    
    # Rounded corners mask
    draw.rounded_rectangle([(0, 0), (w-1, h-1)], radius=16, outline=(*accent, 150), width=2)
    
    # Text shadow (multi-layer for depth)
    for offset in range(3, 0, -1):
        alpha = int(60 - offset * 15)
        draw.multiline_text((w//2 + offset, h//2 + offset), wrapped, font=font, 
                            fill=(0, 0, 0, alpha), anchor="mm", align="center")
    
    # Main text
    draw.multiline_text((w//2, h//2), wrapped, font=font,
                        fill=(255, 255, 255, 255), anchor="mm", align="center")
    
    clip = ImageClip(to_rgb_uint8(np.array(img))).set_duration(duration)
    clip = clip.set_position(("center", int(HEIGHT * 0.75)))
    return clip

def create_title_clip(title: str, duration: float = 3.0) -> CompositeVideoClip:
    """Create PREMIUM animated title intro."""
    # Smart font selection for impact
    fonts = [
        r"C:\Windows\Fonts\impact.ttf",     # Classic impact
        r"C:\Windows\Fonts\georgiab.ttf",   # Cinematic serif
        r"C:\Windows\Fonts\arialbd.ttf"     # Reliable fallback
    ]
    font_path = FONT_PATH
    for f in fonts:
        if Path(f).exists():
            font_path = f
            break

    try:
        font = ImageFont.truetype(font_path, 100)
    except:
        font = ImageFont.load_default()
    
    wrapped = textwrap.fill(title.upper(), width=12)
    
    # Create high-res canvas for crisp text
    # We create a larger image and downscale or use compatible size
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
    w, h = bbox[2] - bbox[0] + 100, bbox[3] - bbox[1] + 80
    
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Cinematic Multi-Layer Glow
    glow_color = (200, 200, 255) # Bluish glow
    for offset in range(8, 0, -2):
        alpha = int(20 - offset * 2)
        draw.multiline_text((w//2+offset, h//2+offset), wrapped, font=font, 
                          fill=(0, 0, 0, alpha + 30), anchor="mm", align="center")
        draw.multiline_text((w//2, h//2), wrapped, font=font,
                          fill=(*glow_color, alpha), anchor="mm", align="center")
    
    # Main Text (Crisp White)
    draw.multiline_text((w//2, h//2), wrapped, font=font,
                        fill=(255, 255, 255, 255), anchor="mm", align="center")
    
    # Convert to clip
    title_clip = ImageClip(to_rgb_uint8(np.array(img))).set_duration(duration)
    title_clip = title_clip.set_position("center")
    
    # Animation: Fade In + Subtle Scale Up (Zoom)
    # This requires MoviePy's resize. If specific version issue, we catch it.
    title_clip = title_clip.resize(lambda t: 1 + 0.08 * t) # Zoom in 8%
    
    title_clip = fadein(title_clip, 0.8)
    title_clip = fadeout(title_clip, 0.5)
    
    # Background: Dark Cinematic Blue/Black
    bg = ColorClip(size=(WIDTH, HEIGHT), color=(5, 8, 15)).set_opacity(0.95).set_duration(duration)
    
    return CompositeVideoClip([bg, title_clip], size=(WIDTH, HEIGHT))

def create_outro_clip(cta: str, duration: float = 3.5) -> CompositeVideoClip:
    """Create PREMIUM outro with animated CTA."""
    # Font selection
    fonts = [
        r"C:\Windows\Fonts\impact.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        FONT_PATH
    ]
    font_path = FONT_PATH
    for f in fonts:
        if Path(f).exists():
            font_path = f
            break
    
    try:
        font_main = ImageFont.truetype(font_path, 60)
        font_sub = ImageFont.truetype(font_path, 36)
    except:
        font_main = font_sub = ImageFont.load_default()
    
    img = Image.new("RGBA", (WIDTH, HEIGHT), (8, 8, 18, 255))
    draw = ImageDraw.Draw(img)
    
    # Radial gradient effect (center lighter)
    cx, cy = WIDTH // 2, HEIGHT // 2
    for r in range(max(WIDTH, HEIGHT) // 2, 0, -5):
        alpha = int(30 * (r / (max(WIDTH, HEIGHT) // 2)))
        draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], fill=(20, 20, 40, alpha))
    
    # Main CTA text
    wrapped = textwrap.fill(cta.upper(), width=20)
    draw.multiline_text((WIDTH//2, HEIGHT//2 - 60), wrapped, font=font_main,
                        fill=(255, 255, 255, 255), anchor="mm", align="center")
    
    # Subscribe prompt
    sub_text = "▶ LIKE & SUBSCRIBE ◀"
    draw.text((WIDTH//2, HEIGHT//2 + 100), sub_text, font=font_sub,
              fill=(255, 215, 0, 255), anchor="mm")
    
    # Decorative line
    line_y = HEIGHT//2 + 160
    draw.line([(WIDTH//4, line_y), (WIDTH*3//4, line_y)], fill=(255, 215, 0, 150), width=3)
    
    clip = ImageClip(to_rgb_uint8(np.array(img))).set_duration(duration)
    clip = clip.set_position("center")
    
    # Animation: Zoom out slightly + Fade
    clip = clip.resize(lambda t: 1.1 - 0.05 * t)  # Zoom out
    clip = fadein(clip, 0.6)
    clip = fadeout(clip, 0.8)
    
    return clip

# ══════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════

def create_cinematic_video(topic: str, progress_callback=None) -> Path:
    """Main pipeline: Create CINEMATIC video with perfect sync."""
    
    # Reset API usage tracker for this generation
    reset_tracker()
    
    def report(percent, msg):
        if progress_callback:
            progress_callback(percent, msg)
        log.info(f"📊 [{percent}%] {msg}")

    report(0, "Starting cinematic pipeline...")
    log.info("=" * 60)
    log.info("🎬 CINEMATIC VIDEO PIPELINE")
    log.info("=" * 60)
    log.info(f"Topic: {topic}")
    
    # 1. Generate Script
    report(5, "Generating cinematic script...")
    script = generate_script(topic)
    log.info(f"✅ Script: {script.title}")
    
    # 2. Build Scenes
    all_texts = [script.hook] + script.beats + [script.cta]
    emotions_raw = ["epic"] + script.emotions + ["uplifting"]
    
    scenes: List[Scene] = []
    for i, text in enumerate(all_texts):
        emotion_str = emotions_raw[i] if i < len(emotions_raw) else "epic"
        emotion = Emotion(emotion_str) if emotion_str in [e.value for e in Emotion] else Emotion.EPIC
        camera = get_camera_for_emotion(emotion)
        scenes.append(Scene(index=i, text=text, emotion=emotion, camera=camera))
    
    log.info(f"📋 {len(scenes)} scenes planned")
    report(10, f"Script ready: {len(scenes)} scenes planned")
    
    # 3. Generate Assets (Audio FIRST for timing)
    work_dir = OUT / "work"; work_dir.mkdir(exist_ok=True)
    
    log.info("\n🎤 PHASE 1: Generating audio (for sync timing)...")
    
    # Audio progress: 10% -> 30%
    audio_step = 20.0 / len(scenes)
    
    for i, scene in enumerate(scenes):
        pct = 10 + int(i * audio_step)
        report(pct, f"Generating audio for scene {i+1}/{len(scenes)}...")
        
        audio_path, duration = generate_scene_tts(
            scene.text, 
            work_dir / f"scene_{scene.index:02}_audio.wav",
            emotion=scene.emotion.value  # Pass emotion for human-like delivery
        )
        scene.audio_path = audio_path
        scene.duration = duration  # LOCKED
    
    total_duration = sum(s.duration for s in scenes)
    log.info(f"✅ Total narration: {total_duration:.1f}s")
    
    log.info("\n🎨 PHASE 2: Generating visuals (stock video → AI image fallback)...")
    
    pexels_available = bool(os.getenv("PEXELS_API_KEY"))
    if pexels_available:
        log.info("   📹 Pexels API available - trying stock videos first")
    else:
        log.info("   ⚠️ No PEXELS_API_KEY - using AI images only")
    
    # Visual progress: 30% -> 70%
    visual_step = 40.0 / len(scenes)
    
    for i, scene in enumerate(scenes):
        pct = 30 + int(i * visual_step)
        report(pct, f"Creating visuals for scene {i+1}/{len(scenes)}...")
        
        video_path = None
        
        # Try stock video first (if Pexels API key is set)
        if pexels_available:
            video_path = fetch_stock_video(
                scene.text,
                scene.emotion.value,
                work_dir / f"scene_{scene.index:02}_video.mp4",
                topic=topic
            )
        
        if video_path and video_path.exists():
            scene.video_path = video_path
            scene.use_video = True
            log.info(f"   ✅ Scene {scene.index}: Stock video")
        else:
            # Fallback to AI image
            prompt = generate_cinematic_prompt(scene.text, scene.emotion)
            scene.image_path = generate_image(
                prompt,
                work_dir / f"scene_{scene.index:02}_image.jpg"
            )
            log.info(f"   ✅ Scene {scene.index}: AI image")
    
    # 4. Master Audio
    report(70, "Mastering audio & soundtrack...")
    log.info("\n🎚️ PHASE 3: Mastering audio...")
    
    # Use ONLY cornfield_chase.mp3 - the exclusive BGM
    bgm_path = ASSETS / "bgm" / "cornfield_chase.mp3"
    if not bgm_path.exists():
        # Try alternative extensions
        alt_paths = [
            ASSETS / "bgm" / "cornfield_chase.wav",
            ASSETS / "bgm" / "cornfield_chase.m4a",
        ]
        for alt in alt_paths:
            if alt.exists():
                bgm_path = alt
                break
        else:
            bgm_path = None
            log.warning("⚠️ cornfield_chase.mp3 not found in assets/bgm/")
            log.warning("   Place the track there for epic cinematic music!")
    
    if bgm_path and bgm_path.exists():
        log.info(f"   🎵 Using BGM: {bgm_path.name} (Hans Zimmer style)")
    
    mastered_audio = work_dir / "mastered_audio.wav"
    master_audio_hollywood(
        [s.audio_path for s in scenes],
        bgm_path,
        mastered_audio,
        total_duration + 4  # +4 for intro/outro
    )
    
    # 5. Build Video Clips with smooth transitions
    report(75, "Rendering final video (this may take a few minutes)...")
    log.info("\n🎞️ PHASE 4: Building video with effects...")
    
    # SYNC FIX: No overlapping crossfades - scenes are sequential for perfect audio sync
    FADE_DURATION = 0.3  # Short fade for visual smoothness
    INTRO_DURATION = 3.0  # Match create_title_clip duration
    
    # Intro
    intro = create_title_clip(script.title, duration=INTRO_DURATION)
    intro = fadeout(intro, 0.5)
    
    # Scene clips - STRICTLY SEQUENTIAL for audio sync
    scene_clips = []
    current_time = INTRO_DURATION  # Start right after intro ends
    
    for i, scene in enumerate(scenes):
        clip = create_scene_clip(scene)
        
        # CRITICAL: Set start time to match audio timeline exactly
        clip = clip.set_start(current_time)
        
        # Visual fades (don't affect timing)
        clip = fadein(clip, FADE_DURATION)
        if i < len(scenes) - 1:
            clip = fadeout(clip, FADE_DURATION)
        else:
            clip = fadeout(clip, 0.5)
        
        scene_clips.append(clip)
        
        # Caption - synced with scene
        cap = create_caption_clip(scene.text, scene.duration, scene.emotion.value)
        cap = cap.set_start(current_time + 0.1)  # Tiny delay after visual
        cap = fadein(cap, 0.2)
        cap = fadeout(cap, 0.2)
        scene_clips.append(cap)
        
        # SYNC FIX: Move forward by EXACTLY scene.duration (no overlap subtraction)
        current_time += scene.duration
        log.info(f"   Scene {i}: starts at {current_time - scene.duration:.2f}s, duration {scene.duration:.2f}s")
    
    # Outro
    outro = create_outro_clip(script.cta, duration=2.0)
    outro = outro.set_start(current_time)
    
    # Composite
    all_clips = [intro] + scene_clips + [outro]
    final_duration = current_time + 2.0
    
    log.info("   Compositing...")
    video = CompositeVideoClip(all_clips, size=(WIDTH, HEIGHT))
    video = video.set_duration(final_duration)
    
    # Add audio - SYNC FIX: Start audio after intro
    audio = AudioFileClip(str(mastered_audio))
    # Offset audio to start after intro (matches when first scene starts)
    audio = audio.set_start(INTRO_DURATION)
    if audio.duration + INTRO_DURATION < final_duration:
        # Pad if needed
        audio = CompositeAudioClip([audio]).set_duration(final_duration)
    video = video.set_audio(audio)
    
    log.info(f"   ✅ Audio synced: starts at {INTRO_DURATION}s, video ends at {final_duration:.1f}s")
    
    # 6. Render
    log.info("\n💾 PHASE 5: Rendering (60fps, 12Mbps, CRF 18)...")
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in script.title)
    output_path = OUT / f"CINEMATIC_{safe_title[:25]}.mp4"
    
    video.write_videofile(
        str(output_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="12000k",
        preset="slow",
        threads=8,
        audio_bitrate="320k",
        ffmpeg_params=[
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-profile:v", "high",
            "-level", "4.2"
        ]
    )
    
    log.info("\n" + "=" * 60)
    log.info("✨ CINEMATIC VIDEO COMPLETE!")
    log.info(f"📹 Output: {output_path}")
    log.info(f"⏱️ Duration: {final_duration:.1f}s")
    log.info(f"🎬 Quality: {FPS}fps @ 12Mbps")
    log.info("=" * 60)
    
    return output_path


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "The future of artificial intelligence"
    create_cinematic_video(topic)
