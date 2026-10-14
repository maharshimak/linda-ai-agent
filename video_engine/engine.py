import os
import logging
import shutil
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from .scripting import ScriptGenerator, Language
from .assets import AssetManager
from .audio import AudioManager
from .editor import VideoEditor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("video-engine")

class VideoEngine:
    def __init__(self):
        load_dotenv()
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.pexels_key = os.getenv("PEXELS_API_KEY")
        
        if not self.openai_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.script_gen = ScriptGenerator(self.openai_key)
        self.asset_mgr = AssetManager(self.pexels_key, self.openai_key)
        self.audio_mgr = AudioManager(self.openai_key)
        self.editor = VideoEditor()
        
        self.output_dir = Path("out")
        self.output_dir.mkdir(exist_ok=True)

    def generate_video(self, topic: str, language: str = "English", duration: str = "30s") -> Path:
        """
        Main pipeline to generate a video using ONLY OpenAI-generated images.
        Perfect audio-visual sync, no random gradients or abstract visuals.
        """
        log.info(f"🚀 Starting generation: {topic} ({language}, {duration})")
        
        # Parse target duration
        target_seconds = int(duration.replace('s', ''))
        log.info(f"🎯 Target duration: {target_seconds} seconds")
        
        # 1. Generate Script
        lang_enum = Language(language)
        script = self.script_gen.generate_script(topic, lang_enum, duration)
        log.info(f"✅ Script generated: {script.title}")
        log.info(f"📊 Script has {len(script.beats)} beats")
        
        # 2. Build Scenes from Script
        scenes = []
        
        # Hook scene
        scenes.append({
            'index': 0,
            'text': script.hook,
            'visual_prompt': f"Cinematic opening scene: {script.hook}. Ultra-realistic, 16:9, high detail, dramatic lighting, no text",
            'role': 'hook'
        })
        
        # Beat scenes
        for i, beat in enumerate(script.beats):
            scenes.append({
                'index': i + 1,
                'text': beat.text,
                'visual_prompt': f"{beat.visual_prompt}. Cinematic, ultra-realistic, 16:9, high detail, rich lighting, no text, no abstract patterns",
                'role': 'beat'
            })
        
        # CTA scene
        scenes.append({
            'index': len(script.beats) + 1,
            'text': script.cta,
            'visual_prompt': f"Cinematic closing scene: {script.cta}. Ultra-realistic, 16:9, high detail, inspiring lighting, no text",
            'role': 'cta'
        })
        
        log.info(f"📋 Created {len(scenes)} scenes from script")
        
        # 3. Generate Assets (Audio & Images) in Parallel
        log.info("🚀 Starting parallel asset generation...")
        import concurrent.futures
        
        scene_assets = [None] * len(scenes)
        
        def process_scene_assets(scene):
            """Helper to generate both audio and image for a scene"""
            idx = scene['index']
            log.info(f"⚡ Processing Scene {idx}...")
            
            # A. Generate Audio
            audio_file = self.output_dir / f"scene_{idx}_audio.wav"
            audio_path = None
            duration = 0.0
            
            try:
                audio_path = self.audio_mgr.generate_tts(scene['text'], audio_file)
                if audio_path and audio_path.exists():
                    from moviepy.editor import AudioFileClip
                    audio_clip = AudioFileClip(str(audio_path))
                    duration = audio_clip.duration
                    audio_clip.close()
                    log.info(f"   🎙️ Scene {idx} Audio: {duration:.2f}s")
                else:
                    # Fallback estimate
                    duration = len(scene['text'].split()) / 2.5
                    log.warning(f"   ⚠️ Scene {idx} Audio failed, estimate: {duration:.2f}s")
            except Exception as e:
                log.error(f"   ❌ Scene {idx} Audio Error: {e}")
                duration = len(scene['text'].split()) / 2.5

            # B. Generate Image
            image_file = self.output_dir / "cache" / f"scene_{idx}_image.png"
            image_file.parent.mkdir(parents=True, exist_ok=True)
            image_path = None
            
            try:
                # Try generation
                image_path = self.asset_mgr.generate_dalle_image(scene['visual_prompt'], image_file)
                log.info(f"   🎨 Scene {idx} Image: OK")
            except Exception as e1:
                log.warning(f"   ⚠️ Scene {idx} Image attempt 1 failed: {e1}")
                try:
                    # Retry once
                    image_path = self.asset_mgr.generate_dalle_image(scene['visual_prompt'], image_file)
                    log.info(f"   🎨 Scene {idx} Image retry: OK")
                except Exception as e2:
                    log.error(f"   ❌ Scene {idx} Image failed: {e2}")
                    raise ValueError(f"Failed to generate image for scene {idx}: {str(e2)}")

            return (idx, image_path, duration, audio_path)

        # Run in parallel
        # Limit workers to 5 to avoid hitting OpenAI rate limits too hard
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_scene = {executor.submit(process_scene_assets, scene): scene for scene in scenes}
            
            for future in concurrent.futures.as_completed(future_to_scene):
                scene = future_to_scene[future]
                try:
                    idx, img_path, dur, aud_path = future.result()
                    # Store results in correct order
                    scene_assets[idx] = (img_path, dur, aud_path)
                except Exception as exc:
                    log.error(f"Scene {scene['index']} generation generated an exception: {exc}")
                    raise exc

        # Unpack results
        scene_images = [x[0] for x in scene_assets]
        scene_durations = [x[1] for x in scene_assets]
        scene_audio_files = [x[2] for x in scene_assets]
        
        total_audio_duration = sum(scene_durations)
        log.info(f"📊 Total audio duration: {total_audio_duration:.2f}s")
        
        # 5. Create Video Clips from Images with Precise Timing
        clips = []
        for i, (scene, image_path, duration, audio_path) in enumerate(zip(scenes, scene_images, scene_durations, scene_audio_files)):
            log.info(f"🎬 Creating clip {i+1}/{len(scenes)}: {duration:.2f}s")
            
            if image_path and image_path.exists():
                # Create animated image clip
                clip = self.editor.create_clip(image_path, duration, scene['text'])
            else:
                # Should not happen due to check above, but just in case
                raise ValueError(f"Image path missing for scene {i}")
            
            # Attach audio if available
            if audio_path and audio_path.exists():
                from moviepy.editor import AudioFileClip
                audio_clip = AudioFileClip(str(audio_path))
                clip = clip.set_audio(audio_clip)
            
            clips.append(clip)
            log.info(f"   ✅ Clip created: {duration:.2f}s")
        
        log.info(f"📊 Total clips created: {len(clips)}")
        
        # 6. Concatenate All Clips
        from moviepy.editor import concatenate_videoclips
        log.info("🎞️ Concatenating all clips...")
        final_video = concatenate_videoclips(clips, method="compose")
        log.info(f"✅ Final video duration: {final_video.duration:.2f}s")
        
        # 7. Add Background Music (Optional)
        bgm_path = Path("assets/bgm/epic.mp3")
        if bgm_path.exists():
            log.info("🎵 Adding background music...")
            from moviepy.editor import AudioFileClip, CompositeAudioClip, afx
            
            video_audio = final_video.audio
            bgm_clip = AudioFileClip(str(bgm_path))
            
            # Loop and duck BGM
            if bgm_clip.duration < final_video.duration:
                bgm_clip = afx.audio_loop(bgm_clip, duration=final_video.duration)
            else:
                bgm_clip = bgm_clip.subclip(0, final_video.duration)
                
            bgm_clip = bgm_clip.volumex(0.12).audio_fadein(1).audio_fadeout(2)
            
            final_audio = CompositeAudioClip([bgm_clip, video_audio])
            final_video = final_video.set_audio(final_audio)
            log.info("✅ Background music added")
        else:
            log.info(f"ℹ️ No BGM file found at {bgm_path}, skipping")
        
        # 8. Render Final Video
        final_filename = f"MASTER_{script.title.replace(' ', '_')[:20]}.mp4"
        final_path = self.output_dir / final_filename
        
        log.info(f"💾 Rendering final video: {final_filename}")
        log.info(f"📊 Final duration: {final_video.duration:.2f}s (target: {target_seconds}s)")
        
        final_video.write_videofile(
            str(final_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            ffmpeg_params=["-crf", "23"],
            threads=4
        )
        
        log.info(f"✅ Video saved: {final_path}")
        return final_path



if __name__ == "__main__":
    # CLI Test
    engine = VideoEngine()
    engine.generate_video("The Future of AI", "English", "30s")
