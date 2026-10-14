import os
import logging
from pathlib import Path
from typing import Optional, List
from openai import OpenAI
from moviepy.editor import AudioFileClip, CompositeAudioClip, afx
import shutil
import subprocess

log = logging.getLogger("video-engine")

class AudioManager:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.tts_model = os.getenv("OPENAI_TTS_MODEL", "tts-1-hd")
        # Use more expressive voices for human-like quality
        self.tts_voice = os.getenv("OPENAI_TTS_VOICE", "nova")  # nova/alloy/echo/fable/onyx/shimmer

    def generate_tts(self, text: str, output_path: Path, voice: Optional[str] = None, speed: float = 1.0) -> Optional[Path]:
        """
        Generate TTS audio from text with human-like quality.
        Speed: 0.25 to 4.0 (1.0 = normal, slightly vary for naturalness)
        """
        try:
            log.info(f"🎤 Generating human-like TTS...")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Vary speed slightly for more natural feel (0.95-1.05 range)
            import random
            natural_speed = speed * random.uniform(0.98, 1.02)
            
            response = self.client.audio.speech.create(
                model=self.tts_model,
                voice=voice or self.tts_voice,
                input=text,
                speed=natural_speed  # Add natural variation
            )
            
            # Save as MP3 first
            mp3_path = output_path.with_suffix(".mp3")
            response.stream_to_file(mp3_path)
            
            # Convert to WAV for better compatibility
            self._convert_to_wav(mp3_path, output_path)
            mp3_path.unlink(missing_ok=True)
            
            return output_path
        except Exception as e:
            log.error(f"TTS generation failed: {e}")
            return None

    def _convert_to_wav(self, input_path: Path, output_path: Path):
        """Convert audio to WAV using ffmpeg."""
        import imageio_ffmpeg
        ffmpeg_exe = os.getenv("FFMPEG_BINARY") or imageio_ffmpeg.get_ffmpeg_exe()
        
        cmd = [
            ffmpeg_exe, "-y",
            "-i", str(input_path),
            "-ar", "48000", "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def mix_audio(self, voice_path: Path, bgm_path: Optional[Path], output_path: Path, duration: float):
        """
        Mix voice and BGM with ducking.
        """
        try:
            log.info("🎚️ Mixing audio...")
            voice_clip = AudioFileClip(str(voice_path))
            
            # Pad voice with silence to match video duration
            # This prevents the "CompositeAudioClip" error if voice is shorter than video
            # But actually, we want the final audio to match the video duration exactly.
            
            clips = [voice_clip]

            if bgm_path and bgm_path.exists():
                bgm_clip = AudioFileClip(str(bgm_path))
                
                # Loop BGM if shorter
                if bgm_clip.duration < duration:
                    bgm_clip = afx.audio_loop(bgm_clip, duration=duration)
                else:
                    bgm_clip = bgm_clip.subclip(0, duration)
                
                # Ducking: Lower BGM volume when voice is present
                # Simple approach: global low volume for BGM, or complex sidechain
                # For reliability, we'll just set BGM to a lower level (-15dB approx 0.18)
                bgm_clip = bgm_clip.volumex(0.15)
                
                # Fade in/out BGM
                bgm_clip = bgm_clip.audio_fadein(1.0).audio_fadeout(2.0)
                
                clips.insert(0, bgm_clip) # BGM first (background)

            final_audio = CompositeAudioClip(clips)
            final_audio = final_audio.set_duration(duration)
            
            final_audio.write_audiofile(str(output_path), fps=48000, verbose=False, logger=None)
            return output_path

        except Exception as e:
            log.error(f"Audio mixing failed: {e}")
            raise
