# cinematic_masterpiece.py — Hollywood-Grade AI Video Production Pipeline
# Enhanced with: Multi-layer compositing, advanced color grading, particle effects,
# camera movements, cinematic transitions, dynamic lighting, parallax, robust logging,
# API compatibility fixes, Pillow 10+ compatibility, and resilient fallbacks.

import os, sys, json, math, subprocess, textwrap, traceback, logging, random, shutil, base64, io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from enum import Enum

import numpy as np
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from moviepy.editor import (
    AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip,
    ColorClip, vfx, CompositeAudioClip
)
from moviepy.video.VideoClip import VideoClip
from moviepy.video.fx.all import fadein, fadeout
from pydub import AudioSegment
from openai import OpenAI

# ══════════════════════════════════════════════════════════════
# UTILITIES & COMPATIBILITY
# ══════════════════════════════════════════════════════════════

def to_rgb_uint8(arr: np.ndarray) -> np.ndarray:
    """Ensure MoviePy-safe frame: HxWx3, uint8 RGB."""
    if not isinstance(arr, np.ndarray):
        arr = np.array(arr)
    if arr.ndim == 2:  # grayscale → RGB
        arr = np.stack([arr] * 3, axis=-1)
    if arr.shape[-1] == 4:  # RGBA → RGB
        arr = arr[..., :3]
    if arr.dtype != np.uint8:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr

# Pillow compatibility (MoviePy and older code may reference ANTIALIAS)
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# Safe text measurement across Pillow versions
def text_size(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont, text: str) -> Tuple[int, int]:
    """
    Cross-version safe text size: prefer draw.textbbox, then font.getbbox,
    and finally a rough fallback.
    """
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except Exception:
        try:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            return (len(text) * 12, 24)

def multiline_text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, spacing: int = 8) -> Tuple[int, int, int, int]:
    """
    Return bbox for multiline text, compatible with new Pillow.
    """
    try:
        return draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    except Exception:
        # Fallback: approximate via per-line width/height
        lines = text.splitlines() or [text]
        widths = []
        heights = []
        for line in lines:
            w, h = text_size(draw, font, line)
            widths.append(w)
            heights.append(h)
        w = max(widths) if widths else 0
        h = sum(heights) + spacing * (len(lines) - 1)
        return (0, 0, w, h)

# ══════════════════════════════════════════════════════════════
# CONFIGURATION & LOGGING
# ══════════════════════════════════════════════════════════════

# Ensure console handles UTF-8 to avoid cp1252 emoji crashes on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Kill inherited proxy vars that can break DNS/HTTP on Windows shells
for _k in ["HTTP_PROXY","HTTPS_PROXY","ALL_PROXY","http_proxy","https_proxy","all_proxy"]:
    os.environ.pop(_k, None)

load_dotenv()

# Paths
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
ASSETS = ROOT / "assets"; ASSETS.mkdir(exist_ok=True)
(ASSETS / "bgm").mkdir(exist_ok=True)
(ASSETS / "overlays").mkdir(exist_ok=True)
(ASSETS / "luts").mkdir(exist_ok=True)

# Logging
LOGFILE = OUT / "cinematic_production.log"
console_handler = logging.StreamHandler(stream=sys.stdout)
file_handler = logging.FileHandler(LOGFILE, encoding="utf-8")
logging.basicConfig(
    level=logging.INFO,
    format="🎬 %(levelname)s | %(message)s",
    handlers=[console_handler, file_handler]
)
log = logging.getLogger("cinematic-ai")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    log.error("OPENAI_API_KEY missing in .env")
    sys.exit(1)

# AI Configuration
OPENAI_TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "tts-1-hd")
OPENAI_TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "onyx")
OPENAI_TTS_FORMAT = os.getenv("OPENAI_TTS_FORMAT", "wav")
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
SCRIPT_MODEL = os.getenv("OPENAI_SCRIPT_MODEL", "gpt-4o")

# FFmpeg paths (optional local)
import imageio_ffmpeg
FFMPEG_LOCAL = os.getenv("FFMPEG_LOCAL", str(ROOT / "Tools/ffmpeg/bin/ffmpeg.exe"))
FFPROBE_LOCAL = os.getenv("FFPROBE_LOCAL", str(ROOT / "Tools/ffmpeg/bin/ffprobe.exe"))

if not Path(FFMPEG_LOCAL).exists():
    try:
        FFMPEG_LOCAL = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

if Path(FFMPEG_LOCAL).exists():
    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", FFMPEG_LOCAL)
    os.environ.setdefault("FFMPEG_BINARY", FFMPEG_LOCAL)
    # Pydub uses these
    AudioSegment.converter = FFMPEG_LOCAL
    AudioSegment.ffmpeg = FFMPEG_LOCAL
    AudioSegment.ffprobe = FFPROBE_LOCAL

