"""
A/B Test Video Variant Generator for MAK AI
Automatically creates multiple versions of videos for testing.

Features:
- Generate 3 variants with different hooks/styles
- Parallel generation for efficiency
- Variant comparison analytics
- Platform-optimized variants
"""

import logging
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from pathlib import Path

log = logging.getLogger("ab_testing")


class VariantType(Enum):
    """Types of video variants"""
    QUESTION_HOOK = "question_hook"
    SHOCK_HOOK = "shock_hook"
    STORY_HOOK = "story_hook"
    LISTICLE = "listicle"
    CHALLENGE = "challenge"
    TUTORIAL = "tutorial"


@dataclass
class VariantConfig:
    """Configuration for a video variant"""
    id: str
    name: str
    variant_type: VariantType
    hook_template: str
    caption_style: str
    music_mood: str
    thumbnail_style: str
    color_adjustment: Optional[str] = None
    pacing: str = "standard"


@dataclass
class GeneratedVariant:
    """Result of variant generation"""
    id: str
    config: VariantConfig
    video_path: str
    thumbnail_path: Optional[str] = None
    hook_text: str = ""
    predicted_score: float = 0.0
    generation_time: float = 0.0


@dataclass
class ABTestResult:
    """Result of A/B test generation"""
    base_topic: str
    variants: List[GeneratedVariant]
    recommended_variant: str
    recommendation_reason: str
    total_generation_time: float


