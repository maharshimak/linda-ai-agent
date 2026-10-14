"""
Viral Hook Analyzer for MAK AI
Scores video hooks for viral potential and suggests improvements.

Features:
- Hook strength scoring (0-100)
- Pattern detection (shock value, curiosity gap, visual impact)
- AI-powered improvement suggestions
- A/B/C grading system
"""

import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum

log = logging.getLogger("hook_analyzer")


class HookPattern(Enum):
    """Types of viral hook patterns"""
    SHOCK_VALUE = "shock_value"
    CURIOSITY_GAP = "curiosity_gap"
    VISUAL_IMPACT = "visual_impact"
    PATTERN_INTERRUPT = "pattern_interrupt"
    EMOTIONAL_TRIGGER = "emotional_trigger"
    SOCIAL_PROOF = "social_proof"
    URGENCY = "urgency"
    CONTROVERSY = "controversy"


@dataclass
class HookScore:
    """Result of hook analysis"""
    score: float  # 0-100
    grade: str    # A, B, C, D, F
    patterns_found: List[str]
    missing_elements: List[str]
    suggestions: List[str]
    breakdown: Dict[str, float]
    viral_potential: str  # "High", "Medium", "Low"


@dataclass
class SceneData:
    """Data structure for a video scene"""
    narration: str
    visual_prompt: str = ""
    emotion: str = "neutral"
    duration: float = 5.0
    has_human_face: bool = False
    music_intensity: float = 0.5
    colors: List[str] = field(default_factory=list)