# Canvas
VERT_W, VERT_H = 1080, 1920
FPS = 60
TARGET_MAX_SECONDS = int(os.getenv("TARGET_MAX_SECONDS", "60"))
MIN_SECONDS = int(os.getenv("MIN_SECONDS", "30"))

# Audio mastering targets
TARGET_LOUDNESS_I = os.getenv("TARGET_LOUDNESS_I", "-14")
TARGET_LOUDNESS_TP = os.getenv("TARGET_LOUDNESS_TP", "-1.0")
TARGET_LOUDNESS_LRA = os.getenv("TARGET_LOUDNESS_LRA", "7")

# Visual Configuration
WINDOWS_FONT = os.getenv("WINDOWS_FONT", r"C:\Windows\Fonts\arial.ttf")
WINDOWS_FONT_BOLD = os.getenv("WINDOWS_FONT_BOLD", r"C:\Windows\Fonts\arialbd.ttf")

# Sanitize prompt for logs (reduce noise)
def _sanitize_prompt_for_logging(s: str) -> str:
    s = s.replace("\n", " ").replace("\r", " ")
    return s if len(s) < 300 else s[:300] + "..."

# ══════════════════════════════════════════════════════════════
# CINEMATIC COLOR PALETTES & CAMERA MOVES
# ══════════════════════════════════════════════════════════════

class ColorPalette(Enum):
    BLOCKBUSTER = {
        "primary": (255, 147, 41),    # Orange
        "secondary": (0, 174, 239),   # Teal
        "accent": (255, 215, 0),      # Gold
        "text": (255, 255, 255),
        "shadow": (0, 20, 40)
    }
    NOIR = {
        "primary": (200, 200, 220),
        "secondary": (100, 100, 120),
        "accent": (255, 50, 50),
        "text": (240, 240, 240),
        "shadow": (10, 10, 20)
    }
    NEON = {
        "primary": (255, 0, 255),
        "secondary": (0, 255, 255),
        "accent": (255, 255, 0),
        "text": (255, 255, 255),
        "shadow": (0, 0, 0)
    }
    EARTHY = {
        "primary": (139, 90, 60),
        "secondary": (107, 142, 35),
        "accent": (255, 140, 0),
        "text": (255, 248, 220),
        "shadow": (40, 30, 20)
    }

class CameraMove(Enum):
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    CRANE_UP = "crane_up"
    CRANE_DOWN = "crane_down"
    ORBIT = "orbit"
    PARALLAX = "parallax"
    DUTCH_ANGLE = "dutch"

# OpenAI client with sane timeout
client = OpenAI(api_key=OPENAI_API_KEY, timeout=120)

# ══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════

@dataclass
class Beat:
    text: str
    start: float
    end: float
    emotion: str = "neutral"  # calm, intense, mysterious, uplifting, epic, ...
    camera_move: CameraMove = CameraMove.DOLLY_IN
    image_style: str = "cinematic"

@dataclass
class Script:
    title: str
    hook: str
    beats: List[str]
    cta: str
    theme: str = "epic"
    palette: ColorPalette = ColorPalette.BLOCKBUSTER
    emotions: List[str] = field(default_factory=list)
    visual_notes: List[str] = field(default_factory=list)

# ══════════════════════════════════════════════════════════════
# LLM SCRIPT GENERATION
# ══════════════════════════════════════════════════════════════

MASTER_SCRIPT_SYS = """You are a legendary Hollywood screenwriter specializing in viral short-form content.
Your scripts are VISUAL MASTERPIECES that create emotional impact in 30-60 seconds.

Return STRICT JSON with this structure:
{
  "title": "Compelling title",
  "hook": "Explosive opening line (5-8 words)",
  "beats": ["Beat 1 (visual, punchy)", "Beat 2", "Beat 3", "Beat 4", "Beat 5"],
  "cta": "Powerful closing line",
  "theme": "epic|mysterious|inspiring|intense|peaceful",
  "emotions": ["emotion for each beat"],
  "visual_notes": ["specific visual description for each beat"]
}

RULES:
- Total: 140-180 spoken words (45-60 seconds)
- Each beat: 1-2 sentences, HIGHLY VISUAL
- Use power words: shattered, blazing, infinite, ancient, forgotten, awakening
- Create emotional escalation
- Paint pictures with words
- NO generic statements
- Build to climactic ending
"""

CRITIC_SYS = """You are a master editor. Enhance this script for MAXIMUM cinematic impact.
Make it more visual, more emotional, more powerful. Return same JSON structure, refined."""

def _call_openai_json(messages, model=None, temperature=0.75) -> dict:
    if model is None:
        model = SCRIPT_MODEL
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=messages,
        response_format={"type": "json_object"},
    )
    txt = resp.choices[0].message.content.strip()
    return json.loads(txt)

