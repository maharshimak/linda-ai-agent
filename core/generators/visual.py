"""
Visual Generator
AI-powered image generation for video scenes.
Upgraded for Hollywood-grade cinematic output.
"""
import io
import base64
import logging
import requests
import numpy as np
from pathlib import Path
from typing import Optional

from PIL import Image, ImageFilter, ImageEnhance
from openai import OpenAI

from ..models import Emotion
from ..effects.grading import grade_image_by_emotion, add_film_grain, add_vignette

log = logging.getLogger("core.generators.visual")


class VisualGenerator:
    """
    Generates images for video scenes using AI models.
    Upgraded for Hollywood-grade cinematic output.
    """
    
    def __init__(self, api_key: str, model: str = "dall-e-3"):
        """
        Initialize with dall-e-3 for vertical format support.
        Note: gpt-image-1 doesn't support 1024x1792 vertical size.
        """
        self.client = OpenAI(api_key=api_key, timeout=180)
        self.model = model
    
    def generate(
        self,
        prompt: str,
        output_path: Path,
        size: str = "1024x1792",
        quality: str = "hd",
        emotion: Optional[Emotion] = None
    ) -> Path:
        """
        Generate an image from a prompt.
        
        Args:
            prompt: Visual description for the image
            output_path: Where to save the image
            size: Image size (1024x1024, 1024x1792, 1792x1024)
            quality: Quality level ('standard' or 'hd' for dall-e-3)
            emotion: Optional emotion for post-processing grading
            
        Returns:
            Path to the saved image
        """
        log.info(f"🎨 Generating cinematic image...")
        log.debug(f"   Prompt: {prompt[:100]}...")
        
        # Try generation with fallback chain
        last_error = None
        quality_options = ["hd", "standard"] if quality == "hd" else ["standard"]
        
        for attempt, q in enumerate(quality_options):
            try:
                log.info(f"   Attempt {attempt + 1}/{len(quality_options)} [quality={q}]")
                response = self.client.images.generate(
                    model=self.model,
                    prompt=prompt,
                    size=size,
                    quality=q,
                    n=1,
                )
                break  # Success
            except Exception as e:
                last_error = e
                log.warning(f"   Attempt {attempt + 1} failed: {e}")
                if attempt == len(quality_options) - 1:
                    raise last_error
                continue
        
        try:
            
            # Handle response (URL or base64)
            image_data = response.data[0]
            
            if hasattr(image_data, 'b64_json') and image_data.b64_json:
                img_bytes = base64.b64decode(image_data.b64_json)
            elif hasattr(image_data, 'url') and image_data.url:
                img_bytes = requests.get(image_data.url).content
            else:
                raise ValueError("No image data in response")
            
            # Load and process
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            
            # Resize to 9:16 vertical format (1080x1920)
            img = self._resize_to_vertical(img)
            
            # Apply cinematic enhancements
            img = self._enhance_cinematic(img)
            
            # Apply emotion-based grading if specified
            if emotion:
                img = grade_image_by_emotion(img, emotion)
            
            # Save
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, format="JPEG", quality=98, optimize=True)
            
            log.info(f"✅ Image saved: {output_path.name}")
            return output_path
            
        except Exception as e:
            log.error(f"Image generation failed: {e}")
            # Create placeholder
            return self._create_placeholder(output_path, prompt)
    
    def _resize_to_vertical(self, img: Image.Image) -> Image.Image:
        """Center-crop and resize to 1080x1920 (9:16)."""
        target_w, target_h = 1080, 1920
        target_ratio = target_w / target_h
        
        iw, ih = img.size
        img_ratio = iw / ih
        
        if img_ratio > target_ratio:
            # Too wide - crop width
            new_w = int(ih * target_ratio)
            x0 = (iw - new_w) // 2
            img = img.crop((x0, 0, x0 + new_w, ih))
        else:
            # Too tall - crop height
            new_h = int(iw / target_ratio)
            y0 = (ih - new_h) // 2
            img = img.crop((0, y0, iw, y0 + new_h))
        
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    def _enhance_cinematic(self, img: Image.Image, emotion: Optional[Emotion] = None) -> Image.Image:
        """
        Apply Hollywood-grade cinematic enhancements.
        Includes sharpening, color grading, vignette, and film grain.
        """
        # 1. Precision sharpening for crisp details
        img = img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=2))
        
        # 2. Cinematic color enhancement
        img = ImageEnhance.Color(img).enhance(1.15)  # Richer colors
        
        # 3. S-curve contrast for cinematic depth
        img = ImageEnhance.Contrast(img).enhance(1.08)
        
        # 4. Slight brightness adjustment for premium look
        img = ImageEnhance.Brightness(img).enhance(1.02)
        
        # 5. Apply cinematic vignette (darkened edges)
        img = add_vignette(img, strength=0.25)
        
        # 6. Add subtle film grain for organic texture
        img = add_film_grain(img, intensity=0.012)
        
        # 7. Apply teal-orange color grading (blockbuster look)
        img = self._apply_teal_orange_grade(img, intensity=0.15)
        
        return img
    
    def _apply_teal_orange_grade(self, img: Image.Image, intensity: float = 0.2) -> Image.Image:
        """
        Apply subtle teal-orange color grading (Hollywood blockbuster look).
        Shadows get teal push, highlights get orange/warm push.
        """
        arr = np.array(img, dtype=np.float32)
        
        # Calculate luminance for each pixel
        luminance = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
        luminance = luminance / 255.0  # Normalize to 0-1
        
        # Shadows (low luminance) → push toward teal (reduce red, boost blue)
        shadow_mask = np.clip(1.0 - luminance * 2, 0, 1)  # Affects darker areas
        arr[:,:,0] -= shadow_mask * intensity * 20  # Reduce red in shadows
        arr[:,:,2] += shadow_mask * intensity * 15  # Boost blue in shadows
        
        # Highlights (high luminance) → push toward orange/warm
        highlight_mask = np.clip(luminance * 2 - 1, 0, 1)  # Affects brighter areas
        arr[:,:,0] += highlight_mask * intensity * 15  # Boost red in highlights
        arr[:,:,1] += highlight_mask * intensity * 8   # Slight green boost
        
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)
    
    def _create_placeholder(self, output_path: Path, prompt: str) -> Path:
        """Create a placeholder image when generation fails."""
        from PIL import ImageDraw, ImageFont
        
        img = Image.new("RGB", (1080, 1920), (12, 12, 18))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 48)
        except Exception:
            font = ImageFont.load_default()
        
        text = "Image Generation Failed"
        draw.text((540, 960), text, fill=(200, 200, 200), font=font, anchor="mm")
        
        # Small prompt preview
        try:
            small_font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 24)
        except Exception:
            small_font = font
        
        preview = prompt[:80] + "..." if len(prompt) > 80 else prompt
        draw.text((540, 1020), preview, fill=(100, 100, 100), font=small_font, anchor="mm")
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "JPEG", quality=95)
        
        return output_path
    
    def generate_batch(
        self,
        prompts: list,
        output_dir: Path,
        emotions: list = None
    ) -> list:
        """
        Generate multiple images.
        
        Args:
            prompts: List of visual prompts
            output_dir: Directory for output images
            emotions: List of emotions for each image
            
        Returns:
            List of output paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        
        emotions = emotions or [None] * len(prompts)
        
        for i, (prompt, emotion) in enumerate(zip(prompts, emotions)):
            output_path = output_dir / f"scene_{i+1:02}.jpg"
            path = self.generate(prompt, output_path, emotion=emotion)
            paths.append(path)
        
        return paths