class ViralHookAnalyzer:
    """
    Analyze video hooks for viral potential.
    
    Based on research from:
    - TikTok algorithm patterns
    - YouTube Shorts retention data
    - Social media engagement studies
    """
    
    # Hook pattern definitions with keywords and weights
    HOOK_PATTERNS = {
        HookPattern.SHOCK_VALUE: {
            "keywords": [
                "you won't believe", "shocking", "secret", "never", "mind-blowing",
                "incredible", "unbelievable", "insane", "crazy", "wild",
                "exposed", "revealed", "hidden", "banned", "forbidden"
            ],
            "score_weight": 0.20,
            "description": "Shocking or surprising content"
        },
        HookPattern.CURIOSITY_GAP: {
            "keywords": [
                "what happens", "how to", "why", "the truth", "what if",
                "here's why", "the reason", "this is how", "did you know",
                "little known", "most people don't", "they don't want you to"
            ],
            "score_weight": 0.20,
            "description": "Creates curiosity that demands resolution"
        },
        HookPattern.EMOTIONAL_TRIGGER: {
            "keywords": [
                "heartbreaking", "beautiful", "inspiring", "terrifying",
                "amazing", "devastating", "powerful", "moving", "unforgettable",
                "tears", "goosebumps", "speechless", "breathtaking"
            ],
            "score_weight": 0.15,
            "description": "Evokes strong emotional response"
        },
        HookPattern.URGENCY: {
            "keywords": [
                "before it's too late", "now", "immediately", "urgent",
                "breaking", "just happened", "right now", "today",
                "must see", "can't miss", "limited time"
            ],
            "score_weight": 0.10,
            "description": "Creates time pressure"
        },
        HookPattern.SOCIAL_PROOF: {
            "keywords": [
                "millions", "everyone", "viral", "trending", "famous",
                "celebrities", "experts", "scientists", "studies show",
                "research proves", "according to"
            ],
            "score_weight": 0.10,
            "description": "Leverages social validation"
        },
        HookPattern.CONTROVERSY: {
            "keywords": [
                "controversial", "debate", "wrong", "mistake", "lie",
                "myth", "actually", "truth is", "stop believing",
                "wake up", "they're lying"
            ],
            "score_weight": 0.10,
            "description": "Challenges common beliefs"
        }
    }
    
    # Visual impact factors
    VISUAL_FACTORS = {
        "human_face": {
            "weight": 0.15,
            "description": "Human faces increase retention by 38%"
        },
        "bright_colors": {
            "weight": 0.05,
            "description": "Vibrant colors catch scrolling attention"
        },
        "movement": {
            "weight": 0.05,
            "description": "Motion in first frame increases engagement"
        },
        "text_overlay": {
            "weight": 0.05,
            "description": "Text hooks help with muted viewing"
        }
    }
    
    # Audio impact factors
    AUDIO_FACTORS = {
        "high_energy": {
            "threshold": 0.7,
            "weight": 0.10,
            "description": "High-energy audio in first 2 seconds"
        },
        "voice_first": {
            "weight": 0.05,
            "description": "Voice starts immediately (no intro silence)"
        }
    }
    
    # Grade thresholds
    GRADE_THRESHOLDS = {
        "A+": 95, "A": 85, "A-": 80,
        "B+": 75, "B": 65, "B-": 60,
        "C+": 55, "C": 45, "C-": 40,
        "D": 30, "F": 0
    }
    
    def __init__(self):
        """Initialize the hook analyzer"""
        log.info("🎯 Hook Analyzer initialized")
    
    def analyze_hook(self, first_scene: SceneData) -> HookScore:
        """
        Analyze the first scene/hook for viral potential.
        
        Args:
            first_scene: The first scene of the video with narration and metadata
            
        Returns:
            HookScore with detailed breakdown and suggestions
        """
        breakdown = {}
        patterns_found = []
        missing_elements = []
        
        narration = first_scene.narration.lower()
        
        # 1. Text Pattern Analysis (60% of score)
        text_score = 0.0
        for pattern, config in self.HOOK_PATTERNS.items():
            keywords = config["keywords"]
            weight = config["score_weight"]
            
            matches = sum(1 for kw in keywords if kw in narration)
            if matches > 0:
                pattern_score = min(matches / 3, 1.0) * weight * 100
                text_score += pattern_score
                patterns_found.append(f"✅ {pattern.value.replace('_', ' ').title()}")
                breakdown[pattern.value] = pattern_score
            else:
                missing_elements.append(config["description"])
        
        # 2. Visual Impact Analysis (20% of score)
        visual_score = 0.0
        
        if first_scene.has_human_face:
            face_score = self.VISUAL_FACTORS["human_face"]["weight"] * 100
            visual_score += face_score
            patterns_found.append("✅ Human face detected (increases retention)")
            breakdown["human_face"] = face_score
        else:
            missing_elements.append("Consider adding a human face in the first frame")
        
        # Check for bright colors
        if first_scene.colors:
            bright_colors = self._detect_bright_colors(first_scene.colors)
            if bright_colors:
                color_score = self.VISUAL_FACTORS["bright_colors"]["weight"] * 100
                visual_score += color_score
                patterns_found.append("✅ Vibrant colors detected")
                breakdown["bright_colors"] = color_score
        
        # Check visual prompt for motion keywords
        if any(word in first_scene.visual_prompt.lower() for word in 
               ["moving", "action", "dynamic", "motion", "running", "flying"]):
            motion_score = self.VISUAL_FACTORS["movement"]["weight"] * 100
            visual_score += motion_score
            patterns_found.append("✅ Motion/action in visuals")
            breakdown["movement"] = motion_score
        
        # 3. Audio Impact Analysis (15% of score)
        audio_score = 0.0
        
        if first_scene.music_intensity >= self.AUDIO_FACTORS["high_energy"]["threshold"]:
            energy_score = self.AUDIO_FACTORS["high_energy"]["weight"] * 100
            audio_score += energy_score
            patterns_found.append("✅ High-energy audio")
            breakdown["high_energy_audio"] = energy_score
        else:
            missing_elements.append("Consider higher-energy audio in opening")
        
        # Check if narration starts immediately (short scene = immediate hook)
        if first_scene.duration <= 5.0 and len(first_scene.narration) > 10:
            voice_score = self.AUDIO_FACTORS["voice_first"]["weight"] * 100
            audio_score += voice_score
            patterns_found.append("✅ Voice starts immediately")
            breakdown["voice_first"] = voice_score
        
        # 4. Emotion Analysis (5% bonus)
        emotion_score = 0.0
        strong_emotions = ["epic", "intense", "emotional", "mysterious", "dramatic"]
        if first_scene.emotion.lower() in strong_emotions:
            emotion_score = 5.0
            patterns_found.append(f"✅ Strong emotion: {first_scene.emotion}")
            breakdown["emotion_strength"] = emotion_score
        
        # Calculate total score
        total_score = min(text_score + visual_score + audio_score + emotion_score, 100)
        
        # Determine grade
        grade = self._calculate_grade(total_score)
        
        # Determine viral potential
        viral_potential = self._calculate_viral_potential(total_score, patterns_found)
        
        # Generate specific suggestions
        suggestions = self._generate_suggestions(
            total_score, narration, first_scene, missing_elements
        )
        
        log.info(f"🎯 Hook Score: {total_score:.1f}/100 (Grade: {grade})")
        
        return HookScore(
            score=round(total_score, 1),
            grade=grade,
            patterns_found=patterns_found,
            missing_elements=missing_elements[:5],  # Top 5 missing
            suggestions=suggestions,
            breakdown=breakdown,
            viral_potential=viral_potential
        )
    
    def _detect_bright_colors(self, colors: List[str]) -> bool:
        """Check if colors are bright/vibrant"""
        bright_indicators = [
            "#ff", "#00ff", "#ffff", "bright", "vivid", "neon",
            "yellow", "orange", "red", "pink", "cyan", "lime"
        ]
        
        for color in colors:
            color_lower = color.lower()
            if any(indicator in color_lower for indicator in bright_indicators):
                return True
        return False
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return "F"
    
    def _calculate_viral_potential(self, score: float, patterns: List[str]) -> str:
        """Determine viral potential category"""
        if score >= 80 and len(patterns) >= 5:
            return "🔥 Very High"
        elif score >= 60 and len(patterns) >= 3:
            return "📈 High"
        elif score >= 40:
            return "📊 Medium"
        else:
            return "📉 Low"
    
    def _generate_suggestions(
        self,
        score: float,
        narration: str,
        scene: SceneData,
        missing_elements: List[str]
    ) -> List[str]:
        """Generate specific improvement suggestions"""
        suggestions = []
        
        # General score-based suggestions
        if score < 40:
            suggestions.append(
                "🎯 Start with a question or shocking statement to grab attention"
            )
            suggestions.append(
                "🎨 Use bright, contrasting colors in your first frame"
            )
        
        if score < 60:
            suggestions.append(
                "⚡ Add high-energy music in the first 2 seconds"
            )
        
        # Specific pattern suggestions
        if "curiosity_gap" not in str(missing_elements).lower() and \
           not any("what" in narration or "how" in narration or "why" in narration):
            suggestions.append(
                "❓ Try starting with 'What if...', 'Here's why...', or 'Did you know...'"
            )
        
        if not scene.has_human_face:
            suggestions.append(
                "👤 Include a human face within the first frame (increases retention 38%)"
            )
        
        # Hook structure suggestions
        if len(narration.split()) < 5:
            suggestions.append(
                "📝 Your opening line is too short. Aim for 8-15 words for optimal hook"
            )
        
        if len(narration.split()) > 30:
            suggestions.append(
                "✂️ Your opening is too long. Cut to the most impactful 10-15 words"
            )
        
        # Advanced suggestions for good scores
        if score >= 70:
            suggestions.append(
                "🎬 Great foundation! Test 2-3 variants of your hook for optimal performance"
            )
        
        if score >= 85:
            suggestions.append(
                "🌟 Excellent hook! Consider A/B testing different visual styles"
            )
        
        # Platform-specific suggestions
        suggestions.append(
            "📱 Tip: Add text overlay of your hook for muted viewers (85% watch without sound)"
        )
        
        return suggestions[:6]  # Return top 6 suggestions
    
    def analyze_script_hooks(self, scenes: List[SceneData]) -> Dict[str, Any]:
        """
        Analyze all potential hooks in a script (first 3 scenes).
        
        Returns analysis of each potential hook point and recommendations
        for the strongest opening.
        """
        results = []
        
        for i, scene in enumerate(scenes[:3]):
            score = self.analyze_hook(scene)
            results.append({
                "position": i + 1,
                "narration_preview": scene.narration[:100] + "..." if len(scene.narration) > 100 else scene.narration,
                "score": score.score,
                "grade": score.grade,
                "viral_potential": score.viral_potential
            })
        
        # Find best hook position
        best = max(results, key=lambda x: x["score"])
        
        return {
            "hook_analysis": results,
            "recommended_start": best["position"],
            "recommendation": f"Scene {best['position']} has the strongest hook (Score: {best['score']})"
        }
    
    def generate_improved_hook(self, original: str, target_score: int = 80) -> str:
        """
        Use AI to generate an improved version of a hook.
        This is a template - actual AI integration would use model_router.
        """
        improvements = []
        original_lower = original.lower()
        
        # Add curiosity gap if missing
        if not any(phrase in original_lower for phrase in ["what", "how", "why", "here's"]):
            improvements.append("Here's what nobody tells you about")
        
        # Add urgency if missing
        if not any(phrase in original_lower for phrase in ["now", "today", "must"]):
            improvements.append("(that you need to know right now)")
        
        # This would be enhanced with actual AI call
        return f"Suggested hook: {' '.join(improvements)} {original[:50]}..."


# Convenience functions
def analyze_hook(narration: str, **kwargs) -> HookScore:
    """Quick hook analysis from just narration text"""
    scene = SceneData(narration=narration, **kwargs)
    analyzer = ViralHookAnalyzer()
    return analyzer.analyze_hook(scene)


def get_hook_score(first_scene_narration: str) -> float:
    """Get just the numeric score for a hook"""
    return analyze_hook(first_scene_narration).score


def is_viral_hook(narration: str, threshold: float = 70.0) -> bool:
    """Quick check if a hook meets viral threshold"""
    return get_hook_score(narration) >= threshold