class VideoVariantGenerator:
    """
    Generate multiple video variants for A/B testing.
    
    Creates 3 distinct versions of each video with:
    - Different hooks (question, shock, story)
    - Different caption styles
    - Different music moods
    - Different thumbnail approaches
    """
    
    # Pre-defined variant templates
    VARIANT_TEMPLATES = [
        VariantConfig(
            id="variant_a_question",
            name="Question Hook",
            variant_type=VariantType.QUESTION_HOOK,
            hook_template="What if I told you that {topic}...",
            caption_style="bold",
            music_mood="intense",
            thumbnail_style="curiosity_face",
            pacing="fast"
        ),
        VariantConfig(
            id="variant_b_shock",
            name="Shock Hook",
            variant_type=VariantType.SHOCK_HOOK,
            hook_template="This will blow your mind: {topic}",
            caption_style="neon",
            music_mood="mysterious",
            thumbnail_style="dramatic_text",
            pacing="varied"
        ),
        VariantConfig(
            id="variant_c_story",
            name="Story Hook",
            variant_type=VariantType.STORY_HOOK,
            hook_template="Here's a story you need to hear about {topic}...",
            caption_style="minimal",
            music_mood="emotional",
            thumbnail_style="cinematic",
            pacing="slow"
        ),
    ]
    
    # Hook templates by category
    HOOK_TEMPLATES = {
        VariantType.QUESTION_HOOK: [
            "What if I told you that {topic}...",
            "Have you ever wondered about {topic}?",
            "Why does {topic} matter more than you think?",
            "What's the truth about {topic}?",
            "Did you know this about {topic}?"
        ],
        VariantType.SHOCK_HOOK: [
            "This will blow your mind: {topic}",
            "You won't believe what I discovered about {topic}",
            "The shocking truth about {topic}",
            "Nobody's talking about this: {topic}",
            "This changes everything about {topic}"
        ],
        VariantType.STORY_HOOK: [
            "Here's a story you need to hear about {topic}...",
            "Let me tell you about {topic}...",
            "The incredible journey of {topic}",
            "Once upon a time, {topic}...",
            "This is the story of {topic}"
        ],
        VariantType.LISTICLE: [
            "5 things you didn't know about {topic}",
            "3 secrets of {topic} revealed",
            "Top facts about {topic}",
            "Everything you need to know about {topic}"
        ],
        VariantType.CHALLENGE: [
            "Can you handle the truth about {topic}?",
            "I bet you didn't know this about {topic}",
            "Most people get {topic} wrong. Here's why.",
            "Think you know {topic}? Think again."
        ],
        VariantType.TUTORIAL: [
            "Here's how {topic} actually works",
            "The complete guide to {topic}",
            "Master {topic} in 60 seconds",
            "Everything explained: {topic}"
        ]
    }
    
    # Caption style configurations
    CAPTION_STYLES = {
        "bold": {
            "font": "Arial-Bold",
            "size": 60,
            "color": "yellow",
            "stroke": True,
            "animation": "scale_in"
        },
        "neon": {
            "font": "Orbitron",
            "size": 52,
            "color": "#00ff88",
            "stroke": False,
            "animation": "glow_pulse"
        },
        "minimal": {
            "font": "Helvetica",
            "size": 48,
            "color": "white",
            "stroke": True,
            "animation": "fade"
        },
        "gradient": {
            "font": "Montserrat-Bold",
            "size": 54,
            "color": "gradient_purple",
            "stroke": False,
            "animation": "slide_up"
        }
    }
    
    # Thumbnail style configurations
    THUMBNAIL_STYLES = {
        "curiosity_face": {
            "include_face": True,
            "expression": "surprised",
            "text_overlay": True,
            "background": "blurred"
        },
        "dramatic_text": {
            "include_face": False,
            "expression": None,
            "text_overlay": True,
            "background": "gradient",
            "text_size": "large"
        },
        "cinematic": {
            "include_face": False,
            "expression": None,
            "text_overlay": False,
            "background": "scene",
            "filter": "cinematic_color"
        }
    }
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize variant generator"""
        self.output_dir = output_dir or Path("out/variants")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        log.info("🧪 A/B Test Variant Generator initialized")
    
    def _generate_hook(self, topic: str, variant_type: VariantType) -> str:
        """Generate hook text for a variant"""
        import random
        templates = self.HOOK_TEMPLATES.get(variant_type, self.HOOK_TEMPLATES[VariantType.QUESTION_HOOK])
        template = random.choice(templates)
        
        # Extract key phrase from topic
        key_phrase = topic.lower()
        if len(key_phrase) > 50:
            key_phrase = key_phrase[:50] + "..."
        
        return template.format(topic=key_phrase)
    
    def _predict_variant_score(self, config: VariantConfig, topic: str) -> float:
        """
        Predict the viral potential score for a variant.
        This is a simplified heuristic - could be enhanced with ML.
        """
        base_score = 50.0
        
        # Hook type bonuses
        hook_bonuses = {
            VariantType.SHOCK_HOOK: 15,
            VariantType.QUESTION_HOOK: 12,
            VariantType.CHALLENGE: 10,
            VariantType.STORY_HOOK: 8,
            VariantType.LISTICLE: 7,
            VariantType.TUTORIAL: 5
        }
        base_score += hook_bonuses.get(config.variant_type, 0)
        
        # Caption style bonuses
        caption_bonuses = {
            "bold": 10,
            "neon": 8,
            "gradient": 6,
            "minimal": 4
        }
        base_score += caption_bonuses.get(config.caption_style, 0)
        
        # Music mood impact
        music_bonuses = {
            "intense": 8,
            "mysterious": 6,
            "emotional": 5,
            "upbeat": 7,
            "calm": 3
        }
        base_score += music_bonuses.get(config.music_mood, 0)
        
        # Pacing impact
        pacing_bonuses = {
            "fast": 8,
            "varied": 5,
            "slow": 2
        }
        base_score += pacing_bonuses.get(config.pacing, 0)
        
        # Add some randomness for realism
        import random
        base_score += random.uniform(-5, 5)
        
        return min(max(base_score, 0), 100)
    
    async def generate_single_variant(
        self,
        topic: str,
        config: VariantConfig,
        base_settings: Dict[str, Any]
    ) -> GeneratedVariant:
        """
        Generate a single video variant.
        
        Args:
            topic: Original video topic
            config: Variant configuration
            base_settings: Base video generation settings
        """
        import time
        start_time = time.time()
        
        log.info(f"🎬 Generating variant: {config.name}")
        
        # Generate customized hook
        hook_text = self._generate_hook(topic, config.variant_type)
        
        # Modify topic with hook
        modified_topic = f"{hook_text}\n\n{topic}"
        
        # Prepare variant-specific settings
        variant_settings = {
            **base_settings,
            "caption_style": config.caption_style,
            "music_mood": config.music_mood,
            "pacing": config.pacing
        }
        
        # In production, this would call the actual video engine
        # For now, simulate generation
        try:
            from video_engine.engine import VideoEngine
            
            engine = VideoEngine()
            video_path = engine.generate_video(
                topic=modified_topic,
                language=variant_settings.get("language", "English"),
                duration=variant_settings.get("duration", "30s")
            )
            video_path_str = str(video_path)
        except Exception as e:
            log.warning(f"Video engine not available, simulating: {e}")
            # Simulate output path
            video_path_str = str(self.output_dir / f"{config.id}_{int(time.time())}.mp4")
        
        generation_time = time.time() - start_time
        predicted_score = self._predict_variant_score(config, topic)
        
        log.info(f"✅ Variant {config.name} completed in {generation_time:.1f}s (Score: {predicted_score:.1f})")
        
        return GeneratedVariant(
            id=config.id,
            config=config,
            video_path=video_path_str,
            hook_text=hook_text,
            predicted_score=predicted_score,
            generation_time=generation_time
        )
    
    async def generate_variants(
        self,
        topic: str,
        settings: Optional[Dict[str, Any]] = None,
        variant_configs: Optional[List[VariantConfig]] = None,
        parallel: bool = True
    ) -> ABTestResult:
        """
        Generate multiple video variants for A/B testing.
        
        Args:
            topic: Base video topic
            settings: Base video settings
            variant_configs: Custom variant configurations (uses defaults if None)
            parallel: Whether to generate variants in parallel
            
        Returns:
            ABTestResult with all generated variants
        """
        import time
        start_time = time.time()
        
        configs = variant_configs or self.VARIANT_TEMPLATES
        base_settings = settings or {}
        
        log.info(f"🧪 Generating {len(configs)} variants for: {topic[:50]}...")
        
        if parallel:
            # Generate all variants in parallel
            tasks = [
                self.generate_single_variant(topic, config, base_settings)
                for config in configs
            ]
            variants = await asyncio.gather(*tasks)
        else:
            # Generate sequentially
            variants = []
            for config in configs:
                variant = await self.generate_single_variant(topic, config, base_settings)
                variants.append(variant)
        
        total_time = time.time() - start_time
        
        # Find recommended variant
        best_variant = max(variants, key=lambda v: v.predicted_score)
        
        # Generate recommendation reason
        reason = self._generate_recommendation_reason(best_variant)
        
        result = ABTestResult(
            base_topic=topic,
            variants=list(variants),
            recommended_variant=best_variant.id,
            recommendation_reason=reason,
            total_generation_time=total_time
        )
        
        log.info(
            f"🎯 A/B Test Complete! {len(variants)} variants in {total_time:.1f}s. "
            f"Recommended: {best_variant.config.name}"
        )
        
        return result
    
    def _generate_recommendation_reason(self, variant: GeneratedVariant) -> str:
        """Generate explanation for why variant is recommended"""
        reasons = []
        
        if variant.config.variant_type == VariantType.SHOCK_HOOK:
            reasons.append("Shock hooks typically drive 30% higher click-through rates")
        elif variant.config.variant_type == VariantType.QUESTION_HOOK:
            reasons.append("Questions create curiosity gaps that increase watch time")
        elif variant.config.variant_type == VariantType.STORY_HOOK:
            reasons.append("Story hooks build emotional connection with viewers")
        
        if variant.config.caption_style == "bold":
            reasons.append("Bold captions capture attention in silent scrolling")
        elif variant.config.caption_style == "neon":
            reasons.append("Neon style stands out in feeds")
        
        if variant.config.pacing == "fast":
            reasons.append("Fast pacing maintains attention on short-form platforms")
        
        return " | ".join(reasons) if reasons else "Best combination of engagement signals"
    
    def get_comparison_report(self, result: ABTestResult) -> Dict[str, Any]:
        """Generate a comparison report for variants"""
        return {
            "topic": result.base_topic,
            "total_time": result.total_generation_time,
            "variants": [
                {
                    "id": v.id,
                    "name": v.config.name,
                    "hook": v.hook_text,
                    "predicted_score": v.predicted_score,
                    "style": {
                        "captions": v.config.caption_style,
                        "music": v.config.music_mood,
                        "pacing": v.config.pacing
                    },
                    "video_path": v.video_path
                }
                for v in result.variants
            ],
            "recommendation": {
                "best_variant": result.recommended_variant,
                "reason": result.recommendation_reason
            },
            "testing_tips": [
                "Post each variant to different audience segments",
                "Compare watch time and completion rates",
                "Track comment sentiment for each hook style",
                "Use the winning hook pattern for future content"
            ]
        }
    
    def create_custom_variant(
        self,
        variant_id: str,
        name: str,
        hook_template: str,
        variant_type: VariantType = VariantType.QUESTION_HOOK,
        caption_style: str = "bold",
        music_mood: str = "intense",
        pacing: str = "fast"
    ) -> VariantConfig:
        """Create a custom variant configuration"""
        return VariantConfig(
            id=variant_id,
            name=name,
            variant_type=variant_type,
            hook_template=hook_template,
            caption_style=caption_style,
            music_mood=music_mood,
            thumbnail_style="dramatic_text",
            pacing=pacing
        )


# Convenience functions
async def generate_ab_test(topic: str, **settings) -> ABTestResult:
    """Quick A/B test generation"""
    generator = VideoVariantGenerator()
    return await generator.generate_variants(topic, settings)


def get_variant_templates() -> List[VariantConfig]:
    """Get default variant templates"""
    return VideoVariantGenerator.VARIANT_TEMPLATES.copy()
