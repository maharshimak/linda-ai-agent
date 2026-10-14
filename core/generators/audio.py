"""
Audio Generator
AI-powered audio generation including TTS and audio processing.
Upgraded for Hollywood-grade professional audio output.
"""
import os
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from openai import OpenAI

from ..utils.helpers import find_ffmpeg

log = logging.getLogger("core.generators.audio")


class AudioGenerator:
    """
    Generates professional-grade audio for video scenes using AI TTS.
    Optimized for cinematic narration with broadcast-standard output.
    """
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-4o-mini-tts",
        voice: str = "onyx"
    ):
        """
        Initialize audio generator with premium TTS settings.
        
        Default voice 'onyx' provides deep, authoritative narration.
        Alternative voices: nova (warm female), alloy (neutral), echo (natural male)
        """
        self.client = OpenAI(api_key=api_key, timeout=120)
        self.model = model
        self.default_voice = voice
        self.ffmpeg = find_ffmpeg()
        
        # Broadcast standard loudness targets
        self.target_lufs = -14.0  # Streaming platform standard
        self.true_peak = -1.0
        self.loudness_range = 7.0
    
    def generate_tts(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        speed: float = 1.0
    ) -> Optional[Path]:
        """
        Generate text-to-speech audio.
        
        Args:
            text: The text to convert to speech
            output_path: Where to save the audio (WAV format)
            voice: Voice to use (nova, alloy, echo, fable, onyx, shimmer)
            speed: Speech speed (0.25 to 4.0)
            
        Returns:
            Path to the generated audio file, or None on failure
        """
        log.info(f"🎤 Generating TTS: {text[:50]}...")
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice or self.default_voice,
                input=text,
                speed=speed
            )
            
            # Save as MP3 first (TTS API returns MP3)
            mp3_path = output_path.with_suffix(".mp3")
            response.stream_to_file(mp3_path)
            
            # Convert to WAV for better compatibility
            if self.ffmpeg:
                self._convert_to_wav(mp3_path, output_path)
                mp3_path.unlink(missing_ok=True)
            else:
                # Fallback: just rename
                shutil.move(str(mp3_path), str(output_path))
            
            log.info(f"✅ TTS saved: {output_path.name}")
            return output_path
            
        except Exception as e:
            log.error(f"TTS generation failed: {e}")
            return None
    
    def _convert_to_wav(self, input_path: Path, output_path: Path):
        """Convert audio to WAV format using FFmpeg."""
        cmd = [
            self.ffmpeg, "-y",
            "-i", str(input_path),
            "-ar", "48000",
            "-ac", "2",
            str(output_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    
    def get_duration(self, audio_path: Path) -> float:
        """Get the duration of an audio file in seconds."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(str(audio_path))
            return len(audio) / 1000.0
        except Exception as e:
            log.warning(f"Could not get audio duration: {e}")
            return 0.0
    
    def transcribe(self, audio_path: Path) -> dict:
        """
        Transcribe audio and get word-level timings.
        
        Returns:
            Dict with 'text' and 'segments' keys
        """
        log.info(f"📝 Transcribing: {audio_path.name}...")
        
        try:
            with open(audio_path, "rb") as f:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    response_format="verbose_json",
                    temperature=0.0
                )
            
            return {
                "text": response.text,
                "segments": [
                    {
                        "text": seg.get("text", "").strip(),
                        "start": float(seg.get("start", 0)),
                        "end": float(seg.get("end", 0))
                    }
                    for seg in getattr(response, "segments", [])
                    if seg.get("text", "").strip()
                ]
            }
            
        except Exception as e:
            log.error(f"Transcription failed: {e}")
            return {"text": "", "segments": []}
    
    def mix_audio(
        self,
        voice_path: Path,
        bgm_path: Optional[Path],
        output_path: Path,
        duration: float,
        bgm_volume: float = 0.12
    ) -> Path:
        """
        Hollywood-grade audio mixing with professional mastering.
        
        Features:
        - Sidechain compression (music ducks under voice)
        - Voice EQ enhancement for clarity
        - BGM EQ to prevent frequency clashing
        - Broadcast-standard loudness normalization
        
        Args:
            voice_path: Path to voice audio
            bgm_path: Path to background music (optional)
            output_path: Where to save mixed audio
            duration: Target duration in seconds
            bgm_volume: Background music volume (0.0 to 1.0)
            
        Returns:
            Path to professionally mixed audio
        """
        log.info("🎬 Hollywood-grade audio mastering...")
        
        if not self.ffmpeg:
            log.warning("FFmpeg not found, returning voice only")
            shutil.copy(voice_path, output_path)
            return output_path
        
        if bgm_path and bgm_path.exists():
            # Professional mixing with sidechain compression
            # The music will automatically lower when voice is speaking
            filter_complex = (
                # BGM processing: EQ to reduce mid-frequencies (voice range)
                f"[1:a]volume={bgm_volume},"
                "equalizer=f=250:t=q:w=1.5:g=-3,"   # Cut low-mids
                "equalizer=f=3000:t=q:w=2:g=-2,"    # Cut voice frequencies
                "equalizer=f=8000:t=h:w=200:g=2,"   # Boost highs for shimmer
                f"aloop=loop=-1:size=2e+09,atrim=0:{duration}[bgm];"
                
                # Sidechain compression: BGM ducks when voice is present
                "[bgm][0:a]sidechaincompress="
                "threshold=0.02:"      # Very sensitive trigger
                "ratio=8:"              # Strong compression when voice present
                "attack=5:"             # Fast attack (5ms)
                "release=250:"          # Smooth release (250ms)
                "makeup=3"              # Makeup gain
                "[ducked_bgm];"
                
                # Voice processing: enhance clarity
                "[0:a]"
                "equalizer=f=80:t=h:w=100:g=-3,"    # Cut rumble
                "equalizer=f=200:t=q:w=2:g=1,"      # Warm body
                "equalizer=f=3000:t=q:w=2:g=2,"     # Presence boost
                "equalizer=f=8000:t=h:w=200:g=1,"   # Air/brilliance
                "acompressor=threshold=0.1:ratio=3:attack=10:release=100:makeup=2"  # Light compression
                "[voice_eq];"
                
                # Final mix with proper balance
                "[ducked_bgm][voice_eq]amix=inputs=2:duration=first:weights=0.3 0.7,"
                
                # Add subtle stereo widening for cinematic feel
                "stereowiden=delay=15:drymix=0.8,"
                
                # Final limiting to prevent clipping
                f"alimiter=limit={self.true_peak}dB:attack=2:release=50,"
                
                # Broadcast loudness normalization
                f"loudnorm=I={self.target_lufs}:TP={self.true_peak}:LRA={self.loudness_range}[out]"
            )
            
            cmd = [
                self.ffmpeg, "-y",
                "-i", str(voice_path),
                "-i", str(bgm_path),
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-ar", "48000",
                "-ac", "2",
                "-b:a", "320k",  # High quality audio bitrate
                str(output_path)
            ]
        else:
            # Voice-only with professional processing
            filter_chain = (
                "equalizer=f=80:t=h:w=100:g=-3,"    # Cut rumble
                "equalizer=f=200:t=q:w=2:g=1,"      # Warm body
                "equalizer=f=3000:t=q:w=2:g=2,"     # Presence boost
                "equalizer=f=8000:t=h:w=200:g=1,"   # Air
                "acompressor=threshold=0.1:ratio=3:attack=10:release=100:makeup=2,"
                f"alimiter=limit={self.true_peak}dB,"
                f"loudnorm=I={self.target_lufs}:TP={self.true_peak}:LRA={self.loudness_range}"
            )
            
            cmd = [
                self.ffmpeg, "-y",
                "-i", str(voice_path),
                "-af", filter_chain,
                "-ar", "48000",
                "-ac", "2",
                "-b:a", "320k",
                str(output_path)
            ]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                log.info(f"✅ Professional audio mastered: {output_path.name}")
            else:
                log.warning(f"Audio mastering had issues, using fallback")
                shutil.copy(voice_path, output_path)
            return output_path
        except Exception as e:
            log.error(f"Audio mixing failed: {e}")
            shutil.copy(voice_path, output_path)
            return output_path
    
    def normalize_loudness(
        self,
        input_path: Path,
        output_path: Path,
        target_lufs: float = -14.0
    ) -> Path:
        """
        Normalize audio loudness to broadcast standards.
        
        Args:
            input_path: Source audio
            output_path: Destination
            target_lufs: Target loudness in LUFS (-14 is standard for streaming)
            
        Returns:
            Path to normalized audio
        """
        if not self.ffmpeg:
            shutil.copy(input_path, output_path)
            return output_path
        
        cmd = [
            self.ffmpeg, "-y",
            "-i", str(input_path),
            "-af", f"loudnorm=I={target_lufs}:TP=-1.0:LRA=7",
            "-ar", "48000",
            "-ac", "2",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return output_path
        except Exception:
            shutil.copy(input_path, output_path)
            return output_path
