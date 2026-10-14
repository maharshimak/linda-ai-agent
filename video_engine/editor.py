import logging
import os
from pathlib import Path
from typing import List, Tuple
from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip, TextClip, 
    ColorClip, VideoClip, vfx, concatenate_videoclips
)
from moviepy.video.fx.all import fadein, fadeout, resize, crop
import numpy as np
from PIL import Image, ImageFont, ImageDraw

log = logging.getLogger("video-engine")

# Monkey-patch for Pillow 10+ compatibility (moviepy uses ANTIALIAS)
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

class VideoEditor:
    def __init__(self):
        self.width = 1080
        self.height = 1920
        self.fps = 30 # Standard for social media
        
        # Font setup
        self.font_path = os.getenv("WINDOWS_FONT_BOLD", r"C:\Windows\Fonts\arialbd.ttf")

    def create_clip(self, asset_path: Path, duration: float, text: str) -> VideoFileClip:
        """
        Create a single video clip from an image with text overlay.
        CRITICAL: Strictly image-only. No video files, no gradients.
        """
        try:
            # Load asset
            if asset_path and asset_path.exists():
                # Image - MUST BE ANIMATED (never static slideshow)
                log.info("🎬 Animating image with cinematic motion")
                clip = ImageClip(str(asset_path)).set_duration(duration)
                clip = self._animate_image(clip, duration)
            else:
                raise ValueError(f"Image asset missing: {asset_path}")

            # Resize to vertical 9:16
            clip = self._resize_to_vertical(clip)
            
            # Add text overlay
            txt_clip = self._create_text_overlay(text, duration)
            
            # Composite
            final_clip = CompositeVideoClip([clip, txt_clip], size=(self.width, self.height))
            final_clip = final_clip.set_duration(duration)
            
            # Transitions
            final_clip = fadein(final_clip, 0.5)
            
            return final_clip

        except Exception as e:
            log.error(f"Clip creation failed: {e}")
            raise

    def _animate_image(self, clip: ImageClip, duration: float) -> ImageClip:
        """
        Apply cinematic animation to images - NEVER static slideshow.
        Randomly chooses: zoom in/out, pan left/right, parallax, or combined effects.
        """
        import random
        effect = random.choice(['zoom_in', 'zoom_out', 'pan_right', 'pan_left', 'parallax'])
        
        if effect == 'zoom_in':
            # Slow zoom in (Ken Burns)
            clip = clip.resize(lambda t: 1 + 0.15 * (t / duration))
        elif effect == 'zoom_out':
            # Slow zoom out
            clip = clip.resize(lambda t: 1.15 - 0.15 * (t / duration))
        elif effect == 'pan_right':
            # Pan from left to right
            clip = clip.resize(1.2)  # Oversized for panning
            clip = clip.set_position(lambda t: (-int(100 * t / duration), 'center'))
        elif effect == 'pan_left':
            # Pan from right to left
            clip = clip.resize(1.2)
            clip = clip.set_position(lambda t: (int(100 * t / duration), 'center'))
        else:  # parallax
            # Parallax effect (zoom + subtle pan)
            clip = clip.resize(lambda t: 1 + 0.12 * (t / duration))
            clip = clip.set_position(lambda t: (int(20 * np.sin(t * np.pi / duration)), 'center'))
        
        return clip



    def _resize_to_vertical(self, clip):
        """Center crop and resize to 1080x1920"""
        w, h = clip.size
        target_ratio = self.width / self.height
        current_ratio = w / h
        
        if current_ratio > target_ratio:
            # Too wide, crop width
            new_w = int(h * target_ratio)
            clip = crop(clip, x1=(w - new_w) // 2, width=new_w, height=h)
        else:
            # Too tall, crop height
            new_h = int(w / target_ratio)
            clip = crop(clip, y1=(h - new_h) // 2, width=w, height=new_h)
            
        return resize(clip, height=self.height)

    def _create_text_overlay(self, text: str, duration: float) -> ImageClip:
        """Create a stylish text overlay using Pillow (more robust than TextClip)"""
        img = Image.new('RGBA', (self.width, self.height), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(self.font_path, 60)
        except:
            font = ImageFont.load_default()

        # Word wrap
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            # Check width
            w = draw.textlength(" ".join(current_line), font=font)
            if w > self.width - 200:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        # Draw text with shadow/outline
        y = self.height * 0.75
        for line in lines:
            w = draw.textlength(line, font=font)
            x = (self.width - w) // 2
            
            # Shadow
            draw.text((x+4, y+4), line, font=font, fill=(0,0,0,200))
            # Text
            draw.text((x, y), line, font=font, fill=(255,255,255,255))
            y += 80
            
        return ImageClip(np.array(img)).set_duration(duration)

    def _create_watermark_overlay(self, duration: float) -> ImageClip:
        """
        Create 'Made with MAK AI' watermark overlay.
        VIRAL MECHANIC: Every free video promotes the platform.
        """
        img = Image.new('RGBA', (self.width, self.height), (0,0,0,0))
        draw = ImageDraw.Draw(img)
        
        try:
            # Use bold font for brand
            font = ImageFont.truetype(self.font_path, 40)
        except:
            font = ImageFont.load_default()
        
        text = "Made with MAK AI 🎬"
        
        # Calculate size
        w = draw.textlength(text, font=font)
        h = 50 # approx height
        
        # Position: Bottom Right with padding
        x = self.width - w - 40
        y = self.height - 120 # Above progress bar area
        
        # Draw background pill
        pad = 15
        draw.rectangle(
            (x - pad, y - pad, x + w + pad, y + h + pad),
            fill=(0, 0, 0, 180), # Semi-transparent black
            outline=(255, 255, 255, 100), # Subtle white border
            width=2
        )
        
        # Draw text
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        
        return ImageClip(np.array(img)).set_duration(duration)

    def assemble_video(self, clips: List[VideoFileClip], audio_path: Path, output_path: Path, add_watermark: bool = True):
        """Concatenate clips and add audio"""
        try:
            log.info("🎞️ Assembling final video...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Add audio
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(str(audio_path))
            final_video = final_video.set_audio(audio)
            
            # Add watermark if requested
            if add_watermark:
                log.info("💧 Adding viral watermark")
                watermark = self._create_watermark_overlay(final_video.duration)
                final_video = CompositeVideoClip([final_video, watermark])
            
            # Write file
            final_video.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset="medium",
                ffmpeg_params=["-crf", "23"]
            )
            return output_path
            
        except Exception as e:
            log.error(f"Video assembly failed: {e}")
            raise