def generate_cinematic_script(idea: str) -> Script:
    log.info("🎭 Generating Hollywood-grade script...")
    data = _call_openai_json([
        {"role": "system", "content": MASTER_SCRIPT_SYS},
        {"role": "user", "content": f'Create a CINEMATIC MASTERPIECE about: "{idea}". Make it unforgettable.'}
    ])
    log.info("✨ Applying creative refinement...")
    data = _call_openai_json([
        {"role": "system", "content": CRITIC_SYS},
        {"role": "user", "content": json.dumps(data, ensure_ascii=False)}
    ])

    theme = data.get("theme", "epic")
    palette_map = {
        "epic": ColorPalette.BLOCKBUSTER,
        "mysterious": ColorPalette.NOIR,
        "intense": ColorPalette.NEON,
        "peaceful": ColorPalette.EARTHY,
        "inspiring": ColorPalette.BLOCKBUSTER,
    }
    data["palette"] = palette_map.get(theme, ColorPalette.BLOCKBUSTER)
    data.setdefault("emotions", [])
    data.setdefault("visual_notes", [])

    allowed = {k: v for k, v in data.items() if k in Script.__dataclass_fields__}
    return Script(**allowed)

# ══════════════════════════════════════════════════════════════
# IMAGE GENERATION
# ══════════════════════════════════════════════════════════════

def generate_cinematic_prompt(title: str, beat_text: str, emotion: str, visual_note: str = "") -> str:
    emotion_styles = {
        "calm": "soft ethereal lighting, pastel tones, peaceful atmosphere, gentle bokeh",
        "intense": "dramatic chiaroscuro, high contrast, saturated colors, dynamic angles",
        "mysterious": "moody fog, rim lighting, desaturated tones, film noir aesthetic",
        "uplifting": "golden hour lighting, warm tones, sun flares, inspirational composition",
        "epic": "cinematic wide angle, dramatic clouds, heroic lighting, IMAX quality",
    }
    style = emotion_styles.get(emotion, emotion_styles["epic"])

    return f"""Cinematic masterpiece photograph, IMAX quality, 9:16 vertical format.
SCENE: {beat_text}
CONTEXT: {title}
{visual_note}

TECHNICAL: {style}, ultra sharp focus, depth of field, bokeh, professional color grading,
film grain texture, anamorphic lens flare, volumetric lighting, atmospheric haze,
ray-traced reflections, 8K resolution, hyper-detailed textures.

COMPOSITION: Rule of thirds, leading lines, dynamic framing, premium cinematography,
establishing shot cinematic feel, movie poster quality.

STYLE: Photorealistic with slight stylization, Denis Villeneuve meets Roger Deakins,
Blade Runner 2049 color palette influence, Christopher Nolan scale and scope.

NO TEXT, NO WATERMARKS, pure visual storytelling."""

def enhance_image_cinematic(img: Image.Image) -> Image.Image:
    img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))
    img = ImageEnhance.Color(img).enhance(1.15)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    # film grain
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, 0.015 * 255, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)

def _to_9x16_1080x1920(pil_img: Image.Image) -> Image.Image:
    """Center-crop/letterbox to 9:16 then resize to 1080x1920."""
    iw, ih = pil_img.size
    target_w, target_h = 1080, 1920
    target_ratio = target_w / target_h
    img_ratio = iw / ih
    if img_ratio > target_ratio:
        new_w = int(ih * target_ratio)
        x0 = (iw - new_w) // 2
        pil_img = pil_img.crop((x0, 0, x0 + new_w, ih))
    else:
        new_h = int(iw / target_ratio)
        y0 = (ih - new_h) // 2
        pil_img = pil_img.crop((0, y0, iw, y0 + new_h))
    return pil_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

