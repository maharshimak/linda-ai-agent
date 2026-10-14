import os
import requests
import logging
import random
from pathlib import Path
from typing import List, Optional
from openai import OpenAI

log = logging.getLogger("video-engine")

class AssetManager:
    def __init__(self, pexels_api_key: Optional[str] = None, openai_api_key: Optional[str] = None):
        self.pexels_key = pexels_api_key or os.getenv("PEXELS_API_KEY")
        self.openai_client = OpenAI(api_key=openai_api_key) if openai_api_key else None
        self.image_model = os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")



    def generate_dalle_image(self, prompt: str, output_path: Path) -> Optional[Path]:
        """
        Generate an image using DALL-E 3 as a fallback.
        """
        if not self.openai_client:
            log.error("OpenAI client not initialized.")
            return None

        try:
            log.info(f"🎨 Generating DALL-E 3 image for: {prompt}")
            response = self.openai_client.images.generate(
                model=self.image_model,
                prompt=f"Cinematic, photorealistic, 16:9 aspect ratio. {prompt}",
                size="1536x1024",
                quality="high",
                n=1
            )
            
            image_url = response.data[0].url
            
            if image_url:
                image_data = requests.get(image_url).content
            elif getattr(response.data[0], 'b64_json', None):
                import base64
                image_data = base64.b64decode(response.data[0].b64_json)
            else:
                log.error(f"DALL-E returned no URL or b64_json. Response: {response}")
                raise ValueError(f"DALL-E API returned success but no image data. Response: {response}")
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_data)
            
            return output_path

        except Exception as e:
            log.error(f"DALL-E generation failed: {e}")
            raise e

    def download_file(self, url: str, output_path: Path) -> Optional[Path]:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return output_path
        except Exception as e:
            log.error(f"Download failed for {url}: {e}")
            return None
