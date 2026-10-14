"""
Video Engine - Main Orchestrator
The heart of the 10× AI Video Platform.
Coordinates all AI components to produce CINEMATIC-QUALITY videos.

Upgraded for Hollywood-grade output:
- 60fps @ 12Mbps rendering
- Professional audio with sidechain ducking
- Intelligent BGM selection
- Premium visual effects and overlays
"""
import os
import logging
import random
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

from dotenv import load_dotenv

from .models import Language, VideoScript, ScriptBeat, Emotion, CameraMove, ColorPalette
from .ai import PromptInterpreter, EmotionMapper, Cinematographer
from .generators import VisualGenerator, AudioGenerator, MusicSelector
from .effects import grade_image_by_emotion, TransitionManager, OverlayManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="🎬 %(levelname)s | %(name)s | %(message)s"
)
log = logging.getLogger("core.engine")


@dataclass
class Beat:
    """Runtime beat with timing info."""
    text: str
    start: float
    end: float
    emotion: Emotion = Emotion.NEUTRAL
    camera_move: CameraMove = CameraMove.DOLLY_IN


class VideoEngine:
    """
    Main video generation orchestrator.
    
    Coordinates:
    - AI Creative Intelligence (prompt interpretation, emotion mapping)
    - Visual generation (DALL-E images)
    - Audio generation (TTS, transcription)
    - Video composition (MoviePy rendering)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        load_dotenv()
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Initialize AI components
        self.interpreter = PromptInterpreter(self.api_key)
        self.emotion_mapper = EmotionMapper()
        self.cinematographer = Cinematographer()
        
        # Initialize generators
        self.visual_gen = VisualGenerator(self.api_key)
        self.audio_gen = AudioGenerator(self.api_key)
        self.music_selector = MusicSelector(Path("assets/bgm"))
        
        # Initialize effects managers
        self.transition_manager = TransitionManager(default_duration=0.5)
        self.overlay_manager = OverlayManager(canvas_size=(1080, 1920))
        
        # Paths
        self.output_dir = Path(os.getenv("OUTPUT_DIR", "out"))
        self.output_dir.mkdir(exist_ok=True)
        
        # Rendering settings (Hollywood-grade)
        self.fps = 60
        self.bitrate = "12000k"
        self.crf = 18  # High quality
        
        log.info("🚀 VideoEngine initialized (Cinematic Mode)")
    
    def generate_video(
        self,
        topic: str,
        language: str = "English",
        duration: str = "30s",
        style: Optional[str] = None
    ) -> Path:
        """
        Generate a complete video from a topic/prompt.
        
        Args:
            topic: The video topic or script
            language: Narration language
            duration: Target duration ("30s", "45s", "60s")
            style: Optional style preset
            
        Returns:
            Path to the generated video
        """
        log.info("=" * 60)
        log.info(f"🎬 GENERATING VIDEO")
        log.info(f"   Topic: {topic[:80]}...")
        log.info(f"   Language: {language}")
        log.info(f"   Duration: {duration}")
        log.info("=" * 60)
        
        # Parse language
        try:
            lang_enum = Language(language)
        except ValueError:
            lang_enum = Language.ENGLISH
        
        # Step 1: Interpret prompt and generate script
        log.info("\n📝 Step 1: Generating script...")
        script = self.interpreter.interpret(topic, lang_enum, duration, style)
        
        # Step 2: Generate TTS audio
        log.info("\n🎤 Step 2: Generating voice-over...")
        tts_text = f"{script.hook}\n\n" + "\n\n".join(b.text for b in script.beats) + f"\n\n{script.cta}"
        voice_path = self.output_dir / "voice_raw.wav"
        self.audio_gen.generate_tts(tts_text, voice_path)
        
        # Step 3: Get timing from transcription
        log.info("\n⏱️ Step 3: Analyzing timing...")
        beats = self._align_beats(voice_path, script)
        
        # Step 4: Generate images
        log.info("\n🎨 Step 4: Generating cinematic visuals...")
        images = self._generate_images(script, beats)
        
        # Step 5: Select and master audio
        log.info("\n🎵 Step 5: Mastering audio with BGM...")
        bgm_path = self.music_selector.select(theme=script.theme)
        audio_duration = beats[-1].end + 2 if beats else 30
        mastered_audio = self.output_dir / "audio_master.wav"
        self.audio_gen.mix_audio(voice_path, bgm_path, mastered_audio, audio_duration)
        
        # Step 6: Compose video
        log.info("\n🎞️ Step 6: Composing cinematic video (60fps)...")
        output_path = self._compose_video(script, beats, images, mastered_audio)
        
        log.info("\n" + "=" * 60)
        log.info("✨ CINEMATIC VIDEO COMPLETE!")
        log.info(f"   Output: {output_path}")
        log.info(f"   Quality: {self.fps}fps @ {self.bitrate}")
        log.info("=" * 60)
        
        return output_path
    
    def _align_beats(self, voice_path: Path, script: VideoScript) -> List[Beat]:
        """Align script beats with audio timing using transcription."""
        transcription = self.audio_gen.transcribe(voice_path)
        segments = transcription.get("segments", [])
        
        if segments:
            # Use Whisper segments for timing
            beats = []
            for seg in segments:
                text = seg["text"]
                start = seg["start"] + 2.0  # Account for title
                end = seg["end"] + 2.0
                
                # Find matching script beat for emotion
                emotion = Emotion.EPIC
                camera_move = CameraMove.DOLLY_IN
                
                for sb in script.beats:
                    if any(word in text.lower() for word in sb.text.lower().split()[:3]):
                        emotion = sb.emotion
                        camera_move = sb.camera_move
                        break
                
                beats.append(Beat(
                    text=text,
                    start=start,
                    end=end,
                    emotion=emotion,
                    camera_move=camera_move
                ))
            
            return beats
        else:
            # Fallback: estimated timing
            log.warning("Transcription failed, using estimated timing")
            all_texts = [script.hook] + [b.text for b in script.beats] + [script.cta]
            slot_dur = 4.0
            
            beats = []
            t = 2.0  # After title
            for i, text in enumerate(all_texts):
                emotion = script.beats[min(i, len(script.beats)-1)].emotion if script.beats else Emotion.EPIC
                camera_move = random.choice(list(CameraMove))
                
                beats.append(Beat(
                    text=text,
                    start=t,
                    end=t + slot_dur,
                    emotion=emotion,
                    camera_move=camera_move
                ))
                t += slot_dur
            
            return beats
    
    def _generate_images(self, script: VideoScript, beats: List[Beat]) -> List[Path]:
        """Generate images for each beat."""
        img_dir = self.output_dir / "images"
        img_dir.mkdir(exist_ok=True)
        
        images = []
        
        # Build visual prompts
        all_items = [
            ("hook", script.hook, Emotion.EPIC),
            *[("beat", b.visual_prompt, b.emotion) for b in script.beats],
            ("cta", script.cta, Emotion.UPLIFTING)
        ]
        
        for i, (item_type, text, emotion) in enumerate(all_items):
            # Enhance prompt with emotion styling
            enhanced_prompt = self.emotion_mapper.enhance_visual_prompt(text, emotion)
            
            output_path = img_dir / f"scene_{i+1:02}.jpg"
            
            log.info(f"   Scene {i+1}/{len(all_items)}: {text[:40]}...")
            
            self.visual_gen.generate(
                prompt=enhanced_prompt,
                output_path=output_path,
                size="1024x1792",
                emotion=emotion
            )
            
            images.append(output_path)
        
        return images
    
    def _compose_video(
        self,
        script: VideoScript,
        beats: List[Beat],
        images: List[Path],
        audio_path: Path
    ) -> Path:
        """Compose final video from generated assets."""
        from moviepy.editor import (
            ImageClip, CompositeVideoClip, AudioFileClip,
            ColorClip, CompositeAudioClip
        )
        from moviepy.video.fx.all import fadein, fadeout
        from moviepy.video.VideoClip import VideoClip
        import numpy as np
        from PIL import Image
        
        from .effects.camera import apply_camera_to_frame
        from .effects.captions import create_cinematic_caption, create_title_card
        from .effects.particles import create_particles_overlay
        from .utils.compatibility import to_rgb_uint8
        
        palette = script.palette.value
        
        # Calculate total duration
        total_duration = beats[-1].end if beats else 30
        
        # Create title sequence
        title_img = create_title_card(script.title, palette)
        title_clip = ImageClip(to_rgb_uint8(np.array(title_img)))
        title_clip = title_clip.set_duration(2.0)
        title_clip = fadein(title_clip, 0.4)
        title_clip = fadeout(title_clip, 0.4)
        
        all_clips = [title_clip]
        
        # Create scene clips
        for idx, beat in enumerate(beats):
            if idx >= len(images):
                continue
                
            img = Image.open(images[idx]).convert("RGB")
            dur = beat.end - beat.start
            
            # Create animated clip with camera movement
            def make_frame(t, img=img, beat=beat, dur=dur):
                frame = apply_camera_to_frame(
                    img,
                    beat.camera_move,
                    t,
                    dur,
                    (1080, 1920)
                )
                return to_rgb_uint8(np.array(frame))
            
            base_clip = VideoClip(make_frame=make_frame, duration=dur)
            base_clip = base_clip.set_start(beat.start)
            
            # Add fade
            if dur > 0.5:
                base_clip = fadein(base_clip, 0.3)
                base_clip = fadeout(base_clip, 0.3)
            
            all_clips.append(base_clip)
            
            # Create caption
            cap_img = create_cinematic_caption(beat.text, palette)
            cap_clip = ImageClip(to_rgb_uint8(np.array(cap_img)))
            cap_clip = cap_clip.set_duration(dur)
            cap_clip = cap_clip.set_start(beat.start)
            cap_clip = cap_clip.set_position(("center", int(1920 * 0.72)))
            cap_clip = fadein(cap_clip, 0.3)
            cap_clip = fadeout(cap_clip, 0.3)
            
            all_clips.append(cap_clip)
        
        # Add particles overlay
        particles_fn = create_particles_overlay(
            total_duration + 2,
            (1080, 1920),
            palette
        )
        particles_clip = VideoClip(make_frame=particles_fn, duration=total_duration + 2)
        particles_clip = particles_clip.set_opacity(0.3)
        all_clips.append(particles_clip)
        
        # Compose video
        log.info("   Compositing layers...")
        final = CompositeVideoClip(all_clips, size=(1080, 1920))
        
        # Add audio
        audio = AudioFileClip(str(audio_path))
        audio = CompositeAudioClip([audio.set_start(0)]).set_duration(total_duration + 2)
        final = final.set_audio(audio)
        final = final.set_duration(total_duration + 2)
        
        # Generate output filename
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in script.title)
        output_path = self.output_dir / f"CINEMATIC_{safe_title[:30].replace(' ', '_')}.mp4"
        
        # Render with Hollywood-grade settings
        log.info(f"   Rendering at {self.fps}fps, {self.bitrate}, CRF {self.crf}...")
        final.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            bitrate=self.bitrate,
            preset="slow",  # Higher quality encoding
            threads=8,
            audio_bitrate="320k",  # High quality audio
            ffmpeg_params=[
                "-crf", str(self.crf),
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",  # Web-optimized
                "-profile:v", "high",  # H.264 High Profile
                "-level", "4.2"  # Compatibility level
            ]
        )
        
        return output_path


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m core.engine \"Your video topic\"")
        sys.exit(1)
    
    topic = " ".join(sys.argv[1:])
    engine = VideoEngine()
    engine.generate_video(topic)