def generate_ai_image_enhanced(prompt: str, out_path: Path, size: str = "1024x1792") -> Path:
    """
    Robust image generation using DALL-E 3 with valid API parameters.
    Valid sizes: '1024x1024', '1024x1792', '1792x1024'
    """
    import requests
    max_retries = 3
    qualities = ["hd", "standard"]  # DALL-E 3 quality options

    for attempt in range(max_retries):
        try:
            q = qualities[min(attempt, len(qualities) - 1)]
            log.info(_sanitize_prompt_for_logging(f"🎨 Generating image (attempt {attempt + 1}/{max_retries}) [quality={q}]..."))
            resp = client.images.generate(
                model=IMAGE_MODEL,
                prompt=prompt,
                size=size,
                quality=q,
                n=1,
            )
            
            # Handle URL or base64 response
            image_data = resp.data[0]
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                img = Image.open(io.BytesIO(base64.b64decode(image_data.b64_json))).convert("RGB")
            elif hasattr(image_data, 'url') and image_data.url:
                img_bytes = requests.get(image_data.url, timeout=60).content
                img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            else:
                raise ValueError("No image data in response")
            
            img = _to_9x16_1080x1920(img)     # normalize to our canvas
            img = enhance_image_cinematic(img)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(out_path, format="JPEG", quality=98, optimize=True)
            log.info(f"✅ Image saved: {out_path.name}")
            return out_path
        except Exception as e:
            log.warning(f"Image generation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                # Placeholder frame
                ph = Image.new("RGB", (1080, 1920), (12, 12, 18))
                d = ImageDraw.Draw(ph)
                txt = "AI IMAGE PLACEHOLDER"
                try:
                    fnt = ImageFont.truetype(WINDOWS_FONT_BOLD, 48)
                except Exception:
                    try:
                        fnt = ImageFont.truetype(WINDOWS_FONT, 48)
                    except Exception:
                        fnt = ImageFont.load_default()
                w, h = text_size(d, fnt, txt)
                d.text(((1080 - w) // 2, (1920 - h) // 2), txt, fill=(230, 230, 230), font=fnt)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                ph.save(out_path, "JPEG", quality=95)
                return out_path
    return out_path

def generate_images_for_beats(title: str, script: Script, img_dir: Path) -> List[Path]:
    paths: List[Path] = []
    beats_data = script.beats
    emotions = script.emotions if script.emotions else ["epic"] * len(beats_data)
    visual_notes = script.visual_notes if script.visual_notes else [""] * len(beats_data)

    all_texts = [script.hook] + beats_data + [script.cta]
    all_emotions = ["epic"] + emotions + ["uplifting"]
    all_notes = [""] + visual_notes + [""]

    for i, (text, emotion, note) in enumerate(zip(all_texts, all_emotions, all_notes), start=1):
        prompt = generate_cinematic_prompt(script.title, text, emotion, note)
        out = img_dir / f"scene_{i:02}_cinematic.jpg"
        log.info(f"🎬 Scene {i}/{len(all_texts)}: {text[:50]}...")
        generate_ai_image_enhanced(prompt, out)  # Uses default 1024x1792
        paths.append(out)
    return paths

# ══════════════════════════════════════════════════════════════
# AUDIO PRODUCTION
# ══════════════════════════════════════════════════════════════

def synth_tts_openai(text: str, wav_path: Path, voice: Optional[str] = None):
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    voice = voice or OPENAI_TTS_VOICE

    # First get MP3 bytes (fastest), then convert to WAV via ffmpeg so
    # the file extension matches the actual codec.
    mp3_tmp = wav_path.with_suffix(".tmp.mp3")

    # Non-streaming create() returns the full payload; no `format` needed.
    resp = client.audio.speech.create(
        model=OPENAI_TTS_MODEL,
        voice=voice,
        input=text,
    )

    with open(mp3_tmp, "wb") as f:
        f.write(resp.read())  # recent SDKs expose .read() for raw audio bytes

    # Convert MP3 → WAV using ffmpeg (if available); otherwise keep MP3
    ff = shutil.which("ffmpeg") or FFMPEG_LOCAL
    if ff and Path(ff).exists():
        subprocess.run([ff, "-y", "-i", str(mp3_tmp), "-ar", "48000", "-ac", "2", str(wav_path)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mp3_tmp.unlink(missing_ok=True)
    else:
        # Fall back: just move MP3 to the expected path (still readable by Whisper/ffmpeg)
        shutil.move(str(mp3_tmp), str(wav_path))

def align_from_transcription(wav_path: Path) -> List[Beat]:
    """Use Whisper to create segment-level timings (robust)."""
    try:
        with open(wav_path, "rb") as f:
            tr = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="verbose_json",
                temperature=0.0,
            )
        beats: List[Beat] = []
        segs = getattr(tr, "segments", []) or []
        for seg in segs:
            txt = (seg.get("text") or "").strip()
            if not txt:
                continue
            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", start + 0.5))
            if end <= start:
                end = start + 0.5
            beats.append(Beat(text=txt, start=start, end=end))
        return beats
    except Exception as e:
        log.warning(f"Transcription alignment failed: {e}")
        return []

def master_audio_hollywood(voice_wav: Path, bgm_path: Optional[Path], out_wav: Path):
    """Professional audio mastering (FFmpeg)."""
    ff = shutil.which("ffmpeg") or FFMPEG_LOCAL
    if not ff or not Path(ff).exists():
        log.warning("FFmpeg not found, using unmastered audio")
        shutil.copy(voice_wav, out_wav)
        return

    I, TP, LRA = TARGET_LOUDNESS_I, TARGET_LOUDNESS_TP, TARGET_LOUDNESS_LRA

    if bgm_path and bgm_path.exists():
        cmd = [
            ff, "-y",
            "-i", str(voice_wav),
            "-i", str(bgm_path),
            "-filter_complex",
            "[1:a]equalizer=f=120:t=q:w=1.5:g=-2,"
            "equalizer=f=3000:t=q:w=2:g=1,"
            "volume=-14dB[bg];"
            "[bg][0:a]sidechaincompress=threshold=0.03:ratio=6:attack=3:release=200:makeup=4[duck];"
            "[0:a]loudnorm=I=-13:TP=-1.5:LRA=7:linear=true[voice_norm];"
            "[duck][voice_norm]amix=inputs=2:duration=first:weights=0.25 0.75,"
            "equalizer=f=80:t=h:w=100:g=-1,"
            "equalizer=f=10000:t=h:w=200:g=1,"
            f"alimiter=limit={TP}dB:attack=2:release=50,"
            f"loudnorm=I={I}:TP={TP}:LRA={LRA}:linear=true[out]",
            "-map", "[out]",
            "-ar", "48000", "-ac", "2",
            str(out_wav)
        ]
    else:
        cmd = [
            ff, "-y",
            "-i", str(voice_wav),
            "-filter_complex",
            f"[0:a]equalizer=f=80:t=h:w=100:g=-2,"
            "equalizer=f=3000:t=q:w=2:g=1.5,"
            f"alimiter=limit={TP}dB,"
            f"loudnorm=I={I}:TP={TP}:LRA={LRA}[out]",
            "-map", "[out]",
            "-ar", "48000", "-ac", "2",
            str(out_wav)
        ]

    log.info("🎼 Mastering audio with Hollywood-grade processing...")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# ══════════════════════════════════════════════════════════════
# ADVANCED VISUAL EFFECTS
# ══════════════════════════════════════════════════════════════

def lerp(a, b, t): return a + (b - a) * t
def ease_in_cubic(t): return t * t * t
def ease_out_cubic(t): return 1 - pow(1 - t, 3)
def ease_out_expo(t): return 1 if t == 1 else 1 - pow(2, -10 * t)

def create_cinematic_caption(text: str, palette: Dict, font_path: str,
                             style: str = "modern") -> Image.Image:
    base_size = 72 if len(text) < 30 else 64 if len(text) < 50 else 56
    try:
        font = ImageFont.truetype(font_path, base_size)
    except Exception:
        try:
            font = ImageFont.truetype(WINDOWS_FONT, base_size)
        except Exception:
            font = ImageFont.load_default()
    try:
        font_bold = ImageFont.truetype(WINDOWS_FONT_BOLD, base_size)
    except Exception:
        try:
            font_bold = ImageFont.truetype(WINDOWS_FONT, base_size)
        except Exception:
            font_bold = ImageFont.load_default()

    wrapped = textwrap.fill(text, width=24)
    dummy = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    draw = ImageDraw.Draw(dummy)
    bbox = multiline_text_bbox(draw, wrapped, font=font, spacing=8)
    w, h = bbox[2] - bbox[0] + 80, bbox[3] - bbox[1] + 60

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if style == "modern":
        bar_height = h - 20
        bar = Image.new("RGBA", (w - 20, bar_height), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar)
        bar_draw.rounded_rectangle([(0, 0), (w - 20, bar_height)], radius=12, fill=(0, 0, 0, 180))
        bar = bar.filter(ImageFilter.GaussianBlur(2))
        img.paste(bar, (10, 10), bar)

        accent_color = palette["accent"]
        draw.rounded_rectangle([(15, 15), (25, h - 15)], radius=3, fill=accent_color)

        shadow_color = (*palette["shadow"], 200)
        for offset in [(0, 2), (2, 0), (-2, 0), (0, -2)]:
            draw.multiline_text((w // 2 + offset[0], h // 2 + offset[1]),
                                wrapped, font=font_bold, fill=shadow_color,
                                spacing=8, align="center", anchor="mm")
        draw.multiline_text((w // 2, h // 2), wrapped, font=font_bold,
                            fill=palette["text"], spacing=8, align="center", anchor="mm")
    else:
        draw.multiline_text((w // 2, h // 2), wrapped, font=font_bold, fill=palette["text"],
                            spacing=8, align="center", anchor="mm",
                            stroke_width=6, stroke_fill=(0, 0, 0, 255))
    return img

def apply_camera_movement(img: Image.Image, camera_move: CameraMove,
                          t: float, duration: float) -> Tuple[float, Tuple[int, int]]:
    progress = min(max(t / max(duration, 0.001), 0), 1)
    eased = ease_out_cubic(progress)
    moves = {
        CameraMove.DOLLY_IN:   (lerp(1.15, 1.05, eased), (0, 0)),
        CameraMove.DOLLY_OUT:  (lerp(1.05, 1.15, eased), (0, 0)),
        CameraMove.PAN_RIGHT:  (1.10, (int(-80 * eased), 0)),
        CameraMove.PAN_LEFT:   (1.10, (int(80 * eased), 0)),
        CameraMove.CRANE_UP:   (1.08, (0, int(60 * eased))),
        CameraMove.CRANE_DOWN: (1.08, (0, int(-60 * eased))),
        CameraMove.ORBIT:      (1.10, (int(50 * math.sin(eased * math.pi)),
                                       int(30 * math.cos(eased * math.pi)))),
        CameraMove.PARALLAX:   (lerp(1.08, 1.12, eased),
                                (int(40 * math.sin(eased * 2 * math.pi)), 0)),
        CameraMove.DUTCH_ANGLE:(1.10, (int(30 * math.sin(eased * 2 * math.pi)), 0)),
    }
    return moves.get(camera_move, moves[CameraMove.DOLLY_IN])


def grade_image_by_emotion(img: Image.Image, emotion: str, palette: Dict) -> Image.Image:
    if emotion == "intense":
        img = ImageEnhance.Contrast(img).enhance(1.25)
        img = ImageEnhance.Color(img).enhance(1.3)
    elif emotion == "mysterious":
        img = ImageEnhance.Color(img).enhance(0.7)
        img = ImageEnhance.Brightness(img).enhance(0.85)
        arr = np.array(img).astype(float)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.15, 0, 255)
        img = Image.fromarray(arr.astype(np.uint8))
    elif emotion == "calm":
        img = ImageEnhance.Color(img).enhance(0.9)
        img = ImageEnhance.Contrast(img).enhance(0.95)
    elif emotion == "uplifting":
        img = ImageEnhance.Brightness(img).enhance(1.1)
        arr = np.array(img).astype(float)
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.08, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.05, 0, 255)
        img = Image.fromarray(arr.astype(np.uint8))
    return img

def create_advanced_clip(img_path: Path, beat: Beat, palette: Dict) -> List[VideoClip]:
    """Create multi-layered clip with advanced effects for one beat."""
    dur = max(0.001, beat.end - beat.start)
    img = Image.open(img_path).convert("RGB")

    # Smart center-crop to 9:16
    iw, ih = img.size
    target_ratio = VERT_W / VERT_H
    img_ratio = iw / ih
    if img_ratio > target_ratio:
        new_w = int(ih * target_ratio); x0 = (iw - new_w) // 2
        img = img.crop((x0, 0, x0 + new_w, ih))
    else:
        new_h = int(iw / target_ratio); y0 = (ih - new_h) // 2
        img = img.crop((0, y0, iw, y0 + new_h))
    img = img.resize((VERT_W, VERT_H), Image.Resampling.LANCZOS)
    img = grade_image_by_emotion(img, beat.emotion, palette)

    # Animated base (Ken Burns style)
    def make_frame(t):
        scale, offset = apply_camera_movement(img, beat.camera_move, t, dur)
        new_size = (int(VERT_W * scale), int(VERT_H * scale))
        scaled = img.resize(new_size, Image.Resampling.LANCZOS)
        x = (VERT_W - new_size[0]) // 2 + offset[0]
        y = (VERT_H - new_size[1]) // 2 + offset[1]
        canvas = Image.new("RGB", (VERT_W, VERT_H), (0, 0, 0))
        canvas.paste(scaled, (x, y))
        return to_rgb_uint8(np.array(canvas))

    base_clip = VideoClip(make_frame=make_frame, duration=dur).set_start(beat.start)
    if dur > 0.5:
        base_clip = fadein(base_clip, 0.3)
        base_clip = fadeout(base_clip, 0.3)

    # Caption
    cap_img = create_cinematic_caption(beat.text, palette, WINDOWS_FONT, style="modern")
    cap_clip = ImageClip(to_rgb_uint8(np.array(cap_img))).set_duration(dur).set_start(beat.start)

    def cap_pos(t):
        if t < beat.start:
            return (VERT_W // 2 - cap_clip.w // 2, VERT_H)
        rel = t - beat.start
        if rel < 0.4:
            p = rel / 0.4
            y = int(lerp(int(VERT_H * 0.85), int(VERT_H * 0.72), ease_out_expo(p)))
        elif rel > dur - 0.3:
            y = int(VERT_H * 0.72)
        else:
            float_amt = 8 * math.sin((rel - 0.4) * 2 * math.pi / max(dur, 0.001))
            y = int(VERT_H * 0.72 + float_amt)
        return (VERT_W // 2 - cap_clip.w // 2, y)

    cap_clip = cap_clip.set_position(cap_pos)
    cap_clip = fadein(cap_clip, 0.3)
    cap_clip = fadeout(cap_clip, 0.3)
    return [base_clip, cap_clip]

def create_title_sequence(title: str, palette: Dict, duration: float = 2.0) -> CompositeVideoClip:
    font_size = 96
    try:
        font = ImageFont.truetype(WINDOWS_FONT_BOLD, font_size)
    except Exception:
        font = ImageFont.truetype(WINDOWS_FONT, font_size)

    wrapped = textwrap.fill(title, width=18)
    dummy = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=12)
    w, h = bbox[2] - bbox[0] + 100, bbox[3] - bbox[1] + 100

    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for offset in [(0, 3), (3, 0), (-3, 0), (0, -3), (2, 2), (-2, 2)]:
        draw.multiline_text(
            (w // 2 + offset[0], h // 2 + offset[1]),
            wrapped, font=font,
            fill=(palette["accent"][0], palette["accent"][1], palette["accent"][2], 100),
            spacing=12, align="center", anchor="mm"
        )
    draw.multiline_text(
        (w // 2, h // 2), wrapped, font=font,
        fill=palette["text"], spacing=12, align="center", anchor="mm"
    )
    line_y = h // 2 + bbox[3] // 2 + 20
    draw.rectangle([(w // 2 - 80, line_y), (w // 2 + 80, line_y + 4)], fill=palette["accent"])

    title_clip = ImageClip(to_rgb_uint8(np.array(img))).set_duration(duration)

    # Smooth scale animation (simplified to static to avoid TypeError)
    title_clip = title_clip.resize(1.05).set_position("center")

    # Use fades instead of time-varying set_opacity
    title_clip = fadein(title_clip, 0.4)
    title_clip = fadeout(title_clip, 0.4)

    bg = ColorClip(size=(VERT_W, VERT_H), color=(5, 5, 15)).set_duration(duration)
    return CompositeVideoClip([bg, title_clip], size=(VERT_W, VERT_H))

def create_particles_overlay(duration: float, palette: Dict) -> VideoClip:
    """Subtle RGB particles overlay; alpha handled by clip opacity."""
    def make_particles(t):
        canvas = Image.new("RGB", (VERT_W, VERT_H), (0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        num_particles = 40
        for i in range(num_particles):
            seed = i * 1337
            x = (seed * 73) % VERT_W
            y_base = (seed * 127) % VERT_H
            y = (y_base - int(t * 30 * (1 + i % 3))) % VERT_H
            size = 2 + (i % 3)
            color = (palette["accent"][0], palette["accent"][1], palette["accent"][2])
            draw.ellipse([x, y, x + size, y + size], fill=tuple(color))
        return to_rgb_uint8(np.array(canvas))

    return VideoClip(make_frame=make_particles, duration=duration)

# ══════════════════════════════════════════════════════════════
# MAIN VIDEO ASSEMBLY
# ══════════════════════════════════════════════════════════════

def assemble_masterpiece(beats: List[Beat], image_paths: List[Path],
                         audio_path: Path, out_path: Path, script: Script) -> Path:
    log.info("🎬 Assembling cinematic masterpiece...")
    palette = script.palette.value
    total_duration = beats[-1].end if beats else 30

    title_seq = create_title_sequence(script.title, palette, duration=2.0)
    all_layers: List[VideoClip] = [title_seq]

    for idx, beat in enumerate(beats):
        img_idx = min(idx, len(image_paths) - 1)
        layers = create_advanced_clip(image_paths[img_idx], beat, palette)
        all_layers.extend(layers)

    particles = create_particles_overlay(total_duration + 2, palette).set_start(0).set_opacity(0.3)
    all_layers.append(particles)

    audio = AudioFileClip(str(audio_path))

    log.info("🎞️  Compositing layers...")
    final = CompositeVideoClip(all_layers, size=(VERT_W, VERT_H))
    # Pad audio to match video duration to avoid IOError
    # Use CompositeAudioClip to ensure silence after the audio ends
    audio = CompositeAudioClip([audio.set_start(0)]).set_duration(total_duration + 2)
    final = final.set_audio(audio).set_duration(total_duration + 2)

    log.info("💾 Rendering final video (this may take several minutes)...")
    final.write_videofile(
        str(out_path),
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="12000k",
        preset="slow",
        threads=8,
        audio_bitrate="320k",
        ffmpeg_params=["-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
    )
    return out_path

# ══════════════════════════════════════════════════════════════
# MASTER PIPELINE
# ══════════════════════════════════════════════════════════════

def create_cinematic_masterpiece(idea: str) -> Path:
    log.info("=" * 70)
    log.info("🎬 CINEMATIC AI MASTERPIECE GENERATOR")
    log.info("=" * 70)
    log.info(f"💡 Concept: {idea}\n")

    # 1) Script
    script = generate_cinematic_script(idea)
    script_path = OUT / "script_master.json"
    script_path.write_text(json.dumps({
        "title": script.title,
        "hook": script.hook,
        "beats": script.beats,
        "cta": script.cta,
        "theme": script.theme,
        "emotions": script.emotions,
        "visual_notes": script.visual_notes,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info(f"✅ Script generated: {script.title}")
    log.info(f"   Theme: {script.theme}")

    # 2) TTS text
    tts_text = f"{script.hook}\n\n" + "\n\n".join(script.beats) + f"\n\n{script.cta}"

    # Paths
    img_dir = OUT / "images_cinematic"; img_dir.mkdir(exist_ok=True)
    voice_raw = OUT / "voice_raw.wav"
    voice_final = OUT / "voice_master.wav"
    srt_path = OUT / "captions.srt"
    safe_title = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in script.title)
    mp4_path = OUT / f"MASTERPIECE_{safe_title[:30].replace(' ', '_')}.mp4"

    # 3) Images
    log.info("\n🎨 Generating AI cinematic images...")
    images = generate_images_for_beats(script.title, script, img_dir)
    log.info(f"✅ Generated {len(images)} stunning images")

    # 4) Voice
    log.info("\n🎤 Generating professional voice-over...")
    synth_tts_openai(tts_text, voice_raw)
    log.info("✅ Voice generated")

    # 5) Timing
    log.info("\n⏱️  Analyzing timing with Whisper...")
    beats = align_from_transcription(voice_raw)
    if not beats:
        log.warning("Alignment failed, using estimated timing")
        all_lines = [script.hook] + script.beats + [script.cta]
        slot_dur = max(3.5, min(6.0, TARGET_MAX_SECONDS / max(1, len(all_lines))))
        beats = []
        t = 2.0  # after title
        for line in all_lines:
            beats.append(Beat(text=line, start=t, end=t + slot_dur,
                              emotion="epic", camera_move=random.choice(list(CameraMove))))
            t += slot_dur
    else:
        emotions = script.emotions if script.emotions else []
        camera_moves = [CameraMove.DOLLY_IN, CameraMove.PAN_RIGHT, CameraMove.DOLLY_OUT,
                        CameraMove.PAN_LEFT, CameraMove.CRANE_UP]
        for i, beat in enumerate(beats):
            beat.emotion = emotions[i] if i < len(emotions) else "epic"
            beat.camera_move = camera_moves[i % len(camera_moves)]
            beat.start += 2.0
            beat.end += 2.0
    log.info(f"✅ {len(beats)} beats aligned")

    # 6) SRT
    def fmt_srt(t: float):
        h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60); ms = int((t - int(t)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    srt_lines = []
    for i, b in enumerate(beats, 1):
        srt_lines += [str(i), f"{fmt_srt(b.start)} --> {fmt_srt(b.end)}", b.text, ""]
    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")

    # 7) Master audio (optional bgm from assets/bgm)
    log.info("\n🎵 Mastering audio...")
    bgm_dir = ASSETS / "bgm"; bgm = None
    if bgm_dir.exists():
        picks = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.wav"))
        if picks:
            bgm = random.choice(picks)
    if bgm:
        log.info(f"   Using BGM: {bgm.name}")
    master_audio_hollywood(voice_raw, bgm, voice_final)
    log.info("✅ Audio mastered")

    # 8) Assemble video
    log.info("\n🎞️  Assembling cinematic video...")
    final_video = assemble_masterpiece(beats, images, voice_final, mp4_path, script)

    log.info("\n" + "=" * 70)
    log.info("✨ MASTERPIECE COMPLETE!")
    log.info("=" * 70)
    log.info(f"📹 Video: {final_video}")
    log.info(f"📝 Script: {script_path}")
    log.info(f"💬 Captions: {srt_path}")
    log.info(f"🖼️  Images: {img_dir}\n")

    try:
        if sys.platform == "win32":
            os.startfile(final_video)
        elif sys.platform == "darwin":
            subprocess.run(["open", str(final_video)])
        else:
            subprocess.run(["xdg-open", str(final_video)])
    except Exception:
        pass

    return final_video

# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(r"""
╔══════════════════════════════════════════════════════════════╗
║      🎬 CINEMATIC AI MASTERPIECE GENERATOR 🎬               ║
╚══════════════════════════════════════════════════════════════╝

Create Hollywood-grade short-form videos with AI.

USAGE:
    python cinematic_masterpiece.py "Your amazing video idea"

EXAMPLES:
    python cinematic_masterpiece.py "The hidden psychology of success"
    python cinematic_masterpiece.py "5 mind-bending space facts"
    python cinematic_masterpiece.py "Ancient wisdom for modern life"

FEATURES:
    ✨ GPT-4o script generation with emotional intelligence
    🎨 OpenAI gpt-image-1 cinematic image generation
    🎤 Premium OpenAI TTS voice-over
    🎵 Professional audio mastering
    🎬 Advanced camera movements (dolly, pan, crane, orbit)
    💫 Kinetic typography with smooth animations
    🌈 Cinematic color grading per scene
    ⚡ Particle effects and transitions
    📱 Perfect 9:16 vertical format
    🎯 60 FPS buttery smooth playback

OUTPUT:
    • High-quality MP4 video (1080x1920)
    • Subtitle file (.srt)
    • Full script JSON
    • Individual scene images

REQUIREMENTS:
    • OPENAI_API_KEY in .env file
    • FFmpeg installed (for audio mastering)
""")
        sys.exit(0)

    idea = " ".join(sys.argv[1:])
    try:
        create_cinematic_masterpiece(idea)
    except KeyboardInterrupt:
        log.info("\n🛑 Generation cancelled by user")
        sys.exit(0)
    except Exception:
        log.error("=" * 70)
        log.error("❌ PIPELINE ERROR")
        log.error("=" * 70)
        log.error(traceback.format_exc())
        log.error("💡 Tips:")
        log.error("   • Check your OPENAI_API_KEY in .env")
        log.error("   • Ensure FFmpeg is installed or set FFMPEG_LOCAL")
        log.error("   • Try a simpler prompt")
        log.error("   • Check cinematic_production.log for details")
        sys.exit(1)
